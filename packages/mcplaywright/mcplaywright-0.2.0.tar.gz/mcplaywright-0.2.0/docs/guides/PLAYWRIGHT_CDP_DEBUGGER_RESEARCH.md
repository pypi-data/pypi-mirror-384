# Playwright Chrome DevTools Protocol (CDP) and JavaScript Debugger Research

## Executive Summary

This document provides comprehensive research on Playwright's capabilities for accessing and interacting with Chrome DevTools, specifically focusing on the JavaScript debugger and Chrome DevTools Protocol (CDP) integration. The research covers official APIs, practical implementation examples, and integration strategies for MCPlaywright.

## Chrome DevTools Protocol (CDP) Overview

The Chrome DevTools Protocol provides a way to instrument, inspect, debug and profile Chromium, Chrome and other Blink-based browsers. CDP is divided into multiple domains, each defining commands it supports and events it generates, using serialized JSON objects for communication.

### Key CDP Domains for JavaScript Debugging

#### 1. **Debugger Domain**
- **Purpose**: Core JavaScript debugging functionality
- **Key Capabilities**:
  - Breakpoint management (set, enable, disable, resolve locations)
  - Code execution control (pause, resume, step into/over/out)
  - Call stack and scope inspection
  - Expression evaluation in call frames
  - Source code retrieval and modification
  - Async call stack depth control
  - Exception handling and pause-on-exceptions

**Notable Methods**:
- `setBreakpoint()`: Sets breakpoints at specific locations
- `evaluateOnCallFrame()`: Runs expressions in current execution context
- `stepInto()`, `stepOver()`, `stepOut()`: Code stepping controls
- `getScriptSource()`: Retrieves source code for scripts
- `setScriptSource()`: Live script editing
- `pause()`, `resume()`: Execution control
- `setAsyncCallStackDepth()`: Async debugging configuration

#### 2. **Runtime Domain**
- **Purpose**: JavaScript execution and object inspection
- **Key Capabilities**:
  - Remote JavaScript evaluation
  - Object introspection and property access
  - Exception handling
  - Execution context management
  - Custom object formatters (experimental)
  - Deep serialization of JavaScript objects

**Notable Methods**:
- `evaluate()`: Execute JavaScript expressions in specific contexts
- `callFunctionOn()`: Call functions on specific objects
- `getProperties()`: Retrieve object properties
- `compileScript()`: Compile JavaScript expressions
- `addBinding()`: Create global function bindings across execution contexts

#### 3. **Console Domain**
- **Purpose**: Browser console functionality and logging
- **Key Capabilities**:
  - Console message capture
  - Logging and console operations
  - Console API interaction

## Playwright CDP Integration

### CDP Session Creation

Playwright provides CDPSession for raw Chrome DevTools Protocol access:

```python
# Python (Async)
client = await page.context().new_cdp_session(page)

# Python (Sync) 
client = page.context.new_cdp_session(page)
```

### Core API Methods

#### 1. **send(method, **kwargs)**
- Sends CDP protocol methods
- Returns dictionary with response
- Supports all CDP domains and methods

```python
# Enable debugger domain
await client.send("Debugger.enable")

# Set breakpoint
response = await client.send("Debugger.setBreakpointByUrl", {
    "lineNumber": 10,
    "url": "https://example.com/script.js"
})
breakpoint_id = response["breakpointId"]
```

#### 2. **on(event_name, handler)**
- Subscribe to CDP events
- Enables real-time monitoring

```python
def on_paused(params):
    call_frames = params["callFrames"]
    print(f"Paused at: {call_frames[0]['location']}")

client.on("Debugger.paused", on_paused)
```

#### 3. **detach()**
- Disconnects CDP session
- Stops event emissions
- Prevents further messaging

### Practical Implementation Examples

#### 1. **JavaScript Breakpoint Management**

```python
class CDPDebugger:
    def __init__(self, page):
        self.page = page
        self.client = None
        self.breakpoints = {}
    
    async def initialize(self):
        """Initialize CDP session and enable debugging"""
        self.client = await self.page.context().new_cdp_session(self.page)
        await self.client.send("Debugger.enable")
        await self.client.send("Runtime.enable")
        
        # Set up event handlers
        self.client.on("Debugger.paused", self._on_paused)
        self.client.on("Debugger.resumed", self._on_resumed)
    
    async def set_breakpoint(self, url, line_number, condition=None):
        """Set a breakpoint at specified location"""
        params = {
            "lineNumber": line_number,
            "url": url
        }
        if condition:
            params["condition"] = condition
        
        response = await self.client.send("Debugger.setBreakpointByUrl", params)
        breakpoint_id = response["breakpointId"]
        
        self.breakpoints[breakpoint_id] = {
            "url": url,
            "line": line_number,
            "condition": condition
        }
        
        return breakpoint_id
    
    async def remove_breakpoint(self, breakpoint_id):
        """Remove a breakpoint"""
        await self.client.send("Debugger.removeBreakpoint", {
            "breakpointId": breakpoint_id
        })
        self.breakpoints.pop(breakpoint_id, None)
    
    def _on_paused(self, params):
        """Handle debugger pause event"""
        reason = params.get("reason", "unknown")
        call_frames = params.get("callFrames", [])
        
        if call_frames:
            current_frame = call_frames[0]
            location = current_frame["location"]
            print(f"Debugger paused: {reason} at {location['scriptId']}:{location['lineNumber']}")
    
    def _on_resumed(self, params):
        """Handle debugger resume event"""
        print("Debugger resumed execution")
```

#### 2. **Advanced JavaScript Evaluation**

```python
async def evaluate_in_debug_context(client, expression, call_frame_id=None):
    """Evaluate JavaScript in debugging context"""
    if call_frame_id:
        # Evaluate in specific call frame
        response = await client.send("Debugger.evaluateOnCallFrame", {
            "callFrameId": call_frame_id,
            "expression": expression
        })
    else:
        # Evaluate in global context
        response = await client.send("Runtime.evaluate", {
            "expression": expression,
            "includeCommandLineAPI": True
        })
    
    result = response.get("result", {})
    if response.get("exceptionDetails"):
        raise Exception(f"Evaluation error: {response['exceptionDetails']}")
    
    return result.get("value")

async def inspect_object_properties(client, object_id):
    """Get properties of a JavaScript object"""
    response = await client.send("Runtime.getProperties", {
        "objectId": object_id,
        "ownProperties": True
    })
    
    properties = []
    for prop in response.get("result", []):
        properties.append({
            "name": prop["name"],
            "type": prop.get("value", {}).get("type", "unknown"),
            "value": prop.get("value", {}).get("value")
        })
    
    return properties
```

#### 3. **Console Message Monitoring**

```python
async def setup_console_monitoring(client):
    """Set up comprehensive console monitoring"""
    await client.send("Runtime.enable")
    await client.send("Log.enable")
    
    console_messages = []
    
    def handle_console_api(params):
        """Handle Runtime.consoleAPICalled events"""
        console_messages.append({
            "type": params["type"],
            "args": [arg.get("value", str(arg)) for arg in params.get("args", [])],
            "timestamp": params.get("timestamp"),
            "source": "console_api"
        })
    
    def handle_runtime_exception(params):
        """Handle Runtime.exceptionThrown events"""
        exception = params.get("exceptionDetails", {})
        console_messages.append({
            "type": "exception",
            "text": exception.get("text", "Unknown exception"),
            "line": exception.get("lineNumber"),
            "column": exception.get("columnNumber"),
            "url": exception.get("url"),
            "timestamp": params.get("timestamp"),
            "source": "exception"
        })
    
    client.on("Runtime.consoleAPICalled", handle_console_api)
    client.on("Runtime.exceptionThrown", handle_runtime_exception)
    
    return console_messages
```

#### 4. **Network Request Debugging**

```python
async def setup_network_debugging(client):
    """Set up network request monitoring for debugging"""
    await client.send("Network.enable")
    
    network_logs = []
    
    def on_request_will_be_sent(params):
        request = params["request"]
        network_logs.append({
            "type": "request",
            "requestId": params["requestId"],
            "url": request["url"],
            "method": request["method"],
            "headers": request["headers"],
            "timestamp": params["timestamp"]
        })
    
    def on_response_received(params):
        response = params["response"]
        network_logs.append({
            "type": "response",
            "requestId": params["requestId"],
            "status": response["status"],
            "headers": response["headers"],
            "timestamp": params["timestamp"]
        })
    
    client.on("Network.requestWillBeSent", on_request_will_be_sent)
    client.on("Network.responseReceived", on_response_received)
    
    return network_logs
```

## Advanced Debugging Features

### 1. **Source Code Access and Manipulation**

```python
async def get_script_source(client, script_id):
    """Retrieve source code for a script"""
    response = await client.send("Debugger.getScriptSource", {
        "scriptId": script_id
    })
    return response["scriptSource"]

async def modify_script_source(client, script_id, new_source):
    """Live edit script source (hot reload)"""
    try:
        response = await client.send("Debugger.setScriptSource", {
            "scriptId": script_id,
            "scriptSource": new_source
        })
        return response.get("status") == "Ok"
    except Exception as e:
        print(f"Script modification failed: {e}")
        return False
```

### 2. **Variable and Scope Inspection**

```python
async def inspect_call_frame_scopes(client, call_frame_id):
    """Inspect all scopes in a call frame"""
    # Get call frame details
    response = await client.send("Debugger.evaluateOnCallFrame", {
        "callFrameId": call_frame_id,
        "expression": "arguments",
        "generatePreview": True
    })
    
    # This would be expanded to walk through scope chains
    scopes = []
    
    # Example: inspect local variables
    local_vars = await client.send("Debugger.evaluateOnCallFrame", {
        "callFrameId": call_frame_id,
        "expression": "Object.getOwnPropertyNames(this)",
        "returnByValue": True
    })
    
    scopes.append({
        "type": "local",
        "variables": local_vars.get("result", {}).get("value", [])
    })
    
    return scopes
```

### 3. **Performance and Profiling Integration**

```python
async def setup_performance_profiling(client):
    """Set up performance profiling with debugging context"""
    await client.send("Profiler.enable")
    await client.send("Profiler.setSamplingInterval", {"interval": 100})
    
    async def start_cpu_profiling():
        await client.send("Profiler.start")
    
    async def stop_cpu_profiling():
        response = await client.send("Profiler.stop")
        return response["profile"]
    
    return start_cpu_profiling, stop_cpu_profiling
```

## MCPlaywright Integration Strategies

### 1. **CDP Debugging Mixin**

```python
from typing import Dict, Any, Optional, List
from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool

class CDPDebuggerMixin(MCPMixin):
    """Advanced CDP debugging capabilities for MCPlaywright"""
    
    def __init__(self):
        super().__init__()
        self.cdp_sessions = {}  # session_id -> CDPSession
        self.breakpoints = {}   # session_id -> {breakpoint_id: info}
        self.console_logs = {}  # session_id -> [messages]
    
    @mcp_tool(
        name="browser_enable_debugger",
        description="Enable Chrome DevTools debugger with advanced JavaScript debugging capabilities"
    )
    async def enable_debugger(
        self,
        session_id: Optional[str] = None,
        pause_on_exceptions: bool = False,
        pause_on_caught_exceptions: bool = False
    ) -> Dict[str, Any]:
        """Enable CDP debugger for advanced JavaScript debugging"""
        try:
            context = await self._get_session_context(session_id)
            page = await context.get_current_page()
            
            # Create CDP session
            client = await page.context().new_cdp_session(page)
            self.cdp_sessions[context.session_id] = client
            
            # Enable debugging domains
            await client.send("Debugger.enable")
            await client.send("Runtime.enable")
            await client.send("Log.enable")
            
            # Configure exception handling
            if pause_on_exceptions or pause_on_caught_exceptions:
                await client.send("Debugger.setPauseOnExceptions", {
                    "state": "all" if pause_on_exceptions else "uncaught"
                })
            
            # Set up event handlers
            self._setup_debugger_event_handlers(client, context.session_id)
            
            return {
                "success": True,
                "debugger_enabled": True,
                "session_id": context.session_id,
                "pause_on_exceptions": pause_on_exceptions,
                "pause_on_caught_exceptions": pause_on_caught_exceptions
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @mcp_tool(
        name="browser_set_breakpoint",
        description="Set a JavaScript breakpoint at specified location"
    )
    async def set_breakpoint(
        self,
        url: str,
        line_number: int,
        session_id: Optional[str] = None,
        condition: Optional[str] = None,
        column_number: Optional[int] = None
    ) -> Dict[str, Any]:
        """Set a JavaScript breakpoint"""
        try:
            context = await self._get_session_context(session_id)
            client = self.cdp_sessions.get(context.session_id)
            
            if not client:
                return {
                    "success": False,
                    "error": "Debugger not enabled. Call browser_enable_debugger first."
                }
            
            # Set breakpoint
            params = {"lineNumber": line_number, "url": url}
            if condition:
                params["condition"] = condition
            if column_number is not None:
                params["columnNumber"] = column_number
            
            response = await client.send("Debugger.setBreakpointByUrl", params)
            breakpoint_id = response["breakpointId"]
            
            # Store breakpoint info
            if context.session_id not in self.breakpoints:
                self.breakpoints[context.session_id] = {}
            
            self.breakpoints[context.session_id][breakpoint_id] = {
                "url": url,
                "line": line_number,
                "column": column_number,
                "condition": condition,
                "locations": response.get("locations", [])
            }
            
            return {
                "success": True,
                "breakpoint_id": breakpoint_id,
                "url": url,
                "line_number": line_number,
                "condition": condition,
                "locations": response.get("locations", [])
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @mcp_tool(
        name="browser_debug_evaluate",
        description="Evaluate JavaScript expression in current debugging context"
    )
    async def debug_evaluate(
        self,
        expression: str,
        session_id: Optional[str] = None,
        call_frame_id: Optional[str] = None,
        include_command_line_api: bool = True
    ) -> Dict[str, Any]:
        """Evaluate JavaScript in debugging context"""
        try:
            context = await self._get_session_context(session_id)
            client = self.cdp_sessions.get(context.session_id)
            
            if not client:
                return {
                    "success": False,
                    "error": "Debugger not enabled. Call browser_enable_debugger first."
                }
            
            if call_frame_id:
                # Evaluate in specific call frame
                response = await client.send("Debugger.evaluateOnCallFrame", {
                    "callFrameId": call_frame_id,
                    "expression": expression
                })
            else:
                # Evaluate in global context
                response = await client.send("Runtime.evaluate", {
                    "expression": expression,
                    "includeCommandLineAPI": include_command_line_api
                })
            
            if response.get("exceptionDetails"):
                return {
                    "success": False,
                    "error": "Evaluation exception",
                    "exception_details": response["exceptionDetails"]
                }
            
            result = response.get("result", {})
            return {
                "success": True,
                "result": {
                    "type": result.get("type"),
                    "value": result.get("value"),
                    "description": result.get("description"),
                    "object_id": result.get("objectId")
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
```

### 2. **Integration with Existing MCPlaywright Architecture**

The CDP debugging capabilities should integrate with MCPlaywright's existing architecture:

1. **Session Management**: CDP sessions should be managed per browser session
2. **Video Recording**: Debugging actions should integrate with video recording
3. **Request Monitoring**: CDP network monitoring should complement existing request interception
4. **Artifact Storage**: Debug logs, profiles, and breakpoint info should be stored as artifacts

## Limitations and Best Practices

### Limitations

1. **Browser Compatibility**: CDP is primarily supported in Chromium-based browsers
2. **Performance Impact**: Extensive debugging can slow down page execution
3. **Security Restrictions**: Some debugging features may be limited in certain contexts
4. **Detection**: Advanced CDP usage can be detected by anti-automation measures

### Best Practices

1. **Resource Management**: Always detach CDP sessions when done
2. **Error Handling**: Implement comprehensive error handling for CDP operations
3. **Performance**: Use debugging features selectively to minimize performance impact
4. **Security**: Be cautious with script modification and evaluation in production environments

## Implementation Priority for MCPlaywright

### High Priority
1. **Basic Debugger Integration**: Enable/disable debugger, set/remove breakpoints
2. **JavaScript Evaluation**: Enhanced evaluation with debugging context
3. **Console Monitoring**: Comprehensive console message capture
4. **Exception Handling**: Advanced exception tracking and debugging

### Medium Priority
1. **Source Code Access**: Script source retrieval and modification
2. **Variable Inspection**: Call frame and scope inspection
3. **Network Debugging**: Advanced network request debugging
4. **Performance Profiling**: CPU and memory profiling integration

### Low Priority
1. **Advanced Features**: WebAssembly debugging, custom formatters
2. **Live Editing**: Hot reload capabilities
3. **Complex Breakpoints**: Conditional and advanced breakpoint types

## Conclusion

Playwright's CDP integration provides powerful JavaScript debugging capabilities that can significantly enhance MCPlaywright's automation and testing capabilities. The implementation should focus on core debugging features first, with careful consideration for performance, security, and integration with existing MCPlaywright architecture.

The CDP debugger integration will enable MCPlaywright users to:
- Set and manage JavaScript breakpoints
- Evaluate expressions in debugging contexts
- Monitor console messages and exceptions
- Inspect variables and object properties
- Access and potentially modify source code
- Profile application performance

This enhanced debugging capability positions MCPlaywright as a comprehensive browser automation and testing platform suitable for advanced development and debugging workflows.