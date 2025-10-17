"""
Data models for the universal filtering system.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class FilterMode(str, Enum):
    """Ripgrep output modes for filtering."""
    CONTENT = "content"              # Show matching lines with content
    FILES_WITH_MATCHES = "files"     # Show only items that have matches
    COUNT = "count"                  # Show count of matches per item


class UniversalFilterParams(BaseModel):
    """Universal filtering parameters that can be applied to any MCPlaywright tool."""
    
    filter_pattern: Optional[str] = Field(
        None,
        description="Ripgrep pattern to search for (supports full regex)",
        json_schema_extra={"example": "api\\/v[0-9]+\\/users"}
    )

    filter_fields: Optional[List[str]] = Field(
        None,
        description="Specific fields to search in (if not provided, searches all filterable fields)",
        json_schema_extra={"example": ["url", "method", "status"]}
    )
    
    filter_mode: FilterMode = Field(
        FilterMode.CONTENT,
        description="How to present filtered results"
    )
    
    case_sensitive: bool = Field(
        False,
        description="Whether pattern matching should be case sensitive"
    )
    
    whole_words: bool = Field(
        False,
        description="Match whole words only (equivalent to ripgrep -w flag)"
    )
    
    context_lines: Optional[int] = Field(
        None,
        ge=0,
        le=20,
        description="Number of context lines to show before and after matches"
    )
    
    context_before: Optional[int] = Field(
        None,
        ge=0,
        le=20,
        description="Number of context lines to show before matches"
    )
    
    context_after: Optional[int] = Field(
        None,
        ge=0,
        le=20,
        description="Number of context lines to show after matches"
    )
    
    invert_match: bool = Field(
        False,
        description="Invert match (show non-matching results)"
    )
    
    multiline: bool = Field(
        False,
        description="Enable multiline pattern matching"
    )
    
    max_matches: Optional[int] = Field(
        None,
        ge=1,
        le=10000,
        description="Maximum number of matches to return"
    )
    
    @field_validator('filter_fields')
    @classmethod
    def validate_filter_fields(cls, v):
        """Ensure filter fields are non-empty strings."""
        if v is not None:
            if not v:
                raise ValueError("filter_fields cannot be empty list")
            for field in v:
                if not isinstance(field, str) or not field.strip():
                    raise ValueError("All filter fields must be non-empty strings")
        return v

    @field_validator('filter_pattern')
    @classmethod
    def validate_pattern(cls, v):
        """Basic validation for filter pattern."""
        if v is not None and not v.strip():
            raise ValueError("filter_pattern cannot be empty string")
        return v


class FilterResult(BaseModel):
    """Result of applying filtering to data."""
    
    filtered_data: Any = Field(
        description="The filtered data in the same structure as input"
    )
    
    match_count: int = Field(
        description="Total number of matches found"
    )
    
    total_items: int = Field(
        description="Total number of items examined"
    )
    
    filtered_items: int = Field(
        description="Number of items that contained matches"
    )
    
    filter_summary: Dict[str, Any] = Field(
        description="Summary of filtering operation"
    )
    
    execution_time_ms: float = Field(
        description="Time taken to execute filtering in milliseconds"
    )
    
    pattern_used: str = Field(
        description="The actual pattern used for filtering"
    )
    
    fields_searched: List[str] = Field(
        description="Fields that were searched"
    )


class FilterableField(BaseModel):
    """Configuration for a filterable field in a tool response."""
    
    field_name: str = Field(
        description="Name of the field"
    )
    
    field_type: str = Field(
        description="Type of field: string, array, object, number"
    )
    
    searchable: bool = Field(
        True,
        description="Whether this field can be searched with text patterns"
    )
    
    nested_path: Optional[str] = Field(
        None,
        description="Dot notation path for nested fields (e.g., 'headers.content-type')"
    )
    
    description: Optional[str] = Field(
        None,
        description="Human-readable description of what this field contains"
    )


class ToolFilterConfig(BaseModel):
    """Configuration defining how filtering should work for a specific tool."""
    
    tool_name: str = Field(
        description="Name of the MCPlaywright tool"
    )
    
    filterable_fields: List[FilterableField] = Field(
        description="Fields that can be filtered in this tool's response"
    )
    
    default_fields: List[str] = Field(
        description="Default fields to search when no specific fields are provided"
    )
    
    content_fields: List[str] = Field(
        description="Fields that contain large text content suitable for full-text search"
    )
    
    supports_streaming: bool = Field(
        False,
        description="Whether this tool supports streaming filtering for large responses"
    )
    
    max_response_size: Optional[int] = Field(
        None,
        description="Maximum response size before streaming filtering is recommended"
    )