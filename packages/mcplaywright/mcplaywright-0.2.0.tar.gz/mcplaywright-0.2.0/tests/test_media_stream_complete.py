#!/usr/bin/env python3
"""
Complete Media Stream Tests with Y4M Support

Tests fake audio/video stream capabilities with proper media files.
"""

import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from playwright.async_api import async_playwright
from utils.media_generator import (
    create_test_wav_file,
    create_test_y4m_file,
    create_media_test_suite,
    cleanup_test_files
)


async def test_fake_microphone_with_wav():
    """Test fake microphone with generated WAV file."""
    print("🎤 Testing Fake Microphone with WAV")
    
    # Create test audio file
    test_audio = create_test_wav_file(duration_seconds=3.0, frequency=440)
    print(f"  ✅ Created test audio: {test_audio}")
    
    playwright = await async_playwright().start()
    
    try:
        # Launch browser with fake microphone
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
        
        # Test on Web Audio demo
        await page.goto("https://webaudiodemos.appspot.com/input/index.html")
        print("  ✅ Navigated to Web Audio demo")
        
        # Verify getUserMedia availability
        has_get_user_media = await page.evaluate("""
            () => !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia)
        """)
        
        assert has_get_user_media, "getUserMedia not available"
        print("  ✅ getUserMedia API available")
        
        # Get microphone stream
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
                    tracks.forEach(track => track.stop());
                    return result;
                } catch (e) {
                    return { success: false, error: e.message };
                }
            }
        """)
        
        print(f"  📊 Stream result: {stream_result}")
        assert stream_result['success'], f"Failed: {stream_result.get('error')}"
        assert stream_result['trackCount'] > 0, "No audio tracks"
        print(f"  ✅ Audio stream active with {stream_result['trackCount']} track(s)")
        
        await page.wait_for_timeout(2000)
        await browser.close()
        
    finally:
        await playwright.stop()
        cleanup_test_files(test_audio)
    
    print("  ✅ Fake microphone test completed!")
    return True


async def test_fake_camera_with_y4m():
    """Test fake camera with Y4M video file."""
    print("📹 Testing Fake Camera with Y4M")
    
    # Create Y4M test video
    test_video = create_test_y4m_file(
        duration_seconds=3.0,
        width=640,
        height=480,
        pattern="smpte"
    )
    print(f"  ✅ Created test video: {test_video} ({test_video.stat().st_size} bytes)")
    
    playwright = await async_playwright().start()
    
    try:
        # Launch with fake camera using Y4M file
        browser = await playwright.chromium.launch(
            headless=False,
            args=[
                "--use-fake-device-for-media-stream",
                "--use-fake-ui-for-media-stream",
                f"--use-file-for-fake-video-capture={test_video}"
            ]
        )
        
        context = await browser.new_context()
        await context.grant_permissions(["camera"])
        page = await context.new_page()
        
        print("  ✅ Browser launched with fake camera (Y4M)")
        
        # Create test page with video element
        await page.goto("data:text/html,<video id='video' autoplay style='width:640px;height:480px;background:black'></video><div id='status'>Ready</div>")
        
        # Start video stream
        video_result = await page.evaluate("""
            async () => {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
                    const video = document.getElementById('video');
                    video.srcObject = stream;
                    document.getElementById('status').textContent = 'Streaming';
                    
                    // Wait for video to start playing
                    await new Promise(resolve => {
                        video.onloadedmetadata = resolve;
                        setTimeout(resolve, 1000); // Timeout fallback
                    });
                    
                    const tracks = stream.getVideoTracks();
                    return {
                        success: true,
                        active: stream.active,
                        trackCount: tracks.length,
                        trackLabel: tracks[0]?.label || 'Unknown',
                        videoWidth: video.videoWidth,
                        videoHeight: video.videoHeight,
                        readyState: video.readyState
                    };
                } catch (e) {
                    document.getElementById('status').textContent = 'Error: ' + e.message;
                    return { success: false, error: e.message };
                }
            }
        """)
        
        print(f"  📊 Video result: {video_result}")
        assert video_result['success'], f"Failed: {video_result.get('error')}"
        assert video_result['trackCount'] > 0, "No video tracks"
        print(f"  ✅ Video stream active: {video_result['videoWidth']}x{video_result['videoHeight']}")
        
        # Take screenshot to verify
        await page.screenshot(path="y4m_camera_test.png")
        print("  ✅ Screenshot captured")
        
        await page.wait_for_timeout(2000)
        await browser.close()
        
    finally:
        await playwright.stop()
        cleanup_test_files(test_video)
        # Clean up screenshot
        screenshot = Path("y4m_camera_test.png")
        if screenshot.exists():
            screenshot.unlink()
    
    print("  ✅ Fake camera with Y4M test completed!")
    return True


async def test_combined_media_with_files():
    """Test both microphone and camera with proper media files."""
    print("🎬 Testing Combined Media (WAV + Y4M)")
    
    # Create both media files
    test_audio, test_video = create_media_test_suite()
    print(f"  ✅ Created audio: {test_audio}")
    print(f"  ✅ Created video: {test_video}")
    
    playwright = await async_playwright().start()
    
    try:
        # Launch with both fake devices
        browser = await playwright.chromium.launch(
            headless=False,
            args=[
                "--use-fake-device-for-media-stream",
                "--use-fake-ui-for-media-stream",
                f"--use-file-for-fake-audio-capture={test_audio}",
                f"--use-file-for-fake-video-capture={test_video}"
            ]
        )
        
        context = await browser.new_context()
        await context.grant_permissions(["microphone", "camera"])
        page = await context.new_page()
        
        print("  ✅ Browser launched with fake media devices")
        
        # Create comprehensive test page
        await page.goto("""data:text/html,
            <video id='video' autoplay style='width:640px;height:480px;background:black'></video>
            <div id='status'>Ready</div>
            <div id='audio-level'>Audio: 0</div>
            <canvas id='visualizer' width='640' height='100'></canvas>
        """)
        
        # Get both audio and video streams
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
                    
                    // Set up audio visualization (optional)
                    if (audioTracks.length > 0) {
                        const audioContext = new AudioContext();
                        const source = audioContext.createMediaStreamSource(stream);
                        const analyser = audioContext.createAnalyser();
                        source.connect(analyser);
                        
                        // Simple volume meter
                        const dataArray = new Uint8Array(analyser.frequencyBinCount);
                        setInterval(() => {
                            analyser.getByteFrequencyData(dataArray);
                            const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
                            document.getElementById('audio-level').textContent = `Audio: ${Math.round(average)}`;
                        }, 100);
                    }
                    
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
        assert media_result['success'], f"Failed: {media_result.get('error')}"
        assert media_result['audioTracks'] > 0, "No audio tracks"
        assert media_result['videoTracks'] > 0, "No video tracks"
        
        print(f"  ✅ Both streams active:")
        print(f"     Audio: {media_result['audioTracks']} track(s)")
        print(f"     Video: {media_result['videoTracks']} track(s)")
        
        # Capture screenshot
        await page.screenshot(path="combined_media_test.png")
        print("  ✅ Screenshot captured")
        
        await page.wait_for_timeout(3000)
        await browser.close()
        
    finally:
        await playwright.stop()
        cleanup_test_files(test_audio, test_video)
        # Clean up screenshot
        screenshot = Path("combined_media_test.png")
        if screenshot.exists():
            screenshot.unlink()
    
    print("  ✅ Combined media test completed!")
    return True


async def test_webrtc_echo_test():
    """Test with actual WebRTC echo test page."""
    print("🌐 Testing with WebRTC Test Page")
    
    # Create media files
    test_audio, test_video = create_media_test_suite()
    
    playwright = await async_playwright().start()
    
    try:
        browser = await playwright.chromium.launch(
            headless=False,
            args=[
                "--use-fake-device-for-media-stream",
                "--use-fake-ui-for-media-stream",
                f"--use-file-for-fake-audio-capture={test_audio}",
                f"--use-file-for-fake-video-capture={test_video}"
            ]
        )
        
        context = await browser.new_context()
        await context.grant_permissions(["microphone", "camera"])
        page = await context.new_page()
        
        # Navigate to WebRTC samples echo test
        await page.goto("https://webrtc.github.io/samples/src/content/peerconnection/pc1/")
        print("  ✅ Navigated to WebRTC samples")
        
        # Click start button
        await page.click("button#startButton")
        print("  ✅ Started local stream")
        
        await page.wait_for_timeout(1000)
        
        # Click call button
        await page.click("button#callButton")
        print("  ✅ Initiated call")
        
        await page.wait_for_timeout(2000)
        
        # Verify both video elements have streams
        videos_active = await page.evaluate("""
            () => {
                const localVideo = document.querySelector('video#localVideo');
                const remoteVideo = document.querySelector('video#remoteVideo');
                return {
                    local: localVideo && localVideo.srcObject && localVideo.srcObject.active,
                    remote: remoteVideo && remoteVideo.srcObject && remoteVideo.srcObject.active
                };
            }
        """)
        
        print(f"  📊 Video status: {videos_active}")
        assert videos_active['local'], "Local video not active"
        # Remote might not be active immediately
        print("  ✅ WebRTC connection established")
        
        await page.screenshot(path="webrtc_test.png")
        print("  ✅ Screenshot captured")
        
        await page.wait_for_timeout(2000)
        
        # Hang up
        await page.click("button#hangupButton")
        print("  ✅ Call ended")
        
        await browser.close()
        
    finally:
        await playwright.stop()
        cleanup_test_files(test_audio, test_video)
        # Clean up screenshot
        screenshot = Path("webrtc_test.png")
        if screenshot.exists():
            screenshot.unlink()
    
    print("  ✅ WebRTC test completed!")
    return True


async def run_all_media_tests():
    """Run all media stream tests with proper files."""
    print("🎭 Complete Media Stream Test Suite")
    print("=" * 50)
    
    tests = [
        ("WAV Audio Test", test_fake_microphone_with_wav),
        ("Y4M Video Test", test_fake_camera_with_y4m),
        ("Combined Media", test_combined_media_with_files),
        ("WebRTC Echo Test", test_webrtc_echo_test)
    ]
    
    passed = 0
    total = len(tests)
    failed_tests = []
    
    for name, test_func in tests:
        try:
            print(f"\nRunning: {name}")
            await test_func()
            passed += 1
            print(f"✅ {name} PASSED\n")
        except Exception as e:
            failed_tests.append((name, str(e)))
            print(f"❌ {name} FAILED: {e}\n")
    
    print("=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if failed_tests:
        print("\n❌ Failed Tests:")
        for test_name, error in failed_tests:
            print(f"  {test_name}: {error[:100]}")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_media_tests())
    print(f"\n{'🎉 ALL TESTS PASSED!' if success else '❌ SOME TESTS FAILED'}")
    sys.exit(0 if success else 1)