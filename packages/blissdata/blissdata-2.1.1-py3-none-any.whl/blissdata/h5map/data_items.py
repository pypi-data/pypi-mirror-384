import numpy as np
from typing import Any, Annotated, Literal
from pydantic import (
    BaseModel,
    RootModel,
    Base64Bytes,
    Field,
    field_validator,
    model_serializer,
    Discriminator,
    Tag,
    TypeAdapter,
)
from numpydantic import NDArray


class InlineRaw(RootModel):
    """Literal values to be embedded into JSON directly (no 'type' field).
    Accepts scalars or arrays of any shape with types that can be coerced using
    the following table:
     -------------- --------- ---------------
    | Python input |   Json  | Python output |
     -------------- --------- ---------------
    | any integer  | integer | np.int64      |
    | any floating | decimal | np.float64    |
    | any boolean  | boolean | np.bool_      |
    | any string   | string  | np.str_       |
     -------------- --------- ---------------
    For mixed types arrays, coercion follows this hierarchy (lowest to highest):
        bool → int64 → float64 → str
    Example:
        [True, 123, 1.23] → [1.0, 123.0, 1.23]

    Non-finite values (nan, -inf, inf) will be refused, one should use Inline
    model instead.
    """

    root: NDArray[Any, np.bool_ | np.str_ | np.int64 | np.float64]

    @field_validator("root", mode="before")
    @classmethod
    def coerce_numbers(cls, value):
        array = np.asarray(value)
        if np.issubdtype(array.dtype, np.floating):
            if not np.isfinite(value).all():
                raise ValueError("non-finite values (nan, -inf, inf) are not allowed.")
            array = array.astype(np.float64)
        elif np.issubdtype(array.dtype, np.integer):
            array = array.astype(np.int64)
        return array

    @model_serializer(when_used="json", mode="wrap")
    def fix_empty_string_serialization(self, nxt, info):
        if np.issubdtype(self.root.dtype, np.str_) and not self.root.shape:
            return str(self.root)
        else:
            return nxt(self, info)

    def __eq__(self, other):
        if other.__class__ is self.__class__:
            return np.array_equal(self.root, other.root)
        return NotImplemented

    def decode(self):
        value = self.model_dump()
        if value.dtype.kind in "UT":
            return value.tolist()
        else:
            return value


# Numpy dtype names (uint8, float16, complex128...), but limited to numbers and
# booleans.
_DType = Annotated[
    str,
    Field(
        pattern=r"^(bool|(int|uint)(8|16|32|64)|float(16|32|64|128)|complex(64|128|256))$"
    ),
]


# Numpy's array interface protocol type strings, but limited to numbers
# and booleans. This notation contains both dtype and endianness.
# See Numpy array interface protocol definition here:
#     https://numpy.org/doc/stable/reference/arrays.interface.html
_BinaryDType = Annotated[
    str, Field(pattern=r"^(\|?[iub]1|[><]([iuf][248]|[fc](8|16)|c32))$")
]


class _InlineValue(RootModel):
    """Value for the 'Inline' model, can be any JSON value other than a mapping
    or null value. Different from InlineRaw because it can be heterogeneous and
    non-finite values (nan, inf, -inf) are coerced into string.
    """

    root: str | bool | int | float | list["_InlineValue"]

    @field_validator("root", mode="before")
    @classmethod
    def coerce_numpy_values(cls, value):
        def coerce_single(item):
            if not np.issubdtype(type(item), np.number):
                # str | bool
                return item
            elif not np.isfinite(item) or np.issubdtype(type(item), np.complexfloating):
                # nan | inf | -inf | complex
                return str(item)
            elif isinstance(item, np.generic):
                # numpy scalar
                return item.item()
            else:
                # python scalar
                return item

        def coerce_all(value):
            if isinstance(value, list):
                return [coerce_all(i) for i in value]
            elif isinstance(value, np.ndarray) and value.ndim > 1:
                return value
            elif isinstance(value, np.ndarray) and value.ndim > 0:
                return [coerce_all(value[i]) for i in range(value.shape[0])]
            else:
                return coerce_single(value)

        return coerce_all(value)


class Inline(BaseModel):
    """Explicitly typed JSON value to produce specific HDF5 type (int8, float32, etc).
    Can be used to transmit string as float like "nan" or "inf".
    """

    type: Literal["inline"] = "inline"
    dtype: _DType
    value: _InlineValue

    def decode(self):
        return np.array(self.value.model_dump(), dtype=self.dtype)


class InlineBase64(BaseModel):
    """Base64 encoded binary value."""

    type: Literal["inline_b64"] = "inline_b64"
    dtype: _BinaryDType
    shape: list[int] | None = None
    value: Base64Bytes

    def decode(self):
        value = np.frombuffer(self.value, dtype=self.dtype)
        if self.shape is not None:
            return value.reshape(self.shape)
        else:
            return value


class Stream(BaseModel):
    type: Literal["stream"] = "stream"
    stream: str

    def decode(self):
        raise TypeError("Stream model is just a reference, can't use decode()")


def get_discriminator_value(v: Any) -> str:
    if isinstance(v, dict):
        return v.get("type")
    if issubclass(type(v), BaseModel):
        return getattr(v, "type", "raw")
    return "raw"


DataItemType = Annotated[
    (
        Annotated[Inline, Tag("inline")]
        | Annotated[InlineBase64, Tag("inline_b64")]
        | Annotated[Stream, Tag("stream")]
        | Annotated[InlineRaw, Tag("raw")]
    ),
    Discriminator(get_discriminator_value),
]

DataItem = TypeAdapter(DataItemType)
