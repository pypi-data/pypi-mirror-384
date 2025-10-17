"""
flet-stack: Component-based routing with automatic view stacking for Flet applications.

A lightweight routing library that provides:
- Decorator-based route definitions with @view
- Automatic view stacking for navigation
- Built-in state management with @ft.observable dataclasses
- Async and sync loading support
- URL parameter extraction
- Component-based architecture using @ft.component
"""

__version__ = "0.2.1"
__author__ = "Fasil"
__email__ = "fasilwdr@hotmail.com"
__license__ = "MIT"

from .router import (
    view,
    FletStack
)

__all__ = [
    "view",
    "FletStack"
]