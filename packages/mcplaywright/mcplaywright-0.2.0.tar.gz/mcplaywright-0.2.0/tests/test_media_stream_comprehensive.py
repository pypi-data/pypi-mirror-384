#!/usr/bin/env python3
"""
Comprehensive Media Stream Tests

Complete test coverage for MediaStreamMixin functionality.
"""

import asyncio
import pytest
from pathlib import Path
import tempfile
import wave
import struct
import sys
import json

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mixins.media_stream_mixin import MediaStreamMixin
from mixins.browser_mixin import BrowserMixin
from mixins.navigation_mixin import NavigationMixin


class TestableMediaServer(BrowserMixin, NavigationMixin, MediaStreamMixin):
    """Test server with media stream capabilities."""
    pass


def create_test_wav_file(duration_seconds: float = 1.0) -> Path:
    """Create a test WAV file."""
    filepath = Path(tempfile.mktemp(suffix='.wav'))
    sample_rate = 44100
    num_samples = int(sample_rate * duration_seconds)
    
    with wave.open(str(filepath), 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)   # 2 bytes per sample
        wav_file.setframerate(sample_rate)
        
        # Generate sine wave
        import math
        frequency = 440  # A4 note
        for i in range(num_samples):
            sample = int(32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
            wav_file.writeframes(struct.pack('<h', sample))
    
    return filepath


class TestMediaStreamMixin:
    """Test suite for MediaStreamMixin."""
    
    @pytest.fixture
    async def server(self):
        """Create test server instance."""
        server = TestableMediaServer()
        yield server
        await server.close_browser()
    
    @pytest.mark.asyncio
    async def test_enable_fake_media_streams(self, server):
        """Test enabling fake media streams."""
        # Create test audio file
        audio_file = create_test_wav_file()
        
        try:
            # Enable fake media
            result = await server.enable_fake_media_streams(
                audio_file=str(audio_file),
                auto_grant_permissions=True
            )
            
            assert result["status"] == "success"
            assert result["audio_file"] == str(audio_file.absolute())
            assert result["restart_required"] is True
            assert "browser_args" in result
            assert "--use-fake-device-for-media-stream" in result["browser_args"]
            assert f"--use-file-for-fake-audio-capture={audio_file.absolute()}" in result["browser_args"]
            assert result["permissions"] == ["microphone", "camera"]
            
        finally:
            # Cleanup
            if audio_file.exists():
                audio_file.unlink()
    
    @pytest.mark.asyncio
    async def test_enable_fake_media_invalid_file(self, server):
        """Test enabling fake media with invalid file."""
        result = await server.enable_fake_media_streams(
            audio_file="/nonexistent/file.wav"
        )
        
        assert result["status"] == "error"
        assert "not found" in result["message"]
    
    @pytest.mark.asyncio
    async def test_grant_media_permissions(self, server):
        """Test granting media permissions."""
        # Setup browser context first
        await server.ensure_browser_context()
        
        # Grant permissions
        result = await server.grant_media_permissions(["microphone", "camera"])
        
        assert result["status"] == "success"
        assert result["permissions"] == ["microphone", "camera"]
        assert server.media_permissions == ["microphone", "camera"]
    
    @pytest.mark.asyncio
    async def test_grant_invalid_permissions(self, server):
        """Test granting invalid permissions."""
        await server.ensure_browser_context()
        
        # Try invalid permissions
        result = await server.grant_media_permissions(["microphone", "invalid_perm"])
        
        assert result["status"] == "success"
        assert "microphone" in result["permissions"]
        assert "invalid_perm" not in result["permissions"]
        assert "invalid_perm" in result["skipped"]
    
    @pytest.mark.asyncio
    async def test_media_stream_args(self, server):
        """Test media stream browser arguments generation."""
        # Test without media enabled
        args = server._get_media_stream_args()
        assert len(args) == 0
        
        # Enable media streams
        server.media_stream_enabled = True
        args = server._get_media_stream_args()
        
        assert "--use-fake-device-for-media-stream" in args
        assert "--use-fake-ui-for-media-stream" in args
        
        # Add audio file
        audio_file = create_test_wav_file()
        try:
            server.fake_audio_file = str(audio_file)
            args = server._get_media_stream_args()
            
            assert f"--use-file-for-fake-audio-capture={audio_file}" in args
        finally:
            if audio_file.exists():
                audio_file.unlink()
    
    @pytest.mark.asyncio
    async def test_test_microphone_basic(self, server):
        """Test basic microphone testing functionality."""
        # This test validates the method exists and handles errors gracefully
        # Real browser testing would require headed mode
        
        await server.ensure_browser_context()
        
        # Navigate to a simple page
        await server.navigate_to_url("data:text/html,<h1>Test Page</h1>")
        
        # Test microphone (will fail gracefully without real media)
        result = await server.test_microphone(
            test_url="data:text/html,<button>Test</button>"
        )
        
        # Check structure
        assert "status" in result
        assert "test_url" in result
        assert "permissions" in result
    
    @pytest.mark.asyncio
    async def test_test_camera_basic(self, server):
        """Test basic camera testing functionality."""
        await server.ensure_browser_context()
        
        # Test camera
        result = await server.test_camera(
            test_url="data:text/html,<video></video>"
        )
        
        # Check structure
        assert "status" in result
        assert "test_url" in result
        assert "permissions" in result
    
    @pytest.mark.asyncio
    async def test_record_media_test(self, server):
        """Test media recording functionality."""
        await server.ensure_browser_context()
        
        # Record test
        result = await server.record_media_test(
            test_url="data:text/html,<video></video>",
            duration_seconds=1
        )
        
        assert "status" in result
        assert "test_url" in result
        assert "duration_seconds" in result
        assert result["duration_seconds"] == 1


class TestMediaStreamIntegration:
    """Integration tests for media stream with browser."""
    
    @pytest.mark.asyncio
    async def test_media_permissions_flow(self):
        """Test complete media permissions flow."""
        server = TestableMediaServer()
        
        try:
            # Setup browser
            await server.ensure_browser_context()
            
            # Grant permissions
            grant_result = await server.grant_media_permissions(["microphone"])
            assert grant_result["status"] == "success"
            
            # Navigate to test page
            await server.navigate_to_url("data:text/html,<h1>Media Test</h1>")
            
            # Check getUserMedia availability
            page = await server.get_current_page()
            has_get_user_media = await page.evaluate("""
                () => !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia)
            """)
            
            assert has_get_user_media is True
            
        finally:
            await server.close_browser()
    
    @pytest.mark.asyncio
    async def test_fake_media_configuration(self):
        """Test fake media configuration."""
        server = TestableMediaServer()
        audio_file = create_test_wav_file()
        
        try:
            # Configure fake media
            config_result = await server.enable_fake_media_streams(
                audio_file=str(audio_file)
            )
            
            assert config_result["status"] == "success"
            assert server.fake_audio_file == str(audio_file.absolute())
            assert server.media_stream_enabled is True
            
            # Check browser args
            args = server._get_media_stream_args()
            assert len(args) >= 3  # Should have at least 3 args
            
        finally:
            await server.close_browser()
            if audio_file.exists():
                audio_file.unlink()
    
    @pytest.mark.asyncio
    async def test_multiple_permission_grants(self):
        """Test granting permissions multiple times."""
        server = TestableMediaServer()
        
        try:
            await server.ensure_browser_context()
            
            # Grant microphone first
            result1 = await server.grant_media_permissions(["microphone"])
            assert "microphone" in result1["permissions"]
            
            # Grant camera next
            result2 = await server.grant_media_permissions(["camera"])
            assert "camera" in result2["permissions"]
            
            # Grant both
            result3 = await server.grant_media_permissions(["microphone", "camera"])
            assert len(result3["permissions"]) == 2
            
        finally:
            await server.close_browser()


class TestMediaStreamEdgeCases:
    """Edge case tests for media stream functionality."""
    
    @pytest.mark.asyncio
    async def test_no_browser_context(self):
        """Test operations without browser context."""
        server = TestableMediaServer()
        
        # Try to grant permissions without context
        result = await server.grant_media_permissions(["microphone"])
        
        assert result["status"] == "error"
        assert "No browser context" in result["message"]
    
    @pytest.mark.asyncio
    async def test_empty_permissions(self):
        """Test with empty permissions list."""
        server = TestableMediaServer()
        
        try:
            await server.ensure_browser_context()
            
            # Grant default permissions (empty list)
            result = await server.grant_media_permissions([])
            
            # Should default to microphone and camera
            assert result["status"] == "success"
            assert "microphone" in result["permissions"]
            assert "camera" in result["permissions"]
            
        finally:
            await server.close_browser()
    
    @pytest.mark.asyncio
    async def test_wav_file_validation(self):
        """Test WAV file validation."""
        server = TestableMediaServer()
        
        # Test with non-WAV extension (should warn but accept)
        mp3_file = Path(tempfile.mktemp(suffix='.mp3'))
        mp3_file.touch()  # Create empty file
        
        try:
            result = await server.enable_fake_media_streams(
                audio_file=str(mp3_file)
            )
            
            # Should succeed but may have logged warning
            assert result["status"] == "success"
            assert result["audio_file"] == str(mp3_file.absolute())
            
        finally:
            if mp3_file.exists():
                mp3_file.unlink()


async def run_all_media_tests():
    """Run all media stream tests."""
    print("🎭 Comprehensive Media Stream Test Suite")
    print("=" * 50)
    
    test_classes = [
        TestMediaStreamMixin,
        TestMediaStreamIntegration,
        TestMediaStreamEdgeCases
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for test_class in test_classes:
        print(f"\n📋 Testing {test_class.__name__}")
        test_instance = test_class()
        
        # Get all test methods
        test_methods = [m for m in dir(test_instance) if m.startswith("test_")]
        
        for method_name in test_methods:
            total_tests += 1
            try:
                method = getattr(test_instance, method_name)
                
                # Create fixtures if needed
                if test_class == TestMediaStreamMixin:
                    server = TestableMediaServer()
                    await method(server)
                    await server.close_browser()
                else:
                    await method()
                
                passed_tests += 1
                print(f"  ✅ {method_name}")
                
            except Exception as e:
                failed_tests.append((test_class.__name__, method_name, str(e)))
                print(f"  ❌ {method_name}: {e}")
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"  Total: {total_tests}")
    print(f"  Passed: {passed_tests}")
    print(f"  Failed: {len(failed_tests)}")
    print(f"  Success Rate: {(passed_tests/total_tests*100):.1f}%")
    
    if failed_tests:
        print("\n❌ Failed Tests:")
        for class_name, method, error in failed_tests:
            print(f"  {class_name}.{method}: {error[:100]}")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    success = asyncio.run(run_all_media_tests())
    print(f"\n{'🎉 ALL TESTS PASSED!' if success else '❌ SOME TESTS FAILED'}")
    sys.exit(0 if success else 1)