"""
Skeleton Manager for managing presentation state and providing LLM-friendly API.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
import json
from pydantic import BaseModel, Field
from .base import ContentBlock, TextSkeletonElement
from ii_slide.templates import TemplateRegistry
from .slides import (
    CoverSlide, TableOfContentSlide,
    ChapterSlide, ContentSlide, EndSlide, SlideContent
)

def enum_default(o):
    if isinstance(o, Enum):
        return o.value
    if hasattr(o, 'model_dump'):
        return o.model_dump()
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")


class PresentationSkeleton(BaseModel):
    """
    Main skeleton state containing all slides.
    This is the central state object for the presentation.
    """
    slides: List[SlideContent] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def get_slide_count(self) -> int:
        """Get total number of slides"""
        return len(self.slides)

    def get_content_slides(self) -> List[ContentSlide]:
        """Get only content slides"""
        return [s for s in self.slides if isinstance(s, ContentSlide)]

    def get_table_of_contents(self) -> Optional[TableOfContentSlide]:
        """Get the table of contents slide if it exists"""
        for slide in self.slides:
            if isinstance(slide, TableOfContentSlide):
                return slide
        return None


    def _slide_to_dict(self, slide: SlideContent) -> Dict[str, Any]:
        """Convert a slide to dictionary"""
        if isinstance(slide, CoverSlide):
            return {
                "id" : slide.unique_id,
                "type": "cover",
                "title": slide.title,
                "subtitle": slide.subtitle,
                "author": slide.author,
                "date": slide.date
            }
        elif isinstance(slide, TableOfContentSlide):
            return {
                "type": "table_of_content",
                "id" : slide.unique_id,
                "title": slide.title,
                "items": slide.items
            }
        elif isinstance(slide, ChapterSlide):
            return {
                "type": "chapter",
                "id" : slide.unique_id,
                "chapter_number": slide.chapter_number,
                "title": slide.title,
                "subtitle": slide.subtitle
            }
        elif isinstance(slide, ContentSlide):
            return {
                "type": "content",
                "id" : slide.unique_id,
                "title": slide.title,
                "content_blocks": [b.model_dump() for b in slide.content_blocks],
                "template_hint": slide.get_template_hint()
            }
        elif isinstance(slide, EndSlide):
            return {
                "type": "end",
                "id" : slide.unique_id,
                "title": slide.title,
                "subtitle": slide.subtitle,
            }
        return {}



class SkeletonManager:
    """
    Manager class providing LLM-friendly API for creating and managing presentations.
    """

    def __init__(self, template_registry: Optional[TemplateRegistry] = None):
        self.skeleton = PresentationSkeleton()
        self.template_registry = template_registry or TemplateRegistry()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _assign_layout(self, slide: SlideContent, layout_id: Optional[str] = None) -> str:
        """Assign a template layout to the slide and return its identifier."""
        if layout_id:
            template = self.template_registry.get(layout_id)
        else:
            template = self.template_registry.decide_for_slide(slide)

        slide.layout_id = template.layout_id
        return slide.layout_id

    def get_slide_by_id(self, slide_id: str) -> Optional[SlideContent]:
        for slide in self.skeleton.slides:
            if slide.unique_id == slide_id:
                return slide
        return None

    def add_cover_slide(self,
                       title: str,
                       subtitle: Optional[str] = None,
                       author: Optional[str] = None,
                       date: Optional[str] = None) -> CoverSlide:
        """
        Add a cover slide to the presentation.

        Args:
            title: Main presentation title
            subtitle: Optional subtitle
            author: Optional author name
            date: Optional date string

        Returns:
            The created CoverSlide

        Example:
            manager.add_cover_slide(
                title='My Presentation',
                subtitle='A great subtitle',
                author='John Doe',
                date='2024-01-01'
            )
        """
        slide = CoverSlide.create(
            title=title,
            subtitle=subtitle,
            author=author,
            date=date
        )
        self._assign_layout(slide)
        self.skeleton.slides.append(slide)
        return slide

    def add_table_of_contents_slide(self,
                                   items: List[str],
                                   title: str) -> TableOfContentSlide:
        """
        Add a table of contents slide.

        Args:
            items: List of section titles
            title: Optional title for the TOC slide (default: "Contents")

        Returns:
            The created TableOfContentSlide

        Example:
            manager.add_table_of_contents_slide([
                'Introduction',
                'Main Content',
                'Conclusion'
            ])
        """
        slide = TableOfContentSlide.create(
            items=items,
            title=title
        )
        self._assign_layout(slide)
        self.skeleton.slides.append(slide)
        return slide

    def add_chapter_slide(self,
                         title: str,
                         chapter_number: str,
                         subtitle: Optional[str] = None) -> ChapterSlide:
        """
        Add a chapter divider slide.

        Args:
            title: Chapter title
            chapter_number: Optional chapter number (e.g., "01", "Chapter 1")
            subtitle: Optional subtitle

        Returns:
            The created ChapterSlide

        Example:
            manager.add_chapter_slide(
                title='Technical Architecture',
                chapter_number='02',
                subtitle='System Overview'
            )
        """
        slide = ChapterSlide.create(
            title=title,
            chapter_number=chapter_number,
            subtitle=subtitle
        )
        self._assign_layout(slide)
        self.skeleton.slides.append(slide)
        return slide

    def add_content_slide(self,
                         title: TextSkeletonElement,
                         content_blocks: List[ContentBlock]) -> ContentSlide:
        """
        Add a content slide with multiple content blocks.

        Args:
            title: Slide title
            content_blocks: List of ContentBlock objects

        Returns:
            The created ContentSlide

        Example:
            manager.add_content_slide(
                title='Key Features',
                content_blocks=[
                    ContentBlock(
                        item_title=TextElement(type=ContentType.ITEM_TITLE, content='Feature 1'),
                        item=TextElement(type=ContentType.ITEM, content='Description'),
                        image=ImageElement(src='http://example.com/img.png')
                    )
                ]
            )
        """
        slide = ContentSlide(
            content_blocks=content_blocks,
            title=title
        )
        slide.content_blocks = content_blocks
        self._assign_layout(slide)
        self.skeleton.slides.append(slide)
        return slide

    def add_end_slide(self,
                     title: str = "Thank You",
                     subtitle: Optional[str] = None) -> EndSlide:
        """
        Add an end slide to the presentation.

        Args:
            title: Main text (default: "Thank You")
            subtitle: Optional subtitle
            contact_info: Optional contact information

        Returns:
            The created EndSlide

        Example:
            manager.add_end_slide(
                title='Thank You',
                subtitle='Questions?',
                contact_info='contact@example.com'
            )
        """
        slide = EndSlide.create(
            title=title,
            subtitle=subtitle,
        )
        self._assign_layout(slide)
        self.skeleton.slides.append(slide)
        return slide


    def get_slide(self, slide_index: int) -> Optional[SlideContent]:
        """
        Get a slide by index for direct updates.

        Args:
            slide_index: Index of the slide (0-based)

        Returns:
            The slide object or None if index is invalid

        Example:
            # Get slide and update it directly
            slide = manager.get_slide(0)
            if isinstance(slide, CoverSlide):
                slide.update(title="New Title", author="New Author")
        """
        if 0 <= slide_index < len(self.skeleton.slides):
            return self.skeleton.slides[slide_index]
        return None

    def remove_slide(self, slide_index: int) -> bool:
        """
        Remove a slide from the presentation.

        Args:
            slide_index: Index of the slide to remove (0-based)

        Returns:
            True if successful, False otherwise
        """
        if 0 <= slide_index < len(self.skeleton.slides):
            self.skeleton.slides.pop(slide_index)
            return True
        return False

    def update_slide_template(self, slide_id: str, layout_id: Optional[str] = None) -> SlideContent:
        """Re-select or explicitly set the template layout for a slide."""
        slide = self.get_slide_by_id(slide_id)
        if not slide:
            raise ValueError(f"Slide '{slide_id}' not found")

        self._assign_layout(slide, layout_id=layout_id)
        return slide

    def auto_generate_toc(self) -> Optional[TableOfContentSlide]:
        """
        Automatically generate a table of contents based on chapter and content slides.

        Returns:
            The generated TableOfContentSlide or None if no content
        """
        items = []
        for slide in self.skeleton.slides:
            if isinstance(slide, ChapterSlide):
                items.append(slide.title)
            elif isinstance(slide, ContentSlide) and slide.title:
                # Optionally include major content slides
                if len(slide.content_blocks) > 1:  # Only include substantial slides
                    items.append(slide.title)

        if items:
            # Find existing TOC or create new one
            toc = self.skeleton.get_table_of_contents()
            if toc:
                toc.items = items
                if not toc.layout_id:
                    self._assign_layout(toc)
            else:
                # Insert after cover slide if it exists
                insert_pos = 1 if isinstance(self.skeleton.slides[0], CoverSlide) else 0
                toc = TableOfContentSlide.create(items)
                self._assign_layout(toc)
                self.skeleton.slides.insert(insert_pos, toc)
            return toc
        return None

    def get_skeleton_json(self) -> str:
        """Get the skeleton as JSON string"""
        return (json.dumps(self.skeleton.model_dump(), default=enum_default, indent=2))

    def load_from_json(self, json_str: str) -> bool:
        """Load skeleton from JSON string"""
        try:
            data = json.loads(json_str)
            # Implementation would recreate slides from the data
            # This is a placeholder for now
            return True
        except Exception:
            return False
