"""
DevTools State Management for MCPlaywright

Manages per-session DevTools enablement state with thread-safe operations.
"""

import logging
import threading
from typing import Set, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class DevToolsState:
    """
    Thread-safe state management for DevTools enablement per session.
    
    This class tracks which sessions have DevTools enabled and provides
    the core state logic for dynamic tool visibility.
    """
    
    def __init__(self):
        self._enabled_sessions: Set[str] = set()
        self._session_metadata: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        logger.info("DevTools state manager initialized")
    
    def enable_for_session(self, session_id: str) -> None:
        """
        Enable DevTools for a specific session.
        
        Args:
            session_id: Unique session identifier
        """
        with self._lock:
            self._enabled_sessions.add(session_id)
            self._session_metadata[session_id] = {
                "enabled_at": datetime.now().isoformat(),
                "tools_accessed": set()
            }
            logger.info(f"DevTools enabled for session: {session_id}")
    
    def disable_for_session(self, session_id: str) -> None:
        """
        Disable DevTools for a specific session.
        
        Args:
            session_id: Unique session identifier
        """
        with self._lock:
            self._enabled_sessions.discard(session_id)
            if session_id in self._session_metadata:
                metadata = self._session_metadata.pop(session_id)
                logger.info(f"DevTools disabled for session: {session_id}, "
                          f"tools accessed: {len(metadata.get('tools_accessed', set()))}")
            else:
                logger.info(f"DevTools disabled for session: {session_id}")
    
    def is_enabled_for_session(self, session_id: str) -> bool:
        """
        Check if DevTools is enabled for a specific session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            True if DevTools is enabled for this session
        """
        with self._lock:
            return session_id in self._enabled_sessions
    
    def track_tool_access(self, session_id: str, tool_name: str) -> None:
        """
        Track which DevTools tools have been accessed by a session.
        
        Args:
            session_id: Unique session identifier
            tool_name: Name of the DevTools tool that was accessed
        """
        with self._lock:
            if session_id in self._session_metadata:
                self._session_metadata[session_id]["tools_accessed"].add(tool_name)
    
    def get_enabled_sessions(self) -> Set[str]:
        """
        Get all sessions that currently have DevTools enabled.
        
        Returns:
            Set of session IDs with DevTools enabled
        """
        with self._lock:
            return self._enabled_sessions.copy()
    
    def get_session_metadata(self, session_id: str) -> Dict[str, Any]:
        """
        Get metadata for a specific session's DevTools usage.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Dictionary containing session metadata or empty dict if not found
        """
        with self._lock:
            return self._session_metadata.get(session_id, {}).copy()
    
    def cleanup_session(self, session_id: str) -> None:
        """
        Clean up DevTools state for a session that's being closed.
        
        Args:
            session_id: Unique session identifier
        """
        with self._lock:
            was_enabled = session_id in self._enabled_sessions
            self._enabled_sessions.discard(session_id)
            metadata = self._session_metadata.pop(session_id, {})
            
            if was_enabled:
                logger.info(f"DevTools state cleaned up for session: {session_id}, "
                          f"tools accessed: {len(metadata.get('tools_accessed', set()))}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get overall DevTools usage statistics.
        
        Returns:
            Dictionary with usage statistics
        """
        with self._lock:
            total_sessions = len(self._session_metadata)
            active_sessions = len(self._enabled_sessions)
            
            all_tools_accessed = set()
            for metadata in self._session_metadata.values():
                all_tools_accessed.update(metadata.get("tools_accessed", set()))
            
            return {
                "total_sessions_with_devtools": total_sessions,
                "currently_active_sessions": active_sessions,
                "unique_tools_ever_accessed": len(all_tools_accessed),
                "tools_accessed": list(all_tools_accessed)
            }


# Global instance for the MCPlaywright server
_devtools_state = DevToolsState()


def get_devtools_state() -> DevToolsState:
    """
    Get the global DevTools state instance.
    
    Returns:
        Global DevTools state manager
    """
    return _devtools_state