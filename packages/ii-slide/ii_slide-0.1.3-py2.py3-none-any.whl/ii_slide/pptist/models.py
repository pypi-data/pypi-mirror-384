"""
Data models for PowerPoint elements and slides
"""
from typing import List, Optional, Dict, Any, Literal, Union
from enum import Enum
import json
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field

from ii_slide.pptist.types import SlideType
from ii_slide.skeleton.manager import PresentationSkeleton
from ii_slide.skeleton.slides import BaseSkeletonSlide, CoverSlide, ContentSlide, ChapterSlide, TableOfContentSlide, EndSlide


class Background(BaseModel):
    type: str = "solid"
    color: str = "#fff"


class Outline(BaseModel):
    color: str = "#000000"
    width: float = 0
    style: str = "solid"
    cap: str = "butt"
    gradient: Optional[Dict[str, Any]] = None


class Padding(BaseModel):
    top: float = 3.6
    bottom: float = 3.6
    left: float = 7.2
    right: float = 7.2


class BaseElement(BaseModel, ABC):
    """Base class for all slide elements"""
    id: str
    type: str
    left: float = 0
    top: float = 0
    width: float = 0
    height: Optional[float] = None
    rotate: float = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to PowerPoint JSON format"""
        result = self.model_dump(exclude_none=True)
        # Special handling for line elements where height=0 should be excluded
        if result.get('height') == 0 and self.type == 'line':
            result.pop('height', None)
        return result


class TextElement(BaseElement):
    type: str = "text"
    content: str = ""
    defaultFontName: str = ""
    defaultColor: str = "#000000"
    lineHeight: float = 1
    outline: Optional[Outline] = None
    fill: str = ""
    vertical: bool = False
    autoFit: bool = True
    padding: Optional[Padding] = None
    vAlign: str = "top"
    textType: Optional[str] = None  # "title", "body", etc.

    def model_post_init(self, __context):
        if self.outline is None:
            self.outline = Outline()
        if self.padding is None:
            self.padding = Padding()


class ImageElement(BaseElement):
    type: str = "image"
    src: str = ""
    fixedRatio: bool = True
    flipH: bool = False
    flipV: bool = False
    opacity: float = 1.0
    clip: Optional[Dict] = None
    viewBox: Optional[List[float]] = None
    adjustments: Optional[List] = None
    path: Optional[str] = None
    pathFormula: Optional[str] = None
    from_user: Optional[bool] = None


class ShapeElement(BaseElement):
    type: str = "shape"
    viewBox: List[float] = Field(default_factory=list)
    path: str = ""
    fill: str = "#E6E6FD"
    fixedRatio: bool = False
    outline: Optional[Outline] = None
    text: Optional[Dict] = None
    flipH: bool = False
    flipV: bool = False
    adjustments: Optional[List] = None
    pathFormula: Optional[str] = None
    keypoints: Optional[List] = None
    lineHeight: Optional[float] = None
    gradient: Optional[Dict] = None

    def model_post_init(self, __context):
        if self.outline is None:
            self.outline = Outline()



class LineElement(BaseElement):
    type: str = "line"
    flip: List[bool] = Field(default_factory=lambda: [False, False])
    pathFormula: str = "line"
    start: List[float] = Field(default_factory=lambda: [0, 0])
    end: List[float] = Field(default_factory=lambda: [0, 0])
    style: str = "solid"
    color: str = "#000000"
    points: List[str] = Field(default_factory=lambda: ["", ""])
    outline: Optional[Outline] = None
    adjustments: Optional[List] = None

    def model_post_init(self, __context):
        if self.outline is None:
            self.outline = Outline()


class UnsupportedElementTypeError(Exception):
    """Raised when an unknown element type is encountered"""
    def __init__(self, elem_type: str, element_data: Dict[str, Any]):
        self.elem_type = elem_type
        self.element_data = element_data
        super().__init__(f"Unsupported element type: '{elem_type}'. Full element data: {json.dumps(element_data, indent=2)}")


class UnsupportedSlideTypeError(Exception):
    """Raised when an unknown slide type is encountered"""
    def __init__(self, slide_type: str):
        self.slide_type = slide_type
        super().__init__(f"Unsupported slide type: '{slide_type}'. Known types: {[t.value for t in SlideType]}")


class Slide(BaseModel):
    id: str
    type: SlideType
    elements: List[Union[TextElement, ImageElement, ShapeElement, LineElement]]
    background: Background = Field(default_factory=Background)
    remark: Optional[str] = None
    from_template: Optional[str] = None  # "traditional", "modern", etc.

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Slide':
        """Create Slide from PowerPoint JSON"""
        elements = []
        for elem_data in data.get("elements", []):
            elem_type = elem_data.get("type")
            try:
                if elem_type == "text":
                    elements.append(TextElement(**elem_data))
                elif elem_type == "image":
                    elements.append(ImageElement(**elem_data))
                elif elem_type == "shape":
                    elements.append(ShapeElement(**elem_data))
                elif elem_type == "line":
                    elements.append(LineElement(**elem_data))
                else:
                    # Throw error with full element data for debugging
                    raise UnsupportedElementTypeError(elem_type, elem_data)
            except TypeError as e:
                print(f"Error parsing {elem_type} element with ID {elem_data.get('id', 'unknown')}: {e}")
                print(f"Element data keys: {list(elem_data.keys())}")
                raise

        # Check if slide type is valid
        try:
            slide_type = SlideType(data["type"])
        except ValueError:
            raise UnsupportedSlideTypeError(data["type"])

        return cls(
            id=data["id"],
            type=slide_type,
            elements=elements,
            background=Background(**data.get("background", {})),
            remark=data.get("remark"),
            from_template=data.get("from")
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to PowerPoint JSON format"""
        result = {
            "id": self.id,
            "type": self.type.value,
            "elements": [elem.to_dict() for elem in self.elements],
            "background": {
                "type": self.background.type,
                "color": self.background.color
            }
        }

        if self.remark:
            result["remark"] = self.remark

        if self.from_template:
            result["from"] = self.from_template

        return result



class Theme(BaseModel):
    """PowerPoint theme settings"""
    themeColors: List[str] = Field(default_factory=lambda: ["#4874CB", "#EE822F", "#F2BA02", "#75BD42", "#30C0B4", "#E54C5E"])
    subColors: List[str] = Field(default_factory=lambda: ["#000000", "#FFFFFF", "#44546A", "#E7E6E6"])
    exportThemeColors: List[str] = Field(default_factory=list)
    fontColor: str = "#000000"
    fontName: str = ""
    backgroundColor: str = "#FFFFFF"
    shadow: Optional[Dict] = None
    outline: Optional[Dict] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Theme':
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)


class Presentation(BaseModel):
    slides: List[Slide]
    type: Optional[str] = None
    width: float = 960  # Changed to float to match PPTist
    height: float = 540  # Changed to float to match PPTist
    theme: Optional[Theme] = None
    templateJSONUrl: Optional[str] = None

    @classmethod
    def from_json(cls, json_data: Union[str, Dict]) -> 'Presentation':
        """Load presentation from JSON"""
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data

        slides = []
        for slide_data in data.get("slides", []):
            try:
                slides.append(Slide.from_dict(slide_data))
            except (UnsupportedElementTypeError, UnsupportedSlideTypeError) as e:
                print(f"Warning: {e}")
                # Continue parsing other slides
                continue

        theme = None
        if "theme" in data:
            theme = Theme.from_dict(data["theme"])

        return cls(
            slides=slides,
            type=data.get("type"),
            width=data.get("width", 960),
            height=data.get("height", 540),
            theme=theme,
            templateJSONUrl=data.get("templateJSONUrl")
        )

    def update_skeleton(self, presentation_skeleton: PresentationSkeleton) -> PresentationSkeleton:
        """
        Convert PPTist Presentation to Skeleton format.

        Args:
            presentation_skeleton: Optional existing skeleton to update

        Returns:
            PresentationSkeleton with extracted/updated content
        """
        # Create new ordered list of slides
        new_slides = []

        # Process each PPTist slide in order
        for pptist_slide in self.slides:
            skeleton_slide = self._find_skeleton_slide_by_id(presentation_skeleton, pptist_slide.id)

            if skeleton_slide:
                self._update_skeleton_slide(skeleton_slide, pptist_slide)
                new_slides.append(skeleton_slide)
            else:
                new_skeleton_slide = self._create_skeleton_slide_from_pptist(pptist_slide)
                if new_skeleton_slide:
                    new_slides.append(new_skeleton_slide)

        # Replace the slides list with the new ordered list
        presentation_skeleton.slides = new_slides

        return presentation_skeleton

    def _find_skeleton_slide_by_id(self, skeleton: PresentationSkeleton, slide_id: str):
        """Find skeleton slide with matching unique_id"""
        for slide in skeleton.slides:
            if slide.unique_id and slide.unique_id == slide_id:
                return slide
        return None

    def _update_skeleton_slide(self, skeleton_slide : BaseSkeletonSlide, pptist_slide : Slide):
        """Update existing skeleton slide based on its type and PPTist slide content"""
        # Extract elements from PPTist slide
        text_elements = [elem for elem in pptist_slide.elements
                        if isinstance(elem, TextElement)]
        image_elements = [elem for elem in pptist_slide.elements
                         if isinstance(elem, ImageElement) and elem.from_user]

        # Use the slide's update_from_powerpoint method (all slides have this as abstract method)
        skeleton_slide.update_from_powerpoint(text_elements, image_elements)

    def _create_skeleton_slide_from_pptist(self, pptist_slide):
        """Create new skeleton slide based on PPTist slide type and content"""
        text_elements = [elem for elem in pptist_slide.elements
                        if isinstance(elem, TextElement)]
        image_elements = [elem for elem in pptist_slide.elements
                         if isinstance(elem, ImageElement) and elem.from_user]

        if pptist_slide.type == SlideType.COVER:
            return CoverSlide.create_from_powerpoint(pptist_slide.id, text_elements, image_elements)
        elif pptist_slide.type in [SlideType.CHAPTER, SlideType.TRANSITION]:
            return ChapterSlide.create_from_powerpoint(pptist_slide.id, text_elements, image_elements)
        elif pptist_slide.type in [SlideType.TABLE_OF_CONTENT, SlideType.CONTENTS]:
            return TableOfContentSlide.create_from_powerpoint(pptist_slide.id, text_elements, image_elements)
        elif pptist_slide.type == SlideType.END:
            return EndSlide.create_from_powerpoint(pptist_slide.id, text_elements, image_elements)
        else:
            # Default to ContentSlide
            return ContentSlide.create_from_powerpoint(pptist_slide.id, text_elements, image_elements)

    def to_json(self) -> str:
        """Convert to PowerPoint JSON string"""
        return json.dumps(self.to_dict(), indent=2)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to PowerPoint JSON format"""
        result = {
            "slides": [slide.to_dict() for slide in self.slides],
            "width": self.width,
            "height": self.height
        }

        if self.type:
            result["type"] = self.type

        if self.theme:
            result["theme"] = self.theme.to_dict()

        if self.templateJSONUrl:
            result["templateJSONUrl"] = self.templateJSONUrl

        return result