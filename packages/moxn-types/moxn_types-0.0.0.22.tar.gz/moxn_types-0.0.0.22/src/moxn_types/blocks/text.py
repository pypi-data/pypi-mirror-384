from typing import Literal

from pydantic import ConfigDict, Field

from moxn_types.blocks.base import BaseContent, BlockType


class TextContentModel(BaseContent):
    block_type: Literal[BlockType.TEXT] = Field(
        default=BlockType.TEXT, alias="blockType"
    )
    text: str

    model_config = ConfigDict(populate_by_name=True)
