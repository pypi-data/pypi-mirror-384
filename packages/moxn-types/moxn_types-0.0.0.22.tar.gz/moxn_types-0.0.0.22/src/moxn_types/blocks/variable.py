from enum import Enum
from typing import Annotated, Literal

from pydantic import ConfigDict, Field

from moxn_types.blocks.base import BaseContent, BlockType


# 1. Enums
# --------------------------------------------------------------------------- #
class VariableFormat(str, Enum):
    INLINE = "inline"
    BLOCK = "block"


class VariableType(str, Enum):
    """Format of a variable."""

    PRIMITIVE = "primitive"
    IMAGE = "image"
    FILE = "file"


# --------------------------------------------------------------------------- #
# 2. Base Variable class
# --------------------------------------------------------------------------- #


class TextVariableModel(BaseContent):
    """A variable that represents text content."""

    block_type: Literal[BlockType.VARIABLE] = Field(
        default=BlockType.VARIABLE, alias="blockType"
    )
    name: str
    variable_type: Literal[VariableType.PRIMITIVE] = Field(
        default=VariableType.PRIMITIVE, alias="variableType"
    )
    format: VariableFormat
    description: str = ""
    required: bool = True
    default_value: str | None = Field(None, alias="defaultValue")

    model_config = ConfigDict(populate_by_name=True)


class ImageVariableModel(BaseContent):
    """A variable that represents image content."""

    block_type: Literal[BlockType.VARIABLE] = Field(
        default=BlockType.VARIABLE, alias="blockType"
    )
    name: str
    variable_type: Literal[VariableType.IMAGE] = Field(
        default=VariableType.IMAGE, alias="variableType"
    )
    format: VariableFormat
    description: str = ""
    required: bool = True

    model_config = ConfigDict(populate_by_name=True)


class FileVariableModel(BaseContent):
    """A variable that represents document content (PDF)."""

    block_type: Literal[BlockType.VARIABLE] = Field(
        default=BlockType.VARIABLE, alias="blockType"
    )
    name: str
    variable_type: Literal[VariableType.FILE] = Field(
        default=VariableType.FILE, alias="variableType"
    )
    format: VariableFormat
    description: str = ""
    required: bool = True

    model_config = ConfigDict(populate_by_name=True)


VariableContentModel = Annotated[
    TextVariableModel | ImageVariableModel | FileVariableModel,
    Field(discriminator="variable_type"),
]
