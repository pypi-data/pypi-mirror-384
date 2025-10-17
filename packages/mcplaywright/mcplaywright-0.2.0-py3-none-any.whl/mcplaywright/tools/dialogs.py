"""
Dialog and File Upload Tools for MCPlaywright

Advanced dialog handling and file upload capabilities with session management.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ..session_manager import get_session_manager
from .video import begin_video_action_for_session, end_video_action_for_session

logger = logging.getLogger(__name__)


class FileUploadParams(BaseModel):
    """Parameters for file upload operations"""
    session_id: Optional[str] = Field(None, description="Session ID")
    selector: str = Field(description="CSS selector for file input element")
    file_paths: List[str] = Field(description="List of file paths to upload")
    timeout: Optional[int] = Field(30000, description="Timeout waiting for element")


class HandleDialogParams(BaseModel):
    """Parameters for dialog handling"""
    session_id: Optional[str] = Field(None, description="Session ID")
    accept: bool = Field(description="Whether to accept or dismiss the dialog")
    prompt_text: Optional[str] = Field(None, description="Text to enter in prompt dialogs")


class DismissFileChooserParams(BaseModel):
    """Parameters for dismissing file chooser dialogs"""
    session_id: Optional[str] = Field(None, description="Session ID")


async def browser_file_upload(params: FileUploadParams) -> Dict[str, Any]:
    """
    Upload files to a file input element.
    
    Handles single or multiple file uploads to file input elements.
    Validates file paths exist before uploading and provides comprehensive
    upload status information.
    
    Features:
    - Multiple file upload support
    - File path validation and existence checking
    - Element visibility and actionability verification
    - Upload progress tracking
    - Video recording integration
    
    Returns:
        File upload result with uploaded file information
    """
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_or_create_session(params.session_id)
        
        # Begin video action
        await context.begin_video_action("file_upload")
        
        # Get current page
        page = await context.get_current_page()
        
        # Validate file paths exist
        validated_files = []
        missing_files = []
        
        for file_path in params.file_paths:
            path = Path(file_path)
            if path.exists() and path.is_file():
                validated_files.append(str(path.resolve()))
            else:
                missing_files.append(file_path)
        
        if missing_files:
            return {
                "success": False,
                "error": f"Files not found: {', '.join(missing_files)}",
                "missing_files": missing_files,
                "session_id": context.session_id,
                "timestamp": datetime.now().isoformat()
            }
        
        if not validated_files:
            return {
                "success": False,
                "error": "No valid files provided for upload",
                "session_id": context.session_id,
                "timestamp": datetime.now().isoformat()
            }
        
        logger.info(f"Uploading {len(validated_files)} file(s) to '{params.selector}'")
        
        # Wait for file input element
        await page.wait_for_selector(params.selector, timeout=params.timeout)
        
        # Get element information
        element = page.locator(params.selector).first
        element_count = await element.count()
        
        if element_count == 0:
            return {
                "success": False,
                "error": f"File input element not found: {params.selector}",
                "session_id": context.session_id,
                "timestamp": datetime.now().isoformat()
            }
        
        # Verify it's a file input
        input_type = await element.get_attribute("type")
        if input_type != "file":
            return {
                "success": False,
                "error": f"Element is not a file input (type: {input_type})",
                "selector": params.selector,
                "session_id": context.session_id,
                "timestamp": datetime.now().isoformat()
            }
        
        # Check if multiple files are allowed
        multiple = await element.get_attribute("multiple")
        accept_attr = await element.get_attribute("accept")
        
        if len(validated_files) > 1 and multiple is None:
            return {
                "success": False,
                "error": "Multiple files provided but element doesn't accept multiple files",
                "selector": params.selector,
                "session_id": context.session_id,
                "timestamp": datetime.now().isoformat()
            }
        
        # Perform file upload
        await element.set_input_files(validated_files)
        
        # Gather file information
        uploaded_files = []
        for file_path in validated_files:
            path = Path(file_path)
            uploaded_files.append({
                "path": file_path,
                "name": path.name,
                "size": path.stat().st_size,
                "extension": path.suffix
            })
        
        # Small delay to let any upload processing begin
        await asyncio.sleep(0.1)
        
        # End video action
        await context.end_video_action("file_upload")
        
        result = {
            "success": True,
            "selector": params.selector,
            "uploaded_files": uploaded_files,
            "file_count": len(uploaded_files),
            "total_size": sum(f["size"] for f in uploaded_files),
            "multiple_allowed": multiple is not None,
            "accept_types": accept_attr,
            "session_id": context.session_id,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"File upload successful: {len(uploaded_files)} file(s) uploaded")
        return result
        
    except Exception as e:
        logger.error(f"File upload failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "selector": params.selector,
            "session_id": params.session_id,
            "timestamp": datetime.now().isoformat()
        }


async def browser_handle_dialog(params: HandleDialogParams) -> Dict[str, Any]:
    """
    Handle browser dialogs (alert, confirm, prompt).
    
    Provides comprehensive dialog handling for JavaScript-generated dialogs
    including alert, confirm, and prompt dialogs. Supports both accepting
    and dismissing dialogs with optional text input for prompts.
    
    Features:
    - Alert, confirm, and prompt dialog handling
    - Accept or dismiss dialog options
    - Text input for prompt dialogs
    - Dialog message capture
    - Automatic dialog detection and handling
    
    Returns:
        Dialog handling result with dialog information
    """
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_or_create_session(params.session_id)
        
        # Begin video action
        await context.begin_video_action("handle_dialog")
        
        # Get current page
        page = await context.get_current_page()
        
        logger.info(f"Setting up dialog handler (accept: {params.accept})")
        
        # Dialog information storage
        dialog_info = {"handled": False}
        
        # Set up dialog handler
        async def dialog_handler(dialog):
            try:
                dialog_info.update({
                    "type": dialog.type,
                    "message": dialog.message,
                    "default_value": dialog.default_value if hasattr(dialog, "default_value") else None,
                    "handled": True
                })
                
                logger.info(f"Handling {dialog.type} dialog: {dialog.message}")
                
                if params.accept:
                    if dialog.type == "prompt" and params.prompt_text is not None:
                        await dialog.accept(params.prompt_text)
                        dialog_info["prompt_text"] = params.prompt_text
                    else:
                        await dialog.accept()
                    dialog_info["action"] = "accepted"
                else:
                    await dialog.dismiss()
                    dialog_info["action"] = "dismissed"
                    
            except Exception as e:
                logger.error(f"Dialog handler error: {str(e)}")
                dialog_info.update({
                    "error": str(e),
                    "action": "error"
                })
        
        # Register dialog handler
        page.on("dialog", dialog_handler)
        
        # Wait a moment for any pending dialogs
        await asyncio.sleep(0.5)
        
        # Remove dialog handler
        page.remove_listener("dialog", dialog_handler)
        
        # End video action
        await context.end_video_action("handle_dialog")
        
        if dialog_info["handled"]:
            result = {
                "success": True,
                "dialog_info": dialog_info,
                "session_id": context.session_id,
                "timestamp": datetime.now().isoformat()
            }
            logger.info(f"Dialog handled: {dialog_info.get('type', 'unknown')} dialog {dialog_info.get('action', 'unknown')}")
        else:
            result = {
                "success": False,
                "error": "No dialog appeared to handle",
                "waited_time": "500ms",
                "session_id": context.session_id,
                "timestamp": datetime.now().isoformat()
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Handle dialog failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "session_id": params.session_id,
            "timestamp": datetime.now().isoformat()
        }


async def browser_dismiss_file_chooser(params: DismissFileChooserParams) -> Dict[str, Any]:
    """
    Dismiss file chooser dialogs without uploading files.
    
    Handles the dismissal of file chooser dialogs that may be stuck open,
    providing a way to cancel file upload operations gracefully.
    
    Features:
    - File chooser dialog detection
    - Graceful dialog dismissal
    - Multiple dialog handling
    - Session state management
    
    Returns:
        File chooser dismissal result
    """
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_or_create_session(params.session_id)
        
        # Begin video action
        await context.begin_video_action("dismiss_file_chooser")
        
        # Get current page
        page = await context.get_current_page()
        
        logger.info("Setting up file chooser dismissal handler")
        
        # File chooser information storage
        chooser_info = {"dismissed_count": 0, "choosers": []}
        
        # Set up file chooser handler
        async def file_chooser_handler(file_chooser):
            try:
                chooser_info["choosers"].append({
                    "element": str(file_chooser.element),
                    "multiple": file_chooser.is_multiple(),
                    "timestamp": datetime.now().isoformat()
                })
                
                logger.info(f"Dismissing file chooser (multiple: {file_chooser.is_multiple()})")
                
                # Dismiss by setting empty file list
                await file_chooser.set_files([])
                chooser_info["dismissed_count"] += 1
                
            except Exception as e:
                logger.error(f"File chooser handler error: {str(e)}")
                chooser_info["error"] = str(e)
        
        # Register file chooser handler
        page.on("filechooser", file_chooser_handler)
        
        # Wait a moment for any pending file choosers
        await asyncio.sleep(1.0)
        
        # Remove file chooser handler
        page.remove_listener("filechooser", file_chooser_handler)
        
        # End video action
        await context.end_video_action("dismiss_file_chooser")
        
        result = {
            "success": True,
            "dismissed_count": chooser_info["dismissed_count"],
            "choosers_found": len(chooser_info["choosers"]),
            "chooser_details": chooser_info["choosers"],
            "session_id": context.session_id,
            "timestamp": datetime.now().isoformat()
        }
        
        if chooser_info["dismissed_count"] > 0:
            result["message"] = f"Dismissed {chooser_info['dismissed_count']} file chooser(s)"
            logger.info(f"File choosers dismissed: {chooser_info['dismissed_count']}")
        else:
            result["message"] = "No file chooser dialogs found to dismiss"
        
        return result
        
    except Exception as e:
        logger.error(f"Dismiss file chooser failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "session_id": params.session_id,
            "timestamp": datetime.now().isoformat()
        }


async def browser_dismiss_all_file_choosers(session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Dismiss all open file chooser dialogs without uploading files.
    
    Comprehensive cleanup function for stuck file chooser dialogs.
    Useful when multiple file choosers are open and need to be cleared.
    
    Returns:
        Result of dismissing all file chooser dialogs
    """
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_or_create_session(session_id)
        
        # Begin video action
        await context.begin_video_action("dismiss_all_file_choosers")
        
        # Get current page
        page = await context.get_current_page()
        
        logger.info("Dismissing all file chooser dialogs")
        
        # Track dismissal attempts
        dismissal_attempts = 0
        max_attempts = 5
        
        # Set up comprehensive file chooser handler
        async def comprehensive_file_chooser_handler(file_chooser):
            nonlocal dismissal_attempts
            try:
                dismissal_attempts += 1
                logger.info(f"Dismissing file chooser attempt {dismissal_attempts}")
                await file_chooser.set_files([])
            except Exception as e:
                logger.error(f"File chooser dismissal error: {str(e)}")
        
        # Register handler and wait for any dialogs
        page.on("filechooser", comprehensive_file_chooser_handler)
        
        # Wait longer to catch any delayed dialogs
        await asyncio.sleep(2.0)
        
        # Try to trigger any remaining file choosers by evaluating page state
        try:
            # Close any programmatically opened file dialogs
            await page.evaluate("""
                () => {
                    // Cancel any active file input clicks
                    const fileInputs = document.querySelectorAll('input[type="file"]');
                    fileInputs.forEach(input => {
                        try {
                            input.value = '';
                            input.blur();
                        } catch (e) {}
                    });
                }
            """)
        except Exception as e:
            logger.debug(f"JavaScript cleanup warning: {str(e)}")
        
        # Remove handler
        page.remove_listener("filechooser", comprehensive_file_chooser_handler)
        
        # End video action
        await context.end_video_action("dismiss_all_file_choosers")
        
        result = {
            "success": True,
            "dismissal_attempts": dismissal_attempts,
            "max_wait_time": "2000ms",
            "session_id": context.session_id,
            "timestamp": datetime.now().isoformat()
        }
        
        if dismissal_attempts > 0:
            result["message"] = f"Made {dismissal_attempts} file chooser dismissal attempt(s)"
        else:
            result["message"] = "No file chooser dialogs detected"
        
        logger.info(f"File chooser cleanup completed: {dismissal_attempts} dismissal attempts")
        return result
        
    except Exception as e:
        logger.error(f"Dismiss all file choosers failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }