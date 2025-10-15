from collections.abc import Sequence
import types
from typing import overload

import _shortfin_default.lib


class DType:
    @property
    def name(self) -> str: ...

    @property
    def is_boolean(self) -> bool: ...

    @property
    def is_integer(self) -> bool: ...

    @property
    def is_float(self) -> bool: ...

    @property
    def is_complex(self) -> bool: ...

    @property
    def bit_count(self) -> int: ...

    @property
    def is_byte_aligned(self) -> bool: ...

    @property
    def dense_byte_count(self) -> int: ...

    def is_integer_bitwidth(self, arg: int, /) -> bool: ...

    def compute_dense_nd_size(self, arg: Sequence[int], /) -> int: ...

    def __eq__(self, arg: DType, /) -> bool: ...

    def __repr__(self) -> str: ...

class RandomGenerator:
    def __init__(self, seed: int | None = None) -> None:
        """
        Returns an object for generating random numbers.

          Every instance is self contained and does not share state with others.

          Args:
            seed: Optional seed for the generator. Not setting a seed will cause an
              implementation defined value to be used, which may in fact be a completely
              fixed number.
        """

def add(lhs: object, rhs: object, *, out: device_array | None = None, device_visible: bool = False) -> device_array: ...

def argmax(input: device_array, axis: int = -1, out: device_array | None = None, *, keepdims: bool = False, device_visible: bool = False) -> device_array:
    """
    Returns the indices of the maximum values along an axis.

    Implemented for dtypes: float16, float32.

    Args:
      input: An input array.
      axis: Axis along which to sort. Defaults to the last axis (note that the
        numpy default is into the flattened array, which we do not support).
      keepdims: Whether to preserve the sort axis. If true, this will become a unit
        dim. If false, it will be removed.
      out: Array to write into. If specified, it must have an expected shape and
        int64 dtype.
      device_visible: Whether to make the result array visible to devices. Defaults to
        False.

    Returns:
      A device_array of dtype=int64, allocated on the host and not visible to the device.
    """

def argpartition(input: device_array, k: int, axis: int = -1, out: device_array | None = None, device_visible: bool = False) -> device_array:
    """
    Partitions the array `input` along the specified `axis` so that certain
        elements occupy the first or last positions depending on `k`.
        Similar to `numpy.argpartition`:

        - If `k` is positive, the first `k` positions along `axis` are the indices of the
          `k` smallest values, while all larger values occupy positions to the right of `k`.
        - If `k` is negative, it counts from the end. For example, `k = -3` means the last
          3 positions along `axis` are the indices of the 3 largest values, while all smaller
          values occupy positions to the left of that boundary.

    Implemented for dtypes: float16, float32.

    Args:
      input: An input array.
      k: The number of maximum values to partition.
      axis: Axis along which to sort. Defaults to the last axis (note that the
        numpy default is into the flattened array, which we do not support).
      out: Array to write into. If specified, it must have an expected shape and
        int64 dtype.
      device_visible: Whether to make the result array visible to devices. Defaults to
        False.

    Returns:
      A device_array of dtype=int64, allocated on the host and not visible to the device.
    """

class base_array:
    @property
    def dtype(self) -> DType: ...

    @property
    def shape(self) -> list[int]: ...

bfloat16: DType = ...

bool8: DType = ...

def ceil(input: device_array, *, dtype: DType | None = None, out: device_array | None = None, device_visible: bool = False) -> device_array:
    """
    Does an elementwise conversion from one dtype to another.

    The same behavior exists for several conversion ops:

    * `convert` : element-wise conversion like a static cast.
    * `round` : element-wise nearest integer to the input, rounding halfway cases
      away from zero.
    * `ceil` : element-wise smallest integer value not less than the input.
    * `floor` : element-wise smallest integer value not greater than the input.
    * `trunc` : element-wise nearest integer not greater in magnitude than the input.

    For nearest-integer conversions (round, ceil, floor, trunc), the input dtype
    must be a floating point array, and the output must be a byte-aligned integer
    type between 8 and 32 bits.

    Args:
      input: An input array of a floating point dtype.
      dtype: If given, then this is the explicit output dtype.
      out: If given, then the results are written to this array. This implies the
        output dtype.
      device_visible: Whether to make the result array visible to devices. Defaults to
        False.

    Returns:
      A device_array of the requested dtype, or the input dtype if not specified.
    """

complex128: DType = ...

complex64: DType = ...

def convert(input: device_array, *, dtype: DType | None = None, out: device_array | None = None, device_visible: bool = False) -> device_array:
    """
    Does an elementwise conversion from one dtype to another.

    The same behavior exists for several conversion ops:

    * `convert` : element-wise conversion like a static cast.
    * `round` : element-wise nearest integer to the input, rounding halfway cases
      away from zero.
    * `ceil` : element-wise smallest integer value not less than the input.
    * `floor` : element-wise smallest integer value not greater than the input.
    * `trunc` : element-wise nearest integer not greater in magnitude than the input.

    For nearest-integer conversions (round, ceil, floor, trunc), the input dtype
    must be a floating point array, and the output must be a byte-aligned integer
    type between 8 and 32 bits.

    Args:
      input: An input array of a floating point dtype.
      dtype: If given, then this is the explicit output dtype.
      out: If given, then the results are written to this array. This implies the
        output dtype.
      device_visible: Whether to make the result array visible to devices. Defaults to
        False.

    Returns:
      A device_array of the requested dtype, or the input dtype if not specified.
    """

class device_array(base_array):
    def __init__(*args, **kwargs) -> None: ...

    def __sfinv_marshal__(self, arg0: types.CapsuleType, arg1: int, /) -> None: ...

    @staticmethod
    def for_device(device: _shortfin_default.lib.local.ScopedDevice, shape: Sequence[int], dtype: DType) -> object: ...

    @staticmethod
    def for_host(device: _shortfin_default.lib.local.ScopedDevice, shape: Sequence[int], dtype: DType) -> object: ...

    def for_transfer(self) -> object: ...

    @property
    def device(self) -> _shortfin_default.lib.local.ScopedDevice: ...

    @property
    def storage(self) -> storage: ...

    def fill(self, pattern: object) -> None:
        """
        Fill an array with a value.

        Note that `fill` is asynchronous and may not be visible immediately. For immediate
        manipulation of host visible arrays, assign to the `items` property or use the
        `map(discard=True)` to get a mapping object which can be used to directly
        update the contents.

        Equivalent to `array.storage.fill(pattern)`.
        """

    def copy_from(self, source_array: device_array) -> None:
        """
        Copy contents from a source array to this array.

        Equivalent to `dest_array.storage.copy_from(source_array.storage)`.
        """

    def copy_to(self, dest_array: device_array) -> None:
        """
        Copy contents this array to a destination array.

        Equivalent to `dest_array.storage.copy_from(source_array.storage)`.
        """

    def view(self, *args) -> device_array:
        """
        Create a view of an array.

        Either integer indices or slices can be passed to the view() method to create
        an aliased device_array that shares a subset of the storage. Only view()
        organizations that result in a row-major, dense array are currently supported.
        """

    def map(self, *, read: bool = False, write: bool = False, discard: bool = False) -> object:
        """
        Create a typed mapping of the buffer contents in host memory.

        Support kwargs of:

        | read: Enables read access to the mapped memory.
        | write: Enables write access to the mapped memory and will flush upon close
          (for non-unified memory systems).
        | discard: Indicates that the entire memory map should be treated as if it will
          be overwritten. Initial contents will be undefined. Implies `write=True`.

        Mapping memory for access from the host requires a compatible buffer that has
        been created with host visibility (which includes host buffers).

        The returned mapping object is a context manager that will close/flush on
        exit. Alternatively, the `close()` method can be invoked explicitly.

        See also `storage.map()` which functions similarly but does not allow access
        to dtype specific functionality.
        """

    @property
    def items(self) -> object:
        """Convenience shorthand for map(...).items"""

    @items.setter
    def items(self, arg: object, /) -> None: ...

    @property
    def __array_interface__(self) -> dict: ...

    def __repr__(self) -> str: ...

    def __str__(self) -> str: ...

class disable_barrier:
    def __init__(self, delegate: object) -> None:
        """Construct a disable_barrier by passing a Python delegate object."""

    def __sfinv_marshal__(self, inv_capsule: types.CapsuleType, ignored_resource_barrier: object) -> None:
        """
        Forward `__sfinv_marshal__` to `delegate`, forcing the barrier argument to ProgramResourceBarrier::DISABLE.
        """

    def delegate(self) -> object:
        """Returns the internal device_array delegate."""

def divide(lhs: object, rhs: object, *, out: device_array | None = None, device_visible: bool = False) -> device_array: ...

def exp(input: device_array, out: device_array | None = None, device_visible: bool = False) -> device_array:
    """
    Return the exp of the `input` array.

    Implemented for dtypes: float16, float32.

    Args:
      input: An input array.
      out: Array to write into. If specified, it must have an expected shape and
        the same dtype as `input`.
      device_visible: Whether to make the result array visible to devices. Defaults to
        False.

    Returns:
      A device_array of dtype=input.dtype(), allocated on the host and not visible to the device.
    """

def fill_randn(out: device_array, generator: RandomGenerator | None = None) -> None:
    """
    Fills an array with numbers sampled from the standard ormal distribution.

    Values are samples with a mean of 0 and standard deviation of 1.

    This operates like torch.randn but only supports in place fills to an existing
    array, deriving shape and dtype from the output array.

    Args:
      out: Output array to fill.
      generator: Uses an explicit generator. If not specified, uses a global
        default.
    """

float16: DType = ...

float32: DType = ...

float64: DType = ...

float8_e4m3fn: DType = ...

float8_e4m3fnuz: DType = ...

def floor(input: device_array, *, dtype: DType | None = None, out: device_array | None = None, device_visible: bool = False) -> device_array:
    """
    Does an elementwise conversion from one dtype to another.

    The same behavior exists for several conversion ops:

    * `convert` : element-wise conversion like a static cast.
    * `round` : element-wise nearest integer to the input, rounding halfway cases
      away from zero.
    * `ceil` : element-wise smallest integer value not less than the input.
    * `floor` : element-wise smallest integer value not greater than the input.
    * `trunc` : element-wise nearest integer not greater in magnitude than the input.

    For nearest-integer conversions (round, ceil, floor, trunc), the input dtype
    must be a floating point array, and the output must be a byte-aligned integer
    type between 8 and 32 bits.

    Args:
      input: An input array of a floating point dtype.
      dtype: If given, then this is the explicit output dtype.
      out: If given, then the results are written to this array. This implies the
        output dtype.
      device_visible: Whether to make the result array visible to devices. Defaults to
        False.

    Returns:
      A device_array of the requested dtype, or the input dtype if not specified.
    """

int16: DType = ...

int32: DType = ...

int4: DType = ...

int64: DType = ...

int8: DType = ...

def log(input: device_array, out: device_array | None = None, device_visible: bool = False) -> device_array:
    """
    Return the log of the `input` array.

    Implemented for dtypes: float16, float32.

    Args:
      input: An input array.
      out: Array to write into. If specified, it must have an expected shape and
        the same dtype as `input`.
      device_visible: Whether to make the result array visible to devices. Defaults to
        False.

    Returns:
      A device_array of dtype=input.dtype(), allocated on the host and not visible to the device.
    """

def log_softmax(input: device_array, axis: int = -1, out: device_array | None = None, device_visible: bool = False) -> device_array:
    """
    Return the log of the softmax of the `input` array. Written to match
        the behavior of `torch.log_softmax`.

    Implemented for dtypes: float16, float32.

    Args:
      input: An input array.
      axis: Axis along which to take log_softmax. Defaults to the last axis.
      out: Array to write into. If specified, it must have an expected shape and
        the same dtype as `input`.
      device_visible: Whether to make the result array visible to devices. Defaults to
        False.

    Returns:
      A device_array of dtype=input.dtype(), allocated on the host and not visible to the device.
    """

class mapping:
    def close(self) -> None: ...

    @property
    def valid(self) -> bool: ...

    def __enter__(self) -> object: ...

    def __exit__(self, exc_type: object | None, exc_value: object | None, exc_tb: object | None) -> None: ...

    @overload
    def fill(self, value: int) -> None:
        """
        Fill the host mapping with a pattern.

        The pattern can either be an object implementing the buffer protocol or a Python
        int/float if the mapping has a dtype. In this case, the numeric value will be
        converted to the appropriate typed pattern. Only dtypes supported by the
        array.array class are supported in this fashion.

        The pattern must evenly divide the mapping.

        Note that like all methods on a mapping, any changes are immediately visible
        (whereas the `fill` method on the array and storage are async operations).
        """

    @overload
    def fill(self, value: float) -> None: ...

    @overload
    def fill(self, buffer: object) -> None: ...

    @property
    def items(self) -> object:
        """
        Access contents as a Python array.

        When reading this attribute, an array.array will be constructed with the
        contents of the mapping. This supports a subset of element types (byte aligned
        integers, floats and doubles) corresponding to Python types.

        On write, the mapping will be written with arbitrary Python types marshaled
        via array.array into its contents.
        """

    @items.setter
    def items(self, arg: object, /) -> None: ...

def multiply(lhs: object, rhs: object, *, out: device_array | None = None, device_visible: bool = False) -> device_array: ...

opaque16: DType = ...

opaque32: DType = ...

opaque64: DType = ...

opaque8: DType = ...

class read_barrier:
    def __init__(self, delegate: object) -> None:
        """Construct a read_barrier by passing a Python delegate object."""

    def __sfinv_marshal__(self, inv_capsule: types.CapsuleType, ignored_resource_barrier: object) -> None:
        """
        Forward `__sfinv_marshal__` to `delegate`, forcing the barrier argument to ProgramResourceBarrier::READ.
        """

    def delegate(self) -> object:
        """Returns the internal device_array delegate."""

def round(input: device_array, *, dtype: DType | None = None, out: device_array | None = None, device_visible: bool = False) -> device_array:
    """
    Does an elementwise conversion from one dtype to another.

    The same behavior exists for several conversion ops:

    * `convert` : element-wise conversion like a static cast.
    * `round` : element-wise nearest integer to the input, rounding halfway cases
      away from zero.
    * `ceil` : element-wise smallest integer value not less than the input.
    * `floor` : element-wise smallest integer value not greater than the input.
    * `trunc` : element-wise nearest integer not greater in magnitude than the input.

    For nearest-integer conversions (round, ceil, floor, trunc), the input dtype
    must be a floating point array, and the output must be a byte-aligned integer
    type between 8 and 32 bits.

    Args:
      input: An input array of a floating point dtype.
      dtype: If given, then this is the explicit output dtype.
      out: If given, then the results are written to this array. This implies the
        output dtype.
      device_visible: Whether to make the result array visible to devices. Defaults to
        False.

    Returns:
      A device_array of the requested dtype, or the input dtype if not specified.
    """

sint16: DType = ...

sint32: DType = ...

sint4: DType = ...

sint64: DType = ...

sint8: DType = ...

def softmax(input: device_array, axis: int = -1, out: device_array | None = None, device_visible: bool = False) -> device_array:
    """
    Return the softmax of the `input` array. Written to match
        the behavior of `torch.softmax`.

    Implemented for dtypes: float16, float32.

    Args:
      input: An input array.
      axis: Axis along which to take softmax. Defaults to the last axis.
      out: Array to write into. If specified, it must have an expected shape and
        the same dtype as `input`.
      device_visible: Whether to make the result array visible to devices. Defaults to
        False.

    Returns:
      A device_array of dtype=input.dtype(), allocated on the host and not visible to the device.
    """

class storage:
    def __sfinv_marshal__(self, arg0: types.CapsuleType, arg1: int, /) -> None: ...

    @staticmethod
    def allocate_host(device: _shortfin_default.lib.local.ScopedDevice, allocation_size: int) -> storage: ...

    @staticmethod
    def allocate_device(device: _shortfin_default.lib.local.ScopedDevice, allocation_size: int) -> storage: ...

    def fill(self, pattern: object) -> None:
        """
        Fill a storage with a value.

        Takes as argument any value that can be interpreted as a buffer with the Python
        buffer protocol of size 1, 2, or 4 bytes. The storage will be filled uniformly
        with the pattern.

        This operation executes asynchronously and the effect will only be visible
        once the execution fiber has been synced to the point of mutation.
        """

    def copy_from(self, source_storage: storage) -> None:
        """
        Copy contents from a source storage to this array.

        This operation executes asynchronously and the effect will only be visible
        once the execution fiber has been synced to the point of mutation.
        """

    def map(self, *, read: bool = False, write: bool = False, discard: bool = False) -> object:
        """
        Create a mapping of the buffer contents in host memory.

        Support kwargs of:

        | read: Enables read access to the mapped memory.
        | write: Enables write access to the mapped memory and will flush upon close
          (for non-unified memory systems).
        | discard: Indicates that the entire memory map should be treated as if it will
          be overwritten. Initial contents will be undefined. Implies `write=True`.

        Mapping memory for access from the host requires a compatible buffer that has
        been created with host visibility (which includes host buffers).

        The returned mapping object is a context manager that will close/flush on
        exit. Alternatively, the `close()` method can be invoked explicitly.

        See also `device_array.map()` which functions similarly but allows some
        additional dtype specific accessors.
        """

    def __eq__(self, arg: storage, /) -> bool: ...

    def __len__(self) -> int: ...

    def __repr__(self) -> str: ...

def subtract(lhs: object, rhs: object, *, out: device_array | None = None, device_visible: bool = False) -> device_array: ...

def transpose(input: device_array, permutation: Sequence[int], out: device_array | None = None, device_visible: bool = False) -> device_array:
    """
    Transposes axes of an array according to a permutation vector.

    Args:
      input: Array to transpose.
      permutation: New sequence of axes. Must have same number of elements as the
        rank of input.
      out: If given, then the results are written to this array.
      device_visible: Whether to make the result array visible to devices. Defaults
        to False.
    """

def trunc(input: device_array, *, dtype: DType | None = None, out: device_array | None = None, device_visible: bool = False) -> device_array:
    """
    Does an elementwise conversion from one dtype to another.

    The same behavior exists for several conversion ops:

    * `convert` : element-wise conversion like a static cast.
    * `round` : element-wise nearest integer to the input, rounding halfway cases
      away from zero.
    * `ceil` : element-wise smallest integer value not less than the input.
    * `floor` : element-wise smallest integer value not greater than the input.
    * `trunc` : element-wise nearest integer not greater in magnitude than the input.

    For nearest-integer conversions (round, ceil, floor, trunc), the input dtype
    must be a floating point array, and the output must be a byte-aligned integer
    type between 8 and 32 bits.

    Args:
      input: An input array of a floating point dtype.
      dtype: If given, then this is the explicit output dtype.
      out: If given, then the results are written to this array. This implies the
        output dtype.
      device_visible: Whether to make the result array visible to devices. Defaults to
        False.

    Returns:
      A device_array of the requested dtype, or the input dtype if not specified.
    """

uint16: DType = ...

uint32: DType = ...

uint4: DType = ...

uint64: DType = ...

uint8: DType = ...

class write_barrier:
    def __init__(self, delegate: object) -> None:
        """Construct a write_barrier by passing a Python delegate object."""

    def __sfinv_marshal__(self, inv_capsule: types.CapsuleType, ignored_resource_barrier: object) -> None:
        """
        Forward `__sfinv_marshal__` to `delegate`, forcing the barrier argument to ProgramResourceBarrier::WRITE.
        """

    def delegate(self) -> object:
        """Returns the internal device_array delegate."""
