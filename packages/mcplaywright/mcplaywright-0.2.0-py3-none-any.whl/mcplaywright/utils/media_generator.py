"""
Media File Generator for Testing

Generates WAV audio and Y4M video files for WebRTC testing.
"""

import wave
import struct
import math
from pathlib import Path
import tempfile
import subprocess
import shutil
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def create_test_wav_file(
    filepath: Optional[Path] = None,
    duration_seconds: float = 2.0,
    frequency: int = 440,
    sample_rate: int = 44100
) -> Path:
    """
    Create a test WAV file with a sine wave tone.
    
    Args:
        filepath: Output file path (auto-generated if None)
        duration_seconds: Duration of the audio
        frequency: Frequency of the sine wave (Hz)
        sample_rate: Sample rate (Hz)
    
    Returns:
        Path to the created WAV file
    """
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
    
    logger.info(f"Created WAV file: {filepath} ({duration_seconds}s, {frequency}Hz)")
    return filepath


def create_test_y4m_file(
    filepath: Optional[Path] = None,
    duration_seconds: float = 2.0,
    width: int = 320,
    height: int = 240,
    fps: int = 30,
    pattern: str = "smpte"  # smpte, color_bars, checkerboard, noise
) -> Path:
    """
    Create a test Y4M video file for fake camera testing.
    
    Y4M (YUV4MPEG2) format is required by Chrome for fake video capture.
    
    Args:
        filepath: Output file path (auto-generated if None)
        duration_seconds: Duration of the video
        width: Video width in pixels
        height: Video height in pixels
        fps: Frames per second
        pattern: Test pattern type
    
    Returns:
        Path to the created Y4M file
    """
    if filepath is None:
        filepath = Path(tempfile.mktemp(suffix='.y4m'))
    
    total_frames = int(fps * duration_seconds)
    
    # Y4M header
    header = f"YUV4MPEG2 W{width} H{height} F{fps}:1 Ip A1:1 C420\n"
    
    with open(filepath, 'wb') as f:
        f.write(header.encode('ascii'))
        
        # Generate frames
        for frame_num in range(total_frames):
            # Frame header
            f.write(b"FRAME\n")
            
            # Generate Y (luminance) plane
            y_plane = _generate_y_plane(width, height, frame_num, total_frames, pattern)
            f.write(y_plane)
            
            # Generate U and V (chrominance) planes (half resolution for 4:2:0)
            u_plane = _generate_uv_plane(width // 2, height // 2, 128)  # Neutral
            v_plane = _generate_uv_plane(width // 2, height // 2, 128)  # Neutral
            f.write(u_plane)
            f.write(v_plane)
    
    logger.info(f"Created Y4M file: {filepath} ({duration_seconds}s, {width}x{height}, {pattern})")
    return filepath


def _generate_y_plane(width: int, height: int, frame: int, total_frames: int, pattern: str) -> bytes:
    """Generate Y (luminance) plane for a frame."""
    pixels = []
    
    if pattern == "smpte":
        # SMPTE color bars
        bar_width = width // 7
        colors = [235, 210, 170, 145, 106, 81, 41]  # Y values for color bars
        
        for y in range(height):
            for x in range(width):
                bar_index = min(x // bar_width, 6)
                pixels.append(colors[bar_index])
                
    elif pattern == "checkerboard":
        # Animated checkerboard
        square_size = 32
        offset = (frame * 2) % square_size
        
        for y in range(height):
            for x in range(width):
                checker = ((x + offset) // square_size + y // square_size) % 2
                pixels.append(235 if checker else 16)
                
    elif pattern == "gradient":
        # Horizontal gradient that shifts
        shift = int((frame / total_frames) * 255)
        
        for y in range(height):
            for x in range(width):
                value = (x * 255 // width + shift) % 255
                pixels.append(min(max(value, 16), 235))
                
    else:  # noise or default
        # Simple noise pattern (actually just alternating)
        import random
        random.seed(frame)
        for _ in range(width * height):
            pixels.append(random.randint(16, 235))
    
    return bytes(pixels)


def _generate_uv_plane(width: int, height: int, value: int) -> bytes:
    """Generate U or V (chrominance) plane."""
    return bytes([value] * (width * height))


def create_test_y4m_with_ffmpeg(
    filepath: Optional[Path] = None,
    duration_seconds: float = 2.0,
    width: int = 320,
    height: int = 240,
    fps: int = 30,
    pattern: str = "testsrc"
) -> Optional[Path]:
    """
    Create Y4M file using FFmpeg (if available).
    
    Args:
        filepath: Output file path
        duration_seconds: Duration
        width: Video width
        height: Video height  
        fps: Frames per second
        pattern: FFmpeg test source pattern
    
    Returns:
        Path to created file or None if FFmpeg not available
    """
    if not shutil.which('ffmpeg'):
        logger.warning("FFmpeg not found, cannot use FFmpeg method")
        return None
    
    if filepath is None:
        filepath = Path(tempfile.mktemp(suffix='.y4m'))
    
    # FFmpeg command to generate Y4M test video
    cmd = [
        'ffmpeg',
        '-f', 'lavfi',
        '-i', f'{pattern}=duration={duration_seconds}:size={width}x{height}:rate={fps}',
        '-pix_fmt', 'yuv420p',
        '-f', 'yuv4mpegpipe',
        '-y',
        str(filepath)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            logger.info(f"Created Y4M with FFmpeg: {filepath}")
            return filepath
        else:
            logger.error(f"FFmpeg failed: {result.stderr}")
            return None
    except subprocess.TimeoutExpired:
        logger.error("FFmpeg timeout")
        return None
    except Exception as e:
        logger.error(f"FFmpeg error: {e}")
        return None


def download_sample_audio(url: str = None) -> Optional[Path]:
    """
    Download a sample audio file for testing.
    
    Args:
        url: URL to download from (uses default if None)
    
    Returns:
        Path to downloaded file or None if failed
    """
    import urllib.request
    
    if url is None:
        # Use a royalty-free sample
        url = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
    
    try:
        output_path = Path(tempfile.mktemp(suffix='.mp3'))
        urllib.request.urlretrieve(url, output_path)
        
        # Convert to WAV if needed
        if output_path.suffix != '.wav':
            wav_path = output_path.with_suffix('.wav')
            if convert_to_wav(output_path, wav_path):
                output_path.unlink()  # Remove original
                return wav_path
        
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to download audio: {e}")
        return None


def convert_to_wav(input_file: Path, output_file: Path) -> bool:
    """
    Convert audio file to WAV format using FFmpeg.
    
    Args:
        input_file: Input audio file
        output_file: Output WAV file path
    
    Returns:
        True if successful, False otherwise
    """
    if not shutil.which('ffmpeg'):
        logger.warning("FFmpeg not found, cannot convert audio")
        return False
    
    cmd = [
        'ffmpeg',
        '-i', str(input_file),
        '-acodec', 'pcm_s16le',
        '-ar', '44100',
        '-ac', '1',
        '-y',
        str(output_file)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Audio conversion failed: {e}")
        return False


def create_media_test_suite() -> Tuple[Path, Path]:
    """
    Create a complete set of test media files.
    
    Returns:
        Tuple of (audio_file, video_file) paths
    """
    # Create test audio (440Hz tone for 3 seconds)
    audio_file = create_test_wav_file(
        duration_seconds=3.0,
        frequency=440
    )
    
    # Create test video (SMPTE color bars)
    video_file = create_test_y4m_file(
        duration_seconds=3.0,
        pattern="smpte"
    )
    
    logger.info(f"Created test suite: audio={audio_file}, video={video_file}")
    return audio_file, video_file


def cleanup_test_files(*files: Path):
    """Clean up test files."""
    for file in files:
        if file and file.exists():
            try:
                file.unlink()
                logger.debug(f"Cleaned up: {file}")
            except Exception as e:
                logger.warning(f"Failed to clean up {file}: {e}")


# Audio capture capabilities (for future implementation)
class AudioCapture:
    """
    Audio capture from microphone or system audio.
    Placeholder for future implementation.
    """
    
    @staticmethod
    def list_audio_devices():
        """List available audio input devices."""
        # This would use pyaudio or sounddevice
        return ["Default Microphone", "System Audio (if available)"]
    
    @staticmethod
    def capture_microphone(output_file: Path, duration: float = 5.0):
        """Capture audio from microphone."""
        # Would implement actual capture using pyaudio
        logger.info(f"Would capture {duration}s of microphone audio to {output_file}")
        # For now, create a test file
        return create_test_wav_file(output_file, duration, frequency=880)
    
    @staticmethod
    def capture_system_audio(output_file: Path, duration: float = 5.0):
        """Capture system audio output."""
        # Would implement loopback capture
        logger.info(f"Would capture {duration}s of system audio to {output_file}")
        # For now, create a test file
        return create_test_wav_file(output_file, duration, frequency=660)


if __name__ == "__main__":
    # Test media generation
    print("Testing media file generation...")
    
    # Create test files
    audio, video = create_media_test_suite()
    print(f"Created audio: {audio} ({audio.stat().st_size} bytes)")
    print(f"Created video: {video} ({video.stat().st_size} bytes)")
    
    # Test FFmpeg method if available
    ffmpeg_video = create_test_y4m_with_ffmpeg()
    if ffmpeg_video:
        print(f"Created with FFmpeg: {ffmpeg_video} ({ffmpeg_video.stat().st_size} bytes)")
        cleanup_test_files(ffmpeg_video)
    
    # Cleanup
    cleanup_test_files(audio, video)
    print("Test complete!")