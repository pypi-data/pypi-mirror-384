"""Template registry and rendering utilities for PPTist conversion."""
from __future__ import annotations

from abc import ABC, abstractmethod
from copy import deepcopy
from html import escape
import json
import random
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from ii_slide.skeleton.base import ContentBlock, SkeletonSupportedType, TextSkeletonElement, ImageSkeletonElement
from ii_slide.skeleton.slides import (
    BaseSkeletonSlide,
    ChapterSlide,
    ContentSlide,
    CoverSlide,
    EndSlide,
    TableOfContentSlide,
)


class SlideTemplate(ABC):
    """Base template definition for converting skeleton slides to PPTist."""

    layout_id: str = ""
    slide_type: SkeletonSupportedType = SkeletonSupportedType.CONTENT
    min_blocks: int = 0
    max_blocks: Optional[int] = None
    requires_images: Optional[bool] = None
    priority: int = 0  # Higher priority wins when multiple templates match

    def matches(self, slide: BaseSkeletonSlide) -> bool:
        """Return True if this template is compatible with the slide."""
        if slide.slide_type != self.slide_type:
            return False

        if isinstance(slide, ContentSlide):
            block_count = len(slide.content_blocks)
            if block_count < self.min_blocks:
                return False
            if self.max_blocks is not None and block_count > self.max_blocks:
                return False

            if self.requires_images is not None:
                has_images = any(block.image is not None for block in slide.content_blocks)
                if has_images != self.requires_images:
                    return False

        return True

    @abstractmethod
    def render(self, slide: BaseSkeletonSlide) -> Dict[str, Any]:
        """Render a PPTist slide definition from the skeleton slide."""

    # ------------------------------------------------------------------
    # Helper methods shared by templates
    # ------------------------------------------------------------------
    @staticmethod
    def _format_html(text: Optional[str], *, size: int, bold: bool = False, align: str = "left") -> str:
        if not text:
            text = ""

        content = text.replace("\n", "<br/>")

        if bold:
            content = f"<strong>{content}</strong>"

        span = f"<span style=\"font-size: {size}px;\">{content}</span>"
        align_style = f"text-align: {align};" if align and align != "left" else ""
        style_attr = f" style=\"{align_style}\"" if align_style else ""

        return f"<p{style_attr}>{span}</p>"

    @staticmethod
    def _text_element(
        element_id: str,
        content: Optional[str],
        *,
        left: float,
        top: float,
        width: float,
        height: float,
        size: int,
        bold: bool = False,
        align: str = "left",
        text_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        return {
            "type": "text",
            "id": element_id,
            "left": left,
            "top": top,
            "width": width,
            "height": height,
            "rotate": 0,
            "content": SlideTemplate._format_html(content, size=size, bold=bold, align=align),
            "defaultFontName": "",
            "defaultColor": "#333333",
            "lineHeight": 1.2,
            "outline": {
                "color": "#000000",
                "width": 0.0,
                "style": "solid",
                "cap": "butt",
                "gradient": None,
            },
            "fill": "",
            "vertical": False,
            "autoFit": True,
            "padding": {"top": 3.6, "bottom": 3.6, "left": 7.2, "right": 7.2},
            "vAlign": "top",
            "textType": text_type,
        }

    @staticmethod
    def _image_element(
        element_id: str,
        *,
        src: str,
        left: float,
        top: float,
        width: float,
        height: float,
    ) -> Dict[str, Any]:
        return {
            "type": "image",
            "id": element_id,
            "src": src,
            "left": left,
            "top": top,
            "width": width,
            "height": height,
            "rotate": 0,
            "fixedRatio": True,
            "flipH": False,
            "flipV": False,
            "opacity": 1.0,
        }

class PPTistSlideTemplate(SlideTemplate):
    """Template backed by a saved PPTist slide with bindings metadata."""

    def __init__(self, slide_template: Dict[str, Any]) -> None:
        self._template = slide_template
        self.bindings: List[Dict[str, Any]] = slide_template.get("bindings", [])

        template_id = slide_template.get("templateId") or slide_template.get("id")
        if not template_id:
            raise ValueError("Template slide missing templateId or id")

        slide_type_value = slide_template.get("type", "content")
        mapped_type = {
            "contents": "table_of_content",
            "table_of_content": "table_of_content",
            "transition": "chapter",
            "chapter": "chapter",
            "background": "content",
        }.get(slide_type_value, slide_type_value)
        try:
            self.slide_type = SkeletonSupportedType(mapped_type)
        except ValueError:
            self.slide_type = SkeletonSupportedType.CONTENT

        self.layout_id = template_id
        self.priority = slide_template.get("priority", 150)

        base_id = template_id.split("_id_")[0]
        match = re.match(r"(.+?)_(\d+)_items_(\d+)_images$", base_id)
        if match:
            self.count_key = (
                self.slide_type.value,
                int(match.group(2)),
                int(match.group(3)),
            )
        else:
            self.count_key = (self.slide_type.value, None, None)

    def render(self, slide: BaseSkeletonSlide) -> Dict[str, Any]:  # type: ignore[override]
        slide_dict = deepcopy(self._template)
        slide_dict["id"] = slide.unique_id
        slide_dict["from_template"] = self.layout_id

        elements: List[Dict[str, Any]] = slide_dict.get("elements", [])
        element_map: Dict[str, Dict[str, Any]] = {}
        for element in elements:
            template_elem_id = element.get("template_id") or element.get("id")
            if template_elem_id:
                element_map[template_elem_id] = element

        for binding in self.bindings:
            template_element_id = binding.get("template_id") or binding.get("elementId")
            slot = binding.get("slot")
            if not template_element_id or not slot:
                continue

            element = element_map.get(template_element_id)
            if not element:
                continue

            source_obj = self._resolve_source_object(slide, binding.get("source"))
            content_type = binding.get("contentType", "text")

            value = self._extract_value(source_obj, content_type)
            if value in (None, ""):
                value = binding.get("fallback", "")

            target_element_id = self._resolve_element_id(source_obj)

            if content_type in {"text", "richText", "list"}:
                rendered = self._format_text_value(value, content_type, binding)
                original_content = element.get("content", "")
                element["content"] = self._replace_placeholder(original_content, slot, rendered)
                if binding.get("textType"):
                    element["textType"] = binding["textType"]

            elif content_type == "image":
                self._apply_image_binding(element, value, binding)

            if target_element_id:
                element["id"] = target_element_id
            else:
                element["id"] = element.get("id") or element.get("template_id")

        slide_dict.pop("bindings", None)
        return slide_dict

    @staticmethod
    def _resolve_source_object(slide: BaseSkeletonSlide, source: Optional[str]) -> Any:
        if not source:
            return None

        if not source.startswith("slide"):
            return None

        parts = source.split(".")
        current: Any = slide

        for part in parts[1:]:
            if part.startswith("content_blocks["):
                try:
                    index = int(part[(len("content_blocks")+1):part.index("]")])
                except ValueError:
                    return None
                blocks = getattr(slide, "content_blocks", [])
                if index < 0 or index >= len(blocks):
                    return None
                current = blocks[index]
                continue

            if isinstance(current, ContentBlock):
                current = getattr(current, part, None)
            else:
                current = getattr(current, part, None)

            if current is None:
                return None

        return current

    @staticmethod
    def _extract_value(source_obj: Any, content_type: str) -> Any:
        if isinstance(source_obj, TextSkeletonElement):
            return source_obj.content
        if isinstance(source_obj, ImageSkeletonElement):
            return source_obj.src
        if isinstance(source_obj, str):
            return source_obj
        return source_obj

    @staticmethod
    def _resolve_element_id(source_obj: Any) -> Optional[str]:
        if isinstance(source_obj, (TextSkeletonElement, ImageSkeletonElement)):
            return source_obj.unique_id
        return None

    @staticmethod
    def _format_text_value(value: Any, content_type: str, binding: Dict[str, Any]) -> str:
        if value is None:
            value = ""

        if isinstance(value, str):
            text = value
        else:
            text = str(value)

        if content_type == "richText":
            return text

        if content_type == "list":
            if isinstance(value, (list, tuple)):
                items = [escape(str(item)) for item in value]
            else:
                items = [escape(part.strip()) for part in text.splitlines() if part.strip()]
            if not items:
                return ""
            return "<ul>" + "".join(f"<li>{item}</li>" for item in items) + "</ul>"

        escaped = escape(text)
        return escaped.replace("\n", "<br/>")

    @staticmethod
    def _replace_placeholder(original: str, slot: str, rendered: str) -> str:
        placeholder = f"{{{{{slot}}}}}"
        if placeholder in original:
            return original.replace(placeholder, rendered)

        if rendered:
            return rendered
        return original

    @staticmethod
    def _apply_image_binding(element: Dict[str, Any], value: Any, binding: Dict[str, Any]) -> None:
        src = None
        if isinstance(value, str):
            src = value
        elif isinstance(value, dict):
            src = value.get("src")

        if not src:
            src = binding.get("fallback")

        if src:
            element["src"] = src
            element["from_user"] = True


class TemplateRegistry:
    """Registry containing PPTist slide templates only."""

    def __init__(self, template_files: Optional[List[Path]] = None) -> None:
        self.template_files = template_files or [Path("templates/template_1_template.json")]
        self._templates = {template.layout_id: template for template in self._build_templates()}
        self._decision_order = sorted(self._templates.values(), key=lambda t: t.priority, reverse=True)
        self._groups: Dict[Tuple[str, Optional[int], Optional[int]], List[PPTistSlideTemplate]] = {}
        for template in self._templates.values():
            key = getattr(template, "count_key", (template.slide_type.value, None, None))
            self._groups.setdefault(key, []).append(template)
            fallback_key = (template.slide_type.value, None, None)
            if key != fallback_key:
                self._groups.setdefault(fallback_key, []).append(template)

    def _build_templates(self) -> List[SlideTemplate]:
        templates: List[SlideTemplate] = []
        seen_ids: Set[str] = set()

        for file_path in self.template_files:
            if not file_path.exists():
                continue
            try:
                data = json.loads(file_path.read_text(encoding="utf-8"))
            except Exception:
                continue

            slides = data.get("slides", [])
            for idx, slide in enumerate(slides):
                slide_copy = json.loads(json.dumps(slide))

                bindings = slide_copy.get("bindings", [])
                binding_ids = {
                    binding.get("template_id") or binding.get("elementId")
                    for binding in bindings
                    if binding.get("template_id") or binding.get("elementId")
                }

                for element in slide_copy.get("elements", []):
                    if "template_id" not in element:
                        elem_id = element.get("id")
                        if elem_id and elem_id in binding_ids:
                            element["template_id"] = elem_id

                if "templateId" not in slide_copy:
                    slide_copy["templateId"] = f"{file_path.stem}_{idx + 1}"

                template_id = slide_copy["templateId"]
                if template_id in seen_ids:
                    counter = 2
                    while f"{template_id}_v{counter}" in seen_ids:
                        counter += 1
                    template_id = f"{template_id}_v{counter}"
                    slide_copy["templateId"] = template_id
                seen_ids.add(template_id)

                try:
                    templates.append(PPTistSlideTemplate(slide_copy))
                except Exception:
                    continue

        return templates

    def get(self, layout_id: str) -> SlideTemplate:
        try:
            return self._templates[layout_id]
        except KeyError as exc:
            raise KeyError(f"Unknown layout_id '{layout_id}'") from exc

    def decide_for_slide(self, slide: BaseSkeletonSlide) -> SlideTemplate:
        slide_type_value = slide.slide_type.value
        text_count, image_count = self._compute_slide_counts(slide)

        key = (slide_type_value, text_count, image_count)
        candidates = self._groups.get(key)
        if candidates:
            return random.choice(candidates)

        fallback_key = (slide_type_value, None, None)
        candidates = self._groups.get(fallback_key)
        if candidates:
            return random.choice(candidates)

        raise ValueError(
            f"No template matches slide type={slide_type_value} (text={text_count}, image={image_count})"
        )

    def render(self, slide: BaseSkeletonSlide, layout_id: Optional[str] = None) -> Dict[str, Any]:
        """Render slide using a specific layout or by auto-deciding if needed."""
        template = self.get(layout_id) if layout_id else self.decide_for_slide(slide)
        return template.render(slide)

    @staticmethod
    def _compute_slide_counts(slide: BaseSkeletonSlide) -> Tuple[int, int]:
        text_count = 0
        image_count = 0

        if isinstance(slide, CoverSlide):
            text_count = sum(
                1
                for attr in (slide.title, slide.subtitle, slide.author, slide.date)
                if attr is not None and getattr(attr, "content", "")
            )
        elif isinstance(slide, TableOfContentSlide):
            items = getattr(slide, "items", []) or []
            text_count = len(items)
        elif isinstance(slide, ChapterSlide):
            text_count = sum(
                1
                for attr in (slide.chapter_number, slide.title, slide.subtitle)
                if attr is not None and getattr(attr, "content", "")
            )
        elif isinstance(slide, ContentSlide):
            for block in slide.content_blocks or []:
                if block.item_title and getattr(block.item_title, "content", ""):
                    text_count += 1
                elif block.item and getattr(block.item, "content", ""):
                    text_count += 1
                if block.image and getattr(block.image, "src", ""):
                    image_count += 1
        elif isinstance(slide, EndSlide):
            text_count = sum(
                1
                for attr in (slide.title, slide.subtitle)
                if attr is not None and getattr(attr, "content", "")
            )

        return text_count, image_count
