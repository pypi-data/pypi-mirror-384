"""
MCP Response Pagination System

Advanced pagination system for managing large response datasets in MCP tools.
Provides cursor-based navigation with performance optimization and session isolation.
"""

from .pagination_manager import (
    PaginationManager,
    PaginatedResponse,
    CursorState,
    QueryState,
    get_pagination_manager,
    cleanup_pagination_manager
)
from .decorators import with_pagination, PaginationParams, PaginationConfig
from .utils import (
    paginate_list, 
    create_pagination_params,
    estimate_response_tokens,
    should_paginate,
    format_pagination_summary,
    create_large_response_warning
)

__all__ = [
    "PaginationManager", 
    "PaginatedResponse", 
    "CursorState", 
    "QueryState",
    "get_pagination_manager",
    "cleanup_pagination_manager",
    "with_pagination",
    "PaginationParams",
    "PaginationConfig",
    "paginate_list",
    "create_pagination_params",
    "estimate_response_tokens",
    "should_paginate",
    "format_pagination_summary",
    "create_large_response_warning"
]