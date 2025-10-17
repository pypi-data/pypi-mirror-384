# MCPlaywright Architecture Documentation

## Overview

MCPlaywright is a comprehensive Python Playwright MCP server that provides advanced browser automation capabilities. This document details the architecture, novel features, and implementation decisions that differentiate it from standard Playwright usage.

## Core Architecture Components

### 1. Context Management System

**Source Reference**: `/home/rpm/claude/playwright-mcp/src/context.ts` (TypeScript original)
**Python Implementation**: `src/mcplaywright/context.py`

The Context class is the heart of the system, managing persistent browser sessions across multiple MCP tool calls:

```python
class Context:
    """Manages browser contexts, video recording, and session state"""
    
    # Browser lifecycle management
    _browser_context_promise: Optional[BrowserContext] = None
    _browser_context_factory: BrowserContextFactory
    _tabs: List[Tab] = []
    _current_tab: Optional[Tab] = None
    
    # Video recording state
    _video_recording_config: Optional[VideoConfig] = None
    _video_base_filename: Optional[str] = None
    _active_pages_with_videos: Set[Page] = set()
    _video_recording_paused: bool = False
    _video_recording_mode: VideoMode = VideoMode.SMART
    
    # HTTP monitoring state
    _request_interceptor: Optional[RequestInterceptor] = None
    
    # Session persistence
    session_id: str
    client_version: Optional[ClientVersion] = None
```

**Key Differences from Standard Playwright:**
- **Persistent Sessions**: Browser contexts survive across multiple MCP calls
- **State Management**: Video recording, request monitoring states maintained
- **Session Isolation**: Each MCP client gets isolated browser context
- **Resource Cleanup**: Automatic cleanup on session termination

### 2. Smart Video Recording System

**Source Reference**: `/home/rpm/claude/playwright-mcp/src/tools/video.ts`
**Python Implementation**: `src/mcplaywright/tools/video.py`

#### Recording Modes

```python
class VideoMode(Enum):
    CONTINUOUS = "continuous"  # Record everything including waits
    SMART = "smart"           # Auto-pause during waits, resume on actions
    ACTION_ONLY = "action-only"  # Only record during active interactions
    SEGMENT = "segment"       # Separate video files per action sequence
```

#### Auto-Viewport Matching

**Novel Feature**: Automatically matches browser viewport to video recording size to eliminate gray borders:

```python
@app.tool()
async def browser_start_recording(
    size: Optional[VideoSize] = None,
    filename: Optional[str] = None,
    auto_set_viewport: bool = True
) -> VideoRecordingResult:
    """Start video recording with intelligent viewport matching"""
    
    video_size = size or VideoSize(width=1280, height=720)
    
    # Automatically set viewport to match video size
    if auto_set_viewport:
        await context.update_browser_config({
            'viewport': {
                'width': video_size.width,
                'height': video_size.height
            }
        })
```

#### Action-Aware Recording

**Novel Feature**: Integrates with all browser tools to provide smart pause/resume:

```python
# In browser interaction tools
async def begin_video_action(self, action_name: str) -> None:
    """Called before browser actions to resume recording"""
    if self._video_recording_mode == VideoMode.SMART and self._video_recording_paused:
        await self.resume_video_recording()

async def end_video_action(self, action_name: str) -> None:
    """Called after browser actions to pause if in smart mode"""
    if self._video_recording_mode == VideoMode.SMART:
        await self.pause_video_recording()
```

### 3. Advanced HTTP Request Monitoring

**Source Reference**: `/home/rpm/claude/playwright-mcp/src/requestInterceptor.ts`
**Python Implementation**: `src/mcplaywright/request_interceptor.py`

#### Comprehensive Request Capture

```python
@dataclass
class InterceptedRequest:
    """Comprehensive request/response capture"""
    id: str
    timestamp: datetime
    url: str
    method: str
    headers: Dict[str, str]
    resource_type: str
    post_data: Optional[str] = None
    start_time: float = 0
    
    # Response data
    response: Optional[ResponseData] = None
    failed: bool = False
    failure: Optional[Dict] = None
    duration: Optional[float] = None
```

#### Advanced Filtering and Analysis

**Novel Feature**: Rich filtering capabilities beyond basic Playwright network events:

```python
class RequestFilter:
    """Advanced request filtering"""
    url_pattern: Optional[str] = None
    method: Optional[str] = None
    status_code: Optional[int] = None
    min_duration: Optional[float] = None
    max_duration: Optional[float] = None
    resource_types: Optional[List[str]] = None
    failed_only: bool = False
    
async def get_filtered_requests(
    filter_config: RequestFilter,
    max_results: int = 100
) -> List[InterceptedRequest]:
    """Apply complex filtering to captured requests"""
```

#### Export Capabilities

**Novel Feature**: Multiple export formats with rich data analysis:

```python
class ExportFormat(Enum):
    JSON = "json"      # Full structured data
    HAR = "har"        # HTTP Archive format
    CSV = "csv"        # Spreadsheet compatible
    SUMMARY = "summary"  # Human-readable report

async def export_requests(
    format_type: ExportFormat,
    filter_config: Optional[RequestFilter] = None
) -> ExportResult:
    """Export captured requests with pandas analysis"""
    
    if format_type == ExportFormat.CSV:
        df = pd.DataFrame([req.dict() for req in filtered_requests])
        return df.to_csv()
    elif format_type == ExportFormat.SUMMARY:
        return generate_performance_report(filtered_requests)
```

### 4. Browser UI Customization System

**Source Reference**: `/home/rpm/claude/playwright-mcp/src/tools/configure.ts`
**Python Implementation**: `src/mcplaywright/tools/configure.py`

#### Visual Demonstration Mode

**Novel Feature**: slowMo integration for training videos and demos:

```python
@app.tool()
async def browser_configure(
    headless: Optional[bool] = None,
    slow_mo: Optional[int] = None,  # Milliseconds between actions
    devtools: Optional[bool] = None,
    args: Optional[List[str]] = None,
    chromium_sandbox: Optional[bool] = None
) -> ConfigurationResult:
    """Configure browser with UI customization"""
    
    # Apply slowMo for visual demonstrations
    if slow_mo is not None:
        launch_options.update({'slow_mo': slow_mo})
    
    # Custom browser arguments for themes
    if args:
        existing_args = launch_options.get('args', [])
        # Merge without duplicates
        launch_options['args'] = list(set(existing_args + args))
```

#### Theme Customization Examples

```python
# Dark mode browser for visual differentiation
DARK_MODE_ARGS = [
    "--force-dark-mode",
    "--enable-features=WebUIDarkMode",
    "--start-maximized"
]

# Demo recording optimized
DEMO_ARGS = [
    "--force-color-profile=srgb",
    "--disable-web-security",
    "--disable-extensions"
]

# Container deployment safe
CONTAINER_ARGS = [
    "--no-sandbox",
    "--disable-setuid-sandbox", 
    "--disable-dev-shm-usage"
]
```

### 5. Session-Based Artifact Management

**Source Reference**: `/home/rpm/claude/playwright-mcp/src/artifactManager.ts`
**Python Implementation**: `src/mcplaywright/artifact_manager.py`

#### Centralized Storage

**Novel Feature**: Session-based artifact organization:

```python
class ArtifactManager:
    """Centralized artifact storage and organization"""
    
    def __init__(self, session_id: str, base_dir: Path):
        self.session_id = session_id
        self.session_dir = base_dir / "sessions" / session_id
        self.create_directories()
    
    def create_directories(self):
        """Create organized directory structure"""
        directories = [
            "videos", "screenshots", "pdfs", 
            "requests", "exports", "logs"
        ]
        for dir_name in directories:
            (self.session_dir / dir_name).mkdir(parents=True, exist_ok=True)
    
    def get_subdirectory(self, artifact_type: str) -> Path:
        """Get organized storage path"""
        return self.session_dir / artifact_type
```

## MCP Integration Patterns

### 1. Tool Definition Pattern

**FastMCP vs TypeScript Interface:**

```python
# Python FastMCP - Clean decorator syntax
@app.tool()
async def browser_navigate(url: str) -> Dict[str, Any]:
    """Navigate to URL with validation and state management"""
    context = await get_browser_context()
    page = await context.get_current_page()
    
    # Begin video action if recording
    await context.begin_video_action("navigate")
    
    try:
        await page.goto(url)
        return {"success": True, "url": url}
    finally:
        # End video action
        await context.end_video_action("navigate")

# TypeScript Original - Interface definition
const navigate = defineTool({
  capability: 'core',
  schema: {
    name: 'browser_navigate',
    description: 'Navigate to URL',
    inputSchema: z.object({
      url: z.string().url(),
    }),
  },
  handle: async (context, params, response) => {
    // Implementation
  }
});
```

### 2. State Management Pattern

**Session Persistence Across MCP Calls:**

```python
class MCPSessionManager:
    """Manages persistent browser sessions across MCP calls"""
    
    def __init__(self):
        self.sessions: Dict[str, Context] = {}
    
    async def get_or_create_session(self, session_id: str) -> Context:
        """Get existing session or create new one"""
        if session_id not in self.sessions:
            self.sessions[session_id] = Context(
                session_id=session_id,
                config=self.config
            )
        return self.sessions[session_id]
    
    async def cleanup_session(self, session_id: str):
        """Clean up session resources"""
        if session_id in self.sessions:
            await self.sessions[session_id].cleanup()
            del self.sessions[session_id]
```

### 3. Error Handling Pattern

**MCP-Specific Error Management:**

```python
from fastmcp.exceptions import MCPError

async def safe_browser_operation(operation: Callable) -> Dict[str, Any]:
    """Wrap browser operations with MCP error handling"""
    try:
        result = await operation()
        return {"success": True, "data": result}
    except playwright.TimeoutError as e:
        raise MCPError(
            code="BROWSER_TIMEOUT",
            message=f"Browser operation timed out: {str(e)}",
            data={"timeout": True, "recoverable": True}
        )
    except playwright.Error as e:
        raise MCPError(
            code="BROWSER_ERROR", 
            message=f"Browser error: {str(e)}",
            data={"browser_error": True, "recoverable": False}
        )
```

## Testing Architecture

### 1. MCP Testing Framework

**Custom FastMCP Test Fixtures:**

```python
# tests/conftest.py
import pytest
from fastmcp.testing import MCPTestClient

@pytest.fixture
async def mcp_client():
    """Create MCP test client with browser context"""
    client = MCPTestClient(app)
    await client.initialize()
    
    # Set up test browser context
    await client.call_tool("browser_configure", {
        "headless": True,
        "args": ["--no-sandbox"]  # CI/CD friendly
    })
    
    yield client
    
    # Cleanup
    await client.call_tool("browser_close")
    await client.cleanup()

@pytest.fixture
async def video_recording_context(mcp_client):
    """Set up video recording for tests"""
    await mcp_client.call_tool("browser_start_recording", {
        "filename": "test-recording",
        "auto_set_viewport": True
    })
    
    yield mcp_client
    
    videos = await mcp_client.call_tool("browser_stop_recording")
    return videos
```

### 2. Feature-Specific Test Suites

**Video Recording Tests:**
```python
# tests/test_video_recording.py
@pytest.mark.asyncio
async def test_smart_recording_auto_pause(mcp_client):
    """Test smart recording automatically pauses during waits"""
    
    # Start smart recording
    await mcp_client.call_tool("browser_start_recording")
    await mcp_client.call_tool("browser_set_recording_mode", {"mode": "smart"})
    
    # Navigate (should record)
    await mcp_client.call_tool("browser_navigate", {"url": "https://example.com"})
    
    # Wait (should auto-pause)
    await mcp_client.call_tool("browser_wait_for", {"time": 2})
    
    # Click (should auto-resume)
    await mcp_client.call_tool("browser_click", {
        "element": "button", 
        "ref": "button-ref"
    })
    
    # Verify recording behavior
    recording_info = await mcp_client.call_tool("browser_recording_status")
    assert recording_info["mode"] == "smart"
    assert "pause_count" in recording_info
```

### 3. Performance Benchmarking

**TypeScript vs Python Comparison:**
```python
# tests/performance/test_benchmarks.py
@pytest.mark.benchmark
async def test_navigation_performance(mcp_client, benchmark):
    """Benchmark navigation performance vs TypeScript"""
    
    async def navigate_and_screenshot():
        await mcp_client.call_tool("browser_navigate", {"url": "https://example.com"})
        await mcp_client.call_tool("browser_take_screenshot")
    
    result = await benchmark.pedantic(navigate_and_screenshot, rounds=10)
    
    # Compare against TypeScript baseline
    assert result.stats.mean < TYPESCRIPT_BASELINE_MEAN * 1.2  # Within 20%
```

## Production Deployment Architecture

### 1. Container Configuration

**Multi-stage Docker with Performance Optimization:**
```dockerfile
FROM python:3.13-slim as base
WORKDIR /app

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget gnupg2 && \
    rm -rf /var/lib/apt/lists/*

FROM base as dev
# Development with hot-reload and debugging
COPY pyproject.toml .
RUN pip install uv && uv sync --dev
RUN playwright install chromium firefox webkit
CMD ["uv", "run", "python", "scripts/dev_server.py"]

FROM base as prod
# Production optimized
COPY . .
RUN pip install uv && uv sync --no-dev
RUN playwright install chromium --with-deps
USER 1000:1000
CMD ["uv", "run", "python", "-m", "mcplaywright.server"]
```

### 2. FastMCP Production Features

**Advanced Server Configuration:**
```python
from fastmcp import FastMCP
from fastmcp.middleware import auth, rate_limit, logging

app = FastMCP("MCPlaywright", version="0.1.0")

# Production middleware
app.add_middleware(
    auth.TokenAuthMiddleware(
        token_validator=validate_api_token
    )
)
app.add_middleware(
    rate_limit.RateLimitMiddleware(
        requests_per_minute=60,
        burst_size=10
    )
)
app.add_middleware(
    logging.RequestLoggingMiddleware(
        log_level="INFO",
        include_bodies=False  # Security
    )
)

# Health checks
@app.tool()
async def health_check() -> Dict[str, Any]:
    """System health check for monitoring"""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "active_sessions": len(session_manager.sessions),
        "uptime": get_uptime(),
        "memory_usage": get_memory_usage()
    }
```

This architecture provides a robust, production-ready browser automation system with advanced features that go well beyond standard Playwright usage, optimized for MCP workflows and enhanced with Python-specific capabilities.