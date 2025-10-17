"""
MCPlaywright Session Manager

Manages multiple browser contexts and sessions for concurrent MCP clients.
Provides session isolation, lifecycle management, and resource cleanup.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from pathlib import Path

from .context import Context, BrowserConfig, ClientVersion
from .state.devtools_state import get_devtools_state
from .pagination.cursor_manager import get_cursor_manager, shutdown_cursor_manager

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages multiple browser sessions for concurrent MCP clients.
    
    Each MCP client gets an isolated browser context with its own
    session state, video recording, request monitoring, and artifacts.
    
    Features:
    - Session isolation and cleanup
    - Automatic session timeout handling
    - Resource management and monitoring
    - Concurrent session support
    - Cursor cleanup on client disconnection
    
    MCP Client Disconnection Handling:
    When an MCP client disconnects (network failure, app crash, etc.),
    the session manager automatically cleans up all associated resources:
    
    1. DevTools state cleanup
    2. Cursor cleanup (all cursors for the session)
    3. Browser context cleanup
    4. Session state removal
    
    This prevents resource leaks and ensures abandoned cursors don't
    consume memory or storage space indefinitely.
    """
    
    def __init__(
        self,
        artifacts_dir: Optional[Path] = None,
        session_timeout: int = 3600,  # 1 hour default
        max_concurrent_sessions: int = 10
    ):
        self.artifacts_dir = artifacts_dir or Path("./artifacts")
        self.session_timeout = session_timeout
        self.max_concurrent_sessions = max_concurrent_sessions
        
        self.sessions: Dict[str, Context] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
        
        logger.info(f"SessionManager initialized with timeout={session_timeout}s, max_sessions={max_concurrent_sessions}")
    
    async def start(self) -> None:
        """Start the session manager with cleanup task"""
        if self._running:
            return
            
        self._running = True
        
        # Create artifacts directory
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        # Start cursor manager for pagination
        await get_cursor_manager()
        
        # Start periodic cleanup task
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        
        logger.info("SessionManager and cursor manager started")
    
    async def stop(self) -> None:
        """Stop the session manager and clean up all sessions"""
        if not self._running:
            return
            
        self._running = False
        
        # Cancel cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Clean up all active sessions
        await self._cleanup_all_sessions()
        
        # Shutdown cursor manager
        await shutdown_cursor_manager()
        
        logger.info("SessionManager and cursor manager stopped")
    
    async def get_or_create_session(
        self,
        session_id: Optional[str] = None,
        client_version: Optional[ClientVersion] = None,
        config: Optional[BrowserConfig] = None
    ) -> Context:
        """
        Get existing session or create new one.
        
        Args:
            session_id: Optional session ID, generates UUID if not provided
            client_version: MCP client version information
            config: Browser configuration, uses defaults if not provided
        
        Returns:
            Context instance for the session
        """
        # Generate session ID if not provided
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        # Check if session already exists
        if session_id in self.sessions:
            context = self.sessions[session_id]
            context.update_last_activity()
            logger.debug(f"Retrieved existing session: {session_id}")
            return context
        
        # Check session limits
        if len(self.sessions) >= self.max_concurrent_sessions:
            await self._cleanup_expired_sessions()
            
            if len(self.sessions) >= self.max_concurrent_sessions:
                raise RuntimeError(f"Maximum concurrent sessions ({self.max_concurrent_sessions}) reached")
        
        # Create new session
        session_artifacts_dir = self.artifacts_dir / "sessions" / session_id
        session_artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        context = Context(
            session_id=session_id,
            config=config or BrowserConfig(),
            artifacts_dir=session_artifacts_dir
        )
        
        # Set client version if provided
        if client_version:
            context.client_version = client_version
        
        # Initialize the context
        await context.initialize()
        
        # Store session
        self.sessions[session_id] = context
        
        logger.info(f"Created new session: {session_id} (total sessions: {len(self.sessions)})")
        return context
    
    async def get_session(self, session_id: str) -> Optional[Context]:
        """Get existing session by ID"""
        context = self.sessions.get(session_id)
        if context:
            context.update_last_activity()
        return context
    
    async def remove_session(self, session_id: str) -> bool:
        """
        Remove and cleanup a specific session.
        
        Performs comprehensive cleanup when an MCP client disconnects:
        1. DevTools state cleanup
        2. All cursors for the session (prevents cursor leaks)
        3. Browser context cleanup
        4. Session state removal
        
        Args:
            session_id: The session identifier to remove
            
        Returns:
            True if session was successfully removed, False otherwise
        
        Note:
            Even if individual cleanup steps fail, the session will still
            be removed from the active sessions to prevent zombie sessions.
        """
        if session_id not in self.sessions:
            return False
        
        context = self.sessions[session_id]
        
        try:
            # Cleanup DevTools state for this session
            devtools_state = get_devtools_state()
            devtools_state.cleanup_session(session_id)
            
            # Cleanup all cursors for this session
            try:
                cursor_manager = await get_cursor_manager()
                removed_cursors = await cursor_manager.invalidate_session_cursors(session_id)
                if removed_cursors > 0:
                    logger.info(f"Cleaned up {removed_cursors} cursors for session {session_id}")
            except Exception as cursor_error:
                logger.warning(f"Cursor cleanup failed for session {session_id}: {cursor_error}")
            
            # Cleanup browser context
            await context.cleanup()
            del self.sessions[session_id]
            logger.info(f"Removed session: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error removing session {session_id}: {str(e)}")
            # Remove from sessions even if cleanup failed
            # Still cleanup DevTools state and cursors
            try:
                devtools_state = get_devtools_state()
                devtools_state.cleanup_session(session_id)
            except Exception as devtools_error:
                logger.warning(f"DevTools cleanup failed for {session_id}: {devtools_error}")
            
            try:
                cursor_manager = await get_cursor_manager()
                removed_cursors = await cursor_manager.invalidate_session_cursors(session_id)
                if removed_cursors > 0:
                    logger.warning(f"Emergency cleanup: removed {removed_cursors} cursors for session {session_id}")
            except Exception as cursor_error:
                logger.warning(f"Emergency cursor cleanup failed for session {session_id}: {cursor_error}")
            
            del self.sessions[session_id]
            return False
    
    async def list_sessions(self) -> List[Dict[str, Any]]:
        """List all active sessions with their information"""
        sessions_info = []
        
        for session_id, context in self.sessions.items():
            try:
                session_info = context.get_session_info()
                sessions_info.append(session_info)
            except Exception as e:
                logger.warning(f"Error getting info for session {session_id}: {str(e)}")
                sessions_info.append({
                    "session_id": session_id,
                    "error": str(e),
                    "status": "error"
                })
        
        return sessions_info
    
    async def get_session_stats(self) -> Dict[str, Any]:
        """Get session manager statistics"""
        now = datetime.now()
        active_sessions = len(self.sessions)
        
        # Calculate session ages
        session_ages = []
        video_sessions = 0
        monitoring_sessions = 0
        cursor_sessions = 0
        
        for context in self.sessions.values():
            try:
                age = (now - context._created_at).total_seconds()
                session_ages.append(age)
                
                if context._video_config:
                    video_sessions += 1
                
                if context._request_monitoring_enabled:
                    monitoring_sessions += 1
                
                if context._cursor_manager:
                    cursor_sessions += 1
                    
            except Exception as e:
                logger.warning(f"Error calculating stats for session: {str(e)}")
        
        avg_age = sum(session_ages) / len(session_ages) if session_ages else 0
        max_age = max(session_ages) if session_ages else 0
        
        # Get global cursor stats
        cursor_stats = {}
        try:
            cursor_manager = await get_cursor_manager()
            cursor_stats = await cursor_manager.get_global_stats()
        except Exception as e:
            logger.warning(f"Error getting cursor manager stats: {str(e)}")
        
        return {
            "active_sessions": active_sessions,
            "max_concurrent_sessions": self.max_concurrent_sessions,
            "session_timeout": self.session_timeout,
            "video_recording_sessions": video_sessions,
            "request_monitoring_sessions": monitoring_sessions,
            "cursor_pagination_sessions": cursor_sessions,
            "average_session_age": avg_age,
            "oldest_session_age": max_age,
            "artifacts_directory": str(self.artifacts_dir),
            "cursor_stats": cursor_stats
        }
    
    async def _periodic_cleanup(self) -> None:
        """Periodic cleanup task for expired sessions"""
        while self._running:
            try:
                await self._cleanup_expired_sessions()
                # Run cleanup every 5 minutes
                await asyncio.sleep(300)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {str(e)}")
                await asyncio.sleep(60)  # Retry after 1 minute on error
    
    async def _cleanup_expired_sessions(self) -> None:
        """Clean up expired sessions based on timeout"""
        now = datetime.now()
        expired_sessions = []
        
        for session_id, context in self.sessions.items():
            try:
                age = (now - context._last_activity).total_seconds()
                if age > self.session_timeout:
                    expired_sessions.append(session_id)
            except Exception as e:
                logger.warning(f"Error checking session {session_id} age: {str(e)}")
                expired_sessions.append(session_id)  # Remove problematic sessions
        
        # Remove expired sessions
        for session_id in expired_sessions:
            try:
                await self.remove_session(session_id)
                logger.info(f"Cleaned up expired session: {session_id}")
            except Exception as e:
                logger.error(f"Error cleaning up session {session_id}: {str(e)}")
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    async def _cleanup_all_sessions(self) -> None:
        """Clean up all active sessions"""
        session_ids = list(self.sessions.keys())
        
        cleanup_tasks = []
        for session_id in session_ids:
            task = asyncio.create_task(self.remove_session(session_id))
            cleanup_tasks.append(task)
        
        if cleanup_tasks:
            results = await asyncio.gather(*cleanup_tasks, return_exceptions=True)
            
            success_count = sum(1 for result in results if result is True)
            logger.info(f"Cleaned up {success_count}/{len(cleanup_tasks)} sessions during shutdown")
    
    async def force_cleanup_session(self, session_id: str) -> bool:
        """Force cleanup a session even if it's unresponsive"""
        if session_id not in self.sessions:
            return False
        
        try:
            # Try normal cleanup first
            return await self.remove_session(session_id)
        except Exception as e:
            logger.warning(f"Normal cleanup failed for {session_id}, forcing removal: {str(e)}")
            
            # Force removal from sessions dict
            if session_id in self.sessions:
                del self.sessions[session_id]
            
            return True
    
    def __len__(self) -> int:
        """Return number of active sessions"""
        return len(self.sessions)
    
    def __contains__(self, session_id: str) -> bool:
        """Check if session exists"""
        return session_id in self.sessions
    
    def __repr__(self) -> str:
        return f"SessionManager(active_sessions={len(self.sessions)}, max_sessions={self.max_concurrent_sessions})"


# Global session manager instance
_session_manager: Optional[SessionManager] = None

def get_session_manager() -> SessionManager:
    """Get the global session manager instance"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager

async def initialize_session_manager(**kwargs) -> SessionManager:
    """Initialize and start the global session manager"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager(**kwargs)
    
    await _session_manager.start()
    return _session_manager

async def cleanup_session_manager() -> None:
    """Clean up the global session manager"""
    global _session_manager
    if _session_manager:
        await _session_manager.stop()
        _session_manager = None