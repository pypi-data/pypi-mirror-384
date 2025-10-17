# Logging-Based Message Queue System

## Overview

MCPlaywright implements an innovative **logging-as-message-bus** pattern where Python's built-in logging infrastructure becomes a zero-dependency pub/sub message queue system. This clever architectural approach provides real-time client communication without external message brokers.

## Core Concept

The pattern overloads standard logging components for message passing:

- **Logger name "queue"** = Message channel/topic identifier
- **Log level** = Message priority (overloaded from traditional DEBUG/INFO/WARNING/ERROR)
- **Log message** = Actual message content sent to clients
- **Log record extras** = Metadata (client_id, session_id, tool_name, etc.)

## Implementation Architecture

### Message Priority Mapping

```python
class MessagePriority(IntEnum):
    """Message priorities using log levels as priority system"""
    LOW = logging.DEBUG      # 10 - Low priority background updates
    NORMAL = logging.INFO    # 20 - Normal operational messages  
    HIGH = logging.WARNING   # 30 - Important notifications
    URGENT = logging.ERROR   # 40 - Urgent messages requiring attention
    CRITICAL = logging.CRITICAL  # 50 - Critical system messages
```

### Core Components

#### 1. MessageQueueHandler
Custom logging handler that intercepts messages from the "queue" logger and converts them to structured messages for the pub/sub system.

#### 2. MessageQueueManager
Central coordinator that manages:
- Message subscribers with priority filtering
- Message history (last 1000 messages)
- Thread-safe message delivery
- Logger setup and teardown

#### 3. QueueMessage Structure
```python
@dataclass
class QueueMessage:
    content: str                    # Message content
    priority: MessagePriority       # Message priority level
    timestamp: datetime            # When message was sent
    metadata: Dict[str, Any]       # Additional context data
    source: str                    # Source logger name ("queue")
```

## Usage Examples

### Basic Message Sending

```python
from mcplaywright.utils.message_queue import send_normal, send_high_priority

# Send operational updates
send_normal("Browser navigation completed", 
           client_id="client123", tool_name="browser_navigate")

# Send important notifications
send_high_priority("Screenshot capture failed, retrying...", 
                  session_id="session456", tool_name="browser_screenshot")
```

### Priority-Based Messaging

```python
from mcplaywright.utils.message_queue import (
    send_low_priority,    # Background updates
    send_normal,          # Standard operations
    send_high_priority,   # Important notifications
    send_urgent,          # Requires attention
    send_critical         # System alerts
)

# Different priority levels
send_low_priority("Background task completed")
send_urgent("Network request failed, retrying...")
send_critical("System memory usage critical")
```

### Subscription and Real-time Updates

```python
from mcplaywright.utils.message_queue import get_message_queue, MessagePriority

queue = get_message_queue()

# Subscribe to all messages
def handle_all_messages(message):
    print(f"[{message.priority.name}] {message.content}")

sub_id = queue.subscribe(handle_all_messages)

# Subscribe only to high priority messages
def handle_urgent_only(message):
    print(f"URGENT: {message.content}")

urgent_sub = queue.subscribe(handle_urgent_only, 
                           priority_filter=MessagePriority.HIGH)
```

### Message History Retrieval

```python
queue = get_message_queue()

# Get recent messages
recent_messages = queue.get_message_history(limit=50)

for message in recent_messages:
    print(f"[{message.timestamp}] {message.content}")
    if message.metadata:
        print(f"  Context: {message.metadata}")
```

## MCP Tool Integration

MCPlaywright exposes the message queue system through three MCP tools:

### 1. send_client_message
```python
# Send messages through MCP
await send_client_message({
    "content": "Processing your request...",
    "priority": "normal",
    "client_id": "web_client_123",
    "metadata": {"step": 1, "total": 5}
})
```

### 2. get_queue_messages
```python
# Retrieve message history
messages = await get_queue_messages({
    "limit": 100,
    "priority_filter": "high"  # Only high priority and above
})
```

### 3. subscribe_to_messages
```python
# Set up real-time subscriptions
subscription = await subscribe_to_messages({
    "priority_filter": "urgent"  # Only urgent and critical messages
})
```

## Technical Benefits

### 1. Zero Dependencies
- Uses Python's built-in logging infrastructure
- No external message brokers (Redis, RabbitMQ, etc.)
- Minimal memory footprint
- Thread-safe by design

### 2. Seamless Integration
- Works with existing logging configuration
- Compatible with log rotation, filtering, and formatting
- Integrates with logging frameworks (structlog, loguru, etc.)
- Preserves standard logging functionality

### 3. Built-in Features
- Message persistence through logging handlers
- Priority-based filtering
- Structured metadata support
- Automatic timestamping
- Thread-safe message delivery

### 4. Development Benefits
- Familiar logging API for developers
- Easy debugging through standard log files
- Configurable via logging.conf files
- Works in both sync and async environments

## Real-World Use Cases

### Browser Automation Progress Updates
```python
# During long-running automation tasks
send_normal("Starting browser automation sequence", 
           session_id=session_id, tool_name="browser_navigate")

send_low_priority("Loading page assets...", 
                 session_id=session_id, progress=25)

send_normal("Page fully loaded, taking screenshot", 
           session_id=session_id, progress=75)

send_normal("Automation completed successfully", 
           session_id=session_id, progress=100)
```

### Error Handling and Recovery
```python
try:
    await browser_action()
except NetworkError as e:
    send_high_priority(f"Network error occurred: {e}", 
                      session_id=session_id, 
                      error_type="NetworkError",
                      retry_attempt=1)
    
    # Retry logic...
    send_normal("Retry successful after network error", 
               session_id=session_id,
               recovery=True)
```

### System Monitoring
```python
# Resource monitoring
if memory_usage > 0.9:
    send_urgent("High memory usage detected",
               memory_usage=memory_usage,
               tool_name="system_monitor")

if cpu_usage > 0.95:
    send_critical("Critical CPU usage - may affect performance",
                 cpu_usage=cpu_usage,
                 tool_name="system_monitor")
```

## Architecture Advantages

### Compared to Traditional Message Queues

| Feature | Logging Queue | Redis/RabbitMQ |
|---------|--------------|----------------|
| Dependencies | None (built-in) | External service |
| Setup complexity | Minimal | Complex |
| Memory usage | Low | High |
| Persistence | Log files | Requires config |
| Development | Familiar API | New concepts |
| Thread safety | Built-in | Requires care |
| Debugging | Standard logs | Separate tools |

### Pattern Innovation

This implementation represents a novel approach to message passing that:

1. **Repurposes existing infrastructure** - Logging is already present in every Python application
2. **Overloads semantic meaning** - Log levels become message priorities naturally  
3. **Maintains compatibility** - Standard logging still works alongside message passing
4. **Provides immediate value** - Zero setup time, instant message passing capability

## Integration with MCPlaywright

The message queue system is deeply integrated into MCPlaywright's architecture:

- **Session Management**: Messages include session context automatically
- **Tool Execution**: Each tool can send progress updates and status messages  
- **Error Handling**: Exceptions automatically generate appropriate priority messages
- **Browser Events**: Page navigation, screenshots, and interactions send status updates
- **Performance Monitoring**: Resource usage and timing information flows through the queue

## Future Enhancements

### Potential Extensions

1. **Message Routing**: Route messages to specific clients based on metadata
2. **Persistent Storage**: Store messages in database for long-term history
3. **WebSocket Integration**: Real-time browser client updates via WebSocket
4. **Message Filtering**: Advanced filtering with regex patterns and conditions
5. **Rate Limiting**: Prevent message flooding with configurable rate limits
6. **Message Clustering**: Group related messages for better UX

### Advanced Patterns

1. **Request-Response**: Correlate responses with original requests using correlation IDs
2. **Event Sourcing**: Use messages as events to reconstruct application state  
3. **Saga Pattern**: Coordinate complex workflows through message orchestration
4. **Dead Letter Queue**: Handle failed message delivery gracefully

## Conclusion

The logging-based message queue system in MCPlaywright demonstrates how creative architectural thinking can provide powerful functionality using existing infrastructure. By overloading the semantic meaning of log levels and leveraging Python's robust logging system, we achieve a zero-dependency pub/sub system that integrates seamlessly with browser automation workflows.

This pattern could be extracted and applied to other systems where lightweight, dependency-free message passing is needed, making it a valuable architectural contribution beyond just MCPlaywright.