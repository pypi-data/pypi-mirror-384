"""
Slide models for different slide types.
Each slide type has its own content structure optimized for that specific layout.
"""
from abc import abstractmethod
from typing import List, Optional, Union
from datetime import datetime
from uuid import uuid4
import uuid
from pydantic import BaseModel, Field

from ii_slide.utils import extract_plain_text
from ii_slide.pptist.types import TextType  # Import here to avoid circular imports
from ii_slide.skeleton.base import SkeletonSupportedType, SkeletonElement, ImageSkeletonElement, ContentBlock, TextSkeletonElement


class BaseSkeletonSlide(SkeletonElement):
    """Base class for all slide types"""
    slide_type: SkeletonSupportedType
    layout_id: Optional[str] = None  # Selected PPTist layout/template identifier

    @abstractmethod
    def update_from_powerpoint(self, text_element, image_elements):
        pass

    @staticmethod
    @abstractmethod
    def create_from_powerpoint(slide_id: str, text_elements, image_elements):
        pass


class CoverSlide(BaseSkeletonSlide):
    """
    Cover slide with title, author, and date.
    This is typically the first slide of a presentation.
    """
    slide_type : SkeletonSupportedType = SkeletonSupportedType.COVER
    title: Optional[TextSkeletonElement] = None
    subtitle: Optional[TextSkeletonElement] = None
    author: Optional[TextSkeletonElement] = None
    date: Optional[TextSkeletonElement] = None
    logo: Optional[ImageSkeletonElement] = None
    background: Optional[ImageSkeletonElement] = None

    @staticmethod
    def create(
        title: str,
        subtitle: Optional[str] = None,
        author: Optional[str] = None,
        date: Optional[str] = None,
        logo: Optional[ImageSkeletonElement] = None
    ) -> 'CoverSlide':
        """Factory method for easy creation"""
        if date is None:
            date = datetime.now().strftime("%Y/%m/%d")
        slide = CoverSlide(
            title=TextSkeletonElement(content=title, text_type="title") if title else None,
            subtitle=TextSkeletonElement(content=subtitle, text_type="subtitle") if subtitle else None,
            author=TextSkeletonElement(content=author, text_type="author") if author else None,
            date=TextSkeletonElement(content=date, text_type="date") if date else None,
            logo=logo
        )
        return slide


    def update_from_powerpoint(self, text_elements, image_elements) -> 'CoverSlide':
        """Update from PowerPoint text and image elements"""

        current_text_ids = {elem.id for elem in text_elements}
        # Check if existing elements are still present and reset them if not
        if self.title and self.title.unique_id not in current_text_ids:
            self.title = None
        if self.subtitle and self.subtitle.unique_id not in current_text_ids:
            self.subtitle = None
        if self.author and self.author.unique_id not in current_text_ids:
            self.author = None
        if self.date and self.date.unique_id not in current_text_ids:
            self.date = None

        # Process new/updated elements
        for elem in text_elements:
            plain_text = extract_plain_text(elem.content)

            if elem.textType == TextType.TITLE.value:
                if not (self.title and self.title.unique_id == elem.id):
                    self.title = TextSkeletonElement(content=plain_text, text_type="title")
                    self.title.unique_id = elem.id
                else:
                    self.title.content = plain_text

            elif elem.textType == TextType.SUBTITLE.value:
                if not (self.subtitle and self.subtitle.unique_id == elem.id):
                    self.subtitle = TextSkeletonElement(content=plain_text, text_type="subtitle")
                    self.subtitle.unique_id = elem.id
                else:
                    self.subtitle.content = plain_text

            elif elem.textType == TextType.AUTHOR.value:
                if not (self.author and self.author.unique_id == elem.id):
                    self.author = TextSkeletonElement(content=plain_text, text_type="author")
                    self.author.unique_id = elem.id
                else:
                    self.author.content = plain_text

            elif elem.textType == TextType.DATE.value:
                if not (self.date and self.date.unique_id == elem.id):
                    self.date = TextSkeletonElement(content=plain_text, text_type="date")
                    self.date.unique_id = elem.id
                else:
                    self.date.content = plain_text

        return self

    @staticmethod
    def create_from_powerpoint(slide_id: str, text_elements, image_elements) -> 'CoverSlide':
        """Create new CoverSlide from PowerPoint text and image elements"""


        title_elem = next((elem for elem in text_elements if elem.textType == TextType.TITLE.value), None)
        subtitle_elem = next((elem for elem in text_elements if elem.textType == TextType.SUBTITLE.value), None)
        author_elem = next((elem for elem in text_elements if elem.textType == TextType.AUTHOR.value), None)
        date_elem = next((elem for elem in text_elements if elem.textType == TextType.DATE.value), None)

        # Create TextSkeletonElement objects with matching IDs
        title_skeleton = None
        if title_elem:
            title_skeleton = TextSkeletonElement(content=extract_plain_text(title_elem.content), text_type=title_elem.textType)
            title_skeleton.unique_id = title_elem.id

        subtitle_skeleton = None
        if subtitle_elem:
            subtitle_skeleton = TextSkeletonElement(content=extract_plain_text(subtitle_elem.content), text_type=subtitle_elem.textType)
            subtitle_skeleton.unique_id = subtitle_elem.id

        author_skeleton = None
        if author_elem:
            author_skeleton = TextSkeletonElement(content=extract_plain_text(author_elem.content), text_type=author_elem.textType)
            author_skeleton.unique_id = author_elem.id

        date_skeleton = None
        if date_elem:
            date_skeleton = TextSkeletonElement(content=extract_plain_text(date_elem.content), text_type=date_elem.textType)
            date_skeleton.unique_id = date_elem.id

        slide =  CoverSlide(
            title=title_skeleton,
            subtitle=subtitle_skeleton,
            author=author_skeleton,
            date=date_skeleton
        )
        slide.unique_id = slide_id

        return slide


class TableOfContentSlide(BaseSkeletonSlide):
    """
    Table of contents slide showing the structure of the presentation.
    """
    title: Optional[TextSkeletonElement] = None
    items: List[TextSkeletonElement] = Field(default_factory=list)
    slide_type : SkeletonSupportedType =SkeletonSupportedType.TABLE_OF_CONTENT

    def add_item(self, item: str) -> None:
        """Add an item to the table of contents"""
        self.items.append(TextSkeletonElement(content=item, text_type="item"))

    @staticmethod
    def create(items: List[str], title: str = "Contents") -> 'TableOfContentSlide':
        """Factory method for easy creation"""
        return TableOfContentSlide(
            title=TextSkeletonElement(content=title, text_type="title"),
            items=[TextSkeletonElement(content=item, text_type="item") for item in items]
        )

    def update_item(self, index: int, new_content: str) -> bool:
        """Update a specific item by index"""
        if 0 <= index < len(self.items):
            self.items[index].content = new_content
            return True
        return False

    def remove_item(self, index: int) -> bool:
        """Remove an item by index"""
        if 0 <= index < len(self.items):
            self.items.pop(index)
            return True
        return False

    def update_from_powerpoint(self, text_elements, image_elements) -> 'TableOfContentSlide':
        """Update from PowerPoint text and image elements"""

        current_text_ids = {elem.id for elem in text_elements}

        # Check if existing title is still present
        if self.title and self.title.unique_id not in current_text_ids:
            self.title = TextSkeletonElement(content="", text_type="title")

        # Remove items whose IDs are no longer present
        if self.items:
            self.items = [item for item in self.items if item.unique_id in current_text_ids]

        # Process current elements
        new_items = []
        for elem in text_elements:
            plain_text = extract_plain_text(elem.content)

            if elem.textType == TextType.TITLE.value:
                if not (self.title and self.title.unique_id == elem.id):
                    self.title = TextSkeletonElement(content=plain_text, text_type="title")
                    self.title.unique_id = elem.id
                else:
                    self.title.content = plain_text

            elif elem.textType == TextType.ITEM.value:
                # Check if this is an existing item
                existing_item = next((item for item in self.items if item.unique_id == elem.id), None)
                if existing_item:
                    existing_item.content = plain_text
                    new_items.append(existing_item)
                else:
                    new_item = TextSkeletonElement(content=plain_text, text_type="item")
                    new_item.unique_id = elem.id
                    new_items.append(new_item)

        # Update items list
        self.items = new_items

        return self

    @staticmethod
    def create_from_powerpoint(slide_id: str, text_elements, image_elements) -> 'TableOfContentSlide':
        """Create new TableOfContentSlide from PowerPoint text and image elements"""

        title_elem = next((elem for elem in text_elements if elem.textType == TextType.TITLE.value), None)
        item_elements = [elem for elem in text_elements if elem.textType == TextType.ITEM.value]

        title_skeleton = TextSkeletonElement(
            content=extract_plain_text(title_elem.content) if title_elem else "Contents",
            text_type=TextType.TITLE.value
        )
        if title_elem:
            title_skeleton.unique_id = title_elem.id

        item_skeletons = []
        for item_elem in item_elements:
            item_skeleton = TextSkeletonElement(content=extract_plain_text(item_elem.content), text_type=item_elem.textType)
            item_skeleton.unique_id = item_elem.id
            item_skeletons.append(item_skeleton)

        slide =  TableOfContentSlide(
            title=title_skeleton,
            items=item_skeletons
        )
        slide.unique_id = slide_id

        return slide


class ChapterSlide(BaseSkeletonSlide):
    """
    Chapter divider slide for separating major sections.
    """
    chapter_number: Optional[TextSkeletonElement] = None
    title: Optional[TextSkeletonElement] = None
    subtitle: Optional[TextSkeletonElement] = None
    slide_type : SkeletonSupportedType =SkeletonSupportedType.CHAPTER

    @staticmethod
    def create(
        title: str,
        chapter_number: str,
        subtitle: Optional[str] = None
    ) -> 'ChapterSlide':
        """Factory method for easy creation"""
        return ChapterSlide(
            chapter_number=TextSkeletonElement(content=chapter_number, text_type="partNumber"),
            title=TextSkeletonElement(content=title, text_type="title"),
            subtitle=TextSkeletonElement(content=subtitle, text_type="subtitle") if subtitle else None
        )

    def update_from_powerpoint(self, text_elements, image_elements) -> 'ChapterSlide':
        """Update from PowerPoint text and image elements"""

        current_text_ids = {elem.id for elem in text_elements}

        # Check if existing elements are still present and reset them if not
        if self.title and self.title.unique_id not in current_text_ids:
            self.title = TextSkeletonElement(content="", text_type="title")
        if self.chapter_number and self.chapter_number.unique_id not in current_text_ids:
            self.chapter_number = TextSkeletonElement(content="", text_type="partNumber")
        if self.subtitle and self.subtitle.unique_id not in current_text_ids:
            self.subtitle = None

        # Process current elements
        for elem in text_elements:
            plain_text = extract_plain_text(elem.content)

            if elem.textType == TextType.TITLE.value:
                if not (self.title and self.title.unique_id == elem.id):
                    self.title = TextSkeletonElement(content=plain_text, text_type="title")
                    self.title.unique_id = elem.id
                else:
                    self.title.content = plain_text

            elif elem.textType == TextType.PART_NUMBER.value:
                if not (self.chapter_number and self.chapter_number.unique_id == elem.id):
                    self.chapter_number = TextSkeletonElement(content=plain_text, text_type="partNumber")
                    self.chapter_number.unique_id = elem.id
                else:
                    self.chapter_number.content = plain_text

            elif elem.textType == TextType.SUBTITLE.value:
                if not (self.subtitle and self.subtitle.unique_id == elem.id):
                    self.subtitle = TextSkeletonElement(content=plain_text, text_type="subtitle")
                    self.subtitle.unique_id = elem.id
                else:
                    self.subtitle.content = plain_text

        return self

    @staticmethod
    def create_from_powerpoint(slide_id: str, text_elements, image_elements) -> 'ChapterSlide':
        """Create new ChapterSlide from PowerPoint text and image elements"""

        title_elem = next((elem for elem in text_elements if elem.textType == TextType.TITLE.value), None)
        chapter_elem = next((elem for elem in text_elements if elem.textType == TextType.PART_NUMBER.value), None)
        subtitle_elem = next((elem for elem in text_elements if elem.textType == TextType.SUBTITLE.value), None)

        title_skeleton = TextSkeletonElement(
            content=extract_plain_text(title_elem.content) if title_elem else "",
            text_type=TextType.TITLE.value
        )
        if title_elem:
            title_skeleton.unique_id = title_elem.id

        chapter_skeleton = TextSkeletonElement(
            content=extract_plain_text(chapter_elem.content) if chapter_elem else "",
            text_type=TextType.PART_NUMBER.value
        )
        if chapter_elem:
            chapter_skeleton.unique_id = chapter_elem.id

        subtitle_skeleton = None
        if subtitle_elem:
            subtitle_skeleton = TextSkeletonElement(content=extract_plain_text(subtitle_elem.content), text_type=subtitle_elem.textType)
            subtitle_skeleton.unique_id = subtitle_elem.id

        slide = ChapterSlide(
            title=title_skeleton,
            chapter_number=chapter_skeleton,
            subtitle=subtitle_skeleton
        )
        slide.unique_id = slide_id
        return slide


class ContentSlide(BaseSkeletonSlide):
    """
    Regular content slide with flexible layout based on content blocks.
    The template will be automatically selected based on:
    - Number of content blocks
    - Presence of images
    - Content density
    """
    title: Optional[TextSkeletonElement] = None
    content_blocks: List[ContentBlock] = Field(default_factory=list)
    slide_type : SkeletonSupportedType =SkeletonSupportedType.CONTENT

    def get_template_hint(self) -> str:
        """
        Suggest a template based on content structure.
        This helps automatically select the right PowerPoint template.
        """
        num_blocks = len(self.content_blocks)
        has_images = any(block.image for block in self.content_blocks)

        if num_blocks == 0:
            return "title_only"
        elif num_blocks == 1:
            block = self.content_blocks[0]
            if block.image and not block.item:
                return "title_image"
            elif block.item and not block.image:
                return "title_content"
            else:
                return "title_content_image"
        elif num_blocks == 2:
            if has_images:
                return "two_content_two_image"
            else:
                return "two_column_text"
        elif num_blocks == 3:
            if has_images:
                return "three_content_three_image"
            else:
                return "three_column_text"
        elif num_blocks == 4:
            if has_images:
                return "four_quadrant"
            else:
                return "four_content"
        else:
            return "multi_content"


    def add_content_block(self, block: ContentBlock) -> 'ContentSlide':
        """Add a content block to the slide"""
        self.content_blocks.append(block)
        return self

    def remove_content_block(self, index: int) -> bool:
        """Remove a content block by index"""
        if 0 <= index < len(self.content_blocks):
            self.content_blocks.pop(index)
            return True
        return False

    def update_content_block(self, index: int, block: ContentBlock) -> bool:
        """Update a content block by index"""
        if 0 <= index < len(self.content_blocks):
            self.content_blocks[index] = block
            return True
        return False

    def update_from_powerpoint(self, text_elements, image_elements) -> 'ContentSlide':
        """Update from PowerPoint text and image elements using ID-based matching"""
        current_text_ids = {elem.id for elem in text_elements}
        current_image_ids = {elem.id for elem in image_elements}

        # Update title if present
        title_elem = next((elem for elem in text_elements if elem.textType == TextType.TITLE.value), None)

        if title_elem:
            plain_text = extract_plain_text(title_elem.content)
            if not (self.title and self.title.unique_id == title_elem.id):
                self.title = TextSkeletonElement(content=plain_text, text_type="title")
                self.title.unique_id = title_elem.id
            else:
                self.title.content = plain_text
        elif self.title and self.title.unique_id not in current_text_ids:
            self.title = None

        # Get all content-related elements (excluding title)
        content_text_elements = [elem for elem in text_elements if elem.textType != TextType.TITLE.value]

        # Create maps for quick ID lookup
        text_elem_by_id = {elem.id: elem for elem in content_text_elements}
        image_elem_by_id = {elem.id: elem for elem in image_elements}

        # Update existing content blocks by matching IDs
        updated_blocks = []
        processed_text_ids = set()
        processed_image_ids = set()

        for block in self.content_blocks:
            updated_block = ContentBlock()
            block_has_content = False

            # Update item_title if it exists and matches
            if block.item_title and block.item_title.unique_id in text_elem_by_id:
                elem = text_elem_by_id[block.item_title.unique_id]
                updated_block.item_title = TextSkeletonElement(
                    content=extract_plain_text(elem.content),
                    text_type="item_title"
                )
                updated_block.item_title.unique_id = elem.id
                processed_text_ids.add(elem.id)
                block_has_content = True

            # Update item if it exists and matches
            if block.item and block.item.unique_id in text_elem_by_id:
                elem = text_elem_by_id[block.item.unique_id]
                updated_block.item = TextSkeletonElement(
                    content=extract_plain_text(elem.content),
                    text_type="item"
                )
                updated_block.item.unique_id = elem.id
                processed_text_ids.add(elem.id)
                block_has_content = True

            # Update image if it exists and matches
            if block.image and block.image.unique_id in image_elem_by_id:
                elem = image_elem_by_id[block.image.unique_id]
                updated_block.image = ImageSkeletonElement(
                    src=elem.src,
                    caption=getattr(elem, 'caption', None)
                )
                updated_block.image.unique_id = elem.id
                processed_image_ids.add(elem.id)
                block_has_content = True

            # Only keep blocks that still have content
            if block_has_content:
                updated_blocks.append(updated_block)

        # Add new elements that weren't matched to existing blocks as separate content blocks
        for elem in content_text_elements:
            if elem.id not in processed_text_ids:
                new_block = ContentBlock()
                text_skeleton = TextSkeletonElement(
                    content=extract_plain_text(elem.content),
                    text_type=elem.textType
                )
                text_skeleton.unique_id = elem.id

                if elem.textType == TextType.ITEM_TITLE.value:
                    new_block.item_title = text_skeleton
                else:
                    new_block.item = text_skeleton

                updated_blocks.append(new_block)

        # Add new images that weren't matched to existing blocks as separate content blocks
        for elem in image_elements:
            if elem.id not in processed_image_ids:
                new_block = ContentBlock()
                image_skeleton = ImageSkeletonElement(
                    src=elem.src,
                    caption=getattr(elem, 'caption', None)
                )
                image_skeleton.unique_id = elem.id
                new_block.image = image_skeleton
                updated_blocks.append(new_block)

        # Update content blocks with the new list (preserves order of existing blocks)
        self.content_blocks = updated_blocks

        return self

    @staticmethod
    def create_from_powerpoint(slide_id: str, text_elements, image_elements) -> 'ContentSlide':
        """Create new ContentSlide from PowerPoint text and image elements"""

        title_elem = next((elem for elem in text_elements if elem.textType == TextType.TITLE.value), None)

        title_skeleton = None
        if title_elem:
            title_skeleton = TextSkeletonElement(content=extract_plain_text(title_elem.content), text_type=title_elem.textType)
            title_skeleton.unique_id = title_elem.id

        # Create content blocks for non-title elements
        content_blocks = []

        # Add text elements (excluding title)
        for elem in text_elements:
            if elem.textType != TextType.TITLE.value:
                content_block = ContentBlock()
                text_skeleton = TextSkeletonElement(content=extract_plain_text(elem.content), text_type=elem.textType)
                text_skeleton.unique_id = elem.id

                if elem.textType == TextType.ITEM_TITLE.value:
                    content_block.item_title = text_skeleton
                else:
                    content_block.item = text_skeleton

                content_blocks.append(content_block)

        # Add image elements
        for elem in image_elements:
            content_block = ContentBlock()
            image_skeleton = ImageSkeletonElement(
                src=elem.src,
                alt=getattr(elem, 'alt', ''),
                caption=getattr(elem, 'caption', None)
            )
            image_skeleton.unique_id = elem.id
            content_block.image = image_skeleton
            content_blocks.append(content_block)

        slide =  ContentSlide(
            title=title_skeleton,
            content_blocks=content_blocks
        )
        slide.unique_id = slide_id
        return slide

class EndSlide(BaseSkeletonSlide):
    """
    End slide for closing the presentation.
    """
    title: Optional[TextSkeletonElement] = None
    subtitle: Optional[TextSkeletonElement] = None
    slide_type: SkeletonSupportedType = SkeletonSupportedType.END

    @staticmethod
    def create(title: str = "Thank You", subtitle: Optional[str] = None) -> 'EndSlide':
        """Factory method for easy creation"""
        return EndSlide(
            slide_type=SkeletonSupportedType.END,
            title=TextSkeletonElement(content=title, text_type="title"),
            subtitle=TextSkeletonElement(content=subtitle, text_type="subtitle") if subtitle else None,
        )


    def update_from_powerpoint(self, text_elements, image_elements) -> 'EndSlide':
        """Update from PowerPoint text and image elements"""
        current_text_ids = {elem.id for elem in text_elements}

        # Check if existing elements are still present and reset them if not
        if self.title and self.title.unique_id not in current_text_ids:
            self.title = TextSkeletonElement(content="", text_type="title")
        if self.subtitle and self.subtitle.unique_id not in current_text_ids:
            self.subtitle = None

        # Process current elements
        for elem in text_elements:
            plain_text = extract_plain_text(elem.content)

            if elem.textType == TextType.TITLE.value:
                if not (self.title and self.title.unique_id == elem.id):
                    self.title = TextSkeletonElement(content=plain_text, text_type="title")
                    self.title.unique_id = elem.id
                else:
                    self.title.content = plain_text

            elif elem.textType == TextType.SUBTITLE.value:
                if not (self.subtitle and self.subtitle.unique_id == elem.id):
                    self.subtitle = TextSkeletonElement(content=plain_text, text_type="subtitle")
                    self.subtitle.unique_id = elem.id
                else:
                    self.subtitle.content = plain_text

        return self

    @staticmethod
    def create_from_powerpoint(slide_id: str, text_elements, image_elements) -> 'EndSlide':
        """Create new EndSlide from PowerPoint text and image elements"""


        title_elem = next((elem for elem in text_elements if elem.textType == TextType.TITLE.value), None)
        subtitle_elem = next((elem for elem in text_elements if elem.textType == TextType.SUBTITLE.value), None)

        title_skeleton = TextSkeletonElement(
            content=extract_plain_text(title_elem.content) if title_elem else "Thank You",
            text_type=TextType.TITLE.value
        )
        if title_elem:
            title_skeleton.unique_id = title_elem.id

        subtitle_skeleton = None
        if subtitle_elem:
            subtitle_skeleton = TextSkeletonElement(content=extract_plain_text(subtitle_elem.content), text_type=subtitle_elem.textType)
            subtitle_skeleton.unique_id = subtitle_elem.id

        slide =  EndSlide(
            title=title_skeleton,
            subtitle=subtitle_skeleton
        )
        slide.unique_id = slide_id
        return slide

# Type alias for all slide types
SlideContent = Union[CoverSlide, TableOfContentSlide, ChapterSlide, ContentSlide, EndSlide]
