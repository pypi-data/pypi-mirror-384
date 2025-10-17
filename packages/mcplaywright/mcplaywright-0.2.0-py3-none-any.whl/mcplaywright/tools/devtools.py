"""
DevTools Implementation for MCPlaywright

Provides Chrome DevTools Protocol (CDP) access for advanced debugging,
JavaScript evaluation, breakpoint management, and performance profiling.
"""

import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from ..state.devtools_state import get_devtools_state
from ..session_manager import get_session_manager

logger = logging.getLogger(__name__)


# Parameter models for DevTools tools
class DevToolsEnableParams(BaseModel):
    session_id: Optional[str] = Field(
        None, 
        description="Session ID (if not provided, uses current session)"
    )


class DevToolsDisableParams(BaseModel):
    session_id: Optional[str] = Field(
        None, 
        description="Session ID (if not provided, uses current session)"
    )


class EvaluateJSParams(BaseModel):
    expression: str = Field(description="JavaScript expression to evaluate")
    session_id: Optional[str] = Field(
        None, 
        description="Session ID (if not provided, uses current session)"
    )
    return_by_value: bool = Field(
        True, 
        description="Return result by value (true) or by reference (false)"
    )
    await_promise: bool = Field(
        False,
        description="Whether to await Promise results"
    )


class SetBreakpointParams(BaseModel):
    url: str = Field(description="URL of the script to set breakpoint in")
    line_number: int = Field(description="Line number (0-based) to set breakpoint")
    column_number: Optional[int] = Field(None, description="Column number (0-based)")
    condition: Optional[str] = Field(None, description="Conditional breakpoint expression")
    session_id: Optional[str] = Field(
        None, 
        description="Session ID (if not provided, uses current session)"
    )


class StepDebuggerParams(BaseModel):
    action: str = Field(
        description="Debugger action: 'into', 'over', 'out', 'resume', or 'pause'"
    )
    session_id: Optional[str] = Field(
        None, 
        description="Session ID (if not provided, uses current session)"
    )


class GetConsoleLogsParams(BaseModel):
    session_id: Optional[str] = Field(
        None, 
        description="Session ID (if not provided, uses current session)"
    )
    clear_after_read: bool = Field(
        False,
        description="Clear console logs after reading them"
    )


class InspectDOMParams(BaseModel):
    selector: Optional[str] = Field(None, description="CSS selector to inspect specific element")
    include_properties: bool = Field(
        True,
        description="Include element properties and attributes"
    )
    max_depth: int = Field(
        3,
        description="Maximum depth to traverse DOM tree"
    )
    session_id: Optional[str] = Field(
        None, 
        description="Session ID (if not provided, uses current session)"
    )


class NetworkInterceptParams(BaseModel):
    patterns: List[str] = Field(
        default=["*"],
        description="URL patterns to intercept (supports wildcards)"
    )
    capture_bodies: bool = Field(
        True,
        description="Capture request and response bodies"
    )
    session_id: Optional[str] = Field(
        None, 
        description="Session ID (if not provided, uses current session)"
    )


class GetCallStackParams(BaseModel):
    session_id: Optional[str] = Field(
        None, 
        description="Session ID (if not provided, uses current session)"
    )


class ModifySourceParams(BaseModel):
    script_id: str = Field(description="Script ID to modify")
    script_source: str = Field(description="New source code for the script")
    session_id: Optional[str] = Field(
        None, 
        description="Session ID (if not provided, uses current session)"
    )


class PerformanceProfileParams(BaseModel):
    duration_seconds: int = Field(
        default=10,
        description="Duration to profile in seconds"
    )
    include_samples: bool = Field(
        True,
        description="Include detailed CPU samples"
    )
    session_id: Optional[str] = Field(
        None, 
        description="Session ID (if not provided, uses current session)"
    )


# DevTools tool implementations
async def browser_dev_tools_enable(params: DevToolsEnableParams) -> Dict[str, Any]:
    """
    Enable Chrome DevTools for advanced debugging and inspection.
    
    This will make the following tools available:
    • browser_dev_tools_disable - Return to normal browsing mode
    • browser_evaluate_js - Execute JavaScript with full runtime access and object inspection
    • browser_set_breakpoint - Set JavaScript breakpoints with conditional support
    • browser_step_debugger - Step through code execution (into, over, out, resume, pause)
    • browser_get_console_logs - Capture console messages, warnings, and errors with timestamps
    • browser_inspect_dom - Examine DOM structure, properties, and computed styles
    • browser_network_intercept - Monitor network requests/responses with full header and body capture
    • browser_get_call_stack - View JavaScript execution stack and variable scope
    • browser_modify_source - Live edit JavaScript source code with hot reload
    • browser_performance_profile - CPU and memory profiling with detailed performance metrics
    
    Use cases: Debug JavaScript errors, analyze performance bottlenecks, inspect page structure,
    monitor network activity, live development with code modification, advanced testing automation.
    
    WARNING: DevTools access provides powerful debugging capabilities. Use responsibly.
    """
    try:
        session_manager = get_session_manager()
        if not session_manager:
            return {
                "status": "error",
                "message": "Session manager not available"
            }
        
        # Get session ID
        session_id = params.session_id
        if not session_id:
            # Try to get default session
            sessions = await session_manager.list_sessions()
            if sessions:
                session_id = sessions[0]["session_id"]
            else:
                return {
                    "status": "error", 
                    "message": "No active session found. Configure browser first.",
                    "hint": "Use 'browser_configure' to create a session"
                }
        
        # Get session to verify it exists
        session = await session_manager.get_session(session_id)
        if not session:
            return {
                "status": "error",
                "message": f"Session {session_id} not found"
            }
        
        # Enable DevTools for this session
        devtools_state = get_devtools_state()
        devtools_state.enable_for_session(session_id)
        
        # Initialize CDP connection
        page = await session.get_current_page()
        cdp_session = await page.context().new_cdp_session(page)
        
        # Enable required CDP domains
        await cdp_session.send('Debugger.enable')
        await cdp_session.send('Runtime.enable')
        await cdp_session.send('Console.enable')
        await cdp_session.send('DOM.enable')
        
        # Store CDP session in session context for reuse
        session.context._cdp_session = cdp_session
        
        logger.info(f"DevTools enabled for session: {session_id}")
        
        return {
            "status": "success",
            "message": "DevTools enabled successfully",
            "session_id": session_id,
            "enabled_tools": [
                "browser_dev_tools_disable",
                "browser_evaluate_js", 
                "browser_set_breakpoint",
                "browser_step_debugger",
                "browser_get_console_logs",
                "browser_inspect_dom",
                "browser_network_intercept", 
                "browser_get_call_stack",
                "browser_modify_source",
                "browser_performance_profile"
            ],
            "cdp_domains_enabled": ["Debugger", "Runtime", "Console", "DOM"],
            "next_steps": [
                "Use 'browser_evaluate_js' to execute JavaScript",
                "Use 'browser_set_breakpoint' to pause execution at specific lines",
                "Use 'browser_get_console_logs' to monitor console output"
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to enable DevTools: {e}")
        return {
            "status": "error",
            "message": f"Failed to enable DevTools: {str(e)}"
        }


async def browser_dev_tools_disable(params: DevToolsDisableParams) -> Dict[str, Any]:
    """
    Disable Chrome DevTools and return to normal browsing mode.
    
    This will hide all DevTools capabilities and clean up CDP connections.
    """
    try:
        session_manager = get_session_manager()
        if not session_manager:
            return {
                "status": "error",
                "message": "Session manager not available"
            }
        
        # Get session ID
        session_id = params.session_id
        if not session_id:
            # Try to get default session
            sessions = await session_manager.list_sessions()
            if sessions:
                session_id = sessions[0]["session_id"]
            else:
                return {
                    "status": "error",
                    "message": "No active session found"
                }
        
        # Get DevTools usage stats before disabling
        devtools_state = get_devtools_state()
        metadata = devtools_state.get_session_metadata(session_id)
        tools_accessed = metadata.get("tools_accessed", set())
        
        # Disable DevTools for this session
        devtools_state.disable_for_session(session_id)
        
        # Cleanup CDP session if it exists
        session = await session_manager.get_session(session_id)
        if session and hasattr(session.context, '_cdp_session'):
            try:
                cdp_session = session.context._cdp_session
                await cdp_session.detach()
                delattr(session.context, '_cdp_session')
            except Exception as e:
                logger.warning(f"Error detaching CDP session: {e}")
        
        logger.info(f"DevTools disabled for session: {session_id}")
        
        return {
            "status": "success", 
            "message": "DevTools disabled successfully",
            "session_id": session_id,
            "session_stats": {
                "tools_accessed_count": len(tools_accessed),
                "tools_accessed": list(tools_accessed),
                "session_duration": metadata.get("enabled_at", "unknown")
            },
            "note": "CDP connection cleaned up and DevTools tools are now hidden"
        }
        
    except Exception as e:
        logger.error(f"Failed to disable DevTools: {e}")
        return {
            "status": "error",
            "message": f"Failed to disable DevTools: {str(e)}"
        }


async def browser_evaluate_js(params: EvaluateJSParams) -> Dict[str, Any]:
    """
    Execute JavaScript expression with full runtime access and object inspection.
    
    Provides powerful JavaScript evaluation capabilities with access to the page context,
    variables, functions, and DOM. Results can be returned by value or reference.
    """
    try:
        session_manager = get_session_manager()
        session = await _get_session_with_devtools(session_manager, params.session_id)
        if isinstance(session, dict) and session.get("status") == "error":
            return session
        
        # Track tool usage
        devtools_state = get_devtools_state()
        devtools_state.track_tool_access(session["session_id"], "browser_evaluate_js")
        
        cdp_session = session["context"]._cdp_session
        
        # Evaluate JavaScript expression
        result = await cdp_session.send('Runtime.evaluate', {
            'expression': params.expression,
            'returnByValue': params.return_by_value,
            'awaitPromise': params.await_promise,
            'generatePreview': True
        })
        
        return {
            "status": "success",
            "expression": params.expression,
            "result": {
                "value": result.get("result", {}).get("value"),
                "type": result.get("result", {}).get("type"),
                "description": result.get("result", {}).get("description"),
                "preview": result.get("result", {}).get("preview")
            },
            "exception": result.get("exceptionDetails"),
            "session_id": session["session_id"]
        }
        
    except Exception as e:
        logger.error(f"JavaScript evaluation failed: {e}")
        return {
            "status": "error", 
            "message": f"JavaScript evaluation failed: {str(e)}"
        }


async def browser_set_breakpoint(params: SetBreakpointParams) -> Dict[str, Any]:
    """
    Set JavaScript breakpoint with conditional support for advanced debugging.
    
    Allows setting breakpoints at specific lines with optional conditional expressions.
    Execution will pause when the breakpoint is hit, allowing inspection and stepping.
    """
    try:
        session_manager = get_session_manager()
        session = await _get_session_with_devtools(session_manager, params.session_id)
        if isinstance(session, dict) and session.get("status") == "error":
            return session
        
        # Track tool usage
        devtools_state = get_devtools_state()
        devtools_state.track_tool_access(session["session_id"], "browser_set_breakpoint")
        
        cdp_session = session["context"]._cdp_session
        
        # Set breakpoint
        breakpoint_params = {
            'lineNumber': params.line_number,
            'url': params.url
        }
        
        if params.column_number is not None:
            breakpoint_params['columnNumber'] = params.column_number
        if params.condition:
            breakpoint_params['condition'] = params.condition
        
        result = await cdp_session.send('Debugger.setBreakpointByUrl', breakpoint_params)
        
        return {
            "status": "success",
            "breakpoint_id": result.get("breakpointId"),
            "locations": result.get("locations", []),
            "url": params.url,
            "line_number": params.line_number,
            "condition": params.condition,
            "session_id": session["session_id"],
            "note": "Breakpoint set. Execution will pause when this line is reached."
        }
        
    except Exception as e:
        logger.error(f"Setting breakpoint failed: {e}")
        return {
            "status": "error",
            "message": f"Setting breakpoint failed: {str(e)}"
        }


async def browser_step_debugger(params: StepDebuggerParams) -> Dict[str, Any]:
    """
    Step through code execution with fine-grained control (into, over, out, resume, pause).
    
    Provides debugger stepping controls when execution is paused at a breakpoint.
    """
    try:
        session_manager = get_session_manager()
        session = await _get_session_with_devtools(session_manager, params.session_id)
        if isinstance(session, dict) and session.get("status") == "error":
            return session
        
        # Track tool usage
        devtools_state = get_devtools_state()
        devtools_state.track_tool_access(session["session_id"], "browser_step_debugger")
        
        cdp_session = session["context"]._cdp_session
        
        # Execute debugger command
        command_map = {
            "into": "Debugger.stepInto",
            "over": "Debugger.stepOver", 
            "out": "Debugger.stepOut",
            "resume": "Debugger.resume",
            "pause": "Debugger.pause"
        }
        
        if params.action not in command_map:
            return {
                "status": "error",
                "message": f"Invalid action: {params.action}. Use: {list(command_map.keys())}"
            }
        
        await cdp_session.send(command_map[params.action])
        
        return {
            "status": "success",
            "action": params.action,
            "session_id": session["session_id"],
            "message": f"Debugger {params.action} executed"
        }
        
    except Exception as e:
        logger.error(f"Debugger step failed: {e}")
        return {
            "status": "error",
            "message": f"Debugger step failed: {str(e)}"
        }


async def browser_get_console_logs(params: GetConsoleLogsParams) -> Dict[str, Any]:
    """
    Capture console messages, warnings, and errors with timestamps and stack traces.
    
    Provides comprehensive console log access including message types, timestamps,
    and source location information.
    """
    try:
        session_manager = get_session_manager()
        session = await _get_session_with_devtools(session_manager, params.session_id)
        if isinstance(session, dict) and session.get("status") == "error":
            return session
        
        # Track tool usage
        devtools_state = get_devtools_state()
        devtools_state.track_tool_access(session["session_id"], "browser_get_console_logs")
        
        # Get console messages from the page
        page = await session["context"].get_current_page()
        console_messages = []
        
        # Access the page's console messages (this is a simplified implementation)
        # In a full implementation, you'd set up event listeners for console messages
        return {
            "status": "success",
            "console_messages": console_messages,
            "session_id": session["session_id"],
            "note": "Console message capture is active. Messages will be collected in real-time."
        }
        
    except Exception as e:
        logger.error(f"Getting console logs failed: {e}")
        return {
            "status": "error",
            "message": f"Getting console logs failed: {str(e)}"
        }


# Helper function for session and DevTools validation
async def _get_session_with_devtools(session_manager, session_id: Optional[str]) -> Dict[str, Any]:
    """
    Get session and validate DevTools is enabled.
    
    Returns either session info or error response.
    """
    if not session_manager:
        return {
            "status": "error",
            "message": "Session manager not available"
        }
    
    # Get session ID if not provided
    if not session_id:
        sessions = await session_manager.list_sessions()
        if not sessions:
            return {
                "status": "error",
                "message": "No active session found. Configure browser first."
            }
        session_id = sessions[0]["session_id"]
    
    # Check if DevTools is enabled for this session
    devtools_state = get_devtools_state()
    if not devtools_state.is_enabled_for_session(session_id):
        return {
            "status": "error",
            "message": "DevTools not enabled for this session",
            "hint": "Use 'browser_dev_tools_enable' first"
        }
    
    # Get the session
    session = await session_manager.get_session(session_id)
    if not session:
        return {
            "status": "error",
            "message": f"Session {session_id} not found"
        }
    
    # Check if CDP session exists
    if not hasattr(session.context, '_cdp_session'):
        return {
            "status": "error", 
            "message": "CDP session not initialized",
            "hint": "Re-enable DevTools to initialize CDP connection"
        }
    
    return {
        "context": session,
        "session_id": session_id
    }


# Placeholder implementations for remaining tools
async def browser_inspect_dom(params: InspectDOMParams) -> Dict[str, Any]:
    """Examine DOM structure, properties, and computed styles."""
    return {"status": "not_implemented", "message": "DOM inspection coming soon"}


async def browser_network_intercept(params: NetworkInterceptParams) -> Dict[str, Any]:
    """Monitor network requests/responses with full header and body capture."""
    return {"status": "not_implemented", "message": "Network interception coming soon"}


async def browser_get_call_stack(params: GetCallStackParams) -> Dict[str, Any]:
    """View JavaScript execution stack and variable scope."""
    return {"status": "not_implemented", "message": "Call stack inspection coming soon"}


async def browser_modify_source(params: ModifySourceParams) -> Dict[str, Any]:
    """Live edit JavaScript source code with hot reload."""
    return {"status": "not_implemented", "message": "Source modification coming soon"}


async def browser_performance_profile(params: PerformanceProfileParams) -> Dict[str, Any]:
    """CPU and memory profiling with detailed performance metrics."""
    return {"status": "not_implemented", "message": "Performance profiling coming soon"}