"""
Message Queue Tools for MCPlaywright

Tools that expose the logging-based message queue system to MCP clients.
"""

import json
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from ..utils.message_queue import (
    get_message_queue, 
    MessagePriority, 
    QueueMessage,
    send_client_message
)


class SendMessageParams(BaseModel):
    """Parameters for sending a message through the queue"""
    content: str = Field(description="Message content to send")
    priority: Optional[str] = Field("normal", description="Message priority: low, normal, high, urgent, critical")
    client_id: Optional[str] = Field(None, description="Target client ID")
    session_id: Optional[str] = Field(None, description="Associated session ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class GetMessagesParams(BaseModel):
    """Parameters for retrieving queue messages"""
    limit: Optional[int] = Field(100, description="Maximum number of messages to return")
    priority_filter: Optional[str] = Field(None, description="Filter by priority: low, normal, high, urgent, critical")


class SubscribeMessagesParams(BaseModel):
    """Parameters for subscribing to queue messages"""
    priority_filter: Optional[str] = Field(None, description="Subscribe only to messages of this priority or higher")


def _priority_from_string(priority_str: str) -> MessagePriority:
    """Convert string priority to MessagePriority enum"""
    priority_map = {
        "low": MessagePriority.LOW,
        "normal": MessagePriority.NORMAL,
        "high": MessagePriority.HIGH,
        "urgent": MessagePriority.URGENT,
        "critical": MessagePriority.CRITICAL
    }
    return priority_map.get(priority_str.lower(), MessagePriority.NORMAL)


def _message_to_dict(message: QueueMessage) -> Dict[str, Any]:
    """Convert QueueMessage to dictionary for JSON serialization"""
    return {
        "content": message.content,
        "priority": message.priority.name.lower(),
        "timestamp": message.timestamp.isoformat(),
        "metadata": message.metadata,
        "source": message.source
    }


async def browser_send_message(params: SendMessageParams) -> Dict[str, Any]:
    """
    Send a message through the logging-based message queue system.
    
    This demonstrates the clever pattern where logging infrastructure becomes a message bus:
    - Logger name "queue" = Message channel
    - Log level = Message priority (overloaded)
    - Log message = Actual content sent to clients
    """
    try:
        priority = _priority_from_string(params.priority or "normal")
        metadata = params.metadata or {}
        
        # Add client and session info to metadata
        if params.client_id:
            metadata['client_id'] = params.client_id
        if params.session_id:
            metadata['session_id'] = params.session_id
        
        # Send message through the queue system
        send_client_message(
            content=params.content,
            priority=priority,
            **metadata
        )
        
        return {
            "status": "message_sent",
            "content": params.content,
            "priority": priority.name.lower(),
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata,
            "queue_system": "logging_based_message_bus"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to send message: {str(e)}",
            "queue_system": "logging_based_message_bus"
        }


async def browser_get_messages(params: GetMessagesParams) -> Dict[str, Any]:
    """
    Retrieve recent messages from the queue history.
    
    Shows how the logging-based message queue maintains message history
    and can be queried for recent communications.
    """
    try:
        queue = get_message_queue()
        messages = queue.get_message_history(limit=params.limit or 100)
        
        # Filter by priority if requested
        if params.priority_filter:
            min_priority = _priority_from_string(params.priority_filter)
            messages = [msg for msg in messages if msg.priority >= min_priority]
        
        message_dicts = [_message_to_dict(msg) for msg in messages]
        
        return {
            "status": "messages_retrieved",
            "count": len(message_dicts),
            "messages": message_dicts,
            "queue_system": "logging_based_message_bus",
            "pattern_explanation": {
                "concept": "Logging infrastructure as message bus",
                "logger_name": "queue (acts as message channel)",
                "log_level": "message_priority (overloaded from DEBUG/INFO/WARNING/ERROR)",
                "log_message": "actual_content_sent_to_clients"
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to retrieve messages: {str(e)}",
            "queue_system": "logging_based_message_bus"
        }


async def browser_subscribe_messages(params: SubscribeMessagesParams) -> Dict[str, Any]:
    """
    Subscribe to real-time messages from the queue system.
    
    Demonstrates the pub/sub capabilities of the logging-based message queue.
    Note: This is a demonstration of the subscription mechanism.
    """
    try:
        queue = get_message_queue()
        
        # Set up priority filter if specified
        priority_filter = None
        if params.priority_filter:
            priority_filter = _priority_from_string(params.priority_filter)
        
        # Create a demonstration callback
        def demo_callback(message: QueueMessage):
            # In a real implementation, this would send to the MCP client
            print(f"[QUEUE] {message.priority.name}: {message.content}")
        
        # Subscribe to messages
        subscription_id = queue.subscribe(demo_callback, priority_filter)
        
        return {
            "status": "subscribed",
            "subscription_id": subscription_id,
            "priority_filter": params.priority_filter,
            "queue_system": "logging_based_message_bus",
            "implementation_note": "In production, messages would be forwarded to MCP client",
            "pattern_benefits": [
                "Zero dependency pub/sub system",
                "Integrates with existing logging infrastructure", 
                "Log levels become message priorities",
                "Built-in message persistence and history",
                "Thread-safe message delivery"
            ]
        }
        
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Failed to subscribe: {str(e)}",
            "queue_system": "logging_based_message_bus"
        }


# Example usage demonstration
async def demo_message_queue_usage():
    """Demonstrate the logging-based message queue system"""
    
    # Send messages of different priorities
    await browser_send_message(SendMessageParams(
        content="Browser navigation started",
        priority="normal",
        session_id="demo_session",
        metadata={"tool": "browser_navigate", "url": "https://example.com"}
    ))
    
    await browser_send_message(SendMessageParams(
        content="Screenshot capture completed successfully",
        priority="low",
        session_id="demo_session", 
        metadata={"tool": "browser_screenshot", "filename": "page_capture.png"}
    ))
    
    await browser_send_message(SendMessageParams(
        content="Network request failed, retrying...",
        priority="high",
        session_id="demo_session",
        metadata={"tool": "browser_request", "url": "https://api.example.com", "retry_count": 1}
    ))
    
    await browser_send_message(SendMessageParams(
        content="Critical: Browser process crashed",
        priority="critical",
        session_id="demo_session",
        metadata={"tool": "browser_monitor", "error_code": "BROWSER_CRASH"}
    ))
    
    # Retrieve message history
    messages_result = await browser_get_messages(GetMessagesParams(limit=10))
    print("Message History:", json.dumps(messages_result, indent=2))
    
    # Subscribe to high priority messages
    subscription_result = await browser_subscribe_messages(
        SubscribeMessagesParams(priority_filter="high")
    )
    print("Subscription:", json.dumps(subscription_result, indent=2))