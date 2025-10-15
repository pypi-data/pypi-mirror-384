from datetime import datetime
from typing import Literal
from uuid import uuid4

from pydantic import ConfigDict, Field

from moxn_types.blocks.base import BaseContent, BlockType


class SignedURLContentModel(BaseContent):
    block_type: Literal[BlockType.SIGNED] = Field(
        default=BlockType.SIGNED, alias="blockType"
    )
    file_path: str = Field(..., alias="filePath")
    expiration: datetime | None = None
    ttl_seconds: int = Field(default=3600, alias="ttlSeconds")
    buffer_seconds: int = Field(default=300, alias="bufferSeconds")
    signed_url: str | None = Field(None, alias="signedUrl")

    model_config = ConfigDict(populate_by_name=True)


class SignedURLImageContentModel(SignedURLContentModel):
    type: Literal["url"] = "url"  # Assuming MediaDataImageFormat.URL is "url"
    media_type: Literal["image/jpeg", "image/png", "image/gif", "image/webp"]


class SignedURLPDFContentModel(SignedURLContentModel):
    type: Literal["url"] = "url"  # Assuming MediaDataPDFFormat.URL is "url"
    media_type: Literal["application/pdf"] = "application/pdf"
    filename: str = Field(default_factory=lambda: f"file-{uuid4()}.pdf")
