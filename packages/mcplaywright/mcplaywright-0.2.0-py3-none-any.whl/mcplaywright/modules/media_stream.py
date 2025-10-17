"""
Media Stream

Provides fake audio/video stream capabilities for testing web applications
that use microphone and camera features.
"""

from typing import Dict, Any, Optional, List
from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class MediaStream(MCPMixin):
    """
    Media stream testing with fake devices.
    
    Enables testing of web applications that use getUserMedia API
    with fake audio and video streams from files.
    """
    
    def __init__(self):
        super().__init__()
        self.media_permissions = []
        self.fake_audio_file = None
        self.fake_video_file = None
        self.media_stream_enabled = False
        
    def _get_media_stream_args(self) -> List[str]:
        """Get browser launch arguments for fake media streams."""
        args = []
        
        if self.media_stream_enabled:
            # Enable fake media streams
            args.append("--use-fake-device-for-media-stream")
            # Bypass permission dialogs
            args.append("--use-fake-ui-for-media-stream")
            
            # Add audio file if specified
            if self.fake_audio_file and Path(self.fake_audio_file).exists():
                args.append(f"--use-file-for-fake-audio-capture={self.fake_audio_file}")
            
            # Add video file if specified
            if self.fake_video_file and Path(self.fake_video_file).exists():
                args.append(f"--use-file-for-fake-video-capture={self.fake_video_file}")
        
        return args
    
    @mcp_tool(
        name="browser_enable_fake_media",
        description="Enable fake media streams for testing microphone and camera features"
    )
    async def enable_fake_media_streams(
        self,
        audio_file: Optional[str] = None,
        video_file: Optional[str] = None,
        auto_grant_permissions: bool = True
    ) -> Dict[str, Any]:
        """Enable fake media streams for testing."""
        try:
            self.media_stream_enabled = True
            
            # Validate and set audio file
            if audio_file:
                audio_path = Path(audio_file)
                if not audio_path.exists():
                    return {
                        "status": "error",
                        "message": f"Audio file not found: {audio_file}"
                    }
                
                # Check file extension
                valid_audio_exts = ['.wav', '.mp3', '.ogg', '.webm']
                if audio_path.suffix.lower() not in valid_audio_exts:
                    logger.warning(f"Audio file may not be compatible: {audio_path.suffix}")
                
                self.fake_audio_file = str(audio_path.absolute())
                logger.info(f"Fake audio configured: {self.fake_audio_file}")
            
            # Validate and set video file
            if video_file:
                video_path = Path(video_file)
                if not video_path.exists():
                    return {
                        "status": "error",
                        "message": f"Video file not found: {video_file}"
                    }
                
                # Check file extension
                valid_video_exts = ['.mp4', '.webm', '.avi', '.mov', '.mjpeg', '.y4m']
                if video_path.suffix.lower() not in valid_video_exts:
                    logger.warning(f"Video file may not be compatible: {video_path.suffix}")
                
                self.fake_video_file = str(video_path.absolute())
                logger.info(f"Fake video configured: {self.fake_video_file}")
            
            # Get media stream arguments
            media_args = self._get_media_stream_args()
            
            # Note: Browser needs to be restarted with these arguments
            result = {
                "status": "success",
                "message": "Fake media streams configured. Browser restart required.",
                "audio_file": self.fake_audio_file,
                "video_file": self.fake_video_file,
                "browser_args": media_args,
                "restart_required": True
            }
            
            # If auto-grant permissions, prepare them
            if auto_grant_permissions:
                self.media_permissions = ["microphone", "camera"]
                result["permissions"] = self.media_permissions
            
            return result
            
        except Exception as e:
            logger.error(f"Error enabling fake media streams: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    @mcp_tool(
        name="browser_grant_media_permissions",
        description="Grant microphone and camera permissions to the current context"
    )
    async def grant_media_permissions(
        self,
        permissions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Grant media permissions to the browser context."""
        try:
            if not permissions:
                permissions = ["microphone", "camera"]
            
            # Validate permissions
            valid_permissions = ["microphone", "camera", "geolocation", "notifications"]
            invalid = [p for p in permissions if p not in valid_permissions]
            if invalid:
                logger.warning(f"Invalid permissions requested: {invalid}")
            
            # Filter to valid permissions
            valid_perms = [p for p in permissions if p in valid_permissions]
            
            # Grant permissions to context
            if hasattr(self, '_context') and self._context:
                await self._context.grant_permissions(valid_perms)
                self.media_permissions = valid_perms
                
                logger.info(f"Granted permissions: {valid_perms}")
                
                return {
                    "status": "success",
                    "message": f"Granted {len(valid_perms)} permissions",
                    "permissions": valid_perms,
                    "skipped": invalid if invalid else None
                }
            else:
                return {
                    "status": "error",
                    "message": "No browser context available"
                }
                
        except Exception as e:
            logger.error(f"Error granting media permissions: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    @mcp_tool(
        name="browser_test_microphone",
        description="Test microphone functionality on a web page"
    )
    async def test_microphone(
        self,
        test_url: str = "https://mictests.com/",
        start_button_selector: Optional[str] = None
    ) -> Dict[str, Any]:
        """Test microphone functionality."""
        try:
            page = await self.get_current_page()
            
            # Navigate to test URL
            await page.goto(test_url)
            
            # Grant microphone permission if not already granted
            if "microphone" not in self.media_permissions:
                await self.grant_media_permissions(["microphone"])
            
            # Click start button if provided
            if start_button_selector:
                await page.click(start_button_selector)
            else:
                # Try common patterns
                try:
                    # Try role-based selector
                    await page.get_by_role("button", name="Test my mic").click()
                except:
                    # Try text-based selectors
                    try:
                        await page.click("text=Start")
                    except:
                        await page.click("text=Test")
            
            # Wait for audio context to be created
            audio_context_exists = await page.evaluate("""
                () => {
                    return typeof AudioContext !== 'undefined' || 
                           typeof webkitAudioContext !== 'undefined';
                }
            """)
            
            # Check if getUserMedia was called
            get_user_media_called = await page.evaluate("""
                () => {
                    return navigator.mediaDevices && 
                           typeof navigator.mediaDevices.getUserMedia === 'function';
                }
            """)
            
            # Try to get microphone stream status
            stream_active = await page.evaluate("""
                async () => {
                    try {
                        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                        const active = stream.active;
                        stream.getTracks().forEach(track => track.stop());
                        return active;
                    } catch (e) {
                        return false;
                    }
                }
            """)
            
            return {
                "status": "success",
                "test_url": test_url,
                "audio_context_available": audio_context_exists,
                "getUserMedia_available": get_user_media_called,
                "stream_active": stream_active,
                "fake_audio_file": self.fake_audio_file,
                "permissions": self.media_permissions
            }
            
        except Exception as e:
            logger.error(f"Error testing microphone: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    @mcp_tool(
        name="browser_test_camera",
        description="Test camera functionality on a web page"
    )
    async def test_camera(
        self,
        test_url: str = "https://webcamtests.com/",
        start_button_selector: Optional[str] = None
    ) -> Dict[str, Any]:
        """Test camera functionality."""
        try:
            page = await self.get_current_page()
            
            # Navigate to test URL
            await page.goto(test_url)
            
            # Grant camera permission if not already granted
            if "camera" not in self.media_permissions:
                await self.grant_media_permissions(["camera"])
            
            # Click start button if provided
            if start_button_selector:
                await page.click(start_button_selector)
            
            # Check if getUserMedia was called for video
            video_stream_active = await page.evaluate("""
                async () => {
                    try {
                        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
                        const active = stream.active;
                        const videoTracks = stream.getVideoTracks();
                        const hasVideo = videoTracks.length > 0;
                        stream.getTracks().forEach(track => track.stop());
                        return { active, hasVideo, trackCount: videoTracks.length };
                    } catch (e) {
                        return { active: false, hasVideo: false, error: e.message };
                    }
                }
            """)
            
            return {
                "status": "success",
                "test_url": test_url,
                "video_stream": video_stream_active,
                "fake_video_file": self.fake_video_file,
                "permissions": self.media_permissions
            }
            
        except Exception as e:
            logger.error(f"Error testing camera: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    @mcp_tool(
        name="browser_record_media_test",
        description="Record a test of media stream functionality"
    )
    async def record_media_test(
        self,
        test_url: str,
        duration_seconds: int = 10,
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """Record a media stream test session."""
        try:
            page = await self.get_current_page()
            
            # Start video recording if not already started
            if output_file:
                await page.video.save_as(output_file)
            
            # Navigate and run test
            await page.goto(test_url)
            
            # Grant all media permissions
            await self.grant_media_permissions(["microphone", "camera"])
            
            # Wait for specified duration
            await page.wait_for_timeout(duration_seconds * 1000)
            
            # Get media stream statistics
            stats = await page.evaluate("""
                async () => {
                    try {
                        const stream = await navigator.mediaDevices.getUserMedia({ 
                            audio: true, 
                            video: true 
                        });
                        
                        const audioTracks = stream.getAudioTracks();
                        const videoTracks = stream.getVideoTracks();
                        
                        const stats = {
                            active: stream.active,
                            audioTracks: audioTracks.length,
                            videoTracks: videoTracks.length,
                            audioEnabled: audioTracks.length > 0 && audioTracks[0].enabled,
                            videoEnabled: videoTracks.length > 0 && videoTracks[0].enabled,
                            audioLabel: audioTracks.length > 0 ? audioTracks[0].label : null,
                            videoLabel: videoTracks.length > 0 ? videoTracks[0].label : null
                        };
                        
                        stream.getTracks().forEach(track => track.stop());
                        return stats;
                    } catch (e) {
                        return { error: e.message };
                    }
                }
            """)
            
            return {
                "status": "success",
                "test_url": test_url,
                "duration_seconds": duration_seconds,
                "media_stats": stats,
                "fake_audio": self.fake_audio_file,
                "fake_video": self.fake_video_file,
                "recording": output_file if output_file else None
            }
            
        except Exception as e:
            logger.error(f"Error recording media test: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def launch_with_fake_media(self):
        """Launch browser with fake media stream support."""
        # Close existing browser
        if hasattr(self, '_browser') and self._browser:
            await self._browser.close()
        
        # Get media stream arguments
        media_args = self._get_media_stream_args()
        
        # Launch with media arguments
        from playwright.async_api import async_playwright
        
        if not self._playwright:
            self._playwright = await async_playwright().start()
        
        # Combine with existing args
        all_args = ["--no-sandbox", "--disable-setuid-sandbox"] + media_args
        
        self._browser = await self._playwright.chromium.launch(
            headless=False,  # Media streams often require headed mode
            args=all_args
        )
        
        self._context = await self._browser.new_context()
        
        # Grant media permissions
        if self.media_permissions:
            await self._context.grant_permissions(self.media_permissions)
        
        self._current_page = await self._context.new_page()
        self._pages = [self._current_page]
        
        logger.info(f"Browser launched with fake media support: {media_args}")
        
        return {
            "status": "success",
            "media_args": media_args,
            "permissions": self.media_permissions
        }
