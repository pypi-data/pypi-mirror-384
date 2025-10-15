"""
Base models for the skeleton system.
These models represent the simplified content structure that AI can easily work with.
"""
from typing import Any, Dict, Optional
from enum import Enum
import uuid
from pydantic import BaseModel, Field


class SkeletonSupportedType(Enum):
    """Types of slides supported by the system"""
    COVER = "cover"
    TABLE_OF_CONTENT = "table_of_content"
    CHAPTER = "chapter"
    CONTENT = "content"
    END = "end"


class ContentType(Enum):
    """Types of content blocks within a slide"""
    TEXT = "text"  # Body text for a content item
    IMAGE = "image"  # Image content
    CONTENT = "content"  # Content Block

class TextType(Enum):
    AUTHOR = "author"  # Author name (for cover)
    DATE = "date"  # Date (for cover)
    ITEM = "item"
    ITEM_TITLE= "itemTitle"
    TITLE= "title"
    PART_NUMBER = "partNumber"



class SkeletonElement(BaseModel):
    """Base class for all skeleton elements"""
    unique_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

class TextSkeletonElement(SkeletonElement):
    """Text element in the skeleton"""
    content: str
    text_type: Optional[str]
    content_type: ContentType = ContentType.TEXT


class ImageSkeletonElement(SkeletonElement):
    """Image element in the skeleton"""
    src: str  # URL or path to the image
    alt: str = ""  # Alt text for accessibility
    caption: Optional[str] = None  # Optional caption for the image
    content_type: ContentType = ContentType.IMAGE


class ContentBlock(BaseModel):
    """
    A content block represents a logical grouping of related content.
    Used in content slides to group title, text, and supporting image.
    """
    item_title: Optional[TextSkeletonElement] = None  # The title of this content block
    item: Optional[TextSkeletonElement] = None  # The main text content
    image: Optional[ImageSkeletonElement] = None  # Supporting image
    content_type: ContentType = ContentType.CONTENT


    def has_content(self) -> bool:
        """Check if this block has any content"""
        return bool(self.item_title or self.item or self.image)

    def content_count(self) -> int:
        """Count non-empty content elements"""
        count = 0
        if self.item_title: count += 1
        if self.item: count += 1
        if self.image: count += 1
        return count
    
