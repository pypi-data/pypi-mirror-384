"""
Logging-Based Message Queue System for MCPlaywright

A clever pattern that uses Python's logging infrastructure as a message bus:
- Logger name "queue" = Message channel/topic
- Log level = Message priority (overloaded from traditional DEBUG/INFO/WARNING/ERROR)
- Log message = Actual message content sent to clients

This provides a zero-dependency pub/sub system that integrates with existing logging.
"""

import logging
import json
from typing import Any, Dict, Optional, Callable, List
from datetime import datetime
from threading import Lock
from collections import defaultdict, deque
import asyncio
from dataclasses import dataclass
from enum import IntEnum


class MessagePriority(IntEnum):
    """Message priorities using log levels as priority system"""
    LOW = logging.DEBUG      # 10 - Low priority background updates
    NORMAL = logging.INFO    # 20 - Normal operational messages
    HIGH = logging.WARNING   # 30 - Important notifications
    URGENT = logging.ERROR   # 40 - Urgent messages requiring attention
    CRITICAL = logging.CRITICAL  # 50 - Critical system messages


@dataclass
class QueueMessage:
    """Structured message for the queue system"""
    content: str
    priority: MessagePriority
    timestamp: datetime
    metadata: Dict[str, Any]
    source: str


class MessageQueueHandler(logging.Handler):
    """Custom logging handler that captures messages for the queue system"""
    
    def __init__(self, queue_manager: 'MessageQueueManager'):
        super().__init__()
        self.queue_manager = queue_manager
        self._lock = Lock()
    
    def emit(self, record: logging.LogRecord) -> None:
        """Process log records as queue messages"""
        try:
            with self._lock:
                # Only process messages from the "queue" logger
                if record.name != "queue":
                    return
                
                # Extract message data
                content = record.getMessage()
                priority = MessagePriority(record.levelno)
                
                # Parse metadata from record
                metadata = {}
                if hasattr(record, 'client_id'):
                    metadata['client_id'] = record.client_id
                if hasattr(record, 'session_id'):
                    metadata['session_id'] = record.session_id
                if hasattr(record, 'tool_name'):
                    metadata['tool_name'] = record.tool_name
                
                message = QueueMessage(
                    content=content,
                    priority=priority,
                    timestamp=datetime.fromtimestamp(record.created),
                    metadata=metadata,
                    source=record.name
                )
                
                # Deliver message to subscribers
                self.queue_manager._deliver_message(message)
                
        except Exception as e:
            # Don't let logging errors break the application
            print(f"MessageQueueHandler error: {e}")


class MessageQueueManager:
    """Manages the logging-based message queue system"""
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._message_history: deque = deque(maxlen=1000)  # Keep last 1000 messages
        self._lock = Lock()
        self._logger = None
        self._handler = None
        self._setup_complete = False
    
    def setup_queue_logger(self) -> None:
        """Initialize the queue logger system"""
        if self._setup_complete:
            return
        
        # Create the special "queue" logger
        self._logger = logging.getLogger("queue")
        self._logger.setLevel(logging.DEBUG)  # Accept all priority levels
        
        # Add our custom handler
        self._handler = MessageQueueHandler(self)
        self._logger.addHandler(self._handler)
        
        # Prevent propagation to avoid duplicate logging
        self._logger.propagate = False
        
        self._setup_complete = True
    
    def subscribe(self, callback: Callable[[QueueMessage], None], 
                  priority_filter: Optional[MessagePriority] = None) -> str:
        """Subscribe to queue messages with optional priority filtering"""
        with self._lock:
            subscriber_id = f"sub_{id(callback)}_{datetime.now().microsecond}"
            
            def filtered_callback(message: QueueMessage):
                if priority_filter is None or message.priority >= priority_filter:
                    callback(message)
            
            self._subscribers[subscriber_id] = filtered_callback
            return subscriber_id
    
    def unsubscribe(self, subscriber_id: str) -> bool:
        """Unsubscribe from queue messages"""
        with self._lock:
            return self._subscribers.pop(subscriber_id, None) is not None
    
    def _deliver_message(self, message: QueueMessage) -> None:
        """Internal method to deliver messages to all subscribers"""
        with self._lock:
            # Store in history
            self._message_history.append(message)
            
            # Deliver to all subscribers
            for subscriber_callback in self._subscribers.values():
                try:
                    subscriber_callback(message)
                except Exception as e:
                    print(f"Subscriber error: {e}")
    
    def send_message(self, content: str, priority: MessagePriority = MessagePriority.NORMAL,
                     **metadata) -> None:
        """Send a message through the queue system"""
        if not self._setup_complete:
            self.setup_queue_logger()
        
        # Use logging with custom metadata
        extra = {key: value for key, value in metadata.items() if key != 'content'}
        self._logger.log(priority.value, content, extra=extra)
    
    def get_message_history(self, limit: int = 100) -> List[QueueMessage]:
        """Get recent message history"""
        with self._lock:
            return list(self._message_history)[-limit:]
    
    def clear_history(self) -> None:
        """Clear message history"""
        with self._lock:
            self._message_history.clear()


# Global instance
_message_queue_manager = MessageQueueManager()


def get_message_queue() -> MessageQueueManager:
    """Get the global message queue manager"""
    return _message_queue_manager


def send_client_message(content: str, priority: MessagePriority = MessagePriority.NORMAL,
                       client_id: Optional[str] = None, 
                       session_id: Optional[str] = None,
                       tool_name: Optional[str] = None) -> None:
    """Convenience function to send messages to clients"""
    queue = get_message_queue()
    queue.send_message(
        content=content,
        priority=priority,
        client_id=client_id,
        session_id=session_id,
        tool_name=tool_name
    )


# Convenience functions for different priority levels
def send_low_priority(content: str, **metadata):
    """Send low priority message (background updates)"""
    send_client_message(content, MessagePriority.LOW, **metadata)


def send_normal(content: str, **metadata):
    """Send normal priority message (operational updates)"""
    send_client_message(content, MessagePriority.NORMAL, **metadata)


def send_high_priority(content: str, **metadata):
    """Send high priority message (important notifications)"""
    send_client_message(content, MessagePriority.HIGH, **metadata)


def send_urgent(content: str, **metadata):
    """Send urgent message (requires attention)"""
    send_client_message(content, MessagePriority.URGENT, **metadata)


def send_critical(content: str, **metadata):
    """Send critical message (system alerts)"""
    send_client_message(content, MessagePriority.CRITICAL, **metadata)


# Example usage patterns
def example_usage():
    """Example usage of the message queue system"""
    
    # Setup the queue
    queue = get_message_queue()
    queue.setup_queue_logger()
    
    # Subscribe to messages
    def handle_message(message: QueueMessage):
        print(f"[{message.priority.name}] {message.content}")
        if message.metadata:
            print(f"  Metadata: {message.metadata}")
    
    # Subscribe to all messages
    sub_id = queue.subscribe(handle_message)
    
    # Subscribe only to high priority messages
    high_priority_sub = queue.subscribe(
        lambda msg: print(f"HIGH PRIORITY: {msg.content}"),
        priority_filter=MessagePriority.HIGH
    )
    
    # Send messages using convenience functions
    send_normal("Browser navigation completed", 
                client_id="client123", tool_name="browser_navigate")
    
    send_high_priority("Screenshot capture failed, retrying...", 
                       session_id="session456", tool_name="browser_screenshot")
    
    send_critical("System memory usage critical", 
                  client_id="monitoring", tool_name="system_monitor")
    
    # Clean up
    queue.unsubscribe(sub_id)
    queue.unsubscribe(high_priority_sub)


if __name__ == "__main__":
    example_usage()