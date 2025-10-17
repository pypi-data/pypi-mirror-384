"""
Wait Tools for MCPlaywright

Advanced wait functionality with smart video recording integration.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from ..session_manager import get_session_manager
from .video import begin_video_action_for_session, end_video_action_for_session

logger = logging.getLogger(__name__)


class WaitForTextParams(BaseModel):
    """Parameters for waiting for text to appear"""
    session_id: Optional[str] = Field(None, description="Session ID")
    text: str = Field(description="Text to wait for")
    timeout: Optional[int] = Field(30000, description="Timeout in milliseconds")
    record_during_wait: Optional[bool] = Field(None, description="Whether to keep recording during wait (overrides smart mode)")


class WaitForTextGoneParams(BaseModel):
    """Parameters for waiting for text to disappear"""
    session_id: Optional[str] = Field(None, description="Session ID")
    text: str = Field(description="Text to wait for to disappear")
    timeout: Optional[int] = Field(30000, description="Timeout in milliseconds")
    record_during_wait: Optional[bool] = Field(None, description="Whether to keep recording during wait (overrides smart mode)")


class WaitForElementParams(BaseModel):
    """Parameters for waiting for elements"""
    session_id: Optional[str] = Field(None, description="Session ID")
    selector: str = Field(description="CSS selector to wait for")
    state: Optional[str] = Field("visible", description="Element state: 'attached', 'detached', 'visible', 'hidden'")
    timeout: Optional[int] = Field(30000, description="Timeout in milliseconds")
    record_during_wait: Optional[bool] = Field(None, description="Whether to keep recording during wait (overrides smart mode)")


class WaitForLoadStateParams(BaseModel):
    """Parameters for waiting for page load states"""
    session_id: Optional[str] = Field(None, description="Session ID")
    state: Optional[str] = Field("load", description="Load state: 'load', 'domcontentloaded', 'networkidle'")
    timeout: Optional[int] = Field(30000, description="Timeout in milliseconds")
    record_during_wait: Optional[bool] = Field(None, description="Whether to keep recording during wait (overrides smart mode)")


class WaitForTimeParams(BaseModel):
    """Parameters for waiting for a specific time"""
    session_id: Optional[str] = Field(None, description="Session ID")
    time: Union[int, float] = Field(description="Time to wait in seconds")
    record_during_wait: Optional[bool] = Field(None, description="Whether to keep recording during wait (overrides smart mode)")


class WaitForRequestParams(BaseModel):
    """Parameters for waiting for network requests"""
    session_id: Optional[str] = Field(None, description="Session ID")
    url_pattern: str = Field(description="URL pattern to match (can be string or regex)")
    timeout: Optional[int] = Field(30000, description="Timeout in milliseconds")
    record_during_wait: Optional[bool] = Field(None, description="Whether to keep recording during wait (overrides smart mode)")


async def browser_wait_for_text(params: WaitForTextParams) -> Dict[str, Any]:
    """
    Wait for text to appear on the page.
    
    Waits for the specified text to appear anywhere on the page.
    Supports smart video recording pause/resume based on recording mode.
    
    Features:
    - Text appearance detection
    - Smart video recording integration
    - Configurable timeout handling
    - Page state monitoring during wait
    
    Returns:
        Wait result with text detection information
    """
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_or_create_session(params.session_id)
        
        # Determine recording behavior
        should_record = _should_record_during_wait(context, params.record_during_wait)
        
        # Begin wait action (may pause recording in smart mode)
        if not should_record:
            await context.pause_video_recording()
        
        # Get current page
        page = await context.get_current_page()
        
        logger.info(f"Waiting for text '{params.text}' to appear (timeout: {params.timeout}ms)")
        
        start_time = datetime.now()
        
        try:
            # Wait for text to appear using Playwright's text locator
            text_locator = page.get_by_text(params.text, exact=False)
            await text_locator.wait_for(state="visible", timeout=params.timeout)
            
            # Get information about where the text was found
            element_count = await text_locator.count()
            
            # Get details of first matching element
            if element_count > 0:
                first_element = text_locator.first
                element_info = {
                    "tag_name": await first_element.evaluate("el => el.tagName.toLowerCase()"),
                    "text_content": await first_element.text_content(),
                    "is_visible": await first_element.is_visible()
                }
            else:
                element_info = None
            
            wait_duration = (datetime.now() - start_time).total_seconds() * 1000
            
            result = {
                "success": True,
                "text": params.text,
                "found": True,
                "element_count": element_count,
                "element_info": element_info,
                "wait_duration_ms": int(wait_duration),
                "session_id": context.session_id,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Text '{params.text}' found after {int(wait_duration)}ms")
            
        except Exception as wait_error:
            wait_duration = (datetime.now() - start_time).total_seconds() * 1000
            
            if "Timeout" in str(wait_error):
                result = {
                    "success": False,
                    "text": params.text,
                    "found": False,
                    "error": f"Text not found within {params.timeout}ms timeout",
                    "wait_duration_ms": int(wait_duration),
                    "session_id": context.session_id,
                    "timestamp": datetime.now().isoformat()
                }
                logger.warning(f"Text '{params.text}' not found within timeout")
            else:
                raise wait_error
        
        # Resume recording if it was paused
        if not should_record:
            await context.resume_video_recording()
        
        return result
        
    except Exception as e:
        logger.error(f"Wait for text failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "text": params.text,
            "session_id": params.session_id,
            "timestamp": datetime.now().isoformat()
        }


async def browser_wait_for_text_gone(params: WaitForTextGoneParams) -> Dict[str, Any]:
    """
    Wait for text to disappear from the page.
    
    Waits for the specified text to no longer be visible on the page.
    Supports smart video recording pause/resume based on recording mode.
    
    Features:
    - Text disappearance detection
    - Smart video recording integration
    - Configurable timeout handling
    - Page state monitoring during wait
    
    Returns:
        Wait result with text disappearance information
    """
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_or_create_session(params.session_id)
        
        # Determine recording behavior
        should_record = _should_record_during_wait(context, params.record_during_wait)
        
        # Begin wait action (may pause recording in smart mode)
        if not should_record:
            await context.pause_video_recording()
        
        # Get current page
        page = await context.get_current_page()
        
        logger.info(f"Waiting for text '{params.text}' to disappear (timeout: {params.timeout}ms)")
        
        start_time = datetime.now()
        
        try:
            # Wait for text to disappear using Playwright's text locator
            text_locator = page.get_by_text(params.text, exact=False)
            await text_locator.wait_for(state="hidden", timeout=params.timeout)
            
            wait_duration = (datetime.now() - start_time).total_seconds() * 1000
            
            result = {
                "success": True,
                "text": params.text,
                "gone": True,
                "wait_duration_ms": int(wait_duration),
                "session_id": context.session_id,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Text '{params.text}' disappeared after {int(wait_duration)}ms")
            
        except Exception as wait_error:
            wait_duration = (datetime.now() - start_time).total_seconds() * 1000
            
            if "Timeout" in str(wait_error):
                result = {
                    "success": False,
                    "text": params.text,
                    "gone": False,
                    "error": f"Text still present after {params.timeout}ms timeout",
                    "wait_duration_ms": int(wait_duration),
                    "session_id": context.session_id,
                    "timestamp": datetime.now().isoformat()
                }
                logger.warning(f"Text '{params.text}' still present after timeout")
            else:
                raise wait_error
        
        # Resume recording if it was paused
        if not should_record:
            await context.resume_video_recording()
        
        return result
        
    except Exception as e:
        logger.error(f"Wait for text gone failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "text": params.text,
            "session_id": params.session_id,
            "timestamp": datetime.now().isoformat()
        }


async def browser_wait_for_element(params: WaitForElementParams) -> Dict[str, Any]:
    """
    Wait for an element to reach a specific state.
    
    Waits for an element matching the CSS selector to reach the specified state.
    Supports various element states and smart video recording integration.
    
    Features:
    - Element state monitoring (visible, hidden, attached, detached)
    - CSS selector-based element targeting
    - Smart video recording integration
    - Element information capture when found
    
    Returns:
        Wait result with element state information
    """
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_or_create_session(params.session_id)
        
        # Determine recording behavior
        should_record = _should_record_during_wait(context, params.record_during_wait)
        
        # Begin wait action (may pause recording in smart mode)
        if not should_record:
            await context.pause_video_recording()
        
        # Get current page
        page = await context.get_current_page()
        
        logger.info(f"Waiting for element '{params.selector}' to be {params.state} (timeout: {params.timeout}ms)")
        
        start_time = datetime.now()
        
        try:
            # Wait for element using Playwright's locator
            element = page.locator(params.selector).first
            await element.wait_for(state=params.state, timeout=params.timeout)
            
            # Get element information if it's visible/attached
            element_info = None
            if params.state in ["visible", "attached"]:
                try:
                    element_info = {
                        "tag_name": await element.evaluate("el => el.tagName.toLowerCase()"),
                        "text_content": (await element.text_content() or "")[:100],  # Limit text length
                        "is_visible": await element.is_visible(),
                        "is_enabled": await element.is_enabled(),
                        "bounding_box": await element.bounding_box()
                    }
                except Exception as info_error:
                    logger.debug(f"Could not get element info: {str(info_error)}")
            
            wait_duration = (datetime.now() - start_time).total_seconds() * 1000
            
            result = {
                "success": True,
                "selector": params.selector,
                "state": params.state,
                "found": True,
                "element_info": element_info,
                "wait_duration_ms": int(wait_duration),
                "session_id": context.session_id,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Element '{params.selector}' reached state '{params.state}' after {int(wait_duration)}ms")
            
        except Exception as wait_error:
            wait_duration = (datetime.now() - start_time).total_seconds() * 1000
            
            if "Timeout" in str(wait_error):
                result = {
                    "success": False,
                    "selector": params.selector,
                    "state": params.state,
                    "found": False,
                    "error": f"Element did not reach state '{params.state}' within {params.timeout}ms timeout",
                    "wait_duration_ms": int(wait_duration),
                    "session_id": context.session_id,
                    "timestamp": datetime.now().isoformat()
                }
                logger.warning(f"Element '{params.selector}' did not reach state '{params.state}' within timeout")
            else:
                raise wait_error
        
        # Resume recording if it was paused
        if not should_record:
            await context.resume_video_recording()
        
        return result
        
    except Exception as e:
        logger.error(f"Wait for element failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "selector": params.selector,
            "session_id": params.session_id,
            "timestamp": datetime.now().isoformat()
        }


async def browser_wait_for_load_state(params: WaitForLoadStateParams) -> Dict[str, Any]:
    """
    Wait for the page to reach a specific load state.
    
    Waits for the page to reach the specified load state (load, domcontentloaded, networkidle).
    Useful for ensuring page readiness before performing actions.
    
    Features:
    - Page load state monitoring
    - Network activity detection (networkidle)
    - Smart video recording integration
    - Load timing information
    
    Returns:
        Wait result with load state information
    """
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_or_create_session(params.session_id)
        
        # Determine recording behavior
        should_record = _should_record_during_wait(context, params.record_during_wait)
        
        # Begin wait action (may pause recording in smart mode)
        if not should_record:
            await context.pause_video_recording()
        
        # Get current page
        page = await context.get_current_page()
        
        logger.info(f"Waiting for load state '{params.state}' (timeout: {params.timeout}ms)")
        
        start_time = datetime.now()
        
        try:
            # Wait for load state
            await page.wait_for_load_state(params.state, timeout=params.timeout)
            
            wait_duration = (datetime.now() - start_time).total_seconds() * 1000
            
            # Get current page info
            page_info = {
                "url": page.url,
                "title": await page.title(),
                "ready_state": await page.evaluate("() => document.readyState")
            }
            
            result = {
                "success": True,
                "load_state": params.state,
                "reached": True,
                "page_info": page_info,
                "wait_duration_ms": int(wait_duration),
                "session_id": context.session_id,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Load state '{params.state}' reached after {int(wait_duration)}ms")
            
        except Exception as wait_error:
            wait_duration = (datetime.now() - start_time).total_seconds() * 1000
            
            if "Timeout" in str(wait_error):
                result = {
                    "success": False,
                    "load_state": params.state,
                    "reached": False,
                    "error": f"Load state '{params.state}' not reached within {params.timeout}ms timeout",
                    "wait_duration_ms": int(wait_duration),
                    "session_id": context.session_id,
                    "timestamp": datetime.now().isoformat()
                }
                logger.warning(f"Load state '{params.state}' not reached within timeout")
            else:
                raise wait_error
        
        # Resume recording if it was paused
        if not should_record:
            await context.resume_video_recording()
        
        return result
        
    except Exception as e:
        logger.error(f"Wait for load state failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "load_state": params.state,
            "session_id": params.session_id,
            "timestamp": datetime.now().isoformat()
        }


async def browser_wait_for_time(params: WaitForTimeParams) -> Dict[str, Any]:
    """
    Wait for a specific amount of time.
    
    Simple time-based wait with smart video recording integration.
    In smart recording mode, video recording is automatically paused during waits
    unless recordDuringWait is explicitly set to true.
    
    Features:
    - Precise timing control
    - Smart video recording pause/resume
    - Wait duration validation
    
    Returns:
        Wait result with timing information
    """
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_or_create_session(params.session_id)
        
        # Determine recording behavior
        should_record = _should_record_during_wait(context, params.record_during_wait)
        
        # Begin wait action (may pause recording in smart mode)
        if not should_record:
            await context.pause_video_recording()
        
        logger.info(f"Waiting for {params.time} seconds (recording: {should_record})")
        
        start_time = datetime.now()
        
        # Wait for the specified time
        await asyncio.sleep(params.time)
        
        actual_duration = (datetime.now() - start_time).total_seconds()
        
        # Resume recording if it was paused
        if not should_record:
            await context.resume_video_recording()
        
        result = {
            "success": True,
            "requested_time": params.time,
            "actual_duration": actual_duration,
            "recording_during_wait": should_record,
            "session_id": context.session_id,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Wait completed: {actual_duration:.2f}s (requested: {params.time}s)")
        return result
        
    except Exception as e:
        logger.error(f"Wait for time failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "requested_time": params.time,
            "session_id": params.session_id,
            "timestamp": datetime.now().isoformat()
        }


async def browser_wait_for_request(params: WaitForRequestParams) -> Dict[str, Any]:
    """
    Wait for a network request matching the URL pattern.
    
    Waits for a network request to be initiated that matches the specified URL pattern.
    Useful for waiting for API calls or resource loading.
    
    Features:
    - URL pattern matching (string or regex)
    - Request information capture
    - Smart video recording integration
    - Timeout handling
    
    Returns:
        Wait result with request information
    """
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_or_create_session(params.session_id)
        
        # Determine recording behavior
        should_record = _should_record_during_wait(context, params.record_during_wait)
        
        # Begin wait action (may pause recording in smart mode)
        if not should_record:
            await context.pause_video_recording()
        
        # Get current page
        page = await context.get_current_page()
        
        logger.info(f"Waiting for request matching '{params.url_pattern}' (timeout: {params.timeout}ms)")
        
        start_time = datetime.now()
        request_info = {}
        
        try:
            # Wait for request using Playwright's request waiting
            async with page.expect_request(params.url_pattern, timeout=params.timeout) as request_future:
                request = await request_future.value
                
                request_info = {
                    "url": request.url,
                    "method": request.method,
                    "headers": dict(request.headers),
                    "resource_type": request.resource_type
                }
            
            wait_duration = (datetime.now() - start_time).total_seconds() * 1000
            
            result = {
                "success": True,
                "url_pattern": params.url_pattern,
                "found": True,
                "request_info": request_info,
                "wait_duration_ms": int(wait_duration),
                "session_id": context.session_id,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Request found: {request_info['method']} {request_info['url']} after {int(wait_duration)}ms")
            
        except Exception as wait_error:
            wait_duration = (datetime.now() - start_time).total_seconds() * 1000
            
            if "Timeout" in str(wait_error):
                result = {
                    "success": False,
                    "url_pattern": params.url_pattern,
                    "found": False,
                    "error": f"No matching request found within {params.timeout}ms timeout",
                    "wait_duration_ms": int(wait_duration),
                    "session_id": context.session_id,
                    "timestamp": datetime.now().isoformat()
                }
                logger.warning(f"No request matching '{params.url_pattern}' found within timeout")
            else:
                raise wait_error
        
        # Resume recording if it was paused
        if not should_record:
            await context.resume_video_recording()
        
        return result
        
    except Exception as e:
        logger.error(f"Wait for request failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "url_pattern": params.url_pattern,
            "session_id": params.session_id,
            "timestamp": datetime.now().isoformat()
        }


def _should_record_during_wait(context, record_during_wait_override: Optional[bool]) -> bool:
    """
    Determine if recording should continue during wait based on context and override.
    
    Smart mode logic:
    - If record_during_wait is explicitly provided, use that
    - If in smart mode, default to False (pause recording)
    - If in continuous mode, default to True (keep recording)
    """
    if record_during_wait_override is not None:
        return record_during_wait_override
    
    # Get current video recording mode
    video_info = context.get_video_recording_info()
    if not video_info.get("enabled", False):
        return False
    
    recording_mode = video_info.get("mode", "continuous")
    
    # In smart mode, default to pausing during waits
    if recording_mode == "smart":
        return False
    
    # In other modes, keep recording by default
    return True