"""
Backend module for ii-slide presentation management
"""
from .app import create_app
from .state_manager import PresentationStateManager, presentation_state

__all__ = ["PresentationStateManager", "presentation_state", "create_app"]