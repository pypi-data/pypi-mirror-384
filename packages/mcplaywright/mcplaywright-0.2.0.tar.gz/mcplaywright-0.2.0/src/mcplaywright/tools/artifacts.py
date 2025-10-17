"""
Advanced Artifacts Management System

Comprehensive artifact storage and management with session-based organization,
tool call logging, statistics tracking, and cleanup automation.

Features:
- Session-based artifact organization
- Tool call logging and tracking
- Comprehensive statistics and analytics
- Automated cleanup and retention policies
- Multi-format artifact support (screenshots, videos, PDFs, JSON, etc.)
- Advanced search and filtering capabilities
"""

import json
import logging
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Literal, Union
from pydantic import BaseModel, Field
from dataclasses import dataclass, asdict
from enum import Enum

from ..context import Context
from ..filters.decorators import filter_response

logger = logging.getLogger(__name__)

class ArtifactType(str, Enum):
    """Supported artifact types"""
    SCREENSHOT = "screenshot"
    VIDEO = "video" 
    PDF = "pdf"
    JSON = "json"
    CSV = "csv"
    HAR = "har"
    LOG = "log"
    REPORT = "report"
    CUSTOM = "custom"

class ArtifactStatus(str, Enum):
    """Artifact processing status"""
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"
    PROCESSING = "processing"

@dataclass
class ArtifactEntry:
    """Individual artifact entry with metadata"""
    timestamp: str
    tool_name: str
    artifact_type: ArtifactType
    status: ArtifactStatus
    file_path: Optional[str] = None
    file_size: int = 0
    parameters: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

class ArtifactManager:
    """
    Advanced artifact manager with session-based organization and comprehensive tracking.
    
    Manages centralized artifact storage with:
    - Session-specific directories
    - Tool call logging with detailed metadata
    - Automatic file organization by type
    - Statistics and analytics
    - Cleanup and retention policies
    """
    
    def __init__(self, base_dir: str, session_id: str):
        self.base_dir = Path(base_dir)
        self.session_id = session_id
        self.session_dir = self.base_dir / self._sanitize_filename(session_id)
        self.log_file = self.session_dir / "tool-calls.json"
        self.metadata_file = self.session_dir / "session-metadata.json"
        
        self.entries: List[ArtifactEntry] = []
        self.session_metadata: Dict[str, Any] = {}
        
        # Initialize session directory and load existing data
        self._ensure_session_directory()
        self._load_existing_log()
        self._load_session_metadata()
        
        logger.debug(f"Artifact manager initialized for session {session_id} in {self.session_dir}")
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe filesystem usage"""
        # Replace invalid characters with underscores
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename[:255]  # Limit length
    
    def _ensure_session_directory(self) -> None:
        """Ensure session directory and subdirectories exist"""
        try:
            self.session_dir.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories for different artifact types
            for artifact_type in ArtifactType:
                subdir = self.session_dir / artifact_type.value
                subdir.mkdir(exist_ok=True)
                
        except Exception as e:
            raise RuntimeError(f"Failed to create session directory {self.session_dir}: {e}")
    
    def _load_existing_log(self) -> None:
        """Load existing artifact log if it exists"""
        try:
            if self.log_file.exists():
                with open(self.log_file, 'r') as f:
                    data = json.load(f)
                    self.entries = [
                        ArtifactEntry(**entry) for entry in data
                    ]
                logger.debug(f"Loaded {len(self.entries)} existing artifact entries")
        except Exception as e:
            logger.warning(f"Failed to load existing artifact log: {e}")
            self.entries = []
    
    def _load_session_metadata(self) -> None:
        """Load session metadata if it exists"""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    self.session_metadata = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load session metadata: {e}")
            self.session_metadata = {
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }
    
    def _save_log(self) -> None:
        """Save artifact log to disk"""
        try:
            with open(self.log_file, 'w') as f:
                json.dump([entry.to_dict() for entry in self.entries], f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save artifact log: {e}")
    
    def _save_metadata(self) -> None:
        """Save session metadata to disk"""
        try:
            self.session_metadata["last_updated"] = datetime.now().isoformat()
            with open(self.metadata_file, 'w') as f:
                json.dump(self.session_metadata, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save session metadata: {e}")
    
    def get_session_dir(self) -> Path:
        """Get the session directory path"""
        return self.session_dir
    
    def get_base_directory(self) -> Path:
        """Get the base artifacts directory"""
        return self.base_dir
    
    def get_subdirectory(self, artifact_type: ArtifactType) -> Path:
        """Get or create subdirectory for specific artifact type"""
        subdir = self.session_dir / artifact_type.value
        subdir.mkdir(exist_ok=True)
        return subdir
    
    def get_artifact_path(self, filename: str, artifact_type: ArtifactType) -> Path:
        """Get full path for an artifact file"""
        subdir = self.get_subdirectory(artifact_type)
        return subdir / self._sanitize_filename(filename)
    
    def log_artifact(
        self,
        tool_name: str,
        artifact_type: ArtifactType,
        status: ArtifactStatus,
        file_path: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ArtifactEntry:
        """Log an artifact creation or operation"""
        
        # Calculate file size if file exists
        file_size = 0
        if file_path and Path(file_path).exists():
            file_size = Path(file_path).stat().st_size
            # Make path relative to session directory for storage
            file_path = str(Path(file_path).relative_to(self.session_dir))
        
        entry = ArtifactEntry(
            timestamp=datetime.now().isoformat(),
            tool_name=tool_name,
            artifact_type=artifact_type,
            status=status,
            file_path=file_path,
            file_size=file_size,
            parameters=parameters,
            error_message=error_message,
            tags=tags or [],
            metadata=metadata
        )
        
        self.entries.append(entry)
        self._save_log()
        self._save_metadata()
        
        logger.debug(f"Logged artifact: {tool_name} -> {artifact_type.value} ({status.value})")
        return entry
    
    def get_artifacts(
        self,
        artifact_type: Optional[ArtifactType] = None,
        status: Optional[ArtifactStatus] = None,
        tool_name: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[ArtifactEntry]:
        """Get artifacts with optional filtering"""
        filtered = self.entries
        
        if artifact_type:
            filtered = [e for e in filtered if e.artifact_type == artifact_type]
        
        if status:
            filtered = [e for e in filtered if e.status == status]
        
        if tool_name:
            filtered = [e for e in filtered if e.tool_name == tool_name]
        
        # Sort by timestamp (newest first)
        filtered.sort(key=lambda x: x.timestamp, reverse=True)
        
        if limit:
            filtered = filtered[:limit]
        
        return filtered
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get comprehensive session statistics"""
        total_artifacts = len(self.entries)
        success_count = len([e for e in self.entries if e.status == ArtifactStatus.SUCCESS])
        error_count = len([e for e in self.entries if e.status == ArtifactStatus.ERROR])
        
        # Calculate total file size
        total_size = sum(e.file_size for e in self.entries if e.file_size)
        
        # Count by artifact type
        type_counts = {}
        for artifact_type in ArtifactType:
            count = len([e for e in self.entries if e.artifact_type == artifact_type])
            if count > 0:
                type_counts[artifact_type.value] = count
        
        # Count by tool
        tool_counts = {}
        for entry in self.entries:
            tool_counts[entry.tool_name] = tool_counts.get(entry.tool_name, 0) + 1
        
        return {
            "session_id": self.session_id,
            "session_dir": str(self.session_dir),
            "total_artifacts": total_artifacts,
            "success_count": success_count,
            "error_count": error_count,
            "success_rate": (success_count / total_artifacts * 100) if total_artifacts > 0 else 0,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "artifact_types": type_counts,
            "tool_usage": tool_counts,
            "created_at": self.session_metadata.get("created_at"),
            "last_updated": self.session_metadata.get("last_updated")
        }
    
    def cleanup_old_artifacts(self, days: int = 30) -> Dict[str, Any]:
        """Clean up artifacts older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        removed_files = []
        removed_entries = []
        total_size_freed = 0
        
        for entry in self.entries[:]:  # Copy list to avoid modification during iteration
            entry_date = datetime.fromisoformat(entry.timestamp.replace('Z', '+00:00').replace('+00:00', ''))
            
            if entry_date < cutoff_date:
                # Remove file if it exists
                if entry.file_path:
                    full_path = self.session_dir / entry.file_path
                    if full_path.exists():
                        size = full_path.stat().st_size
                        full_path.unlink()
                        removed_files.append(str(full_path))
                        total_size_freed += size
                
                removed_entries.append(entry.to_dict())
                self.entries.remove(entry)
        
        # Save updated log
        if removed_entries:
            self._save_log()
            self._save_metadata()
        
        return {
            "cleaned_artifacts": len(removed_entries),
            "removed_files": removed_files,
            "size_freed_bytes": total_size_freed,
            "size_freed_mb": round(total_size_freed / (1024 * 1024), 2),
            "cutoff_date": cutoff_date.isoformat()
        }
    
    def export_session_data(self, include_metadata: bool = True) -> Dict[str, Any]:
        """Export complete session data for backup or analysis"""
        data = {
            "session_id": self.session_id,
            "session_dir": str(self.session_dir),
            "artifacts": [entry.to_dict() for entry in self.entries],
            "statistics": self.get_session_stats(),
            "exported_at": datetime.now().isoformat()
        }
        
        if include_metadata:
            data["metadata"] = self.session_metadata
        
        return data

class ArtifactManagerRegistry:
    """
    Global registry for managing artifact managers across sessions.
    
    Provides centralized access to session-specific artifact managers
    and global statistics across all sessions.
    """
    
    _instance: Optional['ArtifactManagerRegistry'] = None
    
    def __init__(self):
        self._managers: Dict[str, ArtifactManager] = {}
        self._base_dir: Optional[Path] = None
    
    @classmethod
    def get_instance(cls) -> 'ArtifactManagerRegistry':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def set_base_dir(self, base_dir: str) -> None:
        """Set base directory for all artifact storage"""
        self._base_dir = Path(base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Artifact registry base directory set to: {self._base_dir}")
    
    def get_manager(self, session_id: str) -> Optional[ArtifactManager]:
        """Get or create artifact manager for a session"""
        if not self._base_dir:
            return None  # Artifact storage not configured
        
        if session_id not in self._managers:
            self._managers[session_id] = ArtifactManager(str(self._base_dir), session_id)
        
        return self._managers[session_id]
    
    def remove_manager(self, session_id: str) -> bool:
        """Remove session's artifact manager"""
        if session_id in self._managers:
            del self._managers[session_id]
            return True
        return False
    
    def get_all_managers(self) -> Dict[str, ArtifactManager]:
        """Get all active session managers"""
        return self._managers.copy()
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Get summary statistics across all sessions"""
        managers = list(self._managers.values())
        
        total_artifacts = sum(len(m.entries) for m in managers)
        total_success = sum(len([e for e in m.entries if e.status == ArtifactStatus.SUCCESS]) for m in managers)
        total_size = sum(sum(e.file_size for e in m.entries if e.file_size) for m in managers)
        
        # Aggregate artifact types across all sessions
        global_type_counts = {}
        for manager in managers:
            for entry in manager.entries:
                type_name = entry.artifact_type.value
                global_type_counts[type_name] = global_type_counts.get(type_name, 0) + 1
        
        return {
            "base_dir": str(self._base_dir) if self._base_dir else None,
            "active_sessions": len(self._managers),
            "total_artifacts": total_artifacts,
            "total_success": total_success,
            "success_rate": (total_success / total_artifacts * 100) if total_artifacts > 0 else 0,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "artifact_types": global_type_counts
        }
    
    def cleanup_all_sessions(self, days: int = 30) -> Dict[str, Any]:
        """Clean up old artifacts across all sessions"""
        cleanup_results = {}
        total_cleaned = 0
        total_size_freed = 0
        
        for session_id, manager in self._managers.items():
            result = manager.cleanup_old_artifacts(days)
            cleanup_results[session_id] = result
            total_cleaned += result["cleaned_artifacts"]
            total_size_freed += result["size_freed_bytes"]
        
        return {
            "sessions_processed": len(cleanup_results),
            "total_artifacts_cleaned": total_cleaned,
            "total_size_freed_bytes": total_size_freed,
            "total_size_freed_mb": round(total_size_freed / (1024 * 1024), 2),
            "session_results": cleanup_results
        }

# Global registry instance
artifact_registry = ArtifactManagerRegistry.get_instance()

# Parameter models for tools
class GetArtifactPathsParams(BaseModel):
    """Parameters for getting artifact paths"""
    show_files: bool = Field(default=True, description="Show file listings in directories")
    show_stats: bool = Field(default=True, description="Show session statistics")

class ListArtifactsParams(BaseModel):
    """Parameters for listing artifacts with ripgrep filtering"""
    artifact_type: Optional[ArtifactType] = Field(default=None, description="Filter by artifact type")
    status: Optional[ArtifactStatus] = Field(default=None, description="Filter by status")
    tool_name: Optional[str] = Field(default=None, description="Filter by tool name")
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum number of artifacts to return")
    
    # Universal ripgrep filtering parameters
    filter_pattern: Optional[str] = Field(None, description="Ripgrep pattern to search for (supports regex)")
    filter_fields: Optional[List[str]] = Field(None, description="Fields to search: filename, tool_name, artifact_type, metadata, parameters")
    filter_mode: Optional[str] = Field("content", description="Filter mode: content, files, count")
    case_sensitive: Optional[bool] = Field(False, description="Case sensitive pattern matching")
    whole_words: Optional[bool] = Field(False, description="Match whole words only")
    context_lines: Optional[int] = Field(None, description="Context lines before/after matches")
    invert_match: Optional[bool] = Field(False, description="Invert match (show non-matching)")
    max_matches: Optional[int] = Field(None, description="Maximum matches to return")

class GetArtifactStatsParams(BaseModel):
    """Parameters for getting artifact statistics"""
    include_global: bool = Field(default=True, description="Include global statistics across all sessions")
    include_breakdown: bool = Field(default=True, description="Include detailed breakdown by type and tool")

class CleanupArtifactsParams(BaseModel):
    """Parameters for cleaning up old artifacts"""
    days: int = Field(default=30, ge=1, le=365, description="Remove artifacts older than this many days")
    session_only: bool = Field(default=True, description="Clean only current session (false for all sessions)")
    dry_run: bool = Field(default=False, description="Show what would be deleted without actually deleting")

# Tool implementations
async def browser_get_artifact_paths(context: Context, params: GetArtifactPathsParams) -> Dict[str, Any]:
    """Get artifact storage paths and directory information"""
    manager = artifact_registry.get_manager(context.session_id)
    
    if not manager:
        return {
            "status": "no_artifact_storage",
            "message": "Artifact storage not configured for this session",
            "base_dir": None,
            "session_dir": None
        }
    
    base_dir = manager.get_base_directory()
    session_dir = manager.get_session_dir()
    
    result = {
        "status": "artifact_paths_retrieved",
        "session_id": context.session_id,
        "base_directory": str(base_dir),
        "session_directory": str(session_dir),
        "subdirectories": {}
    }
    
    # Check subdirectories for each artifact type
    for artifact_type in ArtifactType:
        subdir = manager.get_subdirectory(artifact_type)
        exists = subdir.exists()
        
        subdir_info = {
            "path": str(subdir),
            "exists": exists,
            "file_count": 0,
            "total_size_bytes": 0
        }
        
        if exists and params.show_files:
            try:
                files = list(subdir.iterdir())
                subdir_info["file_count"] = len([f for f in files if f.is_file()])
                subdir_info["total_size_bytes"] = sum(f.stat().st_size for f in files if f.is_file())
                
                if len(files) > 0:
                    recent_files = sorted([f for f in files if f.is_file()], 
                                        key=lambda x: x.stat().st_mtime, reverse=True)[:3]
                    subdir_info["recent_files"] = [f.name for f in recent_files]
                    
            except Exception as e:
                subdir_info["error"] = str(e)
        
        result["subdirectories"][artifact_type.value] = subdir_info
    
    if params.show_stats:
        result["session_stats"] = manager.get_session_stats()
    
    return result

@filter_response(
    filterable_fields=["filename", "tool_name", "artifact_type", "status", "timestamp", "file_path", "file_size", "metadata", "parameters"],
    content_fields=["filename", "metadata", "parameters"],
    default_fields=["filename", "tool_name", "artifact_type"],
    supports_streaming=True,
    max_response_size=200
)
async def browser_list_artifacts(context: Context, params: ListArtifactsParams) -> Dict[str, Any]:
    """
    List artifacts with advanced ripgrep filtering capabilities.
    
    Retrieves artifacts from the current session with powerful filtering
    options including regex pattern matching across filenames, metadata,
    and tool parameters.
    
    Features:
    - **Ripgrep filtering** with regex patterns across artifact data
    - Filter by artifact type (screenshot, video, PDF, JSON, etc.)
    - Filter by processing status (success, error, pending)
    - Filter by tool name that created the artifact
    - **Streaming support** for large artifact collections
    - Comprehensive metadata search
    
    Filtering Examples:
    - `filter_pattern: "screenshot.*login"` - Find login-related screenshots
    - `filter_pattern: "error|failed"` - Find artifacts with error conditions
    - `filter_fields: ["filename", "metadata"]` - Search specific fields
    - `artifact_type: "video"` - Filter to video artifacts only
    """
    manager = artifact_registry.get_manager(context.session_id)
    
    if not manager:
        return {
            "status": "no_artifact_storage",
            "artifacts": [],
            "total_count": 0
        }
    
    artifacts = manager.get_artifacts(
        artifact_type=params.artifact_type,
        status=params.status,
        tool_name=params.tool_name,
        limit=params.limit
    )
    
    artifact_list = []
    for entry in artifacts:
        artifact_data = entry.to_dict()
        
        # Add computed fields
        if entry.file_path:
            full_path = manager.get_session_dir() / entry.file_path
            artifact_data["absolute_path"] = str(full_path)
            artifact_data["file_exists"] = full_path.exists()
            
            if full_path.exists():
                stat = full_path.stat()
                artifact_data["file_size_mb"] = round(stat.st_size / (1024 * 1024), 2)
                artifact_data["modified_at"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
        
        artifact_list.append(artifact_data)
    
    return {
        "status": "artifacts_listed",
        "session_id": context.session_id,
        "artifacts": artifact_list,
        "total_count": len(artifacts),
        "filters_applied": {
            "artifact_type": params.artifact_type.value if params.artifact_type else None,
            "status": params.status.value if params.status else None,
            "tool_name": params.tool_name,
            "limit": params.limit
        }
    }

async def browser_get_artifact_stats(context: Context, params: GetArtifactStatsParams) -> Dict[str, Any]:
    """Get comprehensive artifact statistics"""
    manager = artifact_registry.get_manager(context.session_id)
    
    if not manager:
        return {
            "status": "no_artifact_storage",
            "session_stats": None,
            "global_stats": None
        }
    
    result = {
        "status": "stats_retrieved",
        "session_stats": manager.get_session_stats()
    }
    
    if params.include_global:
        result["global_stats"] = artifact_registry.get_global_stats()
    
    if params.include_breakdown:
        # Detailed breakdown by time periods
        now = datetime.now()
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(weeks=1)
        month_ago = now - timedelta(days=30)
        
        recent_stats = {
            "last_24h": 0,
            "last_7d": 0,
            "last_30d": 0,
            "older": 0
        }
        
        for entry in manager.entries:
            entry_date = datetime.fromisoformat(entry.timestamp.replace('Z', '+00:00').replace('+00:00', ''))
            
            if entry_date >= day_ago:
                recent_stats["last_24h"] += 1
            elif entry_date >= week_ago:
                recent_stats["last_7d"] += 1
            elif entry_date >= month_ago:
                recent_stats["last_30d"] += 1
            else:
                recent_stats["older"] += 1
        
        result["time_breakdown"] = recent_stats
    
    return result

async def browser_cleanup_artifacts(context: Context, params: CleanupArtifactsParams) -> Dict[str, Any]:
    """Clean up old artifacts"""
    if params.session_only:
        manager = artifact_registry.get_manager(context.session_id)
        
        if not manager:
            return {
                "status": "no_artifact_storage",
                "cleaned_artifacts": 0
            }
        
        if params.dry_run:
            # Simulate cleanup without actually deleting
            cutoff_date = datetime.now() - timedelta(days=params.days)
            would_remove = []
            
            for entry in manager.entries:
                entry_date = datetime.fromisoformat(entry.timestamp.replace('Z', '+00:00').replace('+00:00', ''))
                if entry_date < cutoff_date:
                    would_remove.append(entry.to_dict())
            
            return {
                "status": "dry_run_completed",
                "would_remove_count": len(would_remove),
                "would_remove_artifacts": would_remove,
                "cutoff_date": cutoff_date.isoformat()
            }
        else:
            result = manager.cleanup_old_artifacts(params.days)
            result["status"] = "cleanup_completed"
            return result
    
    else:
        # Clean up all sessions
        if params.dry_run:
            return {
                "status": "error",
                "error": "Dry run not supported for global cleanup"
            }
        
        result = artifact_registry.cleanup_all_sessions(params.days)
        result["status"] = "global_cleanup_completed"
        return result