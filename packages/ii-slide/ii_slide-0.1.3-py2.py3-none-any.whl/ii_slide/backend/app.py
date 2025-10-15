"""
FastAPI application for ii-slide backend
Provides REST API and WebSocket endpoints for presentation management
"""
from enum import Enum
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any, Optional, List

# Configure logging BEFORE any other imports that might create loggers
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from ii_slide.pptist.models import Presentation
from ii_slide.backend.state_manager import presentation_state
from ii_slide.skeleton.base import TextSkeletonElement, ImageSkeletonElement, ContentBlock
from ii_slide.skeleton.manager import PresentationSkeleton
from pathlib import Path
from importlib import resources
import os

# Get logger for this module
logger = logging.getLogger(__name__)
logger.info("=" * 60)
logger.info("Starting ii-slide backend with comprehensive logging")
logger.info("Python imports and module loading enabled")
logger.info("=" * 60)


# Request/Response Models
class InitSlideRequest(BaseModel):
    template_id: str = Field(default="modern", description="Template identifier")


class InitSlideResponse(BaseModel):
    presentation_id: str
    skeleton_manager_available: bool
    pptist_json: str


class AddSlideRequest(BaseModel):
    slide_type: str = Field(description="Type of slide to add")
    position: Optional[int] = Field(None, description="Position to insert slide")
    slide_data: Dict[str, Any] = Field(default_factory=dict, description="Additional slide data")


class UpdateSlideRequest(BaseModel):
    slide_data: Dict[str, Any] = Field(description="Slide data to update")


class UpdateElementRequest(BaseModel):
    element_data: Dict[str, Any] = Field(description="Element data to update")


class FrontendChangeRequest(BaseModel):
    changes: Dict[str, Any] = Field(description="Changes from frontend")


class UpdateTemplateRequest(BaseModel):
    layout_id: Optional[str] = Field(
        default=None,
        description="Explicit layout identifier; omit to trigger template decider",
    )


class ContentBlockRequest(BaseModel):
    item_title: Optional[str] = None
    item: Optional[str] = None
    image_src: Optional[str] = None
    image_caption: Optional[str] = None

class AddContentSlideRequest(BaseModel):
    title: str = Field(description="Slide title")
    content_blocks: List[ContentBlockRequest] = Field(default_factory=list, description="Content blocks")


class AddCoverSlideRequest(BaseModel):
    title: str
    subtitle: Optional[str] = None
    author: Optional[str] = None
    date: Optional[str] = None


class AddChapterSlideRequest(BaseModel):
    title: str
    chapter_number: str
    subtitle: Optional[str] = None


class AddTableOfContentsRequest(BaseModel):
    items: List[str]
    title: str = "Contents"


class AddEndSlideRequest(BaseModel):
    title: str = "Thank You"
    subtitle: Optional[str] = None


# Application lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting ii-slide backend")
    yield
    logger.info("Shutting down ii-slide backend")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    app = FastAPI(
        title="ii-slide Backend",
        description="Backend API for AI-powered PowerPoint synchronization",
        version="1.0.0",
        lifespan=lifespan
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount static files for the built frontend
    static_dir_env = os.environ.get("II_SLIDE_STATIC_DIR")
    static_dir: Optional[Path] = None

    if static_dir_env:
        static_dir_candidate = Path(static_dir_env)
        if static_dir_candidate.exists():
            static_dir = static_dir_candidate
            logger.info(f"Using frontend directory from II_SLIDE_STATIC_DIR: {static_dir}")
        else:
            logger.warning(
                "Environment variable II_SLIDE_STATIC_DIR is set to %s but directory does not exist",
                static_dir_candidate,
            )

    if static_dir is None:
        try:
            packaged_dist = resources.files("ii_slide.frontend").joinpath("dist")
            packaged_path = Path(packaged_dist)
            if packaged_path.exists():
                static_dir = packaged_path
                logger.info(f"Mounted packaged frontend assets from {static_dir}")
        except ModuleNotFoundError:
            logger.debug("Packaged frontend assets not found via importlib.resources")

    if static_dir is None:
        repo_dist = Path(__file__).resolve().parents[3] / "frontend_dist"
        if repo_dist.exists():
            static_dir = repo_dist
            logger.info(f"Mounted repository frontend assets from {static_dir}")

    if static_dir is not None and static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    else:
        logger.warning("Static directory not found; frontend assets will not be served")

    # Root endpoint with API information following skeleton_backend.py pattern
    @app.get("/")
    async def root():
        """Root endpoint with API information"""
        return {
            "message": "ii-slide Backend API",
            "version": "1.0.0",
            "endpoints": {
                "slides": {
                    "cover": "POST /slides/cover",
                    "table-of-content": "POST /slides/table-of-content",
                    "chapter": "POST /slides/chapter",
                    "content": "POST /slides/content",
                    "end": "POST /slides/end"
                },
                "presentation": {
                    "get": "GET /presentation",
                    "reset": "DELETE /presentation",
                    "json": "GET /presentation/json"
                },
                "ai": {
                    "init": "POST /api/ai/init_slide",
                    "skeleton": "GET /api/ai/skeleton"
                },
                "frontend": {
                    "presentation": "GET /api/presentation",
                    "websocket": "WS /ws",
                    "app": "GET /app - Vue.js Frontend"
                }
            }
        }

    # AI-focused endpoints (Skeleton interface)
    @app.post("/api/ai/init_slide", response_model=InitSlideResponse)
    async def init_slide(request: InitSlideRequest):
        """Initialize new presentation - AI entry point"""
        try:
            skeleton_manager, pptist_json = presentation_state.init_slide(request.template_id)
            return InitSlideResponse(
                presentation_id="",
                skeleton_manager_available=True,
                pptist_json=pptist_json
            )
        except Exception as e:
            logger.error(f"Error initializing slide: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/ai/skeleton")
    async def get_skeleton():
        """Get current skeleton representation"""
        try:
            if not presentation_state.is_initialized:
                raise HTTPException(status_code=400, detail="Presentation not initialized")

            return JSONResponse({
                "skeleton": presentation_state.to_skeleton_json(),
                "version": presentation_state.version
            })
        except Exception as e:
            logger.error(f"Error getting skeleton: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.put("/api/ai/skeleton")
    async def update_skeleton():
        """AI updates skeleton and syncs to PPTist"""
        try:
            pptist_json = presentation_state.update_from_skeleton()
            return JSONResponse({
                "pptist_json": pptist_json,
                "version": presentation_state.version
            })
        except Exception as e:
            logger.error(f"Error updating from skeleton: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # Slide creation endpoints following skeleton_backend.py pattern
    @app.post("/slides/cover")
    async def add_cover_slide(request: AddCoverSlideRequest):
        """Add a cover slide to the presentation"""
        try:
            skeleton_manager = presentation_state.get_skeleton_manager()
            skeleton_manager.add_cover_slide(
                title=request.title,
                subtitle=request.subtitle,
                author=request.author,
                date=request.date
            )

            # Sync to PPTist
            pptist_json = presentation_state.update_from_skeleton()

            return JSONResponse({
                "message": "Cover slide added successfully",
                "slide_index": len(skeleton_manager.skeleton.slides) - 1,
                "slide": {
                    "type": "cover",
                    "title": request.title,
                    "subtitle": request.subtitle,
                    "author": request.author,
                    "date": request.date
                },
                "pptist_json": pptist_json
            })
        except Exception as e:
            logger.error(f"Error adding cover slide: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/slides/table-of-content")
    async def add_table_of_content_slide(request: AddTableOfContentsRequest):
        """Add a table of contents slide to the presentation"""
        try:
            skeleton_manager = presentation_state.get_skeleton_manager()
            slide = skeleton_manager.add_table_of_contents_slide(
                items=request.items,
                title=request.title
            )

            # Sync to PPTist
            pptist_json = presentation_state.update_from_skeleton()

            return JSONResponse({
                "message": "Table of contents slide added successfully",
                "slide_index": len(skeleton_manager.skeleton.slides) - 1,
                "slide": {
                    "type": "table_of_content",
                    "title": request.title,
                    "items": request.items
                },
                "pptist_json": pptist_json
            })
        except Exception as e:
            logger.error(f"Error adding table of contents slide: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/slides/chapter")
    async def add_chapter_slide(request: AddChapterSlideRequest):
        """Add a chapter slide to the presentation"""
        try:
            skeleton_manager = presentation_state.get_skeleton_manager()
            slide = skeleton_manager.add_chapter_slide(
                title=request.title,
                chapter_number=request.chapter_number,
                subtitle=request.subtitle
            )

            # Sync to PPTist
            pptist_json = presentation_state.update_from_skeleton()

            return JSONResponse({
                "message": "Chapter slide added successfully",
                "slide_index": len(skeleton_manager.skeleton.slides) - 1,
                "slide": {
                    "type": "chapter",
                    "title": request.title,
                    "chapter_number": request.chapter_number,
                    "subtitle": request.subtitle
                },
                "pptist_json": pptist_json
            })
        except Exception as e:
            logger.error(f"Error adding chapter slide: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/slides/content")
    async def add_content_slide(request: AddContentSlideRequest):
        """Add a content slide to the presentation"""
        try:
            skeleton_manager = presentation_state.get_skeleton_manager()

            # Create content blocks using the helper function pattern from skeleton_backend.py
            content_blocks = []
            for block_req in request.content_blocks:
                block = ContentBlock()

                if block_req.item_title:
                    block.item_title = TextSkeletonElement(
                        content=block_req.item_title,
                        text_type="itemTitle"
                    )

                if block_req.item:
                    block.item = TextSkeletonElement(
                        content=block_req.item,
                        text_type="item"
                    )

                if block_req.image_src:
                    block.image = ImageSkeletonElement(
                        src=block_req.image_src,
                        caption=block_req.image_caption
                    )

                content_blocks.append(block)

            # Create title element
            title_element = TextSkeletonElement(content=request.title, text_type="title")

            slide = skeleton_manager.add_content_slide(
                title=title_element,
                content_blocks=content_blocks
            )

            # Sync to PPTist
            pptist_json = presentation_state.update_from_skeleton()

            return JSONResponse({
                "message": "Content slide added successfully",
                "slide_index": len(skeleton_manager.skeleton.slides) - 1,
                "slide": {
                    "type": "content",
                    "title": request.title,
                    "content_blocks_count": len(content_blocks),
                    "template_hint": slide.get_template_hint()
                },
                "pptist_json": pptist_json
            })
        except Exception as e:
            logger.error(f"Error adding content slide: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/slides/end")
    async def add_end_slide(request: AddEndSlideRequest):
        """Add an end slide to the presentation"""
        try:
            skeleton_manager = presentation_state.get_skeleton_manager()
            slide = skeleton_manager.add_end_slide(
                title=request.title,
                subtitle=request.subtitle
            )

            # Sync to PPTist
            pptist_json = presentation_state.update_from_skeleton()

            return JSONResponse({
                "message": "End slide added successfully",
                "slide_index": len(skeleton_manager.skeleton.slides) - 1,
                "slide": {
                    "type": "end",
                    "title": request.title,
                    "subtitle": request.subtitle
                },
                "pptist_json": pptist_json
            })
        except Exception as e:
            logger.error(f"Error adding end slide: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/slides/{slide_id}/template")
    async def update_slide_template(slide_id: str, request: UpdateTemplateRequest):
        """Re-select or override the template used for a slide."""
        try:
            layout_id, pptist_json = presentation_state.update_slide_template(
                slide_id,
                request.layout_id,
            )
            return JSONResponse({
                "message": "Slide template updated successfully",
                "slide_id": slide_id,
                "layout_id": layout_id,
                "auto_selected": request.layout_id is None,
                "pptist_json": pptist_json,
            })
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except Exception as e:
            logger.error(f"Error updating slide template: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # Presentation management endpoints following skeleton_backend.py pattern
    @app.get("/presentation")
    async def get_presentation():
        """Get the current presentation skeleton"""
        try:
            if not presentation_state.is_initialized:
                raise HTTPException(status_code=400, detail="Presentation not initialized")

            skeleton_manager = presentation_state.get_skeleton_manager()
            return JSONResponse({
                "presentation": skeleton_manager.skeleton.model_dump(),
                "slide_count": skeleton_manager.skeleton.get_slide_count(),
                "version": presentation_state.version
            })
        except Exception as e:
            logger.error(f"Error getting presentation: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.delete("/presentation")
    async def reset_presentation():
        """Reset the presentation (clear all slides)"""
        try:
            # Reinitialize the presentation
            presentation_state.init_slide("modern")

            return JSONResponse({
                "message": "Presentation reset successfully",
                "presentation_id": presentation_state.presentation_id
            })
        except Exception as e:
            logger.error(f"Error resetting presentation: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/presentation/json")
    async def get_presentation_json():
        """Get the presentation skeleton as JSON"""
        try:
            if not presentation_state.is_initialized:
                raise HTTPException(status_code=400, detail="Presentation not initialized")

            return JSONResponse({
                "json": presentation_state.to_skeleton_json(),
                "version": presentation_state.version
            })
        except Exception as e:
            logger.error(f"Error getting presentation JSON: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # Frontend endpoints (PPTist interface)
    @app.get("/api/presentation")
    async def get_presentation_pptist():
        """Get current PPTist JSON for frontend"""
        try:
            if not presentation_state.is_initialized:
                raise HTTPException(status_code=400, detail="Presentation not initialized")

            return JSONResponse({
                "presentation": presentation_state.pptist_json,
                "version": presentation_state.version
            })
        except Exception as e:
            logger.error(f"Error getting PPTist presentation: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.put("/api/presentation/slide/{slide_id}")
    async def update_slide(slide_id: str, request: UpdateSlideRequest):
        """Update specific slide"""
        try:
            presentation_state.update_slide(slide_id, request.slide_data)
            return JSONResponse({
                "slide_id": slide_id,
                "version": presentation_state.version,
                "status": "updated"
            })
        except Exception as e:
            logger.error(f"Error updating slide {slide_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.put("/api/presentation/slide/{slide_id}/element/{element_id}")
    async def update_element(slide_id: str, element_id: str, request: UpdateElementRequest):
        """Update specific element in a slide"""
        try:
            presentation_state.update_element(slide_id, element_id, request.element_data)
            return JSONResponse({
                "slide_id": slide_id,
                "element_id": element_id,
                "version": presentation_state.version,
                "status": "updated"
            })
        except Exception as e:
            logger.error(f"Error updating element {element_id} in slide {slide_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/presentation/slide")
    async def add_slide_to_presentation(request: AddSlideRequest):
        """Add new slide to presentation"""
        try:
            slide_id = presentation_state.add_slide(request.slide_data, request.position)
            return JSONResponse({
                "slide_id": slide_id,
                "position": request.position,
                "version": presentation_state.version,
                "status": "added"
            })
        except Exception as e:
            logger.error(f"Error adding slide: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.delete("/api/presentation/slide/{slide_id}")
    async def remove_slide_from_presentation(slide_id: str):
        """Remove slide from presentation"""
        try:
            success = presentation_state.remove_slide(slide_id)
            if not success:
                raise HTTPException(status_code=404, detail="Slide not found")

            return JSONResponse({
                "slide_id": slide_id,
                "version": presentation_state.version,
                "status": "removed"
            })
        except Exception as e:
            logger.error(f"Error removing slide {slide_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    def enum_default(o):
        if isinstance(o, Enum):
            return o.value
        if hasattr(o, 'model_dump'):
            return o.model_dump()
        raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")

    @app.post("/api/frontend-change")
    async def handle_frontend_change(request: FrontendChangeRequest):
        """Handle changes from frontend UI"""
        try:
            # DEBUG: Log the entire JSON received from frontend
            logger.info("=" * 80)
            logger.info("🔵 FRONTEND CHANGE RECEIVED")
            logger.info("=" * 80)

            # Log specific details
            if "slides" in request.changes:
                logger.info(f"📊 Number of slides: {len(request.changes['slides'])}")
                for i, slide in enumerate(request.changes['slides']):
                    logger.info(f"  Slide {i}: {slide.get('type', 'unknown')} - {slide.get('id', 'no-id')}")
                    if 'elements' in slide:
                        logger.info(f"    Elements: {len(slide['elements'])}")
                        for elem in slide['elements']:
                            logger.info(f"      - {elem.get('type', 'unknown')}: {elem.get('id', 'no-id')}")

            if "theme" in request.changes:
                logger.info(f"🎨 Theme update: {request.changes['theme']}")

            if "title" in request.changes:
                logger.info(f"📝 Title: {request.changes['title']}")

            logger.info("=" * 80)

            # Auto-initialize if not already initialized
            if not presentation_state.is_initialized:
                logger.info("Auto-initializing presentation for frontend changes")
                presentation_state.init_slide("modern")

            # Update all representations in memory and save to files
            presentation_state.update_from_frontend(request.changes)

            logger.info("✅ Successfully updated all representations in memory")
            logger.info(f"   Version: {presentation_state.version}")
            logger.info(f"   Slides count: {len(request.changes.get('slides', []))}")

            # Return response
            return JSONResponse({
                "version": presentation_state.version,
                "status": "updated",
                "message": "Successfully updated presentation, skeleton, and saved to files",
                "slides_count": len(request.changes.get('slides', [])),
                "timestamp": presentation_state.last_updated.isoformat()
            })

        except Exception as e:
            logger.error(f"Error handling frontend change: {e}")
            return JSONResponse({
                "version": presentation_state.version,
                "status": "error",
                "message": f"Failed to process frontend changes: {str(e)}"
            }, status_code=500)

    # Synchronization endpoints
    @app.get("/api/sync/status")
    async def get_sync_status():
        """Get current synchronization status"""
        return JSONResponse(presentation_state.get_status())

    @app.post("/api/sync/skeleton_to_pptist")
    async def force_skeleton_to_pptist_sync():
        """Force synchronization from skeleton to PPTist"""
        try:
            pptist_json = presentation_state.update_from_skeleton()
            return JSONResponse({
                "pptist_json": pptist_json,
                "version": presentation_state.version,
                "status": "synced"
            })
        except Exception as e:
            logger.error(f"Error forcing skeleton to PPTist sync: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/sync/pptist_to_skeleton")
    async def force_pptist_to_skeleton_sync():
        """Force synchronization from PPTist to skeleton"""
        try:
            # This would trigger the reverse sync
            presentation_state.update_from_frontend({"force_sync": True})
            return JSONResponse({
                "skeleton": presentation_state.to_skeleton_json(),
                "version": presentation_state.version,
                "status": "synced"
            })
        except Exception as e:
            logger.error(f"Error forcing PPTist to skeleton sync: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # WebSocket endpoint
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for real-time updates"""
        await websocket.accept()
        presentation_state.add_client(websocket)

        try:
            # Send connection confirmation
            await websocket.send_text(json.dumps({
                "type": "connected",
                "timestamp": datetime.now().isoformat()
            }))

            # Auto-initialize if not already initialized
            if not presentation_state.is_initialized:
                logger.info("Auto-initializing presentation for new WebSocket connection")
                presentation_state.init_slide("modern")

            # Keep connection alive and handle messages
            while True:
                try:
                    # Wait for messages from client
                    message = await websocket.receive_text()
                    logger.info(f"Received WebSocket message: {message}")

                    # Parse and handle client messages
                    try:
                        msg_data = json.loads(message)

                        # Handle request for current state
                        if msg_data.get("type") == "request_current_state":
                            if presentation_state.is_initialized:
                                # Get current presentation as dictionary from memory
                                presentation_dict = presentation_state.get_presentation_dict()
                                logger.info(f"📤 Sending current presentation state: {len(presentation_dict.get('slides', []))} slides")
                                await websocket.send_text(json.dumps({
                                    "type": "current_state",
                                    "presentation": presentation_dict,
                                    "timestamp": datetime.now().isoformat()
                                }, default = enum_default, indent=2))
                                logger.info("✅ Successfully sent current presentation state to client")
                            else:
                                logger.info("❌ No presentation initialized, sending error to client")
                                await websocket.send_text(json.dumps({
                                    "type": "current_state",
                                    "error": "No presentation initialized",
                                    "timestamp": datetime.now().isoformat()
                                }))

                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON received: {message}")

                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"WebSocket error: {e}")
                    break

        finally:
            presentation_state.remove_client(websocket)

    # Health check
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy", "service": "ii-slide-backend"}

    # Serve frontend at root (catch-all route for SPA)
    from fastapi.responses import FileResponse, RedirectResponse
    @app.get("/app/{full_path:path}")
    async def serve_frontend_app(full_path: str):
        """Serve the built Vue.js frontend application"""
        static_dir = os.getenv("II_SLIDE_STATIC_DIR")
        file_path = os.path.join(static_dir, full_path)

        # If file exists, serve it
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)

        # Otherwise, serve index.html for SPA routing
        index_path = os.path.join(static_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)

        raise HTTPException(status_code=404, detail="Frontend not found")

    @app.get("/app/")
    async def serve_frontend_index():
        """Serve the SPA index file when the trailing slash is present"""
        return await serve_frontend_app("")

    @app.get("/app")
    async def serve_frontend_root():
        """Redirect bare /app requests to /app/ so relative asset paths resolve correctly"""
        return RedirectResponse(url="/app/", status_code=307)

    return app


# Create app instance for uvicorn
app = create_app()
