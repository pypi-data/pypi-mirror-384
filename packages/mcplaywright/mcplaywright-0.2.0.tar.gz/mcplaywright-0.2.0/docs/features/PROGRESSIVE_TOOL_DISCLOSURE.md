# 🎯 Progressive Tool Disclosure with Expert Mode Override

## 🌟 Enhanced System Design

MCPlaywright's tool visibility system is evolving from "Dynamic Tool Visibility" to **"Progressive Tool Disclosure with Expert Mode Override"** - a more sophisticated UX pattern that provides both guided discovery and power-user access.

## 🏗️ Current vs Enhanced Architecture

### Current Progressive Disclosure
```
Initial State:     9 tools  → Setup & Discovery
+ Session:        35 tools  → Browser Interaction  
+ Recording:      40 tools  → Video Control
+ Monitoring:     44 tools  → HTTP Analysis
```

### Enhanced with Expert Mode
```
Normal Mode:       9 → 35 → 40 → 44 tools (Progressive)
Expert Mode:      44 tools (All visible with dependency guidance)
```

## 🎯 Core Enhancement: Expert Mode Override

### Problem Solved
- **Power users** frustrated by progressive disclosure delays
- **API developers** need to see full tool surface immediately
- **Debuggers** need to test invalid tool calls
- **Documentation** requires complete tool listing

### Solution: `enable_expert_mode` Tool

#### Tool Response Example
```json
{
  "expert_mode_enabled": true,
  "all_tools_visible": 44,
  "progressive_disclosure_disabled": true,
  "dependency_map": {
    "video_recording_tools": {
      "tools": ["pause_recording", "stop_recording", "resume_recording", "set_recording_mode"],
      "requires": "start_recording",
      "state_check": "active_video_recording"
    },
    "http_monitoring_tools": {
      "tools": ["get_requests", "export_requests", "clear_requests"],
      "requires": "start_request_monitoring", 
      "state_check": "active_http_monitoring"
    },
    "session_required_tools": {
      "tools": ["navigate", "click_element", "take_screenshot", "..."],
      "requires": "configure_browser",
      "state_check": "active_browser_session"
    }
  },
  "usage_warning": "All tools are now visible. Tools may fail if prerequisites not met. Use dependency_map for guidance."
}
```

## 🛡️ Smart Error Handling in Expert Mode

### Current Behavior (Blocks)
```python
# StateValidationMiddleware current
raise ToolError("Tool 'pause_recording' requires active video recording. Use 'start_recording' first.")
```

### Expert Mode Behavior (Guides)
```python
# StateValidationMiddleware in expert mode
return {
    "success": false,
    "error_code": "DEPENDENCY_NOT_MET",
    "message": "No active recording found",
    "required_prerequisite": "start_recording",
    "suggestion": "Run 'start_recording' first, then try 'pause_recording'",
    "can_retry": true,
    "expert_mode": true
}
```

## 📊 Tool Categories & Dependencies

### Always Available (9 tools)
```python
always_available = {
    "configure_browser",     # Core setup
    "list_sessions",         # Session management
    "get_session_info",      # Session management
    "close_session",         # Session management
    "start_recording",       # Video activation
    "start_request_monitoring", # HTTP activation
    "health_check",          # System diagnostics
    "server_info",           # System diagnostics
    "test_playwright_installation" # System diagnostics
}
```

### Session Required (26 tools)
```python
session_required = {
    # Basic interaction
    "navigate", "click_element", "take_screenshot", "type_text", "fill_element",
    
    # Advanced interaction
    "hover_element", "press_key", "drag_and_drop", "select_option", "check_element",
    
    # File & Dialog handling
    "file_upload", "handle_dialog", "dismiss_file_chooser", "dismiss_all_file_choosers",
    
    # Wait & Timing
    "wait_for_text", "wait_for_text_gone", "wait_for_element", "wait_for_load_state", 
    "wait_for_time", "wait_for_request",
    
    # Advanced analysis
    "evaluate", "console_messages", "snapshot", "get_accessibility_tree", "get_page_structure",
    
    # Tab management
    "new_tab", "close_tab", "switch_tab", "list_tabs", "get_page_info"
}
```

### Video Recording (5 tools)
```python
video_recording = {
    "pause_recording",       # Requires: start_recording
    "resume_recording",      # Requires: start_recording
    "stop_recording",        # Requires: start_recording
    "set_recording_mode",    # Requires: start_recording
    "recording_status"       # Requires: start_recording
}
```

### HTTP Monitoring (4 tools)
```python
http_monitoring = {
    "get_requests",          # Requires: start_request_monitoring
    "export_requests",       # Requires: start_request_monitoring
    "clear_requests",        # Requires: start_request_monitoring
    "request_monitoring_status" # Requires: start_request_monitoring
}
```

## 🔄 State Management

### Expert Mode State
```python
# Global state (middleware level)
_expert_mode_enabled: bool = False

# Could be enhanced to per-client state:
# _expert_mode_clients: Set[str] = set()
```

### State Transitions
```
Normal Mode → enable_expert_mode → Expert Mode
Expert Mode → disable_expert_mode → Normal Mode
Expert Mode → [any tool] → Expert Mode (with smart errors)
```

## 🧪 Testing Strategy

### Test Categories

#### 1. Progressive Disclosure Tests
```python
def test_initial_connection_shows_9_tools()
def test_session_creation_shows_35_tools() 
def test_recording_start_shows_40_tools()
def test_monitoring_start_shows_44_tools()
```

#### 2. Expert Mode Tests  
```python
def test_enable_expert_mode_shows_all_44_tools()
def test_expert_mode_dependency_mapping()
def test_expert_mode_smart_error_responses()
def test_disable_expert_mode_returns_to_progressive()
```

#### 3. State Validation Tests
```python
def test_normal_mode_blocks_invalid_tools()
def test_expert_mode_guides_invalid_tools() 
def test_expert_mode_preserves_valid_tool_execution()
```

#### 4. Integration Tests
```python
def test_expert_mode_with_recording_workflow()
def test_expert_mode_with_monitoring_workflow()
def test_expert_mode_session_lifecycle()
```

## 🚀 Implementation Files

### Core Implementation
- `src/mcplaywright/middleware.py` - Enhanced middleware with expert mode
- `src/mcplaywright/server.py` - New expert mode tools

### Test Files
- `tests/test_progressive_disclosure.py` - Progressive disclosure testing
- `tests/test_expert_mode.py` - Expert mode specific testing
- `tests/test_tool_dependencies.py` - Dependency validation testing

## 🎯 Benefits

### For Power Users
- **Immediate access** to all 44 tools
- **Dependency guidance** without trial-and-error
- **Smart error messages** with actionable suggestions
- **No cognitive overhead** from progressive disclosure

### For Regular Users
- **Maintains progressive disclosure** for guided experience
- **No breaking changes** to existing workflows
- **Optional enhancement** - doesn't affect default behavior

### For Developers/Debuggers
- **Full API surface visibility** for documentation
- **Test invalid tool combinations** with helpful errors
- **Understand tool relationships** through dependency mapping
- **Debug tool visibility issues** by seeing everything

## 🔮 Future Enhancements

### Per-Client Expert Mode
```python
# Client-specific expert mode
expert_mode_clients: Dict[str, bool] = {}
```

### Skill-Based Progressive Disclosure
```python
# Track user skill level and adjust progression
user_skill_levels: Dict[str, SkillLevel] = {}
```

### AI-Powered Tool Suggestions
```python
# Suggest tools based on current context and history
def suggest_next_tools(current_state, user_history) -> List[str]
```

---

This enhanced system transforms MCPlaywright from a traditional MCP server into an intelligent, adaptive automation platform that serves both novice and expert users effectively.