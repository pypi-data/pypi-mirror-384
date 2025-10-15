from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from moxn_types.blocks.base import BlockType
from moxn_types.blocks.image import ImageContentFromSourceModel
from moxn_types.blocks.text import TextContentModel

T = TypeVar("T")


class ToolCallModel(BaseModel):
    block_type: Literal[BlockType.TOOL_CALL] = Field(
        default=BlockType.TOOL_CALL, alias="blockType"
    )
    id: str
    arguments: str | dict[str, Any] | None
    name: str

    model_config = ConfigDict(populate_by_name=True)


class ToolResultBase(BaseModel, Generic[T]):
    block_type: Literal[BlockType.TOOL_RESULT] = Field(
        default=BlockType.TOOL_RESULT, alias="blockType"
    )
    type: Literal["tool_use"]
    id: str
    name: str
    content: T | None

    model_config = ConfigDict(populate_by_name=True)


class ToolResultModel(
    ToolResultBase[TextContentModel | ImageContentFromSourceModel | None]
):
    type: Literal["tool_use"]
    id: str
    name: str
    content: TextContentModel | ImageContentFromSourceModel | None
