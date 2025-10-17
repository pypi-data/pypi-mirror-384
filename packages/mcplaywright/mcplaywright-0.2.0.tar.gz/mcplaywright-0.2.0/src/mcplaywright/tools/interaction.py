"""
Browser Interaction Tools for MCPlaywright

Advanced interaction tools including typing, keyboard, mouse operations,
and element manipulation with video recording integration.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field
from playwright.async_api import Page

from ..session_manager import get_session_manager
from .video import begin_video_action_for_session, end_video_action_for_session

logger = logging.getLogger(__name__)


class TypeParams(BaseModel):
    """Parameters for typing text"""
    session_id: Optional[str] = Field(None, description="Session ID")
    selector: str = Field(description="CSS selector for input element")
    text: str = Field(description="Text to type")
    delay: Optional[int] = Field(0, description="Delay between keystrokes in milliseconds")
    timeout: Optional[int] = Field(30000, description="Timeout waiting for element")
    clear_first: Optional[bool] = Field(True, description="Clear existing text before typing")


class FillParams(BaseModel):
    """Parameters for filling form fields"""
    session_id: Optional[str] = Field(None, description="Session ID")
    selector: str = Field(description="CSS selector for input element")
    value: str = Field(description="Value to fill")
    timeout: Optional[int] = Field(30000, description="Timeout waiting for element")
    force: Optional[bool] = Field(False, description="Force fill even if element is not editable")


class KeyboardParams(BaseModel):
    """Parameters for keyboard operations"""
    session_id: Optional[str] = Field(None, description="Session ID")
    key: str = Field(description="Key to press (e.g., 'Enter', 'Tab', 'ArrowDown', 'a', 'Control+a')")
    delay: Optional[int] = Field(0, description="Delay after key press")


class HoverParams(BaseModel):
    """Parameters for hovering over elements"""
    session_id: Optional[str] = Field(None, description="Session ID")
    selector: str = Field(description="CSS selector for element to hover")
    timeout: Optional[int] = Field(30000, description="Timeout waiting for element")
    force: Optional[bool] = Field(False, description="Force hover even if element is not visible")


class DragParams(BaseModel):
    """Parameters for drag and drop operations"""
    session_id: Optional[str] = Field(None, description="Session ID")
    source_selector: str = Field(description="CSS selector for source element")
    target_selector: str = Field(description="CSS selector for target element")
    timeout: Optional[int] = Field(30000, description="Timeout waiting for elements")
    force: Optional[bool] = Field(False, description="Force drag even if elements are not actionable")


class SelectParams(BaseModel):
    """Parameters for selecting options"""
    session_id: Optional[str] = Field(None, description="Session ID")
    selector: str = Field(description="CSS selector for select element")
    values: Union[str, List[str]] = Field(description="Value(s) to select")
    timeout: Optional[int] = Field(30000, description="Timeout waiting for element")


class CheckParams(BaseModel):
    """Parameters for checkbox/radio operations"""
    session_id: Optional[str] = Field(None, description="Session ID")
    selector: str = Field(description="CSS selector for checkbox/radio element")
    checked: Optional[bool] = Field(True, description="Whether to check (true) or uncheck (false)")
    timeout: Optional[int] = Field(30000, description="Timeout waiting for element")
    force: Optional[bool] = Field(False, description="Force check even if element is not actionable")


async def browser_type(params: TypeParams) -> Dict[str, Any]:
    """
    Type text into an input element.
    
    Types text character by character into the specified input element,
    with configurable delays between keystrokes for realistic typing simulation.
    
    Features:
    - Character-by-character typing with delays
    - Automatic element focus and clear
    - Element visibility and actionability checks
    - Video recording integration
    
    Returns:
        Typing operation result with element information
    """
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_or_create_session(params.session_id)
        
        # Begin video action
        await begin_video_action_for_session(context.session_id, "type")
        
        page = await context.get_current_page()
        
        logger.info(f"Typing into element '{params.selector}' (session: {context.session_id})")
        
        # Wait for element and get it
        await page.wait_for_selector(params.selector, timeout=params.timeout)
        element = page.locator(params.selector).first
        
        # Clear existing content if requested
        if params.clear_first:
            await element.clear()
        
        # Focus the element
        await element.focus()
        
        # Type the text with optional delay
        if params.delay > 0:
            await element.type(params.text, delay=params.delay)
        else:
            await element.fill(params.text)
        
        # Get element information for response
        element_value = await element.input_value() if await element.count() > 0 else ""
        element_tag = await element.evaluate("el => el.tagName.toLowerCase()") if await element.count() > 0 else ""
        
        # End video action
        await end_video_action_for_session(context.session_id, "type")
        
        result = {
            "success": True,
            "selector": params.selector,
            "text_typed": params.text,
            "delay": params.delay,
            "element_value": element_value,
            "element_tag": element_tag,
            "session_id": context.session_id,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Text typed successfully into {element_tag} element")
        return result
        
    except Exception as e:
        logger.error(f"Type operation failed: {str(e)}")
        await end_video_action_for_session(params.session_id or "", "type")
        return {
            "success": False,
            "error": str(e),
            "selector": params.selector,
            "text_typed": params.text,
            "session_id": params.session_id,
            "timestamp": datetime.now().isoformat()
        }


async def browser_fill(params: FillParams) -> Dict[str, Any]:
    """
    Fill a form field with a value.
    
    Fast way to set the value of input fields, textareas, and select elements.
    More efficient than typing for long text content.
    
    Returns:
        Fill operation result with element information
    """
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_or_create_session(params.session_id)
        
        await begin_video_action_for_session(context.session_id, "fill")
        
        page = await context.get_current_page()
        
        logger.info(f"Filling element '{params.selector}' (session: {context.session_id})")
        
        # Fill the element
        await page.fill(params.selector, params.value, timeout=params.timeout, force=params.force)
        
        # Get element information
        element = page.locator(params.selector).first
        element_value = await element.input_value() if await element.count() > 0 else ""
        element_tag = await element.evaluate("el => el.tagName.toLowerCase()") if await element.count() > 0 else ""
        
        await end_video_action_for_session(context.session_id, "fill")
        
        result = {
            "success": True,
            "selector": params.selector,
            "value_filled": params.value,
            "element_value": element_value,
            "element_tag": element_tag,
            "session_id": context.session_id,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Form field filled successfully")
        return result
        
    except Exception as e:
        logger.error(f"Fill operation failed: {str(e)}")
        await end_video_action_for_session(params.session_id or "", "fill")
        return {
            "success": False,
            "error": str(e),
            "selector": params.selector,
            "value_filled": params.value,
            "session_id": params.session_id,
            "timestamp": datetime.now().isoformat()
        }


async def browser_press_key(params: KeyboardParams) -> Dict[str, Any]:
    """
    Press a key on the keyboard.
    
    Send keyboard input including special keys, key combinations, and modifiers.
    Supports all Playwright key names and combinations.
    
    Examples:
    - Single keys: 'Enter', 'Tab', 'Escape', 'a', '1'
    - Arrow keys: 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'
    - Modifier combinations: 'Control+a', 'Control+c', 'Control+v'
    - Function keys: 'F1', 'F2', etc.
    
    Returns:
        Key press operation result
    """
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_or_create_session(params.session_id)
        
        await begin_video_action_for_session(context.session_id, "press_key")
        
        page = await context.get_current_page()
        
        logger.info(f"Pressing key '{params.key}' (session: {context.session_id})")
        
        # Press the key
        await page.keyboard.press(params.key)
        
        # Optional delay after key press
        if params.delay > 0:
            await asyncio.sleep(params.delay / 1000.0)
        
        await end_video_action_for_session(context.session_id, "press_key")
        
        result = {
            "success": True,
            "key_pressed": params.key,
            "delay": params.delay,
            "session_id": context.session_id,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Key '{params.key}' pressed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Key press failed: {str(e)}")
        await end_video_action_for_session(params.session_id or "", "press_key")
        return {
            "success": False,
            "error": str(e),
            "key_pressed": params.key,
            "session_id": params.session_id,
            "timestamp": datetime.now().isoformat()
        }


async def browser_hover(params: HoverParams) -> Dict[str, Any]:
    """
    Hover over an element.
    
    Move the mouse cursor over the specified element, triggering hover effects
    and CSS :hover pseudo-class styles.
    
    Returns:
        Hover operation result with element information
    """
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_or_create_session(params.session_id)
        
        await begin_video_action_for_session(context.session_id, "hover")
        
        page = await context.get_current_page()
        
        logger.info(f"Hovering over element '{params.selector}' (session: {context.session_id})")
        
        # Hover over the element
        await page.hover(params.selector, timeout=params.timeout, force=params.force)
        
        # Get element information
        element = page.locator(params.selector).first
        element_text = await element.text_content() if await element.count() > 0 else ""
        element_tag = await element.evaluate("el => el.tagName.toLowerCase()") if await element.count() > 0 else ""
        
        await end_video_action_for_session(context.session_id, "hover")
        
        result = {
            "success": True,
            "selector": params.selector,
            "element_text": element_text,
            "element_tag": element_tag,
            "session_id": context.session_id,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Hover successful on {element_tag} element")
        return result
        
    except Exception as e:
        logger.error(f"Hover operation failed: {str(e)}")
        await end_video_action_for_session(params.session_id or "", "hover")
        return {
            "success": False,
            "error": str(e),
            "selector": params.selector,
            "session_id": params.session_id,
            "timestamp": datetime.now().isoformat()
        }


async def browser_drag_and_drop(params: DragParams) -> Dict[str, Any]:
    """
    Drag an element from source to target.
    
    Perform drag and drop operation by dragging the source element
    and dropping it on the target element.
    
    Returns:
        Drag and drop operation result with element information
    """
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_or_create_session(params.session_id)
        
        await begin_video_action_for_session(context.session_id, "drag")
        
        page = await context.get_current_page()
        
        logger.info(f"Dragging from '{params.source_selector}' to '{params.target_selector}' (session: {context.session_id})")
        
        # Perform drag and drop
        await page.drag_and_drop(
            params.source_selector,
            params.target_selector,
            timeout=params.timeout,
            force=params.force
        )
        
        # Get element information
        source_element = page.locator(params.source_selector).first
        target_element = page.locator(params.target_selector).first
        
        source_info = {
            "text": await source_element.text_content() if await source_element.count() > 0 else "",
            "tag": await source_element.evaluate("el => el.tagName.toLowerCase()") if await source_element.count() > 0 else ""
        }
        
        target_info = {
            "text": await target_element.text_content() if await target_element.count() > 0 else "",
            "tag": await target_element.evaluate("el => el.tagName.toLowerCase()") if await target_element.count() > 0 else ""
        }
        
        await end_video_action_for_session(context.session_id, "drag")
        
        result = {
            "success": True,
            "source_selector": params.source_selector,
            "target_selector": params.target_selector,
            "source_info": source_info,
            "target_info": target_info,
            "session_id": context.session_id,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Drag and drop successful")
        return result
        
    except Exception as e:
        logger.error(f"Drag and drop failed: {str(e)}")
        await end_video_action_for_session(params.session_id or "", "drag")
        return {
            "success": False,
            "error": str(e),
            "source_selector": params.source_selector,
            "target_selector": params.target_selector,
            "session_id": params.session_id,
            "timestamp": datetime.now().isoformat()
        }


async def browser_select_option(params: SelectParams) -> Dict[str, Any]:
    """
    Select option(s) in a select dropdown.
    
    Select one or more options in a select element by value, label, or index.
    Supports both single and multiple selection.
    
    Returns:
        Select operation result with selected values
    """
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_or_create_session(params.session_id)
        
        await begin_video_action_for_session(context.session_id, "select")
        
        page = await context.get_current_page()
        
        # Normalize values to list
        values = params.values if isinstance(params.values, list) else [params.values]
        
        logger.info(f"Selecting options {values} in '{params.selector}' (session: {context.session_id})")
        
        # Select the options
        selected_values = await page.select_option(params.selector, values, timeout=params.timeout)
        
        # Get element information
        element = page.locator(params.selector).first
        element_tag = await element.evaluate("el => el.tagName.toLowerCase()") if await element.count() > 0 else ""
        
        await end_video_action_for_session(context.session_id, "select")
        
        result = {
            "success": True,
            "selector": params.selector,
            "requested_values": values,
            "selected_values": selected_values,
            "element_tag": element_tag,
            "session_id": context.session_id,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Options selected successfully: {selected_values}")
        return result
        
    except Exception as e:
        logger.error(f"Select operation failed: {str(e)}")
        await end_video_action_for_session(params.session_id or "", "select")
        return {
            "success": False,
            "error": str(e),
            "selector": params.selector,
            "requested_values": params.values,
            "session_id": params.session_id,
            "timestamp": datetime.now().isoformat()
        }


async def browser_check(params: CheckParams) -> Dict[str, Any]:
    """
    Check or uncheck a checkbox/radio button.
    
    Set the checked state of checkbox or radio button elements.
    Automatically detects the element type and performs the appropriate action.
    
    Returns:
        Check operation result with final checked state
    """
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_or_create_session(params.session_id)
        
        action_name = "check" if params.checked else "uncheck"
        await begin_video_action_for_session(context.session_id, action_name)
        
        page = await context.get_current_page()
        
        logger.info(f"{action_name.title()}ing element '{params.selector}' (session: {context.session_id})")
        
        # Check or uncheck based on the parameter
        if params.checked:
            await page.check(params.selector, timeout=params.timeout, force=params.force)
        else:
            await page.uncheck(params.selector, timeout=params.timeout, force=params.force)
        
        # Get element information and final state
        element = page.locator(params.selector).first
        is_checked = await element.is_checked() if await element.count() > 0 else False
        element_type = await element.get_attribute("type") if await element.count() > 0 else ""
        element_tag = await element.evaluate("el => el.tagName.toLowerCase()") if await element.count() > 0 else ""
        
        await end_video_action_for_session(context.session_id, action_name)
        
        result = {
            "success": True,
            "selector": params.selector,
            "requested_checked": params.checked,
            "final_checked": is_checked,
            "element_type": element_type,
            "element_tag": element_tag,
            "session_id": context.session_id,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Element {action_name}ed successfully, final state: {is_checked}")
        return result
        
    except Exception as e:
        logger.error(f"Check/uncheck operation failed: {str(e)}")
        await end_video_action_for_session(params.session_id or "", "check")
        return {
            "success": False,
            "error": str(e),
            "selector": params.selector,
            "requested_checked": params.checked,
            "session_id": params.session_id,
            "timestamp": datetime.now().isoformat()
        }