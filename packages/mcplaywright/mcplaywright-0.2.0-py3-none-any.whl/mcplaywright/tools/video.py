"""
Video Recording Tools for MCPlaywright

Smart video recording system with multiple modes, automatic viewport matching,
and action-aware pause/resume functionality.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ..context import VideoMode, VideoConfig
from ..session_manager import get_session_manager

logger = logging.getLogger(__name__)


class StartRecordingParams(BaseModel):
    """Parameters for starting video recording"""
    session_id: Optional[str] = Field(None, description="Session ID (auto-generated if not provided)")
    filename: Optional[str] = Field(None, description="Base filename for video files (auto-generated if not provided)")
    size_width: Optional[int] = Field(1280, description="Video width in pixels")
    size_height: Optional[int] = Field(720, description="Video height in pixels")
    auto_set_viewport: Optional[bool] = Field(True, description="Automatically set browser viewport to match video size")
    mode: Optional[str] = Field("smart", description="Recording mode: 'smart', 'continuous', 'action-only', 'segment'")


class StopRecordingParams(BaseModel):
    """Parameters for stopping video recording"""
    session_id: str = Field(description="Session ID")


class RecordingModeParams(BaseModel):
    """Parameters for setting recording mode"""
    session_id: str = Field(description="Session ID")
    mode: str = Field(description="Recording mode: 'smart', 'continuous', 'action-only', 'segment'")


class RecordingControlParams(BaseModel):
    """Parameters for recording control (pause/resume)"""
    session_id: str = Field(description="Session ID")


async def browser_start_recording(params: StartRecordingParams) -> Dict[str, Any]:
    """
    Start video recording browser session with intelligent viewport matching.
    
    This is the core smart video recording feature ported from TypeScript.
    
    Key Features:
    - Automatic viewport matching to eliminate gray borders
    - Multiple recording modes (smart, continuous, action-only, segment)
    - Session-based artifact storage
    - Action-aware recording integration
    
    The smart mode automatically pauses during waits and resumes during actions,
    creating professional demo videos without dead time.
    
    Returns:
        Video recording startup result with configuration details
    """
    try:
        # Get or create session
        session_manager = get_session_manager()
        context = await session_manager.get_or_create_session(params.session_id)
        
        # Generate filename if not provided
        if params.filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            params.filename = f"session_{timestamp}"
        
        # Create video size configuration
        video_size = {
            "width": params.size_width or 1280,
            "height": params.size_height or 720
        }
        
        # Create video recording directory
        video_dir = context.artifacts_dir / "videos"
        video_dir.mkdir(exist_ok=True)
        
        # Set up video configuration
        video_config = VideoConfig(
            directory=video_dir,
            size=video_size,
            base_filename=params.filename,
            auto_set_viewport=params.auto_set_viewport or True
        )
        
        # Set recording mode
        try:
            video_mode = VideoMode(params.mode or "smart")
            video_config.mode = video_mode
            context.set_video_recording_mode(video_mode)
        except ValueError:
            return {
                "success": False,
                "error": f"Invalid recording mode: {params.mode}. Must be 'smart', 'continuous', 'action-only', or 'segment'",
                "session_id": context.session_id
            }
        
        # Automatically set viewport to match video size (key feature from TypeScript)
        if video_config.auto_set_viewport:
            try:
                await context.update_browser_config({
                    "viewport": video_size
                })
                viewport_info = f"🖥️ Browser viewport automatically set to {video_size['width']}x{video_size['height']} to match video size"
            except Exception as e:
                viewport_info = f"⚠️ Could not auto-set viewport: {str(e)}"
        else:
            viewport_info = "⚠️ Viewport not automatically set - you may see gray borders around content"
        
        # Configure video recording in context
        context.set_video_recording(video_config)
        
        # Get the current page to trigger browser context creation with video recording
        try:
            page = await context.get_current_page()
            logger.info(f"Video recording enabled for page in session {context.session_id}")
        except Exception as e:
            logger.warning(f"Could not get page for video recording: {str(e)}")
        
        # Get recording info for response
        recording_info = context.get_video_recording_info()
        
        result = {
            "success": True,
            "session_id": context.session_id,
            "video_config": {
                "filename": params.filename,
                "size": video_size,
                "directory": str(video_dir),
                "mode": video_mode.value,
                "auto_set_viewport": video_config.auto_set_viewport
            },
            "recording_info": recording_info,
            "viewport_info": viewport_info,
            "mode_info": get_mode_description(video_mode),
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Video recording started for session {context.session_id} in {video_mode.value} mode")
        return result
        
    except Exception as e:
        logger.error(f"Start video recording failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "session_id": params.session_id,
            "timestamp": datetime.now().isoformat()
        }


async def browser_stop_recording(params: StopRecordingParams) -> Dict[str, Any]:
    """
    Stop video recording and finalize video files.
    
    Stops all active video recordings, collects video file paths,
    and cleans up recording state while preserving artifacts.
    
    Returns:
        Recording stop result with video file paths
    """
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_session(params.session_id)
        
        if not context:
            return {
                "success": False,
                "error": f"Session {params.session_id} not found",
                "session_id": params.session_id,
                "timestamp": datetime.now().isoformat()
            }
        
        # Stop video recording and collect video paths
        video_paths = await context.stop_video_recording()
        
        # Get final recording info before cleanup
        recording_info = context.get_video_recording_info()
        
        result = {
            "success": True,
            "session_id": context.session_id,
            "video_files": video_paths,
            "total_videos": len(video_paths),
            "recording_info": recording_info,
            "timestamp": datetime.now().isoformat()
        }
        
        if video_paths:
            result["message"] = f"🎬 Video recording stopped! {len(video_paths)} video file(s) created"
            logger.info(f"Video recording stopped for session {context.session_id}, {len(video_paths)} files created")
        else:
            result["message"] = "📹 Video recording stopped (no video files were created)"
            logger.info(f"Video recording stopped for session {context.session_id}, no files created")
        
        return result
        
    except Exception as e:
        logger.error(f"Stop video recording failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "session_id": params.session_id,
            "timestamp": datetime.now().isoformat()
        }


async def browser_pause_recording(params: RecordingControlParams) -> Dict[str, Any]:
    """
    Manually pause video recording to eliminate dead time.
    
    This allows manual control over recording pauses, useful for creating
    professional demo videos. In smart recording mode, pausing happens
    automatically during waits.
    
    Returns:
        Pause operation result with affected recordings count
    """
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_session(params.session_id)
        
        if not context:
            return {
                "success": False,
                "error": f"Session {params.session_id} not found",
                "session_id": params.session_id,
                "timestamp": datetime.now().isoformat()
            }
        
        # Pause video recording
        pause_result = await context.pause_video_recording()
        
        result = {
            "success": True,
            "session_id": context.session_id,
            "paused_recordings": pause_result["paused"],
            "message": pause_result["message"],
            "recording_info": context.get_video_recording_info(),
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Video recording paused for session {context.session_id}")
        return result
        
    except Exception as e:
        logger.error(f"Pause video recording failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "session_id": params.session_id,
            "timestamp": datetime.now().isoformat()
        }


async def browser_resume_recording(params: RecordingControlParams) -> Dict[str, Any]:
    """
    Resume previously paused video recording.
    
    New video segments will capture subsequent browser actions. In smart
    recording mode, resuming happens automatically when browser actions begin.
    
    Returns:
        Resume operation result with affected recordings count
    """
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_session(params.session_id)
        
        if not context:
            return {
                "success": False,
                "error": f"Session {params.session_id} not found",
                "session_id": params.session_id,
                "timestamp": datetime.now().isoformat()
            }
        
        # Resume video recording
        resume_result = await context.resume_video_recording()
        
        result = {
            "success": True,
            "session_id": context.session_id,
            "resumed_recordings": resume_result["resumed"],
            "message": resume_result["message"],
            "recording_info": context.get_video_recording_info(),
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Video recording resumed for session {context.session_id}")
        return result
        
    except Exception as e:
        logger.error(f"Resume video recording failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "session_id": params.session_id,
            "timestamp": datetime.now().isoformat()
        }


async def browser_set_recording_mode(params: RecordingModeParams) -> Dict[str, Any]:
    """
    Configure intelligent video recording behavior.
    
    Choose from continuous recording, smart auto-pause/resume, action-only
    capture, or segmented recording. Smart mode is recommended for marketing
    demos as it eliminates dead time automatically.
    
    Recording Modes:
    - continuous: Record everything including waits (traditional behavior)
    - smart: Automatically pause during waits, resume during actions (RECOMMENDED)
    - action-only: Only record during active browser interactions
    - segment: Create separate video files for each action sequence
    
    Returns:
        Recording mode update result with mode information
    """
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_session(params.session_id)
        
        if not context:
            return {
                "success": False,
                "error": f"Session {params.session_id} not found",
                "session_id": params.session_id,
                "timestamp": datetime.now().isoformat()
            }
        
        # Validate and set recording mode
        try:
            video_mode = VideoMode(params.mode.lower())
            context.set_video_recording_mode(video_mode)
        except ValueError:
            return {
                "success": False,
                "error": f"Invalid recording mode: {params.mode}. Must be 'smart', 'continuous', 'action-only', or 'segment'",
                "session_id": context.session_id,
                "timestamp": datetime.now().isoformat()
            }
        
        result = {
            "success": True,
            "session_id": context.session_id,
            "recording_mode": video_mode.value,
            "mode_info": get_mode_description(video_mode),
            "recording_info": context.get_video_recording_info(),
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Video recording mode set to {video_mode.value} for session {context.session_id}")
        return result
        
    except Exception as e:
        logger.error(f"Set recording mode failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "session_id": params.session_id,
            "timestamp": datetime.now().isoformat()
        }


async def browser_recording_status(session_id: str) -> Dict[str, Any]:
    """
    Check if video recording is currently enabled and get recording details.
    
    Use this to verify recording is active before performing actions, or to
    check output directory and settings.
    
    Returns:
        Current recording status and configuration details
    """
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_session(session_id)
        
        if not context:
            return {
                "success": False,
                "error": f"Session {session_id} not found",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
        
        recording_info = context.get_video_recording_info()
        
        result = {
            "success": True,
            "session_id": context.session_id,
            "recording_active": recording_info["enabled"],
            "recording_info": recording_info,
            "timestamp": datetime.now().isoformat()
        }
        
        if recording_info["enabled"]:
            result["mode_info"] = get_mode_description(VideoMode(recording_info["mode"]))
            result["message"] = f"🎬 Recording active in {recording_info['mode']} mode"
        else:
            result["message"] = "📹 No active video recording"
        
        return result
        
    except Exception as e:
        logger.error(f"Get recording status failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }


def get_mode_description(mode: VideoMode) -> str:
    """Get detailed description of recording mode behavior"""
    descriptions = {
        VideoMode.SMART: "🤖 Smart mode: Auto-pause during waits, resume during actions (recommended for demos)",
        VideoMode.CONTINUOUS: "⏺️ Continuous mode: Record everything including waits (traditional behavior)",
        VideoMode.ACTION_ONLY: "⚡ Action-only mode: Only record during active browser interactions",
        VideoMode.SEGMENT: "📂 Segment mode: Create separate video files for each action sequence"
    }
    return descriptions.get(mode, f"Unknown mode: {mode.value}")


# Helper functions for action-aware recording integration

async def begin_video_action_for_session(session_id: str, action_name: str) -> None:
    """Helper to begin video action for a session"""
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_session(session_id)
        if context:
            await context.begin_video_action(action_name)
    except Exception as e:
        logger.warning(f"Could not begin video action for session {session_id}: {str(e)}")


async def end_video_action_for_session(session_id: str, action_name: str) -> None:
    """Helper to end video action for a session"""
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_session(session_id)
        if context:
            await context.end_video_action(action_name)
    except Exception as e:
        logger.warning(f"Could not end video action for session {session_id}: {str(e)}")