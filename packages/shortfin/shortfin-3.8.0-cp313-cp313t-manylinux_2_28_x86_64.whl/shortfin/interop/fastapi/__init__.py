# Copyright 2024 Advanced Micro Devices, Inc.
#
# Licensed under the Apache License v2.0 with LLVM Exceptions.
# See https://llvm.org/LICENSE.txt for license information.
# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception

import asyncio
import logging
import threading

from shortfin.support.deps import ShortfinDepNotFoundError
from shortfin.support.responder import AbstractResponder, ResponderErrorCodes
from shortfin.support.status_tracker import AbstractStatusTracker

try:
    from fastapi import status
    from fastapi import Request, Response
    from fastapi.responses import StreamingResponse, JSONResponse
except ModuleNotFoundError as e:
    raise ShortfinDepNotFoundError(__name__, "fastapi") from e


__all__ = [
    "FastAPIResponder",
]

logger = logging.getLogger(__name__)

_fastapi_response_map = {
    ResponderErrorCodes.INVALID_REQUEST_ARGS: status.HTTP_400_BAD_REQUEST,
    ResponderErrorCodes.QUEUE_FULL: status.HTTP_503_SERVICE_UNAVAILABLE,
    ResponderErrorCodes.KVCACHE_PAGES_FULL: status.HTTP_503_SERVICE_UNAVAILABLE,
    ResponderErrorCodes.CANCELLED: 499,  # NIGINX code for Client Closed Request
}


class RequestStatusTracker(AbstractStatusTracker):
    def __init__(self, request: Request):
        super().__init__()
        self._request = request
        self._is_disconnected = False
        self._task = self._loop.create_task(self._monitor_disconnection())
        self._cancellable = []
        self._lock = threading.Lock()

    def close(self):
        if self._task is not None:
            self._task.cancel()

    def add_cancellable(self, cancellable):
        with self._lock as _:
            if self._is_disconnected:
                cancellable.cancel()
                return
            self._cancellable.append(cancellable)

    async def _monitor_disconnection(self):
        while not self._is_disconnected:
            if await self._request.is_disconnected():
                with self._lock as _:
                    self._is_disconnected = True
                    for cancellable in self._cancellable:
                        cancellable.cancel()
                    self._cancellable = []
                    return
            await asyncio.sleep(1)


class FastAPIResponder(AbstractResponder):
    """Bridge between FastAPI and shortfin that can be used to send out of band
    responses back to a waiting FastAPI async request.

    This isn't really shortfin specific and can be used to bridge to any non
    webserver owned loop.

    It is typically used by putting it in a Message that is sent to some processing
    queue. Then return/awaiting it from an API callback. Example:

    ```
    @app.get("/predict")
    async def predict(value: int, request: Request):
        message = RequestMessage(value, FastAPIResponder(request))
        system.request_writer(message)
        return await message.responder.response
    ```

    See: examples/python/fastapi/server.py
    """

    def __init__(self, request: Request):
        super().__init__()
        self.request = request
        # Capture the running loop so that we can send responses back.
        self._loop = asyncio.get_running_loop()
        self.response = asyncio.Future(loop=self._loop)
        self.responded = False
        self._streaming_queue: asyncio.Queue | None = None
        self._status_tracker = RequestStatusTracker(request)

    def close(self):
        self._status_tracker.close()

    def is_disconnected(self) -> bool:
        return self._status_tracker.is_disconnected()

    def get_status_tracker(self) -> RequestStatusTracker:
        return self._status_tracker

    def ensure_response(self):
        """Called as part of some finally type block to ensure responses are made."""
        if self.responded:
            if self._streaming_queue:
                logging.error("Streaming response not finished. Force finishing.")
                self.stream_part(None)
        else:
            logging.error("One-shot response not finished. Responding with error.")
            self.send_response(Response(status_code=500))

    def send_error(
        self, error_message: str, code: ResponderErrorCodes, extra_fields: dict
    ):
        """Sends an error response back for the transaction.

        This is intended to sending error responses back to the user
        """
        status_code = _fastapi_response_map[code]
        error_response = JSONResponse(
            status_code=status_code,
            content={"error": error_message, "code": code.value, **extra_fields},
        )
        self.send_response(error_response)
        self.ensure_response()

    def send_response(self, response: Response | bytes):
        """Sends a response back for this transaction.

        This is intended for sending single part responses back. See
        stream_start() for sending back a streaming, multi-part response.
        """
        assert not self.responded, "Response already sent"
        if self._loop.is_closed():
            raise IOError("Web server is shut down")
        self.responded = True
        if not isinstance(response, Response):
            response = Response(response)
        self._loop.call_soon_threadsafe(self.response.set_result, response)

    def stream_start(self, **kwargs):
        """Starts a streaming response, passing the given kwargs to the
        fastapi.responses.StreamingResponse constructor.

        This is appropriate to use for generating a sparse response stream as is
        typical of chat apps. As it will hop threads for each part, other means should
        be used for bulk transfer (i.e. by scheduling on the webserver loop
        directly).
        """
        assert not self.responded, "Response already sent"
        if self._loop.is_closed():
            raise IOError("Web server is shut down")
        self.responded = True
        self._streaming_queue = asyncio.Queue()

        async def gen(request, streaming_queue):
            while True:
                if self._status_tracker.is_disconnected():
                    break
                part = await streaming_queue.get()
                if part is None:
                    break
                yield part

        def start(request, streaming_queue, response_future):
            response = StreamingResponse(gen(request, streaming_queue), **kwargs)
            response_future.set_result(response)

        self._loop.call_soon_threadsafe(
            start, self.request, self._streaming_queue, self.response
        )

    def stream_part(self, content: bytes | None):
        """Streams content to a response started with stream_start().

        Streaming must be ended by sending None.
        """
        assert self._streaming_queue is not None, "stream_start() not called"
        if self._loop.is_closed():
            raise IOError("Web server is shut down")
        self._loop.call_soon_threadsafe(self._streaming_queue.put_nowait, content)
        if content is None:
            self._streaming_queue = None
