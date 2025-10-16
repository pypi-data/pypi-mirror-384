from pydantic import (
    BaseModel,
    Field,
    NonNegativeInt,
    model_serializer,
    model_validator,
    field_validator,
    Discriminator,
    Tag,
    TypeAdapter,
)
from typing import Any, Annotated, Literal
from .data_items import DataItemType, _BinaryDType


class Dataset(BaseModel):
    type: Literal["dataset"] = "dataset"
    attributes: dict[str, DataItemType] = Field(default_factory=dict)
    value: DataItemType

    @model_serializer(mode="wrap")
    def serialize_value_only(self, _next):
        if self.attributes:
            return _next(self)
        else:
            return _next(self)["value"]

    @model_validator(mode="before")
    @classmethod
    def validate_value_only(cls, data: Any) -> Any:
        if isinstance(data, dict) and data.get("type", "dataset") == "dataset":
            return data
        else:
            return {"type": "dataset", "value": data}


class ExternalBinaryFile(BaseModel):
    name: str
    offset: NonNegativeInt
    size: NonNegativeInt | None = None  # None means H5F_UNLIMITED


class ExternalBinaryDataset(BaseModel):
    type: Literal["external_binary_dataset"] = "external_binary_dataset"
    attributes: dict[str, DataItemType] = Field(default_factory=dict)
    dtype: _BinaryDType
    shape: list[int]
    files: list[ExternalBinaryFile] = Field(min_length=1)

    @model_serializer(mode="wrap")
    def serialize(self, _next):
        serialized = _next(self)
        if not self.attributes:
            serialized.pop("attributes", None)
        return serialized


class SpaceSelection(BaseModel):
    start: list[NonNegativeInt]
    stride: list[NonNegativeInt] | None = None
    count: list[NonNegativeInt]
    block: list[NonNegativeInt] | None = None

    @field_validator("stride", mode="after")
    @classmethod
    def hide_all_ones_stride(cls, value):
        if value is None or all(x == 1 for x in value):
            return None
        else:
            return value

    @field_validator("block", mode="after")
    @classmethod
    def hide_all_ones_block(cls, value):
        if value is None or all(x == 1 for x in value):
            return None
        else:
            return value


class VirtualSource(BaseModel):
    vspace: SpaceSelection
    src_file: str
    src_dataset: str
    src_space: SpaceSelection


class VirtualDataset(BaseModel):
    type: Literal["virtual_dataset"] = "virtual_dataset"
    attributes: dict[str, DataItemType] = Field(default_factory=dict)
    dtype: _BinaryDType
    shape: list[int]
    virtual_sources: list[VirtualSource] = Field(min_length=1)

    @model_serializer(mode="wrap")
    def serialize(self, _next):
        serialized = _next(self)
        if not self.attributes:
            serialized.pop("attributes", None)
        return serialized


class SoftLink(BaseModel):
    type: Literal["soft_link"] = "soft_link"
    target_path: str


class ExternalLink(BaseModel):
    type: Literal["external_link"] = "external_link"
    target_file: str
    target_path: str


def get_discriminator_value(v: Any) -> str:
    h5_type = {
        "group",
        "dataset",
        "external_binary_dataset",
        "soft_link",
        "external_link",
        "virtual_dataset",
    }
    # A dataset can be represented by its value only, therefore data_item types
    # such as "inline" or "stream" may be end up here. Because of this we check
    # wether or not type is an h5_type, otherwise it is a dataset.
    if isinstance(v, dict):
        type = v.get("type")
        return type if type in h5_type else "dataset"
    elif isinstance(v, BaseModel):
        type = getattr(v, "type", None)
        return type if type in h5_type else "dataset"
    else:
        return "dataset"


HDF5ItemType = Annotated[
    (
        Annotated["Group", Tag("group")]
        | Annotated[Dataset, Tag("dataset")]
        | Annotated[ExternalBinaryDataset, Tag("external_binary_dataset")]
        | Annotated[SoftLink, Tag("soft_link")]
        | Annotated[ExternalLink, Tag("external_link")]
        | Annotated[VirtualDataset, Tag("virtual_dataset")]
    ),
    Discriminator(get_discriminator_value),
]


class Group(BaseModel):
    type: Literal["group"] = "group"
    attributes: dict[str, DataItemType] = Field(default_factory=dict)
    children: dict[str, HDF5ItemType] = Field(default_factory=dict)

    @model_serializer(mode="wrap")
    def skip_empty_fields(self, _next):
        serialized = _next(self)
        if not self.attributes:
            serialized.pop("attributes", None)
        if not self.children:
            serialized.pop("children", None)
        return serialized


HDF5Item = TypeAdapter(HDF5ItemType)
