# 🎯 Dynamic Tool Visibility System

MCPlaywright implements a revolutionary **dynamic tool visibility system** using FastMCP middleware that automatically shows/hides MCP tools based on current session state. This creates a contextual, guided user experience that reduces cognitive load and prevents invalid operations.

## 🌟 Core Concept

Instead of overwhelming users with all 48 tools at once, MCPlaywright intelligently presents only the tools that are relevant to the current browser session state:

- **No active session?** → Only show setup tools (`browser_configure`, `health_check`)
- **Recording started?** → Show recording control tools (`pause_recording`, `stop_recording`)  
- **Monitoring enabled?** → Show request analysis tools (`get_requests`, `export_requests`)
- **Invalid state?** → Block tool execution with helpful error messages

## 🏗️ Architecture

### Three Middleware Components

#### 1. **DynamicToolMiddleware** - Tool Visibility Control
```python
class DynamicToolMiddleware(Middleware):
    async def on_list_tools(self, context: MiddlewareContext, call_next):
        # Filter tools based on session state
        # Add contextual descriptions for hidden tools
        # Return only relevant tools to MCP client
```

**Responsibilities:**
- Filters tool list in real-time based on session state
- Adds helpful descriptions explaining why tools are hidden
- Categorizes tools into state-dependent groups
- Checks active recording/monitoring status across all sessions

#### 2. **SessionAwareMiddleware** - Context Management
```python
class SessionAwareMiddleware(Middleware):
    async def on_call_tool(self, context: MiddlewareContext, call_next):
        # Extract session_id from tool parameters
        # Store current session info in FastMCP context
        # Enable cross-tool state sharing within requests
```

**Responsibilities:**
- Extracts session IDs from tool parameters automatically
- Stores session context for other middleware to use
- Enables request-level state sharing between tools
- Provides debugging and logging context

#### 3. **StateValidationMiddleware** - Operation Safety
```python
class StateValidationMiddleware(Middleware):
    async def on_call_tool(self, context: MiddlewareContext, call_next):
        # Validate tool calls against current state
        # Block invalid operations with clear error messages
        # Suggest corrective actions to users
```

**Responsibilities:**
- Prevents invalid tool calls (e.g., pausing non-existent recording)
- Provides clear error messages with suggested solutions
- Validates state consistency before tool execution
- Acts as safety layer preventing resource conflicts

## 📊 Tool Categories

### Always Available Tools (5)
**Core management tools that are always needed:**
- `browser_configure` - Initial browser setup
- `browser_list_sessions` - Session management
- `browser_start_recording` - Video recording activation
- `browser_start_request_monitoring` - HTTP monitoring activation  
- `health_check` / `server_info` - System diagnostics

### Session-Required Tools (25+)
**Hidden when no active browser sessions exist:**
```python
session_required_tools = {
    "browser_navigate", "browser_click", "browser_screenshot",
    "browser_type", "browser_fill", "browser_hover",
    "browser_press_key", "browser_snapshot", "browser_drag",
    "browser_select_option", "browser_check", "browser_file_upload",
    "browser_handle_dialog", "browser_dismiss_file_chooser",
    "browser_wait_for", "browser_wait_for_element", 
    "browser_wait_for_load_state", "browser_wait_for_request",
    "browser_wait_for_text", "browser_wait_for_text_gone",
    "browser_evaluate", "browser_console_messages",
    "browser_tab_new", "browser_tab_close", 
    "browser_tab_select", "browser_tab_list",
    "browser_resize", "browser_get_page_info"
}
```

### Video Recording Tools (5)
**Only visible when video recording is active:**
```python
video_recording_tools = {
    "browser_pause_recording",
    "browser_resume_recording", 
    "browser_stop_recording",
    "browser_set_recording_mode",
    "browser_recording_status"
}
```

### HTTP Monitoring Tools (4)
**Only visible when HTTP monitoring is enabled:**
```python
http_monitoring_tools = {
    "browser_get_requests",
    "browser_export_requests", 
    "browser_clear_requests",
    "browser_request_monitoring_status"
}
```

## 🔄 State Detection Logic

### Active Recording Detection
```python
async def _check_active_recording(self, session_manager) -> bool:
    """Check if any session has active video recording"""
    sessions = await session_manager.list_sessions()
    for session_info in sessions:
        session = await session_manager.get_session(session_info["session_id"])
        if session and hasattr(session.context, '_video_config') and session.context._video_config:
            return True
    return False
```

### Active Monitoring Detection  
```python
async def _check_active_monitoring(self, session_manager) -> bool:
    """Check if any session has active HTTP monitoring"""
    sessions = await session_manager.list_sessions()
    for session_info in sessions:
        session = await session_manager.get_session(session_info["session_id"])
        if session and hasattr(session.context, '_request_monitor') and session.context._request_monitor:
            return True
    return False
```

## 🎯 User Experience Impact

### Before Dynamic Visibility
```
📋 Available Tools (48):
✅ browser_configure
✅ browser_navigate  
✅ browser_click
✅ browser_start_recording
✅ browser_pause_recording    ← Invalid (no recording)
✅ browser_resume_recording   ← Invalid (no recording)  
✅ browser_stop_recording     ← Invalid (no recording)
✅ browser_start_request_monitoring
✅ browser_get_requests       ← Invalid (no monitoring)
✅ browser_export_requests    ← Invalid (no monitoring)
... (39 more tools)
```
**Problems:** Overwhelming choice, invalid operations possible, poor UX

### After Dynamic Visibility

**Initial State (No Sessions):**
```
📋 Available Tools (5):
✅ browser_configure
✅ browser_list_sessions  
✅ browser_start_recording
✅ browser_start_request_monitoring
✅ health_check
```

**After Creating Session:**
```
📋 Available Tools (30+):
✅ browser_configure
✅ browser_navigate
✅ browser_click
✅ browser_screenshot
✅ browser_type
... (25+ interaction tools)
✅ browser_start_recording
✅ browser_start_request_monitoring
```

**After Starting Recording:**
```
📋 Available Tools (35+):
✅ (all previous tools)
✅ browser_pause_recording    ← Now valid!
✅ browser_resume_recording   ← Now valid!
✅ browser_stop_recording     ← Now valid!
✅ browser_set_recording_mode ← Now valid!
✅ browser_recording_status   ← Now valid!
```

## 🛡️ Error Prevention

### State Validation Examples

**Attempting to pause non-existent recording:**
```python
# Tool call: browser_pause_recording
# Middleware response:
{
  "error": {
    "code": "INVALID_STATE",
    "message": "Tool 'browser_pause_recording' requires active video recording. Use 'browser_start_recording' first."
  }
}
```

**Attempting to get requests without monitoring:**
```python
# Tool call: browser_get_requests  
# Middleware response:
{
  "error": {
    "code": "INVALID_STATE",
    "message": "Tool 'browser_get_requests' requires active HTTP monitoring. Use 'browser_start_request_monitoring' first."
  }
}
```

## 💡 Implementation Benefits

### For Users
- **Reduced Cognitive Load:** See only 5-15 relevant tools instead of 48
- **Guided Workflows:** Tools appear as features are enabled, naturally guiding usage
- **Error Prevention:** Invalid operations blocked with helpful suggestions
- **Professional UX:** Applications feel polished and contextually aware

### For Developers
- **Clean Architecture:** State management centralized in middleware  
- **Maintainable Code:** Tool visibility logic separated from tool implementation
- **Extensible Design:** Easy to add new state-dependent tool categories
- **FastMCP Integration:** Leverages framework's middleware capabilities fully

### For MCP Clients
- **Faster Tool Discovery:** Smaller tool lists load and display faster
- **Better Organization:** Tools grouped by functionality and availability
- **Reduced API Calls:** Clients can cache smaller, more focused tool lists
- **Enhanced UX:** Natural progressive disclosure of functionality

## 🔧 Configuration

### Middleware Registration
```python
# Initialize FastMCP app with dynamic tool middleware
app = FastMCP(
    name="MCPlaywright",
    version="0.1.0",
    description="Advanced browser automation with Playwright, video recording, and request monitoring"
)

# Add middleware for dynamic tool management
app.add_middleware(DynamicToolMiddleware())
app.add_middleware(SessionAwareMiddleware())  
app.add_middleware(StateValidationMiddleware())
```

### Customization Options

**Adding New Tool Categories:**
```python
# In DynamicToolMiddleware.__init__()
self.new_feature_tools = {
    "browser_new_feature_tool1",
    "browser_new_feature_tool2"
}

# In on_list_tools()
elif tool_name in self.new_feature_tools:
    has_new_feature = await self._check_new_feature_active(session_manager)
    should_show = has_new_feature
```

**Custom State Validation:**
```python
# In StateValidationMiddleware.on_call_tool()
elif tool_name in {"browser_new_feature_tool1"}:
    if not await self._check_new_feature_requirements(session_manager):
        raise ValueError(f"Tool '{tool_name}' requires X, Y, Z conditions.")
```

## 🚀 Future Enhancements

### Potential Additions
- **Permission-based visibility:** Show tools based on user authorization level
- **Feature flag integration:** Hide experimental tools behind feature flags
- **Performance-based filtering:** Hide resource-intensive tools on low-spec systems
- **Workflow-based grouping:** Show tools relevant to detected automation workflows
- **AI-powered suggestions:** Recommend next tools based on usage patterns

### Advanced State Management
- **Cross-session state:** Tools visible based on global server state
- **Time-based visibility:** Tools appear/disappear based on schedules
- **Resource-aware filtering:** Hide tools when system resources are constrained
- **Integration triggers:** Show tools when external systems are available

## 📚 Technical References

### FastMCP Middleware Documentation
- **Middleware System:** https://gofastmcp.com/servers/middleware
- **Context Management:** https://gofastmcp.com/servers/context
- **Tool Registration:** https://gofastmcp.com/servers/tools

### Implementation Files
- **Main Implementation:** `/src/mcplaywright/middleware.py`
- **Server Integration:** `/src/mcplaywright/server.py` (lines 103-105)
- **Session State Logic:** `/src/mcplaywright/session_manager.py`
- **Context Management:** `/src/mcplaywright/context.py`

---

## 🎉 Summary

The **Dynamic Tool Visibility System** transforms MCPlaywright from a traditional static MCP server into an intelligent, context-aware automation platform. By leveraging FastMCP's middleware capabilities, it creates a professional user experience that guides users through browser automation workflows naturally while preventing errors and reducing cognitive load.

This system represents a **new paradigm for MCP servers** - moving beyond simple tool registration to intelligent, state-aware tool orchestration that adapts to user workflows in real-time.