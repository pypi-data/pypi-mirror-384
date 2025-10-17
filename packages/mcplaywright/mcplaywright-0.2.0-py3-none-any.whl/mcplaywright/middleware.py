"""
Progressive tool disclosure middleware for MCPlaywright

Progressive disclosure system with expert mode override:
- Video recording tools only visible when recording is active
- HTTP monitoring tools only visible when monitoring is enabled  
- Session-specific tools only visible when session exists
- Expert mode shows all tools with dependency guidance
"""

from typing import List, Dict, Any, Optional
from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.exceptions import ToolError
from .session_manager import get_session_manager
from .state.devtools_state import get_devtools_state

# Global expert mode state (could be moved to session manager later)
_expert_mode_enabled = False


class DynamicToolMiddleware(Middleware):
    """Middleware for progressive tool disclosure with expert mode override"""
    
    def __init__(self):
        self.video_recording_tools = {
            "pause_recording",
            "resume_recording", 
            "stop_recording",
            "set_recording_mode",
            "recording_status"
        }
        
        self.http_monitoring_tools = {
            "get_requests",
            "export_requests", 
            "clear_requests",
            "request_monitoring_status"
        }
        
        self.session_required_tools = {
            "navigate",
            "click_element", 
            "take_screenshot",
            "type_text",
            "fill_element",
            "hover_element",
            "press_key",
            "snapshot",
            "drag_and_drop",
            "select_option",
            "check_element",
            "file_upload",
            "handle_dialog",
            "dismiss_file_chooser",
            "wait_for_text",
            "wait_for_element", 
            "wait_for_load_state",
            "wait_for_request",
            "wait_for_text_gone",
            "wait_for_time",
            "evaluate",
            "console_messages",
            "new_tab",
            "close_tab", 
            "switch_tab",
            "list_tabs",
            "get_page_info"
        }
        
        # DevTools tool categories for dynamic visibility
        self.devtools_tools = {
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
        }
        
        self.devtools_enable_tool = "browser_dev_tools_enable"
    
    async def on_list_tools(self, context: MiddlewareContext, call_next):
        """Filter tools based on current session state"""
        
        # Get all available tools from the next middleware/handler
        all_tools = await call_next(context)
        
        # Get session manager state
        session_manager = get_session_manager()
        if not session_manager:
            # No session manager - only show configuration tools
            return [tool for tool in all_tools 
                   if tool.name not in self.session_required_tools]
        
        visible_tools = []
        
        try:
            active_sessions = await session_manager.list_sessions()
            has_active_session = len(active_sessions) > 0
            
            # Check for active recording and monitoring across all sessions
            has_recording = await self._check_active_recording(session_manager)
            has_monitoring = await self._check_active_monitoring(session_manager)
            
            # Check DevTools state for current session  
            current_session_id = self._extract_session_id_from_context(context)
            devtools_state = get_devtools_state()
            has_devtools = devtools_state.is_enabled_for_session(current_session_id) if current_session_id else False
            
        except Exception:
            # If session manager fails, default to no sessions/features
            has_active_session = False
            has_recording = False
            has_monitoring = False
            has_devtools = False
        
        for tool in all_tools:
            tool_name = tool.name
            should_show = True
            original_description = tool.description
            
            # Always show core configuration and management tools
            if tool_name in {"configure_browser", "list_sessions", 
                           "get_session_info", "close_session",
                           "start_recording", "start_request_monitoring",
                           "health_check", "server_info", "test_playwright_installation"}:
                should_show = True
                
            # Hide session-dependent tools if no active sessions
            elif tool_name in self.session_required_tools and not has_active_session:
                should_show = False
                # Add helpful message explaining why tool is hidden
                tool.description = f"{original_description} (requires active browser session - use 'configure_browser' first)"
                
            # Hide video recording control tools if no recording active
            elif tool_name in self.video_recording_tools:
                should_show = has_recording
                if not has_recording:
                    tool.description = f"{original_description} (requires active video recording - use 'start_recording' first)"
                    
            # Hide HTTP monitoring tools if monitoring not enabled
            elif tool_name in self.http_monitoring_tools:
                should_show = has_monitoring
                if not has_monitoring:
                    tool.description = f"{original_description} (requires active HTTP monitoring - use 'start_request_monitoring' first)"
            
            # DevTools visibility logic - key implementation for dynamic tool hiding
            elif tool_name in self.devtools_tools:
                # DevTools tools only visible when DevTools is enabled for current session
                should_show = has_devtools
                # No description change - invisible tools don't need descriptions
                
            elif tool_name == self.devtools_enable_tool:
                # Enable tool only visible when DevTools is DISABLED
                should_show = not has_devtools
                # Description already contains list of tools it will enable
            
            if should_show:
                visible_tools.append(tool)
        
        return visible_tools
    
    async def _check_active_recording(self, session_manager) -> bool:
        """Check if any session has active video recording"""
        try:
            sessions = await session_manager.list_sessions()
            for session_info in sessions:
                session = await session_manager.get_session(session_info["session_id"])
                if session and hasattr(session.context, '_video_config') and session.context._video_config:
                    return True
            return False
        except Exception:
            return False
    
    async def _check_active_monitoring(self, session_manager) -> bool:
        """Check if any session has active HTTP monitoring"""
        try:
            sessions = await session_manager.list_sessions()
            for session_info in sessions:
                session = await session_manager.get_session(session_info["session_id"])
                if (session and hasattr(session.context, '_request_monitor') 
                    and session.context._request_monitor):
                    return True
            return False
        except Exception:
            return False
    
    def _extract_session_id_from_context(self, context: MiddlewareContext) -> Optional[str]:
        """
        Extract session ID from middleware context.
        
        For DevTools visibility, we need to determine which session (if any)
        is making the tool list request to check per-session DevTools state.
        """
        try:
            # Try to get session ID from FastMCP context state
            if hasattr(context, 'fastmcp_context') and hasattr(context.fastmcp_context, 'get_state'):
                session_id = context.fastmcp_context.get_state('current_session_id')
                if session_id:
                    return session_id
            
            # Fallback: try to extract from request parameters
            if hasattr(context, 'message') and hasattr(context.message, 'params'):
                params = context.message.params
                if hasattr(params, 'arguments') and params.arguments:
                    session_id = params.arguments.get('session_id')
                    if session_id:
                        return session_id
            
            # If no session context found, return None (DevTools will be disabled)
            return None
            
        except Exception:
            # If extraction fails, err on the side of caution - no DevTools
            return None


class SessionAwareMiddleware(Middleware):
    """Middleware for session-aware context management"""
    
    async def on_call_tool(self, context: MiddlewareContext, call_next):
        """Add session context to tool calls"""
        
        # Extract session_id from tool parameters if available
        try:
            if hasattr(context, 'message') and hasattr(context.message, 'params'):
                params = context.message.params
                if hasattr(params, 'arguments') and params.arguments:
                    session_id = params.arguments.get('session_id')
                    if session_id and hasattr(context, 'fastmcp_context'):
                        context.fastmcp_context.set_state('current_session_id', session_id)
            
            # Store tool name for logging/debugging
            if hasattr(context, 'message') and hasattr(context.message, 'params'):
                tool_name = context.message.params.name
                if tool_name and hasattr(context, 'fastmcp_context'):
                    context.fastmcp_context.set_state('current_tool', tool_name)
        except Exception:
            # If context extraction fails, continue without setting state
            pass
        
        return await call_next(context)


class StateValidationMiddleware(Middleware):
    """Middleware for validating tool calls against current state"""
    
    async def on_call_tool(self, context: MiddlewareContext, call_next):
        """Validate tool calls against current server state"""
        
        # Extract tool name from context
        tool_name = ""
        try:
            if hasattr(context, 'message') and hasattr(context.message, 'params'):
                tool_name = context.message.params.name
        except Exception:
            pass
        
        # Validate video recording tools
        if tool_name in {"pause_recording", "resume_recording", 
                        "stop_recording", "set_recording_mode"}:
            session_manager = get_session_manager()
            if not session_manager:
                raise ToolError("No session manager available")
                
            has_recording = await self._check_active_recording(session_manager)
            if not has_recording:
                raise ToolError(f"Tool '{tool_name}' requires active video recording. Use 'start_recording' first.")
        
        # Validate HTTP monitoring tools
        elif tool_name in {"get_requests", "export_requests", 
                          "clear_requests"}:
            session_manager = get_session_manager()
            if not session_manager:
                raise ToolError("No session manager available")
                
            has_monitoring = await self._check_active_monitoring(session_manager)
            if not has_monitoring:
                raise ToolError(f"Tool '{tool_name}' requires active HTTP monitoring. Use 'start_request_monitoring' first.")
        
        return await call_next(context)
    
    async def _check_active_recording(self, session_manager) -> bool:
        """Check if any session has active video recording"""
        try:
            sessions = await session_manager.list_sessions()
            for session_info in sessions:
                session = await session_manager.get_session(session_info["session_id"])
                if session and hasattr(session.context, '_video_config') and session.context._video_config:
                    return True
            return False
        except Exception:
            return False
    
    async def _check_active_monitoring(self, session_manager) -> bool:
        """Check if any session has active HTTP monitoring"""
        try:
            sessions = await session_manager.list_sessions()
            for session_info in sessions:
                session = await session_manager.get_session(session_info["session_id"])
                if (session and hasattr(session.context, '_request_monitor') 
                    and session.context._request_monitor):
                    return True
            return False
        except Exception:
            return False