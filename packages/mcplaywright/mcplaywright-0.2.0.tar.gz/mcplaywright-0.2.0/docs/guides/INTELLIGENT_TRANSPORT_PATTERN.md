# Intelligent Transport Selection Pattern

## Overview

The Intelligent Transport Selection pattern is a novel FastMCP architectural pattern that automatically detects the intended transport mode (stdio vs HTTP) based on command-line arguments, eliminating the need for explicit transport flags while maintaining an intuitive user experience.

## Problem Statement

Traditional MCP servers often require users to explicitly specify transport mode:

```bash
# Confusing: explicit transport flags
myserver --transport stdio
myserver --transport http --port 8001

# Or separate commands
myserver-stdio
myserver-http --port 8001
```

This creates several issues:
- **Cognitive Overhead**: Users must remember transport-specific flags
- **Port Conflicts**: HTTP servers may bind to ports by default
- **Poor UX**: Non-intuitive command-line interface
- **Documentation Complexity**: Multiple usage patterns to explain

## Solution: Intelligent Transport Selection

Auto-detect transport mode based on user intent expressed through command-line arguments.

### Core Logic

```python
def main():
    """Server with intelligent transport selection"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MCP Server")
    parser.add_argument("--host", default="127.0.0.1", 
                       help="Host to bind to (enables HTTP transport)")
    parser.add_argument("--port", type=int, 
                       help="Port to bind to (enables HTTP transport)")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    # Auto-detect transport mode
    use_http = args.port is not None
    if not use_http and args.host != "127.0.0.1":
        # Host specified but no port, assume HTTP with default port
        use_http = True
        args.port = 8000
    
    if use_http:
        # HTTP transport when network options specified
        logger.info(f"Starting server via HTTP on {args.host}:{args.port}")
        import uvicorn
        uvicorn.run(app, host=args.host, port=args.port)
    else:
        # Default stdio transport for MCP
        logger.info("Starting server via stdio transport")
        app.run()
```

### Decision Matrix

| Command | Transport | Reasoning |
|---------|-----------|-----------|
| `myserver` | stdio | No network args = MCP standard |
| `myserver --port 8001` | HTTP | Port specified = HTTP intent |
| `myserver --host 0.0.0.0` | HTTP | Host specified = HTTP intent |
| `myserver --host 0.0.0.0 --port 8001` | HTTP | Both specified = HTTP intent |
| `myserver --log-level DEBUG` | stdio | Only logging arg = MCP standard |

## Implementation Details

### Complete Implementation

```python
def main():
    """Main entry point with intelligent transport selection"""
    import argparse
    import signal
    import logging
    
    parser = argparse.ArgumentParser(description="MCPlaywright MCP Server")
    parser.add_argument("--host", default="127.0.0.1", 
                       help="Host to bind to (enables HTTP transport)")
    parser.add_argument("--port", type=int, 
                       help="Port to bind to (enables HTTP transport)")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.getLogger().setLevel(getattr(logging, args.log_level.upper()))
    
    # Auto-detect transport mode
    use_http = args.port is not None
    if not use_http and args.host != "127.0.0.1":
        # Host specified without port, assume HTTP with default
        use_http = True
        args.port = 8000
    
    # Setup cleanup handlers
    def cleanup_handler(signum, frame):
        logger.info("Shutdown signal received, cleaning up...")
        # Cleanup logic here
        sys.exit(0)
    
    signal.signal(signal.SIGINT, cleanup_handler)
    signal.signal(signal.SIGTERM, cleanup_handler)
    
    try:
        if use_http:
            # HTTP transport
            logger.info(f"Starting server via HTTP on {args.host}:{args.port}")
            logger.info(f"Log level: {args.log_level}")
            import uvicorn
            uvicorn.run(
                app,
                host=args.host,
                port=args.port,
                log_level=args.log_level.lower()
            )
        else:
            # stdio transport (MCP standard)
            logger.info("Starting server via stdio transport")
            logger.info(f"Log level: {args.log_level}")
            app.run()
            
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        sys.exit(1)
```

### Script Configuration

Align script names with project names for simplicity:

```toml
# pyproject.toml
[project.scripts]
myproject = "myproject.server:main"        # Clean, matches project name
myproject-server = "myproject.server:main" # Backward compatibility

[project.entry-points."fastmcp.servers"]
myproject = "myproject.server:app"
```

## User Experience

### Intuitive Command Patterns

```bash
# Default: stdio transport (MCP standard)
uvx myproject

# Logging configuration still uses stdio
uvx myproject --log-level DEBUG

# HTTP automatically enabled when port specified
uvx myproject --port 8001

# HTTP with custom host
uvx myproject --host 0.0.0.0 --port 8000

# HTTP with just host (default port 8000)
uvx myproject --host 0.0.0.0
```

### Claude Code Integration

```bash
# Clean MCP integration
claude mcp add myproject -- myproject

# With environment variables
claude mcp add myproject --env LOG_LEVEL=DEBUG -- myproject

# Local development
claude mcp add myproject -- uv run python -m myproject.server
```

### Help Output

```
usage: myproject [-h] [--host HOST] [--port PORT] [--log-level LOG_LEVEL]

MyProject MCP Server

options:
  -h, --help            show this help message and exit
  --host HOST           Host to bind to (enables HTTP transport)
  --port PORT           Port to bind to (enables HTTP transport)  
  --log-level LOG_LEVEL Logging level
```

The help text clearly indicates that `--host` and `--port` enable HTTP transport.

## Benefits

### 1. **Intuitive User Experience**
- Natural command-line interface
- Port specified = HTTP transport (obvious intent)
- No transport flags to remember

### 2. **MCP Standards Compliance**
- Defaults to stdio transport without arguments
- Follows MCP best practices
- No port conflicts with default behavior

### 3. **Reduced Cognitive Load**
- Single command with intelligent behavior
- Clear intent mapping (network args = HTTP)
- Consistent with user expectations

### 4. **Error Prevention**
```bash
# ❌ Old way: port conflicts
myserver             # Binds to 8000 by default - conflict!

# ✅ New way: no conflicts  
myserver             # stdio - no port binding
myserver --port 8001 # HTTP only when intended
```

### 5. **Documentation Simplicity**
- Single usage pattern to document
- Clear decision logic
- Fewer edge cases to explain

## Testing Strategy

### Test Transport Detection

```python
def test_transport_detection():
    """Test intelligent transport selection logic"""
    import argparse
    from unittest.mock import Mock
    
    # Test stdio (default)
    sys.argv = ['server']
    args = parser.parse_args()
    assert not should_use_http(args)
    
    # Test HTTP with port
    sys.argv = ['server', '--port', '8001'] 
    args = parser.parse_args()
    assert should_use_http(args)
    
    # Test HTTP with host
    sys.argv = ['server', '--host', '0.0.0.0']
    args = parser.parse_args() 
    assert should_use_http(args)

def test_command_line_scenarios():
    """Test various command-line scenarios"""
    test_cases = [
        (['server'], 'stdio'),
        (['server', '--log-level', 'DEBUG'], 'stdio'),
        (['server', '--port', '8001'], 'http'),
        (['server', '--host', '0.0.0.0'], 'http'),
        (['server', '--host', '0.0.0.0', '--port', '8001'], 'http'),
    ]
    
    for args, expected_transport in test_cases:
        with mock_argv(args):
            actual = detect_transport()
            assert actual == expected_transport
```

### Integration Testing

```python
def test_server_startup_modes():
    """Test server starts correctly in both modes"""
    
    # Test stdio startup
    with mock_argv(['server']):
        with patch('app.run') as mock_run:
            main()
            mock_run.assert_called_once()
    
    # Test HTTP startup  
    with mock_argv(['server', '--port', '8001']):
        with patch('uvicorn.run') as mock_uvicorn:
            main()
            mock_uvicorn.assert_called_once_with(
                app, host='127.0.0.1', port=8001, log_level='info'
            )
```

## Error Handling

### Common Scenarios

```python
def main():
    try:
        if use_http:
            # HTTP transport
            uvicorn.run(app, host=args.host, port=args.port)
        else:
            # stdio transport
            app.run()
            
    except OSError as e:
        if "Address already in use" in str(e):
            logger.error(f"Port {args.port} is already in use. Try a different port:")
            logger.error(f"  {sys.argv[0]} --port {args.port + 1}")
            sys.exit(1)
        raise
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        sys.exit(1)
```

### Helpful Error Messages

When HTTP mode fails, provide actionable guidance:

```python
except OSError as e:
    if use_http and "permission denied" in str(e).lower():
        logger.error(f"Permission denied binding to {args.host}:{args.port}")
        logger.error("Try:")
        logger.error(f"  {sys.argv[0]} --port {1024 + random.randint(1000, 8000)}")
        logger.error("  Or run with sudo (not recommended)")
    else:
        logger.error(f"Network error: {e}")
```

## Production Considerations

### Container Deployment

```dockerfile
# Default stdio for container orchestration
CMD ["myproject"]

# HTTP mode for load balancer scenarios
CMD ["myproject", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Detection

```python
def detect_container_environment():
    """Auto-detect if running in container"""
    return (
        os.path.exists('/.dockerenv') or 
        os.environ.get('KUBERNETES_SERVICE_HOST') or
        os.environ.get('CONTAINER') == 'true'
    )

def main():
    # ... argument parsing ...
    
    # Container-aware defaults
    if detect_container_environment() and not use_http:
        logger.info("Container environment detected")
        if args.host == "127.0.0.1":
            logger.info("Consider using --host 0.0.0.0 for container networking")
```

### Health Checks

```python
def main():
    if use_http:
        # Add health check endpoint for HTTP mode
        @app.get("/health")
        async def health_check():
            return {"status": "healthy", "transport": "http"}
        
        logger.info(f"Health check available at http://{args.host}:{args.port}/health")
```

## Comparison with Other Patterns

### Traditional Approach

```bash
# Multiple commands or complex flags
myserver-stdio
myserver-http --port 8001
# or
myserver --transport stdio
myserver --transport http --port 8001
```

**Issues:**
- Multiple entry points to maintain
- Cognitive overhead for users
- Complex documentation
- Easy to bind ports accidentally

### Intelligent Transport Selection

```bash  
# Single command, intelligent behavior
myserver             # stdio (safe default)
myserver --port 8001 # HTTP (clear intent)
```

**Benefits:**
- Single entry point
- Intuitive command interface
- Safe defaults
- Clear intent mapping

## Real-World Example: MCPlaywright

MCPlaywright implements this pattern:

```python
# mcplaywright/server.py
def main():
    parser = argparse.ArgumentParser(description="MCPlaywright MCP Server")
    parser.add_argument("--host", default="127.0.0.1", 
                       help="Host to bind to (enables HTTP transport)")
    parser.add_argument("--port", type=int, 
                       help="Port to bind to (enables HTTP transport)")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    # Auto-detect transport
    use_http = args.port is not None
    if not use_http and args.host != "127.0.0.1":
        use_http = True
        args.port = 8000
    
    if use_http:
        logger.info(f"Starting MCPlaywright server via HTTP on {args.host}:{args.port}")
        import uvicorn
        uvicorn.run(app, host=args.host, port=args.port, log_level=args.log_level.lower())
    else:
        logger.info("Starting MCPlaywright server via stdio transport")
        app.run()
```

**Usage:**
```bash
# pyproject.toml
[project.scripts]
mcplaywright = "mcplaywright.server:main"

# Users run:
uvx mcplaywright                    # stdio
uvx mcplaywright --port 8001       # HTTP
claude mcp add mcplaywright -- mcplaywright  # MCP integration
```

## Adoption Guidelines

### For New Projects

1. **Implement from Start**: Easier than retrofitting
2. **Document Decision Logic**: Help output should explain transport selection
3. **Test Both Modes**: Ensure both stdio and HTTP work correctly
4. **Consider Defaults**: Always default to stdio for MCP compliance

### For Existing Projects

1. **Backward Compatibility**: Keep existing flags working
2. **Migration Path**: Provide migration guide for users
3. **Gradual Rollout**: Update documentation progressively
4. **Deprecation**: Gradually phase out explicit transport flags

## Conclusion

The Intelligent Transport Selection pattern represents a significant improvement in MCP server usability. By automatically detecting user intent through command-line arguments, it eliminates cognitive overhead while maintaining standards compliance and preventing common errors.

**Key Success Factors:**
- ✅ Intuitive mapping (port specified = HTTP)
- ✅ Safe defaults (stdio without arguments)  
- ✅ Clear documentation (help explains behavior)
- ✅ Error prevention (no accidental port binding)
- ✅ Standards compliance (MCP stdio by default)

This pattern should become standard practice for all FastMCP server implementations, providing users with a cleaner, more intuitive experience while maintaining the flexibility needed for debugging and development scenarios.