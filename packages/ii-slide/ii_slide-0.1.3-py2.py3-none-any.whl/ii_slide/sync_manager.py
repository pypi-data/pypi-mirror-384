"""
Backend sync manager for PowerPoint <-> Skeleton synchronization
"""
import asyncio
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, Set
from datetime import datetime
from enum import Enum
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent
import hashlib
import time

from .models import Presentation


class ChangeSource(Enum):
    """Track where changes originated from"""
    FRONTEND = "frontend"
    AI = "ai"
    FILE = "file"
    INITIAL = "initial"


class SyncState(Enum):
    """Track synchronization state"""
    IDLE = "idle"
    AI_PROCESSING = "ai_processing"
    USER_EDITING = "user_editing"
    SYNCING = "syncing"


class SkeletonFileHandler(FileSystemEventHandler):
    """Watch skeleton file for AI-driven changes"""

    def __init__(self, sync_manager):
        self.sync_manager = sync_manager
        self.last_modified_time = 0
        self.debounce_time = 0.5  # 500ms debounce

    def on_modified(self, event):
        if isinstance(event, FileModifiedEvent):
            current_time = time.time()
            if current_time - self.last_modified_time > self.debounce_time:
                self.last_modified_time = current_time

                # Check if this is the skeleton file we're watching
                if event.src_path == str(self.sync_manager.skeleton_file):
                    print(f"[FileWatcher] Detected skeleton file change: {event.src_path}")
                    asyncio.create_task(self.sync_manager.on_skeleton_file_change())


class SyncManager:
    """Manages bidirectional sync between PowerPoint JSON and AI Skeleton"""

    def __init__(self,
                 presentation_file: Path,
                 skeleton_file: Path,
                 auto_start: bool = True):
        self.presentation_file = Path(presentation_file)
        self.skeleton_file = Path(skeleton_file)

        # State management
        self.state = SyncState.IDLE
        self.last_source = ChangeSource.INITIAL

        # Prevent circular updates
        self.update_lock = asyncio.Lock()
        self.ignore_next_file_change = False

        # Track changes for conflict resolution
        self.last_presentation_hash = ""
        self.last_skeleton_hash = ""

        # Modified element tracking
        self.user_modified_elements: Set[str] = set()

        # Presentation object
        self.presentation: Optional[Presentation] = None

        # File watcher
        self.observer = Observer()
        self.file_handler = SkeletonFileHandler(self)

        # Change queue for batching frontend changes
        self.change_queue = []
        self.debounce_timer = None

        if auto_start:
            self.start()

    def start(self):
        """Initialize the sync manager"""
        print("[SyncManager] Starting...")

        # Load initial presentation
        if self.presentation_file.exists():
            self.load_presentation()

        # Initialize skeleton if needed
        if not self.skeleton_file.exists():
            self.create_initial_skeleton()

        # File watching disabled - frontend will request current state via WebSocket
        print(f"[SyncManager] File watching disabled. Skeleton file: {self.skeleton_file}")

    def stop(self):
        """Stop the sync manager"""
        print("[SyncManager] Stopping...")
        # No file observer to stop since file watching is disabled

    def load_presentation(self):
        """Load presentation from JSON file"""
        try:
            with open(self.presentation_file, 'r') as f:
                data = json.load(f)
            self.presentation = Presentation.from_json(data)
            self.last_presentation_hash = self._hash_dict(data)
            print(f"[SyncManager] Loaded presentation with {len(self.presentation.slides)} slides")
        except Exception as e:
            print(f"[SyncManager] Error loading presentation: {e}")

    def create_initial_skeleton(self):
        """Create initial skeleton file from presentation"""
        if self.presentation:
            skeleton = self.presentation.to_skeleton()
            self.save_skeleton(skeleton, ChangeSource.INITIAL)
            print("[SyncManager] Created initial skeleton file")

    def save_skeleton(self, skeleton: Dict[str, Any], source: ChangeSource):
        """Save skeleton to file"""
        self.ignore_next_file_change = (source != ChangeSource.AI)

        with open(self.skeleton_file, 'w') as f:
            json.dump(skeleton, f, indent=2)

        self.last_skeleton_hash = self._hash_dict(skeleton)
        print(f"[SyncManager] Saved skeleton (source: {source.value})")

    def save_presentation(self):
        """Save presentation to JSON file"""
        if self.presentation:
            data = self.presentation.to_dict()

            with open(self.presentation_file, 'w') as f:
                json.dump(data, f, indent=2)

            self.last_presentation_hash = self._hash_dict(data)
            print("[SyncManager] Saved presentation")

    async def on_frontend_change(self,
                                  element_id: str,
                                  change_type: str,
                                  changes: Dict[str, Any]) -> Dict[str, Any]:
        """Handle changes from frontend"""
        async with self.update_lock:
            if self.state == SyncState.AI_PROCESSING:
                return {"status": "error", "message": "AI is processing, please wait"}

            self.state = SyncState.USER_EDITING
            self.last_source = ChangeSource.FRONTEND

            print(f"[Frontend] Change detected - Element: {element_id}, Type: {change_type}")

            # Find and update the element
            element_found = False
            for slide in self.presentation.slides:
                for element in slide.elements:
                    if element.id == element_id:
                        element_found = True

                        if change_type == "content_edit":
                            # Content changes should sync to skeleton
                            if hasattr(element, 'content'):
                                element.content = changes.get('content', element.content)
                            elif hasattr(element, 'src'):
                                element.src = changes.get('src', element.src)

                            # Mark as user modified
                            self.user_modified_elements.add(element_id)

                            # Update skeleton
                            skeleton = self.presentation.to_skeleton()
                            self.save_skeleton(skeleton, ChangeSource.FRONTEND)

                        elif change_type == "style_edit":
                            # Style changes stay local, don't sync to skeleton
                            for key, value in changes.items():
                                if hasattr(element, key):
                                    setattr(element, key, value)

                        break
                if element_found:
                    break

            # Save updated presentation
            self.save_presentation()

            self.state = SyncState.IDLE

            return {
                "status": "success",
                "element_id": element_id,
                "synced_to_skeleton": change_type == "content_edit"
            }

    async def on_skeleton_file_change(self):
        """Handle skeleton file changes (from AI)"""
        if self.ignore_next_file_change:
            self.ignore_next_file_change = False
            print("[FileWatcher] Ignoring self-triggered file change")
            return

        async with self.update_lock:
            if self.state != SyncState.IDLE:
                print(f"[FileWatcher] Skipping - system in {self.state.value} state")
                return

            self.state = SyncState.SYNCING
            self.last_source = ChangeSource.AI

            try:
                # Load new skeleton
                with open(self.skeleton_file, 'r') as f:
                    new_skeleton = json.load(f)

                new_hash = self._hash_dict(new_skeleton)
                if new_hash == self.last_skeleton_hash:
                    print("[FileWatcher] No actual changes detected")
                    return

                print("[AI] Processing skeleton changes")

                # Apply skeleton changes to presentation
                self.apply_skeleton_changes(new_skeleton)

                # Save updated presentation
                self.save_presentation()

                self.last_skeleton_hash = new_hash

                # Notify frontend (would be WebSocket in real implementation)
                print("[AI] Changes applied to presentation")

            except Exception as e:
                print(f"[FileWatcher] Error processing skeleton changes: {e}")
            finally:
                self.state = SyncState.IDLE

    def apply_skeleton_changes(self, skeleton: Dict[str, Any]):
        """Apply skeleton changes to presentation"""
        # Smart merge: preserve user styling while updating content
        self.presentation.update_from_skeleton(skeleton)

        # Clear user modifications for elements that were updated by AI
        for slide_skel in skeleton.get("slides", []):
            for text in slide_skel.get("texts", []):
                if text["id"] in self.user_modified_elements:
                    # AI has updated this element, clear user flag
                    self.user_modified_elements.discard(text["id"])

    def _hash_dict(self, data: Dict[str, Any]) -> str:
        """Create hash of dictionary for change detection"""
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(json_str.encode()).hexdigest()

    def get_status(self) -> Dict[str, Any]:
        """Get current sync status"""
        return {
            "state": self.state.value,
            "last_source": self.last_source.value,
            "presentation_file": str(self.presentation_file),
            "skeleton_file": str(self.skeleton_file),
            "user_modified_elements": list(self.user_modified_elements),
            "slide_count": len(self.presentation.slides) if self.presentation else 0
        }


# Example usage
async def main():
    """Example usage of SyncManager"""

    # Create sync manager
    manager = SyncManager(
        presentation_file=Path("presentation.json"),
        skeleton_file=Path("skeleton.json"),
        auto_start=False
    )

    # Start the manager
    manager.start()

    # Simulate frontend change
    await asyncio.sleep(1)
    result = await manager.on_frontend_change(
        element_id="rf7b-AqA74",
        change_type="content_edit",
        changes={"content": "<p>GOODBYE!</p>"}
    )
    print(f"Frontend change result: {result}")

    # Keep running to watch for file changes
    try:
        await asyncio.sleep(30)
    except KeyboardInterrupt:
        pass
    finally:
        manager.stop()


if __name__ == "__main__":
    asyncio.run(main())