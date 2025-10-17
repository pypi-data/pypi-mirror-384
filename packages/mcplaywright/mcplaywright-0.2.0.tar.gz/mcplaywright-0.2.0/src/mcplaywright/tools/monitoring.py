"""
HTTP Request Monitoring Tools for MCPlaywright

Advanced HTTP request/response interception and analysis capabilities.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from ..session_manager import get_session_manager
from .video import begin_video_action_for_session, end_video_action_for_session
from ..pagination.models import (
    RequestMonitoringParams, PaginatedResponse, PaginationMetadata, QueryState
)
from ..pagination.cursor_manager import CursorNotFoundError, CursorExpiredError, CrossSessionAccessError
from ..filters.decorators import filter_response

logger = logging.getLogger(__name__)


class StartRequestMonitoringParams(BaseModel):
    """Parameters for starting HTTP request monitoring"""
    session_id: Optional[str] = Field(None, description="Session ID")
    capture_body: Optional[bool] = Field(True, description="Whether to capture request and response bodies")
    max_body_size: Optional[int] = Field(10485760, description="Maximum body size to capture in bytes (10MB default)")
    url_filter: Optional[str] = Field(None, description="Filter URLs to capture (string contains match)")
    output_path: Optional[str] = Field(None, description="Custom output directory path")
    auto_save: Optional[bool] = Field(False, description="Automatically save captured requests after each response")


# Note: GetRequestsParams now uses RequestMonitoringParams from pagination.models
# This provides cursor-based pagination for HTTP request monitoring


class ExportRequestsParams(BaseModel):
    """Parameters for exporting captured requests"""
    session_id: Optional[str] = Field(None, description="Session ID")
    format: Optional[str] = Field("json", description="Export format: 'json', 'har', 'csv', 'summary'")
    filename: Optional[str] = Field(None, description="Custom filename for export")
    include_body: Optional[bool] = Field(False, description="Include request/response bodies in export")
    filter: Optional[str] = Field("all", description="Filter which requests to export")


class ClearRequestsParams(BaseModel):
    """Parameters for clearing captured requests"""
    session_id: Optional[str] = Field(None, description="Session ID")


async def browser_start_request_monitoring(params: StartRequestMonitoringParams) -> Dict[str, Any]:
    """
    Enable comprehensive HTTP request/response interception and analysis.
    
    Captures headers, bodies, timing, and failure information for all browser
    traffic. Essential for security testing, API analysis, and performance debugging.
    
    Features:
    - Complete request/response capture
    - Body content capture with size limits
    - URL filtering and pattern matching
    - Performance timing analysis
    - Automatic export capabilities
    - Session-based storage organization
    
    Returns:
        Request monitoring startup result with configuration details
    """
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_or_create_session(params.session_id)
        
        # Begin video action
        await context.begin_video_action("start_request_monitoring")
        
        # Get current page
        page = await context.get_current_page()
        
        logger.info("Starting HTTP request monitoring")
        
        # Create monitoring directory
        if params.output_path:
            monitoring_dir = Path(params.output_path)
        else:
            monitoring_dir = context.artifacts_dir / "requests"
        
        monitoring_dir.mkdir(exist_ok=True)
        
        # Initialize request storage for this session
        if not hasattr(context, '_captured_requests'):
            context._captured_requests = []
        
        # Configuration for monitoring
        monitoring_config = {
            "capture_body": params.capture_body,
            "max_body_size": params.max_body_size,
            "url_filter": params.url_filter,
            "output_path": str(monitoring_dir),
            "auto_save": params.auto_save,
            "start_time": datetime.now().isoformat()
        }
        
        # Store config in context
        context._request_monitoring_config = monitoring_config
        
        # Set up request interception
        async def request_handler(request):
            try:
                # Apply URL filter if specified
                if params.url_filter and params.url_filter not in request.url:
                    return
                
                request_start_time = datetime.now()
                
                # Capture request information
                request_info = {
                    "id": f"req_{len(context._captured_requests) + 1}",
                    "url": request.url,
                    "method": request.method,
                    "headers": dict(request.headers),
                    "resource_type": request.resource_type,
                    "start_time": request_start_time.isoformat(),
                    "timing": {"start": request_start_time.timestamp()}
                }
                
                # Capture request body if enabled and available
                if params.capture_body:
                    try:
                        post_data = request.post_data
                        if post_data and len(post_data) <= params.max_body_size:
                            request_info["request_body"] = post_data
                        elif post_data:
                            request_info["request_body"] = f"<Body too large: {len(post_data)} bytes>"
                    except Exception as body_error:
                        request_info["request_body_error"] = str(body_error)
                
                # Store request info temporarily
                context._captured_requests.append(request_info)
                
                logger.debug(f"Captured request: {request.method} {request.url}")
                
            except Exception as e:
                logger.error(f"Request handler error: {str(e)}")
        
        async def response_handler(response):
            try:
                # Apply URL filter if specified
                if params.url_filter and params.url_filter not in response.url:
                    return
                
                response_end_time = datetime.now()
                
                # Find matching request
                matching_request = None
                for req in context._captured_requests:
                    if req["url"] == response.url and "response" not in req:
                        matching_request = req
                        break
                
                if not matching_request:
                    return
                
                # Update request with response information
                matching_request.update({
                    "response": {
                        "status": response.status,
                        "status_text": response.status_text,
                        "headers": dict(response.headers),
                        "end_time": response_end_time.isoformat(),
                        "ok": response.ok
                    },
                    "timing": {
                        **matching_request["timing"],
                        "end": response_end_time.timestamp(),
                        "duration_ms": int((response_end_time.timestamp() - matching_request["timing"]["start"]) * 1000)
                    }
                })
                
                # Capture response body if enabled
                if params.capture_body:
                    try:
                        response_body = await response.body()
                        if response_body and len(response_body) <= params.max_body_size:
                            try:
                                # Try to decode as text
                                matching_request["response"]["body"] = response_body.decode('utf-8')
                            except UnicodeDecodeError:
                                # Store as base64 for binary content
                                import base64
                                matching_request["response"]["body"] = base64.b64encode(response_body).decode('ascii')
                                matching_request["response"]["body_encoding"] = "base64"
                        elif response_body:
                            matching_request["response"]["body"] = f"<Body too large: {len(response_body)} bytes>"
                    except Exception as body_error:
                        matching_request["response"]["body_error"] = str(body_error)
                
                # Auto-save if enabled
                if params.auto_save:
                    await _save_request_data(context, monitoring_dir)
                
                logger.debug(f"Captured response: {response.status} {response.url}")
                
            except Exception as e:
                logger.error(f"Response handler error: {str(e)}")
        
        # Register event handlers
        page.on("request", request_handler)
        page.on("response", response_handler)
        
        # Store handlers for cleanup
        context._request_handlers = {
            "request": request_handler,
            "response": response_handler
        }
        
        # End video action
        await context.end_video_action("start_request_monitoring")
        
        result = {
            "success": True,
            "monitoring_config": monitoring_config,
            "output_directory": str(monitoring_dir),
            "session_id": context.session_id,
            "message": "HTTP request monitoring started successfully",
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"HTTP request monitoring started for session {context.session_id}")
        return result
        
    except Exception as e:
        logger.error(f"Start request monitoring failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "session_id": params.session_id,
            "timestamp": datetime.now().isoformat()
        }


@filter_response(
    filterable_fields=["url", "method", "status", "headers", "request_body", "response_body", "status_text", "timing"],
    content_fields=["request_body", "response_body", "url"],
    default_fields=["url", "method", "status"],
    supports_streaming=True,
    max_response_size=1000
)
async def browser_get_requests(params: RequestMonitoringParams) -> PaginatedResponse:
    """
    Retrieve and analyze captured HTTP requests with cursor-based pagination and ripgrep filtering.
    
    Shows timing, status codes, headers, and bodies with efficient pagination
    for large datasets. Perfect for identifying performance issues, failed requests,
    or analyzing API usage patterns across many requests.
    
    Features:
    - **Cursor-based pagination** for efficient large dataset navigation
    - **Ripgrep filtering** with regex patterns across all request fields
    - Advanced filtering by status, method, domain, performance
    - Multiple response formats (summary, detailed, statistics)
    - Performance analysis and categorization
    - Session-scoped cursor management with automatic cleanup
    - Query state consistency validation
    - **Streaming filtering** for large datasets to save memory and context
    
    Filtering Examples:
    - `filter_pattern: "api\\/v[0-9]+\\/users"` - Find API versioning patterns
    - `filter_pattern: "error|exception|failed"` - Find error patterns
    - `filter_fields: ["url", "response_body"]` - Search specific fields
    - `context_lines: 3` - Show context around matches
    
    Returns:
        PaginatedResponse with filtered request data and pagination metadata
    """
    start_time = datetime.now()
    
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_or_create_session(params.session_id)
        
        # Get captured requests
        captured_requests = getattr(context, '_captured_requests', [])
        
        if not captured_requests:
            return PaginatedResponse.create_fresh(
                items=[],
                estimated_total=0,
                fetch_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                query_fingerprint=QueryState.from_params(params).fingerprint()
            )
        
        # Detect if this is a fresh query or cursor continuation
        is_fresh_query = await context.detect_fresh_pagination_query("browser_get_requests", params)
        
        if is_fresh_query:
            # Fresh query - apply filters and create new cursor if needed
            query_state = QueryState.from_params(params)
            
            # Apply all filters to get filtered dataset
            filtered_requests = _filter_requests(
                captured_requests,
                params.filter,
                params.domain,
                params.method,
                params.status,
                params.slow_threshold
            )
            
            # Get page of results
            page_items = filtered_requests[:params.limit] if params.limit else filtered_requests
            
            # Create cursor if there are more results
            cursor_id = None
            if params.limit and len(filtered_requests) > params.limit:
                # Create cursor for next page
                cursor_position = {
                    "last_index": params.limit - 1,
                    "filtered_total": len(filtered_requests),
                    "filter_fingerprint": query_state.fingerprint()
                }
                cursor_id = await context.create_pagination_cursor(
                    tool_name="browser_get_requests",
                    query_state=query_state,
                    initial_position=cursor_position
                )
            
            # Format items based on requested format
            formatted_items = _format_request_items(page_items, params.format, captured_requests)
            
            fetch_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            return PaginatedResponse.create_fresh(
                items=formatted_items,
                cursor_id=cursor_id,
                estimated_total=len(filtered_requests),
                fetch_time_ms=fetch_time_ms,
                query_fingerprint=query_state.fingerprint()
            )
        
        else:
            # Cursor continuation
            try:
                cursor = await context.get_pagination_cursor(params.cursor_id)
                cursor_age = datetime.now() - cursor.last_accessed
                
                # Verify query consistency
                current_query = QueryState.from_params(params)
                if not cursor.matches_query_state({"filters": current_query.filters, "parameters": current_query.parameters}):
                    # Query changed, treat as fresh query
                    logger.warning(f"Query state changed for cursor {params.cursor_id}, treating as fresh query")
                    return await browser_get_requests(
                        RequestMonitoringParams(**{**params.model_dump(), "cursor_id": None})
                    )
                
                # Get current position
                position = cursor.position
                last_index = position.get("last_index", 0)
                filtered_total = position.get("filtered_total", 0)
                
                # Re-apply filters (data may have changed since cursor creation)
                filtered_requests = _filter_requests(
                    captured_requests,
                    params.filter,
                    params.domain,
                    params.method,
                    params.status,
                    params.slow_threshold
                )
                
                # Get next page starting from cursor position
                start_index = last_index + 1
                end_index = start_index + params.limit if params.limit else len(filtered_requests)
                page_items = filtered_requests[start_index:end_index]
                
                # Update cursor position
                new_cursor_id = None
                if end_index < len(filtered_requests):
                    # More data available, update cursor
                    new_position = {
                        "last_index": end_index - 1,
                        "filtered_total": len(filtered_requests),
                        "filter_fingerprint": current_query.fingerprint()
                    }
                    await context.update_cursor_position(
                        params.cursor_id, new_position, len(page_items)
                    )
                    new_cursor_id = params.cursor_id
                else:
                    # No more data, invalidate cursor
                    await context.invalidate_cursor(params.cursor_id)
                
                # Format items
                formatted_items = _format_request_items(page_items, params.format, captured_requests)
                
                fetch_time_ms = (datetime.now() - start_time).total_seconds() * 1000
                
                return PaginatedResponse.create_continuation(
                    items=formatted_items,
                    cursor_id=new_cursor_id,
                    cursor_age=cursor_age,
                    total_fetched=cursor.result_count + len(page_items),
                    fetch_time_ms=fetch_time_ms
                )
                
            except (CursorNotFoundError, CursorExpiredError, CrossSessionAccessError) as e:
                # Cursor issue, treat as fresh query
                logger.warning(f"Cursor error for {params.cursor_id}: {e}, treating as fresh query")
                return await browser_get_requests(
                    RequestMonitoringParams(**{**params.model_dump(), "cursor_id": None})
                )
        
    except Exception as e:
        logger.error(f"Get requests failed: {str(e)}")
        # Return error as fresh response
        return PaginatedResponse.create_fresh(
            items=[],
            estimated_total=0,
            fetch_time_ms=(datetime.now() - start_time).total_seconds() * 1000
        )


async def browser_export_requests(params: ExportRequestsParams) -> Dict[str, Any]:
    """
    Export captured HTTP requests to various formats.
    
    Perfect for sharing analysis results, importing into other tools,
    or creating audit reports with comprehensive request/response data.
    
    Features:
    - Multiple export formats (JSON, HAR, CSV, summary)
    - Optional body inclusion for complete data
    - Automatic filename generation with timestamps
    - Request filtering before export
    - Comprehensive metadata preservation
    
    Returns:
        Export result with file path and export statistics
    """
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_session(params.session_id)
        
        if not context:
            return {
                "success": False,
                "error": f"Session {params.session_id} not found",
                "session_id": params.session_id,
                "timestamp": datetime.now().isoformat()
            }
        
        # Get captured requests
        captured_requests = getattr(context, '_captured_requests', [])
        
        if not captured_requests:
            return {
                "success": False,
                "error": "No requests to export",
                "session_id": context.session_id,
                "timestamp": datetime.now().isoformat()
            }
        
        # Apply filters
        filtered_requests = _filter_requests(captured_requests, params.filter)
        
        # Generate filename if not provided
        if not params.filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            extension = _get_export_extension(params.format)
            params.filename = f"requests_export_{timestamp}.{extension}"
        
        # Ensure output directory exists
        output_dir = context.artifacts_dir / "requests"
        output_dir.mkdir(exist_ok=True)
        export_path = output_dir / params.filename
        
        # Export based on format
        if params.format == "har":
            export_data = _generate_har_format(filtered_requests, params.include_body)
        elif params.format == "csv":
            export_data = _generate_csv_format(filtered_requests, params.include_body)
        elif params.format == "summary":
            export_data = _generate_summary_report(filtered_requests, captured_requests)
        else:  # JSON format
            export_data = {
                "export_info": {
                    "timestamp": datetime.now().isoformat(),
                    "session_id": context.session_id,
                    "total_requests": len(captured_requests),
                    "exported_requests": len(filtered_requests),
                    "include_body": params.include_body,
                    "filter": params.filter
                },
                "requests": filtered_requests if params.include_body else _strip_bodies(filtered_requests)
            }
        
        # Write export file
        with open(export_path, 'w', encoding='utf-8') as f:
            if params.format == "csv":
                f.write(export_data)
            else:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        # Get file statistics
        file_size = export_path.stat().st_size
        
        result = {
            "success": True,
            "export_path": str(export_path),
            "filename": params.filename,
            "format": params.format,
            "file_size_bytes": file_size,
            "exported_requests": len(filtered_requests),
            "total_requests": len(captured_requests),
            "include_body": params.include_body,
            "session_id": context.session_id,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Exported {len(filtered_requests)} requests to {export_path} ({file_size} bytes)")
        return result
        
    except Exception as e:
        logger.error(f"Export requests failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "session_id": params.session_id,
            "timestamp": datetime.now().isoformat()
        }


async def browser_clear_requests(params: ClearRequestsParams) -> Dict[str, Any]:
    """
    Clear all captured HTTP request data from memory.
    
    Useful for freeing up memory during long sessions or when starting
    fresh analysis after completing a testing phase.
    
    Returns:
        Clear operation result with statistics
    """
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_session(params.session_id)
        
        if not context:
            return {
                "success": False,
                "error": f"Session {params.session_id} not found",
                "session_id": params.session_id,
                "timestamp": datetime.now().isoformat()
            }
        
        # Get current request count
        captured_requests = getattr(context, '_captured_requests', [])
        request_count = len(captured_requests)
        
        # Clear requests
        context._captured_requests = []
        
        result = {
            "success": True,
            "cleared_requests": request_count,
            "message": f"Cleared {request_count} captured request(s)",
            "session_id": context.session_id,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Cleared {request_count} captured requests for session {context.session_id}")
        return result
        
    except Exception as e:
        logger.error(f"Clear requests failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "session_id": params.session_id,
            "timestamp": datetime.now().isoformat()
        }


async def browser_request_monitoring_status(session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Check if request monitoring is active and view current configuration.
    
    Shows capture statistics, filter settings, and output paths for
    understanding the current monitoring state.
    
    Returns:
        Current monitoring status and configuration details
    """
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_session(session_id)
        
        if not context:
            return {
                "success": False,
                "error": f"Session {session_id} not found",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
        
        # Check if monitoring is active
        monitoring_config = getattr(context, '_request_monitoring_config', None)
        captured_requests = getattr(context, '_captured_requests', [])
        
        is_active = monitoring_config is not None
        
        if is_active:
            result = {
                "success": True,
                "monitoring_active": True,
                "configuration": monitoring_config,
                "statistics": {
                    "total_requests": len(captured_requests),
                    "requests_with_responses": sum(1 for req in captured_requests if "response" in req),
                    "failed_requests": sum(1 for req in captured_requests if req.get("response", {}).get("status", 0) >= 400),
                    "average_duration_ms": _calculate_average_duration(captured_requests)
                },
                "session_id": context.session_id,
                "timestamp": datetime.now().isoformat()
            }
        else:
            result = {
                "success": True,
                "monitoring_active": False,
                "message": "Request monitoring is not currently active",
                "session_id": context.session_id,
                "timestamp": datetime.now().isoformat()
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Request monitoring status check failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }


# Helper functions

def _format_request_items(requests: List[Dict[str, Any]], format_type: str, all_requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format request items based on requested format"""
    if format_type == "stats":
        # Return statistics instead of individual items
        return [_generate_request_statistics(requests, all_requests)]
    
    elif format_type == "detailed":
        # Return full request details
        return requests
    
    else:  # summary format (default)
        summary_requests = []
        for req in requests:
            summary = {
                "id": req["id"],
                "method": req["method"],
                "url": req["url"],
                "status": req.get("response", {}).get("status"),
                "duration_ms": req.get("timing", {}).get("duration_ms"),
                "resource_type": req["resource_type"],
                "timestamp": req["start_time"]
            }
            summary_requests.append(summary)
        return summary_requests


def _filter_requests(requests, filter_type, domain=None, method=None, status=None, slow_threshold=1000):
    """Filter requests based on various criteria"""
    filtered = requests[:]
    
    # Apply domain filter
    if domain:
        filtered = [req for req in filtered if domain.lower() in req["url"].lower()]
    
    # Apply method filter
    if method:
        filtered = [req for req in filtered if req["method"].upper() == method.upper()]
    
    # Apply status filter
    if status:
        filtered = [req for req in filtered if req.get("response", {}).get("status") == status]
    
    # Apply type filter
    if filter_type == "failed":
        filtered = [req for req in filtered if not req.get("response") or not req["response"].get("ok", True)]
    elif filter_type == "slow":
        filtered = [req for req in filtered if req.get("timing", {}).get("duration_ms", 0) > slow_threshold]
    elif filter_type == "errors":
        filtered = [req for req in filtered if req.get("response", {}).get("status", 0) >= 400]
    elif filter_type == "success":
        filtered = [req for req in filtered if req.get("response", {}).get("ok", False)]
    
    return filtered


def _generate_request_statistics(filtered_requests, all_requests):
    """Generate comprehensive statistics for requests"""
    stats = {
        "success": True,
        "format": "stats",
        "total_requests": len(all_requests),
        "filtered_requests": len(filtered_requests),
        "statistics": {
            "methods": {},
            "status_codes": {},
            "domains": {},
            "resource_types": {},
            "performance": {
                "average_duration_ms": _calculate_average_duration(filtered_requests),
                "min_duration_ms": min((req.get("timing", {}).get("duration_ms", 0) for req in filtered_requests), default=0),
                "max_duration_ms": max((req.get("timing", {}).get("duration_ms", 0) for req in filtered_requests), default=0),
            }
        }
    }
    
    # Count methods, status codes, domains, resource types
    for req in filtered_requests:
        # Method counts
        method = req["method"]
        stats["statistics"]["methods"][method] = stats["statistics"]["methods"].get(method, 0) + 1
        
        # Status code counts
        status = req.get("response", {}).get("status")
        if status:
            stats["statistics"]["status_codes"][str(status)] = stats["statistics"]["status_codes"].get(str(status), 0) + 1
        
        # Domain counts
        from urllib.parse import urlparse
        domain = urlparse(req["url"]).netloc
        stats["statistics"]["domains"][domain] = stats["statistics"]["domains"].get(domain, 0) + 1
        
        # Resource type counts
        resource_type = req.get("resource_type", "unknown")
        stats["statistics"]["resource_types"][resource_type] = stats["statistics"]["resource_types"].get(resource_type, 0) + 1
    
    return stats


def _calculate_average_duration(requests):
    """Calculate average request duration"""
    durations = [req.get("timing", {}).get("duration_ms", 0) for req in requests if req.get("timing", {}).get("duration_ms")]
    return int(sum(durations) / len(durations)) if durations else 0


def _generate_har_format(requests, include_body):
    """Generate HAR (HTTP Archive) format export"""
    # Simplified HAR format implementation
    har_data = {
        "log": {
            "version": "1.2",
            "creator": {
                "name": "MCPlaywright",
                "version": "1.0.0"
            },
            "entries": []
        }
    }
    
    for req in requests:
        entry = {
            "startedDateTime": req["start_time"],
            "time": req.get("timing", {}).get("duration_ms", 0),
            "request": {
                "method": req["method"],
                "url": req["url"],
                "headers": [{"name": k, "value": v} for k, v in req["headers"].items()],
                "bodySize": len(req.get("request_body", "")),
            },
            "response": {
                "status": req.get("response", {}).get("status", 0),
                "statusText": req.get("response", {}).get("status_text", ""),
                "headers": [{"name": k, "value": v} for k, v in req.get("response", {}).get("headers", {}).items()],
                "content": {
                    "size": len(req.get("response", {}).get("body", "")),
                    "mimeType": req.get("response", {}).get("headers", {}).get("content-type", ""),
                }
            }
        }
        
        if include_body:
            if req.get("request_body"):
                entry["request"]["postData"] = {"text": req["request_body"]}
            if req.get("response", {}).get("body"):
                entry["response"]["content"]["text"] = req["response"]["body"]
        
        har_data["log"]["entries"].append(entry)
    
    return har_data


def _generate_csv_format(requests, include_body):
    """Generate CSV format export"""
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Header row
    headers = ["ID", "Method", "URL", "Status", "Duration (ms)", "Resource Type", "Start Time"]
    if include_body:
        headers.extend(["Request Body", "Response Body"])
    
    writer.writerow(headers)
    
    # Data rows
    for req in requests:
        row = [
            req["id"],
            req["method"],
            req["url"],
            req.get("response", {}).get("status", ""),
            req.get("timing", {}).get("duration_ms", ""),
            req.get("resource_type", ""),
            req["start_time"]
        ]
        
        if include_body:
            row.append(req.get("request_body", ""))
            row.append(req.get("response", {}).get("body", ""))
        
        writer.writerow(row)
    
    return output.getvalue()


def _generate_summary_report(filtered_requests, all_requests):
    """Generate human-readable summary report"""
    return {
        "report_type": "HTTP Request Analysis Summary",
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_requests": len(all_requests),
            "analyzed_requests": len(filtered_requests),
            "success_rate": f"{(sum(1 for req in filtered_requests if req.get('response', {}).get('ok', False)) / len(filtered_requests) * 100):.1f}%" if filtered_requests else "0%",
            "average_response_time": f"{_calculate_average_duration(filtered_requests)}ms",
        },
        "requests": [
            {
                "id": req["id"],
                "method": req["method"],
                "url": req["url"],
                "status": req.get("response", {}).get("status", "No response"),
                "duration_ms": req.get("timing", {}).get("duration_ms", "Unknown"),
                "size_bytes": len(req.get("response", {}).get("body", "")),
            } for req in filtered_requests
        ]
    }


def _strip_bodies(requests):
    """Remove body content from requests for lighter export"""
    stripped = []
    for req in requests:
        req_copy = req.copy()
        req_copy.pop("request_body", None)
        if "response" in req_copy:
            resp_copy = req_copy["response"].copy()
            resp_copy.pop("body", None)
            req_copy["response"] = resp_copy
        stripped.append(req_copy)
    return stripped


def _get_export_extension(format_type):
    """Get file extension for export format"""
    extensions = {
        "json": "json",
        "har": "har",
        "csv": "csv",
        "summary": "json"
    }
    return extensions.get(format_type, "json")


async def _save_request_data(context, output_dir):
    """Save captured request data to file (for auto-save functionality)"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = output_dir / f"requests_autosave_{timestamp}.json"
        
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(context._captured_requests, f, indent=2, ensure_ascii=False)
        
        logger.debug(f"Auto-saved {len(context._captured_requests)} requests to {save_path}")
    except Exception as e:
        logger.error(f"Auto-save failed: {str(e)}")