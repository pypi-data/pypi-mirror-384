"""
Decorators for applying universal filtering to MCPlaywright tool responses.
"""

import asyncio
import logging
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union

from .engine import RipgrepFilterEngine
from .models import UniversalFilterParams, ToolFilterConfig

logger = logging.getLogger(__name__)


def filter_response(
    filterable_fields: List[str],
    content_fields: Optional[List[str]] = None,
    default_fields: Optional[List[str]] = None,
    supports_streaming: bool = False,
    max_response_size: Optional[int] = None
):
    """
    Decorator to add ripgrep filtering capabilities to MCPlaywright tools.
    
    This decorator integrates seamlessly with the existing pagination system
    and provides powerful server-side filtering to reduce response sizes.
    
    Args:
        filterable_fields: List of fields that can be filtered
        content_fields: Fields containing large text content for full-text search
        default_fields: Default fields to search when none specified
        supports_streaming: Whether tool supports streaming for large responses
        max_response_size: Size threshold for recommending streaming
        
    Example:
        @filter_response(
            filterable_fields=["url", "method", "status", "headers"],
            content_fields=["request_body", "response_body"],
            default_fields=["url", "method", "status"]
        )
        @paginate_response(default_limit=50, max_limit=1000)
        async def browser_get_requests(params: RequestMonitoringParams):
            # Tool implementation
    """
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            
            # Extract filter parameters from kwargs
            filter_params = _extract_filter_params(kwargs)
            
            # If no filtering requested, execute normally
            if not filter_params or not filter_params.filter_pattern:
                return await func(*args, **kwargs)
            
            # Execute the original function to get full response
            response = await func(*args, **kwargs)
            
            # Apply filtering to the response
            filtered_response = await _apply_filtering(
                response,
                filter_params,
                filterable_fields,
                content_fields or default_fields or filterable_fields,
                supports_streaming,
                max_response_size
            )
            
            return filtered_response
            
        # Add metadata about filtering capabilities
        wrapper._filter_config = ToolFilterConfig(
            tool_name=func.__name__,
            filterable_fields=[
                {"field_name": field, "field_type": "string", "searchable": True}
                for field in filterable_fields
            ],
            default_fields=default_fields or filterable_fields[:3],  # First 3 as default
            content_fields=content_fields or [],
            supports_streaming=supports_streaming,
            max_response_size=max_response_size
        )
        
        return wrapper
    
    return decorator


def _extract_filter_params(kwargs: Dict[str, Any]) -> Optional[UniversalFilterParams]:
    """Extract filtering parameters from function kwargs."""
    
    # Look for filter parameters in various possible locations
    filter_data = {}
    
    # Check direct parameters (for functions that accept filter params directly)
    filter_param_names = [
        'filter_pattern', 'filter_fields', 'filter_mode', 'case_sensitive',
        'whole_words', 'context_lines', 'context_before', 'context_after',
        'invert_match', 'multiline', 'max_matches'
    ]
    
    for param_name in filter_param_names:
        if param_name in kwargs:
            filter_data[param_name] = kwargs.pop(param_name)
    
    # Check if parameters are nested in a params object
    if 'params' in kwargs and hasattr(kwargs['params'], '__dict__'):
        params_obj = kwargs['params']
        for param_name in filter_param_names:
            if hasattr(params_obj, param_name):
                value = getattr(params_obj, param_name)
                if value is not None:
                    filter_data[param_name] = value
    
    # Create UniversalFilterParams if we found any filter data
    if filter_data:
        try:
            return UniversalFilterParams(**filter_data)
        except Exception as e:
            logger.warning(f"Invalid filter parameters: {e}")
            return None
    
    return None


async def _apply_filtering(
    response: Any,
    filter_params: UniversalFilterParams,
    filterable_fields: List[str],
    content_fields: List[str],
    supports_streaming: bool,
    max_response_size: Optional[int]
) -> Any:
    """Apply filtering to the response data."""
    
    try:
        # Initialize the filtering engine
        engine = RipgrepFilterEngine()
        
        # Determine if we should use streaming based on response size
        use_streaming = _should_use_streaming(
            response,
            supports_streaming,
            max_response_size
        )
        
        if use_streaming:
            # Use streaming filtering for large responses
            return await _apply_streaming_filtering(
                response,
                filter_params,
                filterable_fields,
                content_fields,
                engine
            )
        else:
            # Use standard filtering
            filter_result = await engine.filter_response(
                response,
                filter_params,
                filterable_fields,
                content_fields
            )
            
            # Return the filtered data with metadata
            return _prepare_filtered_response(response, filter_result)
    
    except Exception as e:
        logger.error(f"Filtering failed: {e}")
        # Return original response if filtering fails
        return response


def _should_use_streaming(
    response: Any,
    supports_streaming: bool,
    max_response_size: Optional[int]
) -> bool:
    """Determine if streaming filtering should be used."""
    
    if not supports_streaming:
        return False
    
    if max_response_size is None:
        return False
    
    # Estimate response size
    try:
        if isinstance(response, list):
            response_size = len(response)
        elif isinstance(response, dict):
            response_size = len(str(response))
        else:
            response_size = len(str(response))
        
        return response_size > max_response_size
    
    except Exception:
        return False


async def _apply_streaming_filtering(
    response: Any,
    filter_params: UniversalFilterParams,
    filterable_fields: List[str],
    content_fields: List[str],
    engine: RipgrepFilterEngine
) -> Any:
    """Apply streaming filtering for large responses."""
    
    # Convert response to async iterator
    async def response_iterator():
        if isinstance(response, list):
            for item in response:
                yield item
        else:
            yield response
    
    # Apply streaming filtering
    filtered_chunks = []
    async for chunk_result in engine.filter_streaming_response(
        response_iterator(),
        filter_params,
        filterable_fields,
        chunk_size=100
    ):
        if chunk_result.filtered_data:
            if isinstance(chunk_result.filtered_data, list):
                filtered_chunks.extend(chunk_result.filtered_data)
            else:
                filtered_chunks.append(chunk_result.filtered_data)
    
    return {
        "filtered_data": filtered_chunks,
        "streaming": True,
        "total_chunks_processed": len(filtered_chunks)
    }


def _prepare_filtered_response(original_response: Any, filter_result) -> Any:
    """Prepare the final filtered response with metadata."""
    
    # For paginated responses, preserve pagination structure
    if isinstance(original_response, dict) and "data" in original_response:
        # Looks like a paginated response
        return {
            **original_response,
            "data": filter_result.filtered_data,
            "filter_applied": True,
            "filter_metadata": {
                "match_count": filter_result.match_count,
                "total_items": filter_result.total_items,
                "filtered_items": filter_result.filtered_items,
                "execution_time_ms": filter_result.execution_time_ms,
                "pattern_used": filter_result.pattern_used,
                "fields_searched": filter_result.fields_searched
            }
        }
    
    # For list responses with filtering metadata
    elif isinstance(filter_result.filtered_data, list):
        return {
            "data": filter_result.filtered_data,
            "filter_applied": True,
            "filter_metadata": {
                "match_count": filter_result.match_count,
                "total_items": filter_result.total_items,
                "filtered_items": filter_result.filtered_items,
                "execution_time_ms": filter_result.execution_time_ms,
                "pattern_used": filter_result.pattern_used,
                "fields_searched": filter_result.fields_searched
            }
        }
    
    # For simple responses, return the filtered data directly
    else:
        return filter_result.filtered_data


def get_tool_filter_config(func: Callable) -> Optional[ToolFilterConfig]:
    """Get the filter configuration for a decorated tool function."""
    return getattr(func, '_filter_config', None)


def list_filterable_tools() -> Dict[str, ToolFilterConfig]:
    """List all tools that support filtering and their configurations."""
    # This would be populated by a registry system in a full implementation
    # For now, return empty dict - this could be extended to scan decorated functions
    return {}


class FilterRegistry:
    """Registry for tracking filterable tools and their configurations."""
    
    def __init__(self):
        self._tools: Dict[str, ToolFilterConfig] = {}
    
    def register_tool(self, tool_name: str, config: ToolFilterConfig):
        """Register a tool's filter configuration."""
        self._tools[tool_name] = config
    
    def get_tool_config(self, tool_name: str) -> Optional[ToolFilterConfig]:
        """Get filter configuration for a tool."""
        return self._tools.get(tool_name)
    
    def list_filterable_tools(self) -> Dict[str, ToolFilterConfig]:
        """List all registered filterable tools."""
        return self._tools.copy()
    
    def get_available_fields(self, tool_name: str) -> List[str]:
        """Get list of filterable fields for a tool."""
        config = self._tools.get(tool_name)
        if config:
            return [field.field_name for field in config.filterable_fields]
        return []


# Global filter registry instance
filter_registry = FilterRegistry()