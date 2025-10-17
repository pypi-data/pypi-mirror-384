"""
Universal filtering system for MCPlaywright responses.

This module provides ripgrep-based filtering capabilities that can be applied
to any MCPlaywright tool response, enabling powerful server-side filtering
to reduce response sizes and save client context.
"""

from .models import UniversalFilterParams, FilterMode, FilterResult
from .engine import RipgrepFilterEngine
from .decorators import filter_response

__all__ = [
    "UniversalFilterParams",
    "FilterMode", 
    "FilterResult",
    "RipgrepFilterEngine",
    "filter_response",
]