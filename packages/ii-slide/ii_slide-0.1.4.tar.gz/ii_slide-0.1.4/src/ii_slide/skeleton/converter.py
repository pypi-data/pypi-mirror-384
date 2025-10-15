"""Skeleton ↔ PPTist conversion built on the template registry."""
from __future__ import annotations

from typing import Dict, Optional

from ii_slide.templates import TemplateRegistry
from .manager import PresentationSkeleton
from .slides import BaseSkeletonSlide


class SkeletonConverter:
    """Converts between the skeleton representation and PPTist JSON."""

    def __init__(self, template_registry: Optional[TemplateRegistry] = None) -> None:
        self.template_registry = template_registry or TemplateRegistry()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def skeleton_to_powerpoint(self, skeleton: PresentationSkeleton) -> Dict[str, object]:
        """Render the entire skeleton into PPTist JSON."""
        ppt_slides = []
        for slide in skeleton.slides:
            ppt_slide = self.render_slide(slide)
            if ppt_slide:
                ppt_slides.append(ppt_slide)

        return {
            "type": "traditional",
            "slides": ppt_slides,
            "width": 960,
            "height": 540,
            "theme": self._default_theme(),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def render_slide(self, slide: BaseSkeletonSlide) -> Dict[str, object]:
        layout_id = slide.layout_id

        if layout_id:
            template = self.template_registry.get(layout_id)
        else:
            template = self.template_registry.decide_for_slide(slide)
            slide.layout_id = template.layout_id

        return template.render(slide)

    @staticmethod
    def _default_theme() -> Dict[str, object]:
        # Keep a simple default to avoid surprising style changes
        return {
            "themeColors": ["#4874CB", "#EE822F", "#F2BA02", "#75BD42", "#30C0B4", "#E54C5E"],
            "subColors": ["#000000", "#FFFFFF", "#44546A", "#E7E6E6"],
            "exportThemeColors": [],
            "fontColor": "#000000",
            "backgroundColor": "#FFFFFF",
        }
