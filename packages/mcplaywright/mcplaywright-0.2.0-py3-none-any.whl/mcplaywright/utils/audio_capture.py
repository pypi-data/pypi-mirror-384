"""
Audio Capture Utilities for MCPlaywright

Implements browser-based audio capture using JavaScript injection.
Leverages the same injection techniques used by the MCP client identification system.
"""

from typing import Dict, Any, Optional, List
import logging
import base64
import json

logger = logging.getLogger(__name__)


class BrowserAudioCapture:
    """
    Browser-based audio capture using Web Audio API.
    
    This solves the OS compatibility problem by using JavaScript
    to capture audio directly in the browser, similar to how we
    inject code for client identification.
    """
    
    @staticmethod
    def get_audio_capture_script() -> str:
        """
        Get JavaScript code for audio capture functionality.
        
        Returns:
            JavaScript code to inject into the page
        """
        return """
        // MCPlaywright Audio Capture System
        window.MCPAudioCapture = {
            context: null,
            recorder: null,
            chunks: [],
            stream: null,
            analyser: null,
            isRecording: false,
            volumeHistory: [],
            
            // Initialize audio capture
            async init(options = {}) {
                try {
                    // Create audio context
                    this.context = new (window.AudioContext || window.webkitAudioContext)();
                    
                    // Get user media (microphone)
                    this.stream = await navigator.mediaDevices.getUserMedia({
                        audio: {
                            echoCancellation: options.echoCancellation ?? false,
                            noiseSuppression: options.noiseSuppression ?? false,
                            autoGainControl: options.autoGainControl ?? false,
                            sampleRate: options.sampleRate || 48000
                        }
                    });
                    
                    // Create media recorder
                    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus') 
                        ? 'audio/webm;codecs=opus' 
                        : 'audio/webm';
                    
                    this.recorder = new MediaRecorder(this.stream, {
                        mimeType: mimeType,
                        audioBitsPerSecond: options.bitrate || 128000
                    });
                    
                    // Set up analyser for volume monitoring
                    const source = this.context.createMediaStreamSource(this.stream);
                    this.analyser = this.context.createAnalyser();
                    this.analyser.fftSize = 256;
                    source.connect(this.analyser);
                    
                    // Handle data available
                    this.recorder.ondataavailable = (event) => {
                        if (event.data.size > 0) {
                            this.chunks.push(event.data);
                        }
                    };
                    
                    console.log('🎤 MCPAudioCapture initialized');
                    return { success: true, mimeType: mimeType };
                    
                } catch (error) {
                    console.error('Failed to initialize audio capture:', error);
                    return { success: false, error: error.message };
                }
            },
            
            // Start recording
            startRecording() {
                if (!this.recorder) {
                    return { success: false, error: 'Not initialized' };
                }
                
                this.chunks = [];
                this.volumeHistory = [];
                this.isRecording = true;
                
                // Start recorder
                this.recorder.start(100); // Collect data every 100ms
                
                // Start volume monitoring
                this.monitorVolume();
                
                console.log('🔴 Recording started');
                return { success: true };
            },
            
            // Stop recording and return audio data
            async stopRecording() {
                if (!this.recorder || !this.isRecording) {
                    return { success: false, error: 'Not recording' };
                }
                
                this.isRecording = false;
                
                return new Promise((resolve) => {
                    this.recorder.onstop = async () => {
                        // Create blob from chunks
                        const blob = new Blob(this.chunks, { type: this.recorder.mimeType });
                        
                        // Convert to base64 for easy transfer
                        const reader = new FileReader();
                        reader.onloadend = () => {
                            const base64 = reader.result.split(',')[1];
                            
                            resolve({
                                success: true,
                                data: base64,
                                mimeType: this.recorder.mimeType,
                                size: blob.size,
                                duration: this.chunks.length * 0.1, // Approximate
                                volumeHistory: this.volumeHistory
                            });
                        };
                        reader.readAsDataURL(blob);
                        
                        console.log('⏹️ Recording stopped');
                    };
                    
                    this.recorder.stop();
                });
            },
            
            // Monitor audio volume
            monitorVolume() {
                if (!this.isRecording || !this.analyser) return;
                
                const dataArray = new Uint8Array(this.analyser.frequencyBinCount);
                this.analyser.getByteFrequencyData(dataArray);
                
                // Calculate RMS volume
                let sum = 0;
                for (let i = 0; i < dataArray.length; i++) {
                    sum += dataArray[i] * dataArray[i];
                }
                const volume = Math.sqrt(sum / dataArray.length);
                
                this.volumeHistory.push({
                    timestamp: Date.now(),
                    volume: volume
                });
                
                // Keep only last 1000 samples
                if (this.volumeHistory.length > 1000) {
                    this.volumeHistory.shift();
                }
                
                // Continue monitoring
                if (this.isRecording) {
                    requestAnimationFrame(() => this.monitorVolume());
                }
            },
            
            // Get current volume level
            getCurrentVolume() {
                if (!this.analyser) return 0;
                
                const dataArray = new Uint8Array(this.analyser.frequencyBinCount);
                this.analyser.getByteFrequencyData(dataArray);
                
                let sum = 0;
                for (let i = 0; i < dataArray.length; i++) {
                    sum += dataArray[i] * dataArray[i];
                }
                return Math.sqrt(sum / dataArray.length);
            },
            
            // Get volume statistics
            getVolumeStats() {
                if (this.volumeHistory.length === 0) {
                    return { average: 0, max: 0, min: 0 };
                }
                
                const volumes = this.volumeHistory.map(h => h.volume);
                return {
                    average: volumes.reduce((a, b) => a + b, 0) / volumes.length,
                    max: Math.max(...volumes),
                    min: Math.min(...volumes),
                    current: this.getCurrentVolume()
                };
            },
            
            // Clean up resources
            cleanup() {
                if (this.stream) {
                    this.stream.getTracks().forEach(track => track.stop());
                    this.stream = null;
                }
                if (this.context) {
                    this.context.close();
                    this.context = null;
                }
                this.recorder = null;
                this.analyser = null;
                this.chunks = [];
                this.volumeHistory = [];
                this.isRecording = false;
                
                console.log('🧹 Audio capture cleaned up');
            }
        };
        
        // Also inject audio output capture for browser audio
        window.MCPAudioOutput = {
            context: null,
            destination: null,
            recorder: null,
            chunks: [],
            isCapturing: false,
            
            // Capture audio from page elements
            async captureElementAudio(selector) {
                try {
                    const element = document.querySelector(selector);
                    if (!element || !element.captureStream) {
                        return { success: false, error: 'Element not found or captureStream not supported' };
                    }
                    
                    // Get stream from element (video/audio tag)
                    const stream = element.captureStream();
                    
                    // Create recorder
                    this.recorder = new MediaRecorder(stream);
                    this.chunks = [];
                    
                    this.recorder.ondataavailable = (event) => {
                        if (event.data.size > 0) {
                            this.chunks.push(event.data);
                        }
                    };
                    
                    this.recorder.start(100);
                    this.isCapturing = true;
                    
                    console.log('🎵 Capturing audio from element:', selector);
                    return { success: true };
                    
                } catch (error) {
                    console.error('Failed to capture element audio:', error);
                    return { success: false, error: error.message };
                }
            },
            
            // Stop capturing and get audio
            async stopCapture() {
                if (!this.recorder || !this.isCapturing) {
                    return { success: false, error: 'Not capturing' };
                }
                
                this.isCapturing = false;
                
                return new Promise((resolve) => {
                    this.recorder.onstop = async () => {
                        const blob = new Blob(this.chunks, { type: 'audio/webm' });
                        
                        const reader = new FileReader();
                        reader.onloadend = () => {
                            const base64 = reader.result.split(',')[1];
                            resolve({
                                success: true,
                                data: base64,
                                size: blob.size
                            });
                        };
                        reader.readAsDataURL(blob);
                    };
                    
                    this.recorder.stop();
                });
            }
        };
        
        // Visual indicator for recording status
        window.MCPAudioCapture.showRecordingIndicator = function(show = true) {
            let indicator = document.getElementById('mcp-recording-indicator');
            
            if (show && !indicator) {
                indicator = document.createElement('div');
                indicator.id = 'mcp-recording-indicator';
                indicator.innerHTML = '🔴 REC';
                indicator.style.cssText = `
                    position: fixed;
                    top: 10px;
                    right: 10px;
                    background: rgba(255, 0, 0, 0.9);
                    color: white;
                    padding: 5px 10px;
                    border-radius: 5px;
                    font-family: monospace;
                    font-size: 14px;
                    z-index: 999999;
                    animation: pulse 1s infinite;
                `;
                
                const style = document.createElement('style');
                style.textContent = `
                    @keyframes pulse {
                        0% { opacity: 1; }
                        50% { opacity: 0.5; }
                        100% { opacity: 1; }
                    }
                `;
                document.head.appendChild(style);
                document.body.appendChild(indicator);
                
            } else if (!show && indicator) {
                indicator.remove();
            }
        };
        
        console.log('🎙️ MCPAudioCapture and MCPAudioOutput loaded');
        """
    
    @staticmethod
    def get_volume_visualizer_script() -> str:
        """
        Get JavaScript for audio volume visualization.
        
        Returns:
            JavaScript code for volume meter
        """
        return """
        // Audio Volume Visualizer
        window.MCPVolumeVisualizer = {
            canvas: null,
            ctx: null,
            animationId: null,
            
            create(selector = '#volume-meter') {
                // Find or create canvas
                this.canvas = document.querySelector(selector);
                if (!this.canvas) {
                    this.canvas = document.createElement('canvas');
                    this.canvas.id = 'volume-meter';
                    this.canvas.width = 200;
                    this.canvas.height = 50;
                    this.canvas.style.cssText = `
                        position: fixed;
                        bottom: 10px;
                        right: 10px;
                        background: rgba(0, 0, 0, 0.8);
                        border: 1px solid #333;
                        border-radius: 5px;
                        z-index: 999998;
                    `;
                    document.body.appendChild(this.canvas);
                }
                
                this.ctx = this.canvas.getContext('2d');
                this.startVisualization();
            },
            
            startVisualization() {
                const draw = () => {
                    if (!window.MCPAudioCapture || !window.MCPAudioCapture.analyser) {
                        this.animationId = requestAnimationFrame(draw);
                        return;
                    }
                    
                    const bufferLength = window.MCPAudioCapture.analyser.frequencyBinCount;
                    const dataArray = new Uint8Array(bufferLength);
                    window.MCPAudioCapture.analyser.getByteFrequencyData(dataArray);
                    
                    // Clear canvas
                    this.ctx.fillStyle = 'rgba(0, 0, 0, 0.2)';
                    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
                    
                    // Draw frequency bars
                    const barWidth = (this.canvas.width / bufferLength) * 2.5;
                    let x = 0;
                    
                    for (let i = 0; i < bufferLength; i++) {
                        const barHeight = (dataArray[i] / 255) * this.canvas.height;
                        
                        // Color based on intensity
                        const r = barHeight + 25 * (i / bufferLength);
                        const g = 250 * (i / bufferLength);
                        const b = 50;
                        
                        this.ctx.fillStyle = `rgb(${r}, ${g}, ${b})`;
                        this.ctx.fillRect(x, this.canvas.height - barHeight, barWidth, barHeight);
                        
                        x += barWidth + 1;
                    }
                    
                    this.animationId = requestAnimationFrame(draw);
                };
                
                draw();
            },
            
            stop() {
                if (this.animationId) {
                    cancelAnimationFrame(this.animationId);
                    this.animationId = null;
                }
                if (this.canvas) {
                    this.canvas.remove();
                    this.canvas = null;
                }
            }
        };
        """
    
    @staticmethod
    def create_audio_test_page() -> str:
        """
        Create a complete HTML page for audio testing.
        
        Returns:
            HTML content for audio test page
        """
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>MCPlaywright Audio Test</title>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }
                .container {
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 10px;
                    padding: 30px;
                    backdrop-filter: blur(10px);
                }
                h1 {
                    text-align: center;
                    margin-bottom: 30px;
                }
                .controls {
                    display: flex;
                    gap: 10px;
                    justify-content: center;
                    margin: 20px 0;
                }
                button {
                    padding: 10px 20px;
                    font-size: 16px;
                    border: none;
                    border-radius: 5px;
                    background: white;
                    color: #667eea;
                    cursor: pointer;
                    transition: transform 0.2s;
                }
                button:hover {
                    transform: scale(1.05);
                }
                button:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                }
                #status {
                    text-align: center;
                    margin: 20px 0;
                    font-size: 18px;
                }
                #volume {
                    text-align: center;
                    font-size: 24px;
                    margin: 20px 0;
                }
                .meter {
                    width: 100%;
                    height: 30px;
                    background: rgba(0, 0, 0, 0.3);
                    border-radius: 15px;
                    overflow: hidden;
                    margin: 20px 0;
                }
                .meter-fill {
                    height: 100%;
                    background: linear-gradient(90deg, #00ff00, #ffff00, #ff0000);
                    width: 0%;
                    transition: width 0.1s;
                }
                audio {
                    width: 100%;
                    margin: 20px 0;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎤 MCPlaywright Audio Capture Test</h1>
                
                <div id="status">Ready to record</div>
                
                <div class="controls">
                    <button id="init">Initialize</button>
                    <button id="start" disabled>Start Recording</button>
                    <button id="stop" disabled>Stop Recording</button>
                    <button id="play" disabled>Play Recording</button>
                </div>
                
                <div class="meter">
                    <div class="meter-fill" id="meter-fill"></div>
                </div>
                
                <div id="volume">Volume: 0</div>
                
                <audio id="playback" controls style="display: none;"></audio>
                
                <div id="stats" style="margin-top: 20px;"></div>
            </div>
            
            <script>
                // UI Elements
                const status = document.getElementById('status');
                const initBtn = document.getElementById('init');
                const startBtn = document.getElementById('start');
                const stopBtn = document.getElementById('stop');
                const playBtn = document.getElementById('play');
                const volumeDisplay = document.getElementById('volume');
                const meterFill = document.getElementById('meter-fill');
                const playback = document.getElementById('playback');
                const stats = document.getElementById('stats');
                
                let recordedBlob = null;
                let volumeInterval = null;
                
                // Initialize audio capture
                initBtn.addEventListener('click', async () => {
                    status.textContent = 'Initializing...';
                    
                    const result = await window.MCPAudioCapture.init({
                        echoCancellation: false,
                        noiseSuppression: false,
                        autoGainControl: false
                    });
                    
                    if (result.success) {
                        status.textContent = 'Ready to record';
                        initBtn.disabled = true;
                        startBtn.disabled = false;
                        
                        // Create visualizer
                        window.MCPVolumeVisualizer.create();
                    } else {
                        status.textContent = `Error: ${result.error}`;
                    }
                });
                
                // Start recording
                startBtn.addEventListener('click', () => {
                    const result = window.MCPAudioCapture.startRecording();
                    
                    if (result.success) {
                        status.textContent = '🔴 Recording...';
                        startBtn.disabled = true;
                        stopBtn.disabled = false;
                        
                        // Show recording indicator
                        window.MCPAudioCapture.showRecordingIndicator(true);
                        
                        // Start volume monitoring
                        volumeInterval = setInterval(() => {
                            const volume = window.MCPAudioCapture.getCurrentVolume();
                            volumeDisplay.textContent = `Volume: ${Math.round(volume)}`;
                            meterFill.style.width = `${Math.min(100, volume)}%`;
                        }, 100);
                    }
                });
                
                // Stop recording
                stopBtn.addEventListener('click', async () => {
                    status.textContent = 'Processing...';
                    
                    // Stop volume monitoring
                    clearInterval(volumeInterval);
                    volumeDisplay.textContent = 'Volume: 0';
                    meterFill.style.width = '0%';
                    
                    // Hide recording indicator
                    window.MCPAudioCapture.showRecordingIndicator(false);
                    
                    const result = await window.MCPAudioCapture.stopRecording();
                    
                    if (result.success) {
                        status.textContent = 'Recording complete';
                        stopBtn.disabled = true;
                        startBtn.disabled = false;
                        playBtn.disabled = false;
                        
                        // Convert base64 to blob
                        const byteCharacters = atob(result.data);
                        const byteNumbers = new Array(byteCharacters.length);
                        for (let i = 0; i < byteCharacters.length; i++) {
                            byteNumbers[i] = byteCharacters.charCodeAt(i);
                        }
                        const byteArray = new Uint8Array(byteNumbers);
                        recordedBlob = new Blob([byteArray], { type: result.mimeType });
                        
                        // Show stats
                        const volumeStats = window.MCPAudioCapture.getVolumeStats();
                        stats.innerHTML = `
                            <h3>Recording Statistics</h3>
                            <p>Size: ${(result.size / 1024).toFixed(2)} KB</p>
                            <p>Duration: ~${result.duration.toFixed(1)} seconds</p>
                            <p>Average Volume: ${volumeStats.average.toFixed(1)}</p>
                            <p>Max Volume: ${volumeStats.max.toFixed(1)}</p>
                            <p>Min Volume: ${volumeStats.min.toFixed(1)}</p>
                        `;
                    }
                });
                
                // Play recording
                playBtn.addEventListener('click', () => {
                    if (recordedBlob) {
                        const url = URL.createObjectURL(recordedBlob);
                        playback.src = url;
                        playback.style.display = 'block';
                        playback.play();
                    }
                });
            </script>
        </body>
        </html>
        """


# Example functions for MCP tools
async def inject_audio_capture(page) -> Dict[str, Any]:
    """
    Inject audio capture capabilities into a page.
    
    Args:
        page: Playwright page object
    
    Returns:
        Result dictionary
    """
    try:
        # Inject the audio capture script
        script = BrowserAudioCapture.get_audio_capture_script()
        await page.evaluate(script)
        
        # Also inject visualizer
        visualizer_script = BrowserAudioCapture.get_volume_visualizer_script()
        await page.evaluate(visualizer_script)
        
        logger.info("Audio capture capabilities injected")
        return {
            "status": "success",
            "message": "Audio capture ready"
        }
        
    except Exception as e:
        logger.error(f"Failed to inject audio capture: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


async def start_browser_audio_recording(page, options: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Start recording audio in the browser.
    
    Args:
        page: Playwright page object
        options: Recording options
    
    Returns:
        Result dictionary
    """
    try:
        # Initialize if needed
        init_result = await page.evaluate("""
            async () => {
                if (!window.MCPAudioCapture) {
                    return { success: false, error: 'Audio capture not injected' };
                }
                
                if (!window.MCPAudioCapture.context) {
                    return await window.MCPAudioCapture.init();
                }
                
                return { success: true };
            }
        """)
        
        if not init_result.get('success'):
            return {
                "status": "error",
                "message": init_result.get('error', 'Initialization failed')
            }
        
        # Start recording
        result = await page.evaluate("window.MCPAudioCapture.startRecording()")
        
        if result.get('success'):
            return {
                "status": "success",
                "message": "Recording started"
            }
        else:
            return {
                "status": "error",
                "message": result.get('error', 'Failed to start recording')
            }
            
    except Exception as e:
        logger.error(f"Failed to start recording: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


async def stop_browser_audio_recording(page) -> Dict[str, Any]:
    """
    Stop recording and get audio data.
    
    Args:
        page: Playwright page object
    
    Returns:
        Result dictionary with audio data
    """
    try:
        result = await page.evaluate("window.MCPAudioCapture.stopRecording()")
        
        if result.get('success'):
            return {
                "status": "success",
                "message": "Recording stopped",
                "data": result.get('data'),  # Base64 encoded audio
                "mimeType": result.get('mimeType'),
                "size": result.get('size'),
                "duration": result.get('duration'),
                "volumeStats": await page.evaluate("window.MCPAudioCapture.getVolumeStats()")
            }
        else:
            return {
                "status": "error",
                "message": result.get('error', 'Failed to stop recording')
            }
            
    except Exception as e:
        logger.error(f"Failed to stop recording: {e}")
        return {
            "status": "error",
            "message": str(e)
        }