"""
PresentationStateManager - Central state management for presentations
Handles dual representation (Skeleton + PPTist JSON) with automatic synchronization
"""
import json
import asyncio
import os
from typing import Dict, Any, Optional, Set, Tuple, List
from datetime import datetime
import uuid
import logging

from ii_slide.skeleton.manager import SkeletonManager, PresentationSkeleton
from ii_slide.skeleton.converter import SkeletonConverter
from ii_slide.templates import TemplateRegistry
from ii_slide.pptist.models import Presentation, Slide
from ii_slide.utils import enum_default

logger = logging.getLogger(__name__)


class PresentationStateManager:
    """
    Central manager for presentation state and synchronization.
    Maintains both Skeleton (AI-friendly) and PPTist (frontend) representations.
    """

    def __init__(self):
        self.presentation_id: Optional[str] = None
        self.presentation: Optional[Presentation] = None  # Store Presentation object
        self.template_registry: TemplateRegistry = TemplateRegistry()
        self.skeleton_manager: SkeletonManager = SkeletonManager(template_registry=self.template_registry)
        self.converter: SkeletonConverter = SkeletonConverter(template_registry=self.template_registry)
        self.version: int = 0
        self.clients: Set = set()  # WebSocket connections
        self.last_updated: datetime = datetime.now()
        self.is_initialized: bool = False

        # Auto-initialize from local JSON on startup
        self._load_from_local_json()

    def _load_from_local_json(self) -> bool:
        """
        Load presentation from local JSON files according to requirements:
        1. If sample.json exists, load it and create skeleton from it
        2. If sample.json doesn't exist, create blank skeleton based on template 1 and save as sample.json

        Returns:
            True if loaded/created successfully, False otherwise
        """
        presentation_file = "sample.json"

        # Check if sample.json exists
        if os.path.exists(presentation_file):
            try:
                # Load presentation data and create Presentation object
                logger.info(f"Loading presentation from {presentation_file}")
                with open(presentation_file, 'r', encoding='utf-8') as f:
                    presentation_data = json.load(f)

                self.presentation = Presentation.from_json(presentation_data)
                logger.info(f"Created Presentation object with {len(self.presentation.slides) if self.presentation.slides else 0} slides")

                # Generate skeleton from presentation (always regenerate to ensure sync)
                self.skeleton_manager.skeleton = self.presentation.update_skeleton(PresentationSkeleton())
                logger.info(f"Generated skeleton from presentation with {self.skeleton_manager.skeleton.get_slide_count()} slides")

                # Set initialized state
                self.presentation_id = str(uuid.uuid4())
                self.version = 1
                self.is_initialized = True
                self.last_updated = datetime.now()

                # Save the generated skeleton
                self._save_to_files()

                logger.info(f"Successfully loaded presentation and generated skeleton")
                return True

            except Exception as e:
                logger.error(f"Failed to load presentation: {e}")
                return False
        else:
            # sample.json doesn't exist - create blank skeleton, then create sample.json from skeleton
            try:
                logger.info("No sample.json found - creating blank skeleton")

                # Step 1: Create completely blank skeleton
                self.skeleton_manager = SkeletonManager(template_registry=self.template_registry)
                # Skeleton starts empty - no slides added

                logger.info(f"Created blank skeleton with {self.skeleton_manager.skeleton.get_slide_count()} slides")

                # Step 2: Convert blank skeleton to PPTist format to create sample.json
                pptist_dict = {
                    "slides": [],
                    "width": 960,
                    "height": 540,
                    "theme": {
                        "themeColors": ["#4874CB", "#EE822F", "#F2BA02", "#75BD42", "#30C0B4", "#E54C5E"],
                        "subColors": ["#000000", "#FFFFFF", "#44546A", "#E7E6E6"],
                        "exportThemeColors": [],
                        "fontColor": "#000000",
                        "fontName": "",
                        "backgroundColor": "#FFFFFF",
                        "shadow": None,
                        "outline": None
                    },
                    "type": "",
                    "templateJSONUrl": ""
                }

                # Render each skeleton slide to PPTist format (will be empty initially)
                for slide in self.skeleton_manager.skeleton.slides:
                    ppt_slide_dict = self.converter.render_slide(slide)
                    pptist_dict["slides"].append(ppt_slide_dict)

                # Step 3: Create Presentation object from the skeleton-generated PPTist data
                self.presentation = Presentation.from_json(pptist_dict)
                logger.info(f"Created presentation from blank skeleton with {len(self.presentation.slides)} slides")

                # Set initialized state
                self.presentation_id = str(uuid.uuid4())
                self.version = 1
                self.is_initialized = True
                self.last_updated = datetime.now()

                # Step 4: Save both skeleton.json and sample.json
                self._save_to_files()

                logger.info("Successfully created blank skeleton and generated sample.json from skeleton")
                return True

            except Exception as e:
                logger.error(f"Failed to create blank skeleton and sample.json: {e}")
                return False

    def update_from_frontend(self, pptist_changes: Dict[str, Any]) -> None:
        """
        Update both presentation and skeleton objects from frontend changes.

        Args:
            pptist_changes: Complete PPTist JSON data from frontend
        """
        if not self.is_initialized:
            raise RuntimeError("Presentation not initialized")

        logger.info("Updating presentation and skeleton objects from frontend changes")

        try:
            # Create new Presentation object from frontend data
            self.presentation = Presentation.from_json(pptist_changes)
            logger.info(f"Updated Presentation object with {len(self.presentation.slides) if self.presentation.slides else 0} slides")

            # Update skeleton from presentation
            self.skeleton_manager.skeleton = self.presentation.update_skeleton(
                self.skeleton_manager.skeleton if self.skeleton_manager.skeleton else PresentationSkeleton()
            )
            logger.info(f"Updated PresentationSkeleton object with {self.skeleton_manager.skeleton.get_slide_count()} slides")

            # Save both to files
            self._save_to_files()

            self.version += 1
            self.last_updated = datetime.now()

            logger.info(f"Successfully updated objects and files (version: {self.version})")

        except Exception as e:
            logger.error(f"Error updating from frontend changes: {e}")
            raise

    def _save_to_files(self) -> None:
        """Save both presentation and skeleton objects to JSON files using model_dump"""
        try:
            # Save Presentation object to sample.json
            if self.presentation:
                with open("sample.json", "w", encoding='utf-8') as f:
                    json.dump(self.presentation.model_dump(), f, default=enum_default, indent=2)
                logger.info("Saved Presentation object to sample.json")

            # Save PresentationSkeleton object to skeleton.json
            if self.skeleton_manager.skeleton:
                with open("skeleton.json", "w", encoding='utf-8') as f:
                    json.dump(self.skeleton_manager.skeleton.model_dump(), f, default=enum_default, indent=2)
                logger.info("Saved PresentationSkeleton object to skeleton.json")

        except Exception as e:
            logger.error(f"Error saving objects to files: {e}")

    def init_slide(self, template_id: str = "modern") -> Tuple[SkeletonManager, str]:
        """
        Initialize new presentation - Primary AI entry point.
        First tries to load from local JSON, otherwise creates default.

        Args:
            template_id: Template identifier for styling

        Returns:
            Tuple of (SkeletonManager instance, PPTist JSON string)
        """
        logger.info(f"Initializing presentation with template: {template_id}")

        # If already initialized from local JSON, just return current state
        if self.is_initialized:
            logger.info("Presentation already initialized from local JSON")
            return self.skeleton_manager, self.to_pptist_json()

        # Generate unique presentation ID
        self.presentation_id = str(uuid.uuid4())

        # Reset state
        self.skeleton_manager = SkeletonManager(template_registry=self.template_registry)
        self.version = 0
        self.is_initialized = True
        self.last_updated = datetime.now()

        # Create default presentation structure
        default_pptist_data = {
            "type": "traditional",
            "slides": [],
            "width": 960,
            "height": 540,
            "theme": {
                "themeColors": ["#4874CB", "#EE822F", "#F2BA02", "#75BD42", "#30C0B4", "#E54C5E"],
                "fontColor": "#000000",
                "backgroundColor": "#FFFFFF"
            }
        }

        # Create Presentation and PresentationSkeleton objects
        self.presentation = Presentation.from_json(default_pptist_data)
        self.skeleton_manager.skeleton = self.presentation.update_skeleton(PresentationSkeleton())

        # Broadcast initialization
        self._schedule_async(self._broadcast_update("init", {
            "presentation_id": self.presentation_id,
            "template_id": template_id,
            "skeleton": True,
            "pptist": True
        }))

        return self.skeleton_manager, self.to_pptist_json()

    def get_skeleton_manager(self) -> SkeletonManager:
        """Get the skeleton manager for AI operations"""
        if not self.is_initialized:
            raise RuntimeError("Presentation not initialized. Call init_slide() first.")
        return self.skeleton_manager

    def _ensure_presentation(self) -> Presentation:
        if not self.presentation:
            self.presentation = Presentation(slides=[], type="traditional", width=960, height=540)
        elif self.presentation.slides is None:
            self.presentation.slides = []
        return self.presentation

    def _find_presentation_slide_index(self, slide_id: str) -> Optional[int]:
        if not self.presentation or not self.presentation.slides:
            return None
        for index, slide in enumerate(self.presentation.slides):
            if slide.id == slide_id:
                return index
        return None

    def update_from_skeleton(self) -> str:
        """
        Convert only newly added skeleton slides to PPTist and append them to the
        presentation, preserving existing user edits.

        Returns:
            Updated PPTist JSON string
        """
        if not self.is_initialized:
            raise RuntimeError("Presentation not initialized")

        presentation = self._ensure_presentation()
        skeleton_slides = self.skeleton_manager.skeleton.slides

        existing_map = {slide.id: idx for idx, slide in enumerate(presentation.slides)}
        ppt_updated = False
        new_slides: List[Dict[str, Any]] = []

        for index, skeleton_slide in enumerate(skeleton_slides):
            slide_id = skeleton_slide.unique_id
            if slide_id in existing_map:
                continue

            ppt_slide_dict = self.converter.render_slide(skeleton_slide)
            ppt_slide = Slide.from_dict(ppt_slide_dict)

            presentation.slides.insert(index, ppt_slide)
            ppt_updated = True
            new_slides.append({
                "slide_id": slide_id,
                "index": index
            })

            existing_map = {slide.id: idx for idx, slide in enumerate(presentation.slides)}

        if ppt_updated:
            self.version += 1
            self.last_updated = datetime.now()
            self._save_to_files()
            metadata = {"action": "skeleton_sync"}
            if new_slides:
                metadata["slides"] = new_slides
            self._schedule_async(self._broadcast_skeleton_update(metadata))

        return presentation.to_json()

    def update_slide(self, slide_id: str, slide_data: Dict[str, Any]) -> None:
        """Update specific slide in presentation"""
        if not self.presentation:
            logger.warning("No presentation to update")
            return

        # Get current presentation as dict, modify it, then recreate presentation object
        presentation_dict = self.presentation.model_dump()
        if "slides" not in presentation_dict:
            presentation_dict["slides"] = []

        # Find and update the slide
        for i, slide in enumerate(presentation_dict["slides"]):
            if slide.get("id") == slide_id:
                presentation_dict["slides"][i] = {**slide, **slide_data}
                break
        else:
            # Slide not found, add new one
            slide_data["id"] = slide_id
            presentation_dict["slides"].append(slide_data)

        # Recreate presentation and skeleton objects
        self.presentation = Presentation.from_json(presentation_dict)
        self.skeleton_manager.skeleton = self.presentation.update_skeleton(self.skeleton_manager.skeleton)

        self.version += 1
        self.last_updated = datetime.now()
        self._save_to_files()
        metadata = {
            "action": "update_slide",
            "slide_id": slide_id
        }
        self._schedule_async(self._broadcast_skeleton_update(metadata))

    def update_element(self, slide_id: str, element_id: str, element_data: Dict[str, Any]) -> None:
        """Update specific element in a slide"""
        if not self.presentation:
            logger.warning("No presentation to update")
            return

        # Get current presentation as dict, modify it, then recreate presentation object
        presentation_dict = self.presentation.model_dump()
        if "slides" not in presentation_dict:
            return

        for slide in presentation_dict["slides"]:
            if slide.get("id") == slide_id:
                elements = slide.get("elements", [])
                for i, element in enumerate(elements):
                    if element.get("id") == element_id:
                        elements[i] = {**element, **element_data}
                        break
                else:
                    # Element not found, add new one
                    element_data["id"] = element_id
                    elements.append(element_data)
                slide["elements"] = elements
                break

        # Recreate presentation and skeleton objects
        self.presentation = Presentation.from_json(presentation_dict)
        self.skeleton_manager.skeleton = self.presentation.update_skeleton(self.skeleton_manager.skeleton)

        self.version += 1
        self.last_updated = datetime.now()
        self._save_to_files()
        metadata = {
            "action": "update_element",
            "slide_id": slide_id,
            "element_id": element_id
        }
        self._schedule_async(self._broadcast_skeleton_update(metadata))

    def add_slide(self, slide_data: Dict[str, Any], position: Optional[int] = None) -> str:
        """Add new slide to presentation"""
        if not self.presentation:
            logger.warning("No presentation to update")
            return ""

        # Get current presentation as dict, modify it, then recreate presentation object
        presentation_dict = self.presentation.model_dump()
        if "slides" not in presentation_dict:
            presentation_dict["slides"] = []

        # Generate ID if not provided
        if "id" not in slide_data:
            slide_data["id"] = str(uuid.uuid4())

        # Insert at position or append
        if position is not None:
            presentation_dict["slides"].insert(position, slide_data)
        else:
            presentation_dict["slides"].append(slide_data)

        # Recreate presentation and skeleton objects
        self.presentation = Presentation.from_json(presentation_dict)
        self.skeleton_manager.skeleton = self.presentation.update_skeleton(self.skeleton_manager.skeleton)

        self.version += 1
        self.last_updated = datetime.now()
        self._save_to_files()
        new_index = position if position is not None else len(presentation_dict["slides"]) - 1
        metadata = {
            "action": "add_slide",
            "slide_id": slide_data["id"],
            "index": new_index
        }
        self._schedule_async(self._broadcast_skeleton_update(metadata))

        return slide_data["id"]

    def update_slide_template(self, slide_id: str, layout_id: Optional[str] = None) -> Tuple[str, str]:
        """Re-run or override template selection for a specific slide."""
        if not self.is_initialized:
            raise RuntimeError("Presentation not initialized")

        slide = self.skeleton_manager.update_slide_template(slide_id, layout_id=layout_id)

        presentation = self._ensure_presentation()
        ppt_slide_dict = self.converter.render_slide(slide)
        ppt_slide = Slide.from_dict(ppt_slide_dict)

        insert_index = self._find_presentation_slide_index(slide_id)
        if insert_index is None:
            presentation.slides.append(ppt_slide)
        else:
            presentation.slides[insert_index] = ppt_slide

        self.version += 1
        self.last_updated = datetime.now()
        self._save_to_files()
        metadata = {
            "action": "update_slide_template",
            "slide_id": slide_id,
            "layout_id": slide.layout_id or ""
        }
        slide_type = getattr(slide, "slide_type", None)
        if slide_type:
            metadata["slide_type"] = getattr(slide_type, "value", slide_type)
        self._schedule_async(self._broadcast_skeleton_update(metadata))

        return (slide.layout_id or "", presentation.to_json())

    def remove_slide(self, slide_id: str) -> bool:
        """Remove slide from presentation"""
        if not self.presentation:
            logger.warning("No presentation to update")
            return False

        # Get current presentation as dict, modify it, then recreate presentation object
        presentation_dict = self.presentation.model_dump()
        if "slides" not in presentation_dict:
            return False

        original_count = len(presentation_dict["slides"])
        presentation_dict["slides"] = [
            slide for slide in presentation_dict["slides"]
            if slide.get("id") != slide_id
        ]

        if len(presentation_dict["slides"]) < original_count:
            # Recreate presentation and skeleton objects
            self.presentation = Presentation.from_json(presentation_dict)
            self.skeleton_manager.skeleton = self.presentation.update_skeleton(self.skeleton_manager.skeleton)

            self.version += 1
            self.last_updated = datetime.now()
            self._save_to_files()
            metadata = {
                "action": "remove_slide",
                "slide_id": slide_id
            }
            self._schedule_async(self._broadcast_skeleton_update(metadata))
            return True

        return False

    def to_pptist_json(self) -> str:
        """Export current presentation as PPTist JSON for frontend"""
        if not self.presentation:
            return json.dumps({}, indent=2)

        # Use presentation object's to_json method if available, otherwise model_dump
        if hasattr(self.presentation, 'to_json'):
            return self.presentation.to_json()
        else:
            return json.dumps(self.presentation.model_dump(), indent=2, default=self._json_serializer)

    def to_skeleton_json(self) -> str:
        """Export current skeleton as JSON for AI"""
        if not self.skeleton_manager.skeleton:
            return json.dumps({}, indent=2)

        return json.dumps(self.skeleton_manager.skeleton.model_dump(), indent=2, default=self._json_serializer)

    def get_presentation(self) -> Optional[Presentation]:
        """Get the current presentation object"""
        return self.presentation

    def get_skeleton(self) -> Optional[PresentationSkeleton]:
        """Get the current skeleton object"""
        return self.skeleton_manager.skeleton

    def get_presentation_dict(self) -> Dict[str, Any]:
        """Get current presentation as dictionary for frontend"""
        if not self.presentation:
            return {}
        return self.presentation.model_dump()

    def _json_serializer(self, obj):
        """JSON serializer for model objects"""
        if hasattr(obj, 'value'):  # Enum
            return obj.value
        if hasattr(obj, 'model_dump'):  # Pydantic model
            return obj.model_dump()
        raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

    def get_status(self) -> Dict[str, Any]:
        """Get current state status"""
        return {
            "presentation_id": self.presentation_id,
            "is_initialized": self.is_initialized,
            "version": self.version,
            "last_updated": self.last_updated.isoformat(),
            "slide_count": len(self.presentation.slides) if self.presentation and self.presentation.slides else 0,
            "skeleton_slide_count": self.skeleton_manager.skeleton.get_slide_count() if self.skeleton_manager.skeleton else 0,
            "has_presentation": self.presentation is not None,
            "has_skeleton": self.skeleton_manager.skeleton is not None,
            "connected_clients": len(self.clients)
        }

    def add_client(self, websocket) -> None:
        """Add WebSocket client for real-time updates"""
        self.clients.add(websocket)
        logger.info(f"Client connected. Total clients: {len(self.clients)}")

    def remove_client(self, websocket) -> None:
        """Remove WebSocket client"""
        self.clients.discard(websocket)
        logger.info(f"Client disconnected. Total clients: {len(self.clients)}")

    @staticmethod
    def _schedule_async(coro) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(coro)
        else:
            loop.create_task(coro)

    async def _broadcast_update(self, event_type: str, data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> None:
        """Send real-time updates to connected clients"""
        if not self.clients:
            return

        message = {
            "type": event_type,
            "version": self.version,
            "timestamp": datetime.now().isoformat(),
            "presentation_id": self.presentation_id,
            "data": data,
            "meta": metadata or {}
        }

        # Send to all connected clients
        disconnected_clients = set()
        for client in self.clients:
            try:
                await client.send_text(json.dumps(message, default=enum_default))
            except Exception as e:
                logger.warning(f"Failed to send message to client: {e}")
                disconnected_clients.add(client)

        # Remove disconnected clients
        for client in disconnected_clients:
            self.clients.discard(client)

    async def _broadcast_skeleton_update(self, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Send skeleton update message to frontend clients"""
        if not self.clients:
            return

        # Format message for frontend expecting "skeleton_update" type
        message = {
            "type": "skeleton_update",
            "data": self.get_presentation_dict(),  # Send complete presentation data
            "version": self.version,
            "timestamp": datetime.now().isoformat(),
            "meta": metadata or {}
        }

        # Send to all connected clients
        disconnected_clients = set()
        for client in self.clients:
            try:
                await client.send_text(json.dumps(message, default=enum_default))
                logger.info(f"Sent skeleton update to client (version: {self.version})")
            except Exception as e:
                logger.warning(f"Failed to send skeleton update to client: {e}")
                disconnected_clients.add(client)

        # Remove disconnected clients
        for client in disconnected_clients:
            self.clients.discard(client)

# Global state manager instance
presentation_state = PresentationStateManager()
