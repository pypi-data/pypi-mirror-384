#!/usr/bin/env python3
"""
Test Media Stream Functionality

Tests fake audio/video stream capabilities for web application testing.
"""

import asyncio
from pathlib import Path
import tempfile
import wave
import struct
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from playwright.async_api import async_playwright


def create_test_wav_file(filepath: Path, duration_seconds: float = 2.0, frequency: int = 440):
    """Create a test WAV file with a sine wave tone."""
    sample_rate = 44100
    num_samples = int(sample_rate * duration_seconds)
    
    with wave.open(str(filepath), 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)   # 2 bytes per sample
        wav_file.setframerate(sample_rate)
        
        # Generate sine wave
        import math
        for i in range(num_samples):
            sample = int(32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
            wav_file.writeframes(struct.pack('<h', sample))
    
    return filepath


async def test_fake_microphone():
    """Test fake microphone functionality."""
    print("🎤 Testing Fake Microphone")
    
    # Create a test audio file
    test_audio = Path(tempfile.mktemp(suffix='.wav'))
    create_test_wav_file(test_audio, duration_seconds=3.0, frequency=440)
    print(f"  ✅ Created test audio file: {test_audio}")
    
    playwright = await async_playwright().start()
    
    try:
        # Launch browser with fake media streams
        browser = await playwright.chromium.launch(
            headless=False,
            args=[
                "--use-fake-device-for-media-stream",
                "--use-fake-ui-for-media-stream",
                f"--use-file-for-fake-audio-capture={test_audio}"
            ]
        )
        
        context = await browser.new_context()
        await context.grant_permissions(["microphone"])
        page = await context.new_page()
        
        print("  ✅ Browser launched with fake microphone")
        
        # Test on a microphone testing site
        await page.goto("https://webaudiodemos.appspot.com/input/index.html")
        print("  ✅ Navigated to Web Audio demo")
        
        # Check if getUserMedia is available
        has_get_user_media = await page.evaluate("""
            () => {
                return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
            }
        """)
        
        assert has_get_user_media, "getUserMedia not available"
        print("  ✅ getUserMedia API available")
        
        # Try to get microphone access
        stream_result = await page.evaluate("""
            async () => {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    const tracks = stream.getAudioTracks();
                    const result = {
                        success: true,
                        active: stream.active,
                        trackCount: tracks.length,
                        trackLabel: tracks[0]?.label || 'Unknown'
                    };
                    // Clean up
                    tracks.forEach(track => track.stop());
                    return result;
                } catch (e) {
                    return { success: false, error: e.message };
                }
            }
        """)
        
        print(f"  📊 Stream result: {stream_result}")
        assert stream_result['success'], f"Failed to get audio stream: {stream_result.get('error')}"
        assert stream_result['trackCount'] > 0, "No audio tracks found"
        print(f"  ✅ Audio stream active with {stream_result['trackCount']} track(s)")
        
        await page.wait_for_timeout(2000)  # Let it run for 2 seconds
        
        await browser.close()
        
    finally:
        await playwright.stop()
        # Clean up test file
        if test_audio.exists():
            test_audio.unlink()
    
    print("  ✅ Fake microphone test completed successfully!")
    return True


async def test_fake_camera():
    """Test fake camera functionality."""
    print("📹 Testing Fake Camera")
    
    playwright = await async_playwright().start()
    
    try:
        # Launch browser with fake video stream
        browser = await playwright.chromium.launch(
            headless=False,
            args=[
                "--use-fake-device-for-media-stream",
                "--use-fake-ui-for-media-stream"
            ]
        )
        
        context = await browser.new_context()
        await context.grant_permissions(["camera"])
        page = await context.new_page()
        
        print("  ✅ Browser launched with fake camera")
        
        # Create a simple HTML page with video element
        await page.goto("data:text/html,<video id='video' autoplay></video><button id='start'>Start Camera</button>")
        
        # Add JavaScript to start camera
        await page.evaluate("""
            () => {
                document.getElementById('start').addEventListener('click', async () => {
                    try {
                        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
                        document.getElementById('video').srcObject = stream;
                        console.log('Camera started');
                    } catch (e) {
                        console.error('Camera error:', e);
                    }
                });
            }
        """)
        
        # Click start button
        await page.click('#start')
        print("  ✅ Camera start requested")
        
        # Wait a moment for stream to start
        await page.wait_for_timeout(1000)
        
        # Check if video stream is active
        video_result = await page.evaluate("""
            () => {
                const video = document.getElementById('video');
                const stream = video.srcObject;
                if (stream) {
                    const tracks = stream.getVideoTracks();
                    return {
                        success: true,
                        active: stream.active,
                        trackCount: tracks.length,
                        videoWidth: video.videoWidth,
                        videoHeight: video.videoHeight,
                        readyState: video.readyState
                    };
                }
                return { success: false, message: 'No stream found' };
            }
        """)
        
        print(f"  📊 Video result: {video_result}")
        assert video_result['success'], "Failed to get video stream"
        assert video_result['trackCount'] > 0, "No video tracks found"
        print(f"  ✅ Video stream active with {video_result['trackCount']} track(s)")
        
        await page.wait_for_timeout(2000)  # Let it run for 2 seconds
        
        await browser.close()
        
    finally:
        await playwright.stop()
    
    print("  ✅ Fake camera test completed successfully!")
    return True


async def test_combined_media():
    """Test both microphone and camera together."""
    print("🎬 Testing Combined Media (Mic + Camera)")
    
    # Create test audio file
    test_audio = Path(tempfile.mktemp(suffix='.wav'))
    create_test_wav_file(test_audio, duration_seconds=3.0, frequency=880)
    
    playwright = await async_playwright().start()
    
    try:
        # Launch with both fake devices
        browser = await playwright.chromium.launch(
            headless=False,
            args=[
                "--use-fake-device-for-media-stream",
                "--use-fake-ui-for-media-stream",
                f"--use-file-for-fake-audio-capture={test_audio}"
            ]
        )
        
        context = await browser.new_context()
        await context.grant_permissions(["microphone", "camera"])
        page = await context.new_page()
        
        print("  ✅ Browser launched with fake media devices")
        
        # Create test page
        await page.goto("data:text/html,<video id='video' autoplay></video><div id='status'>Ready</div>")
        
        # Get both audio and video
        media_result = await page.evaluate("""
            async () => {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ 
                        audio: true, 
                        video: true 
                    });
                    
                    document.getElementById('video').srcObject = stream;
                    document.getElementById('status').textContent = 'Streaming';
                    
                    const audioTracks = stream.getAudioTracks();
                    const videoTracks = stream.getVideoTracks();
                    
                    return {
                        success: true,
                        active: stream.active,
                        audioTracks: audioTracks.length,
                        videoTracks: videoTracks.length,
                        audioLabel: audioTracks[0]?.label,
                        videoLabel: videoTracks[0]?.label
                    };
                } catch (e) {
                    document.getElementById('status').textContent = 'Error: ' + e.message;
                    return { success: false, error: e.message };
                }
            }
        """)
        
        print(f"  📊 Combined media result: {media_result}")
        assert media_result['success'], f"Failed to get media: {media_result.get('error')}"
        assert media_result['audioTracks'] > 0, "No audio tracks"
        assert media_result['videoTracks'] > 0, "No video tracks"
        
        print(f"  ✅ Both streams active:")
        print(f"     Audio: {media_result['audioTracks']} track(s)")
        print(f"     Video: {media_result['videoTracks']} track(s)")
        
        # Take a screenshot to verify
        await page.screenshot(path="media_test_screenshot.png")
        print("  ✅ Screenshot captured")
        
        await page.wait_for_timeout(2000)
        
        await browser.close()
        
    finally:
        await playwright.stop()
        # Clean up
        if test_audio.exists():
            test_audio.unlink()
        screenshot = Path("media_test_screenshot.png")
        if screenshot.exists():
            screenshot.unlink()
    
    print("  ✅ Combined media test completed successfully!")
    return True


async def run_all_media_tests():
    """Run all media stream tests."""
    print("🎭 Media Stream Test Suite")
    print("=" * 40)
    
    tests = [
        ("Fake Microphone", test_fake_microphone),
        ("Fake Camera", test_fake_camera),
        ("Combined Media", test_combined_media)
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        try:
            print(f"\nRunning: {name}")
            await test_func()
            passed += 1
            print(f"✅ {name} PASSED\n")
        except Exception as e:
            print(f"❌ {name} FAILED: {e}\n")
    
    print("=" * 40)
    print(f"📊 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_media_tests())
    print(f"\n{'🎉 ALL TESTS PASSED!' if success else '❌ SOME TESTS FAILED'}")
    sys.exit(0 if success else 1)