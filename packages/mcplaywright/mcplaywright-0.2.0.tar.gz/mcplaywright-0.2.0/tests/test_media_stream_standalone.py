#!/usr/bin/env python3
"""
Standalone Media Stream Tests with Y4M Support

Tests without importing from main package to avoid conflicts.
"""

import asyncio
from pathlib import Path
import sys
import tempfile
import wave
import struct
import math
from typing import Optional, Tuple

from playwright.async_api import async_playwright


def create_test_wav_file(
    filepath: Optional[Path] = None,
    duration_seconds: float = 2.0,
    frequency: int = 440,
    sample_rate: int = 44100
) -> Path:
    """Create a test WAV file with a sine wave tone."""
    if filepath is None:
        filepath = Path(tempfile.mktemp(suffix='.wav'))
    
    num_samples = int(sample_rate * duration_seconds)
    
    with wave.open(str(filepath), 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)   # 2 bytes per sample (16-bit)
        wav_file.setframerate(sample_rate)
        
        # Generate sine wave
        for i in range(num_samples):
            sample = int(32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
            wav_file.writeframes(struct.pack('<h', sample))
    
    print(f"  📝 Created WAV: {filepath} ({duration_seconds}s, {frequency}Hz)")
    return filepath


def create_test_y4m_file(
    filepath: Optional[Path] = None,
    duration_seconds: float = 2.0,
    width: int = 320,
    height: int = 240,
    fps: int = 30
) -> Path:
    """Create a test Y4M video file for fake camera testing."""
    if filepath is None:
        filepath = Path(tempfile.mktemp(suffix='.y4m'))
    
    total_frames = int(fps * duration_seconds)
    
    # Y4M header
    header = f"YUV4MPEG2 W{width} H{height} F{fps}:1 Ip A1:1 C420\n"
    
    with open(filepath, 'wb') as f:
        f.write(header.encode('ascii'))
        
        # Generate frames with SMPTE color bars
        bar_width = width // 7
        colors = [235, 210, 170, 145, 106, 81, 41]  # Y values for SMPTE bars
        
        for frame_num in range(total_frames):
            # Frame header
            f.write(b"FRAME\n")
            
            # Y plane (luminance)
            y_data = []
            for y in range(height):
                for x in range(width):
                    bar_index = min(x // bar_width, 6)
                    # Add slight animation by shifting colors
                    color_idx = (bar_index + frame_num // 10) % 7
                    y_data.append(colors[color_idx])
            f.write(bytes(y_data))
            
            # U and V planes (chrominance) - half resolution for 4:2:0
            uv_size = (width // 2) * (height // 2)
            # U plane (blue-yellow)
            u_data = [128] * uv_size  # Neutral
            f.write(bytes(u_data))
            # V plane (red-green)
            v_data = [128] * uv_size  # Neutral
            f.write(bytes(v_data))
    
    print(f"  📹 Created Y4M: {filepath} ({width}x{height}, {fps}fps, {filepath.stat().st_size} bytes)")
    return filepath


async def test_fake_microphone_wav():
    """Test fake microphone with WAV file."""
    print("\n🎤 Testing Fake Microphone with WAV")
    
    test_audio = create_test_wav_file(duration_seconds=3.0, frequency=440)
    
    playwright = await async_playwright().start()
    try:
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
        
        # Simple test page
        await page.goto("""data:text/html,
            <h1>Microphone Test</h1>
            <button id='start'>Start Mic</button>
            <div id='status'>Ready</div>
        """)
        
        # Test getUserMedia
        result = await page.evaluate("""
            async () => {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    const tracks = stream.getAudioTracks();
                    document.getElementById('status').textContent = 'Microphone Active';
                    const info = {
                        success: true,
                        tracks: tracks.length,
                        label: tracks[0]?.label || 'Unknown'
                    };
                    tracks.forEach(t => t.stop());
                    return info;
                } catch (e) {
                    document.getElementById('status').textContent = 'Error: ' + e.message;
                    return { success: false, error: e.message };
                }
            }
        """)
        
        print(f"  Result: {result}")
        assert result['success'], f"Failed: {result.get('error')}"
        print(f"  ✅ Audio stream working: {result['tracks']} track(s)")
        
        await page.wait_for_timeout(1000)
        await browser.close()
        
    finally:
        await playwright.stop()
        if test_audio.exists():
            test_audio.unlink()
    
    return True


async def test_fake_camera_y4m():
    """Test fake camera with Y4M file."""
    print("\n📹 Testing Fake Camera with Y4M")
    
    test_video = create_test_y4m_file(
        duration_seconds=2.0,
        width=640,
        height=480,
        fps=30
    )
    
    playwright = await async_playwright().start()
    try:
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
        
        # Test page with video element
        await page.goto("""data:text/html,
            <h1>Camera Test</h1>
            <video id='video' autoplay style='width:640px;height:480px;background:black;border:2px solid blue'></video>
            <div id='status'>Ready</div>
        """)
        
        # Start video stream
        result = await page.evaluate("""
            async () => {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
                    const video = document.getElementById('video');
                    video.srcObject = stream;
                    
                    // Wait for video to load
                    await new Promise((resolve, reject) => {
                        video.onloadedmetadata = () => {
                            document.getElementById('status').textContent = 'Video Streaming';
                            resolve();
                        };
                        setTimeout(() => reject('Timeout'), 5000);
                    });
                    
                    const tracks = stream.getVideoTracks();
                    return {
                        success: true,
                        tracks: tracks.length,
                        label: tracks[0]?.label || 'Unknown',
                        width: video.videoWidth,
                        height: video.videoHeight
                    };
                } catch (e) {
                    document.getElementById('status').textContent = 'Error: ' + e.message;
                    return { success: false, error: e.message };
                }
            }
        """)
        
        print(f"  Result: {result}")
        assert result['success'], f"Failed: {result.get('error')}"
        print(f"  ✅ Video stream working: {result.get('width', 0)}x{result.get('height', 0)}")
        
        await page.screenshot(path="y4m_test.png")
        print("  ✅ Screenshot captured")
        
        await page.wait_for_timeout(2000)
        await browser.close()
        
    finally:
        await playwright.stop()
        if test_video.exists():
            test_video.unlink()
        screenshot = Path("y4m_test.png")
        if screenshot.exists():
            screenshot.unlink()
    
    return True


async def test_combined_media():
    """Test both audio and video together."""
    print("\n🎬 Testing Combined Media (WAV + Y4M)")
    
    test_audio = create_test_wav_file(duration_seconds=3.0, frequency=880)
    test_video = create_test_y4m_file(duration_seconds=3.0, width=320, height=240)
    
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
        
        await page.goto("""data:text/html,
            <h1>Combined Media Test</h1>
            <video id='video' autoplay style='width:320px;height:240px;background:black'></video>
            <div id='status'>Ready</div>
            <div id='tracks'>Tracks: 0</div>
        """)
        
        result = await page.evaluate("""
            async () => {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ 
                        audio: true, 
                        video: true 
                    });
                    
                    document.getElementById('video').srcObject = stream;
                    
                    const audioTracks = stream.getAudioTracks();
                    const videoTracks = stream.getVideoTracks();
                    
                    document.getElementById('status').textContent = 'Streaming';
                    document.getElementById('tracks').textContent = 
                        `Audio: ${audioTracks.length}, Video: ${videoTracks.length}`;
                    
                    return {
                        success: true,
                        audio: audioTracks.length,
                        video: videoTracks.length,
                        active: stream.active
                    };
                } catch (e) {
                    document.getElementById('status').textContent = 'Error: ' + e.message;
                    return { success: false, error: e.message };
                }
            }
        """)
        
        print(f"  Result: {result}")
        assert result['success'], f"Failed: {result.get('error')}"
        assert result['audio'] > 0, "No audio tracks"
        assert result['video'] > 0, "No video tracks"
        print(f"  ✅ Both streams working - Audio: {result['audio']}, Video: {result['video']}")
        
        await page.wait_for_timeout(2000)
        await browser.close()
        
    finally:
        await playwright.stop()
        if test_audio.exists():
            test_audio.unlink()
        if test_video.exists():
            test_video.unlink()
    
    return True


async def test_webrtc_samples():
    """Test with real WebRTC samples page."""
    print("\n🌐 Testing with WebRTC Samples")
    
    test_audio = create_test_wav_file(duration_seconds=5.0, frequency=440)
    test_video = create_test_y4m_file(duration_seconds=5.0, width=640, height=480)
    
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
        
        # Test with getUserMedia sample
        await page.goto("https://webrtc.github.io/samples/src/content/getusermedia/gum/")
        print("  ✅ Navigated to WebRTC samples")
        
        # Click open camera button
        await page.click("button#showVideo")
        await page.wait_for_timeout(1000)
        
        # Check if video is streaming
        video_active = await page.evaluate("""
            () => {
                const video = document.querySelector('video#gum-local');
                return video && video.srcObject && video.srcObject.active;
            }
        """)
        
        print(f"  Video active: {video_active}")
        assert video_active, "Video stream not active"
        print("  ✅ WebRTC sample working with fake media")
        
        await page.screenshot(path="webrtc_sample.png")
        print("  ✅ Screenshot captured")
        
        await page.wait_for_timeout(2000)
        await browser.close()
        
    finally:
        await playwright.stop()
        if test_audio.exists():
            test_audio.unlink()
        if test_video.exists():
            test_video.unlink()
        screenshot = Path("webrtc_sample.png")
        if screenshot.exists():
            screenshot.unlink()
    
    return True


async def run_all_tests():
    """Run all media stream tests."""
    print("🎭 Media Stream Tests with Y4M Support")
    print("=" * 50)
    
    tests = [
        ("WAV Audio", test_fake_microphone_wav),
        ("Y4M Video", test_fake_camera_y4m),
        ("Combined Media", test_combined_media),
        ("WebRTC Samples", test_webrtc_samples)
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        try:
            await test_func()
            passed += 1
            print(f"✅ {name} PASSED\n")
        except Exception as e:
            print(f"❌ {name} FAILED: {e}\n")
    
    print("=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    print(f"\n{'🎉 ALL TESTS PASSED!' if success else '❌ SOME TESTS FAILED'}")
    sys.exit(0 if success else 1)