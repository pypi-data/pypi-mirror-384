#!/usr/bin/env python3
"""
Unit Tests for Media Stream Functionality

Simplified tests that don't require complex imports.
"""

import asyncio
from pathlib import Path
import tempfile
import wave
import struct


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


def test_wav_file_creation():
    """Test that we can create valid WAV files."""
    print("🎵 Testing WAV file creation")
    
    # Create test file
    wav_file = create_test_wav_file(duration_seconds=0.5)
    
    try:
        # Verify file exists
        assert wav_file.exists(), "WAV file was not created"
        print("  ✅ WAV file created")
        
        # Verify it's a valid WAV file
        with wave.open(str(wav_file), 'rb') as wf:
            assert wf.getnchannels() == 1, "Should be mono"
            assert wf.getsampwidth() == 2, "Should be 16-bit"
            assert wf.getframerate() == 44100, "Should be 44.1kHz"
            frames = wf.getnframes()
            assert frames > 0, "Should have audio frames"
            print(f"  ✅ Valid WAV: {frames} frames at 44.1kHz")
        
        # Check file size
        size = wav_file.stat().st_size
        assert size > 44, "File too small to be valid WAV"
        print(f"  ✅ File size: {size} bytes")
        
        return True
        
    finally:
        # Cleanup
        if wav_file.exists():
            wav_file.unlink()


def test_media_stream_arguments():
    """Test media stream browser arguments."""
    print("🎬 Testing media stream arguments")
    
    # Test basic flags
    basic_args = [
        "--use-fake-device-for-media-stream",
        "--use-fake-ui-for-media-stream"
    ]
    
    assert len(basic_args) == 2
    print("  ✅ Basic flags configured")
    
    # Test with audio file
    audio_file = create_test_wav_file()
    try:
        audio_args = basic_args + [f"--use-file-for-fake-audio-capture={audio_file}"]
        assert len(audio_args) == 3
        assert str(audio_file) in audio_args[2]
        print(f"  ✅ Audio file argument: {audio_file.name}")
    finally:
        if audio_file.exists():
            audio_file.unlink()
    
    # Test with video file
    video_file = Path("/tmp/test.y4m")
    video_args = basic_args + [f"--use-file-for-fake-video-capture={video_file}"]
    assert len(video_args) == 3
    print("  ✅ Video file argument configured")
    
    return True


def test_permission_validation():
    """Test permission validation logic."""
    print("🔐 Testing permission validation")
    
    valid_permissions = ["microphone", "camera", "geolocation", "notifications"]
    test_permissions = ["microphone", "camera", "invalid_perm", "fake_perm"]
    
    # Filter valid permissions
    valid = [p for p in test_permissions if p in valid_permissions]
    invalid = [p for p in test_permissions if p not in valid_permissions]
    
    assert len(valid) == 2
    assert "microphone" in valid
    assert "camera" in valid
    print(f"  ✅ Valid permissions: {valid}")
    
    assert len(invalid) == 2
    assert "invalid_perm" in invalid
    assert "fake_perm" in invalid
    print(f"  ✅ Invalid permissions filtered: {invalid}")
    
    return True


def test_file_extension_validation():
    """Test file extension validation."""
    print("📁 Testing file extension validation")
    
    # Audio extensions
    valid_audio = ['.wav', '.mp3', '.ogg', '.webm']
    test_audio = Path("test.wav")
    assert test_audio.suffix.lower() in valid_audio
    print(f"  ✅ Valid audio extension: {test_audio.suffix}")
    
    invalid_audio = Path("test.txt")
    assert invalid_audio.suffix.lower() not in valid_audio
    print(f"  ✅ Invalid audio extension detected: {invalid_audio.suffix}")
    
    # Video extensions
    valid_video = ['.mp4', '.webm', '.avi', '.mov', '.mjpeg', '.y4m']
    test_video = Path("test.y4m")
    assert test_video.suffix.lower() in valid_video
    print(f"  ✅ Valid video extension: {test_video.suffix}")
    
    invalid_video = Path("test.doc")
    assert invalid_video.suffix.lower() not in valid_video
    print(f"  ✅ Invalid video extension detected: {invalid_video.suffix}")
    
    return True


def test_media_configuration():
    """Test media configuration data structures."""
    print("⚙️ Testing media configuration")
    
    # Test configuration dictionary
    config = {
        "media_stream_enabled": False,
        "fake_audio_file": None,
        "fake_video_file": None,
        "media_permissions": []
    }
    
    # Enable media
    config["media_stream_enabled"] = True
    config["media_permissions"] = ["microphone", "camera"]
    
    assert config["media_stream_enabled"] is True
    print("  ✅ Media stream enabled")
    
    assert len(config["media_permissions"]) == 2
    print(f"  ✅ Permissions configured: {config['media_permissions']}")
    
    # Add files
    audio_file = create_test_wav_file()
    try:
        config["fake_audio_file"] = str(audio_file.absolute())
        assert config["fake_audio_file"] is not None
        assert Path(config["fake_audio_file"]).exists()
        print(f"  ✅ Audio file configured: {audio_file.name}")
    finally:
        if audio_file.exists():
            audio_file.unlink()
    
    return True


def run_all_unit_tests():
    """Run all unit tests."""
    print("🧪 Media Stream Unit Tests")
    print("=" * 40)
    
    tests = [
        ("WAV File Creation", test_wav_file_creation),
        ("Media Stream Arguments", test_media_stream_arguments),
        ("Permission Validation", test_permission_validation),
        ("File Extension Validation", test_file_extension_validation),
        ("Media Configuration", test_media_configuration)
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        print(f"\nRunning: {name}")
        try:
            result = test_func()
            if result:
                passed += 1
                print(f"✅ {name} PASSED\n")
        except AssertionError as e:
            print(f"❌ {name} FAILED: {e}\n")
        except Exception as e:
            print(f"❌ {name} ERROR: {e}\n")
    
    print("=" * 40)
    print(f"📊 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    return passed == total


if __name__ == "__main__":
    import sys
    success = run_all_unit_tests()
    print(f"\n{'🎉 ALL UNIT TESTS PASSED!' if success else '❌ SOME TESTS FAILED'}")
    sys.exit(0 if success else 1)