"""
Voice Communication System for AI-Human Collaboration

Enables real-time voice communication between AI models and users during
browser automation using Web Speech API and Speech Synthesis API.
"""

from typing import Dict, Any, Optional, Callable
from pydantic import BaseModel
from playwright.async_api import Page
import json

class VoiceSettings(BaseModel):
    """Voice communication configuration"""
    voice_enabled: bool = True
    speech_rate: float = 1.0  # 0.1 to 10
    speech_pitch: float = 1.0  # 0 to 2
    speech_volume: float = 0.8  # 0 to 1
    voice_name: Optional[str] = None  # Specific voice to use
    language: str = "en-US"
    continuous_listening: bool = False

class VoiceCommunication:
    """
    Voice communication system enabling AI models to speak to users
    and listen for voice responses during browser automation.
    
    Features both text-to-speech output and speech recognition input
    with Web Speech API integration.
    """
    
    VOICE_SCRIPT = """
// MCP Voice Communication System
// Real-time voice chat during browser automation

if (typeof window.mcpVoiceInit === 'undefined') {
    window.mcpVoiceInit = true;
    
    class MCPVoiceSystem {
        constructor() {
            this.speechSynthesis = window.speechSynthesis;
            this.speechRecognition = null;
            this.isListening = false;
            this.settings = {
                voiceEnabled: true,
                speechRate: 1.0,
                speechPitch: 1.0,
                speechVolume: 0.8,
                voiceName: null,
                language: 'en-US',
                continuousListening: false
            };
            this.onVoiceResult = null;
            this.currentUtterance = null;
            
            this.initializeSpeechRecognition();
            this.createVoiceControls();
        }
        
        initializeSpeechRecognition() {
            // Initialize Speech Recognition API
            if ('webkitSpeechRecognition' in window) {
                this.speechRecognition = new webkitSpeechRecognition();
            } else if ('SpeechRecognition' in window) {
                this.speechRecognition = new SpeechRecognition();
            } else {
                console.warn('Speech Recognition not supported in this browser');
                return;
            }
            
            const recognition = this.speechRecognition;
            recognition.continuous = true;
            recognition.interimResults = true;
            recognition.lang = this.settings.language;
            
            recognition.onstart = () => {
                this.isListening = true;
                this.updateVoiceStatus('🎤 LISTENING...', '#00ff00');
                console.log('🎤 Voice recognition started');
            };
            
            recognition.onend = () => {
                this.isListening = false;
                this.updateVoiceStatus('🔇 VOICE INACTIVE', '#666');
                console.log('🔇 Voice recognition stopped');
                
                // Restart if continuous listening is enabled
                if (this.settings.continuousListening && this.onVoiceResult) {
                    setTimeout(() => this.startListening(), 100);
                }
            };
            
            recognition.onresult = (event) => {
                let finalTranscript = '';
                let interimTranscript = '';
                
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    const transcript = event.results[i][0].transcript;
                    if (event.results[i].isFinal) {
                        finalTranscript += transcript;
                    } else {
                        interimTranscript += transcript;
                    }
                }
                
                // Update live transcript display
                this.updateTranscript(finalTranscript, interimTranscript);
                
                // Call callback with final results
                if (finalTranscript && this.onVoiceResult) {
                    this.onVoiceResult({
                        transcript: finalTranscript.trim(),
                        confidence: event.results[event.results.length - 1][0].confidence,
                        isFinal: true,
                        timestamp: Date.now()
                    });
                }
            };
            
            recognition.onerror = (event) => {
                console.error('Voice recognition error:', event.error);
                this.updateVoiceStatus(`❌ ERROR: ${event.error.toUpperCase()}`, '#ff4444');
            };
        }
        
        createVoiceControls() {
            // Create voice control overlay
            const voicePanel = document.createElement('div');
            voicePanel.id = 'mcp-voice-panel';
            voicePanel.style.cssText = `
                position: fixed;
                bottom: 20px;
                left: 20px;
                background: rgba(0, 0, 0, 0.95);
                border: 2px solid #00ff00;
                border-radius: 12px;
                padding: 16px;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                z-index: 999999;
                max-width: 350px;
                box-shadow: 0 0 25px rgba(0, 255, 0, 0.4);
                display: none;
                pointer-events: auto;
            `;
            
            voicePanel.innerHTML = `
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                    <div style="font-weight: bold; font-size: 14px;">🤖 AI VOICE CHAT</div>
                    <div id="mcp-voice-status" style="font-size: 11px; color: #666;">🔇 VOICE INACTIVE</div>
                </div>
                
                <div id="mcp-transcript-display" style="
                    background: rgba(0, 20, 0, 0.8);
                    border: 1px solid #004400;
                    border-radius: 6px;
                    padding: 8px;
                    min-height: 40px;
                    margin-bottom: 12px;
                    font-size: 11px;
                    line-height: 1.3;
                    max-height: 80px;
                    overflow-y: auto;
                ">
                    <div style="color: #888; font-style: italic;">Voice transcript will appear here...</div>
                </div>
                
                <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                    <button id="mcp-voice-toggle" style="
                        background: rgba(0, 255, 0, 0.1);
                        border: 1px solid #00ff00;
                        color: #00ff00;
                        padding: 6px 12px;
                        border-radius: 4px;
                        font-family: inherit;
                        font-size: 11px;
                        cursor: pointer;
                        font-weight: bold;
                    ">START LISTENING</button>
                    
                    <button id="mcp-voice-settings" style="
                        background: rgba(255, 170, 0, 0.1);
                        border: 1px solid #ffaa00;
                        color: #ffaa00;
                        padding: 6px 12px;
                        border-radius: 4px;
                        font-family: inherit;
                        font-size: 11px;
                        cursor: pointer;
                    ">SETTINGS</button>
                    
                    <button id="mcp-voice-close" style="
                        background: rgba(255, 68, 68, 0.1);
                        border: 1px solid #ff4444;
                        color: #ff4444;
                        padding: 6px 12px;
                        border-radius: 4px;
                        font-family: inherit;
                        font-size: 11px;
                        cursor: pointer;
                    ">CLOSE</button>
                </div>
            `;
            
            document.body.appendChild(voicePanel);
            this.voicePanel = voicePanel;
            
            // Attach event listeners
            this.attachVoiceControlEvents();
        }
        
        attachVoiceControlEvents() {
            const toggleBtn = document.getElementById('mcp-voice-toggle');
            const settingsBtn = document.getElementById('mcp-voice-settings');
            const closeBtn = document.getElementById('mcp-voice-close');
            
            toggleBtn.addEventListener('click', () => {
                if (this.isListening) {
                    this.stopListening();
                } else {
                    this.startListening();
                }
            });
            
            settingsBtn.addEventListener('click', () => {
                this.showVoiceSettings();
            });
            
            closeBtn.addEventListener('click', () => {
                this.hideVoicePanel();
            });
        }
        
        // Text-to-Speech Methods
        
        speak(text, options = {}) {
            if (!this.settings.voiceEnabled) return;
            
            // Cancel current speech
            if (this.currentUtterance) {
                this.speechSynthesis.cancel();
            }
            
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.rate = options.rate || this.settings.speechRate;
            utterance.pitch = options.pitch || this.settings.speechPitch;
            utterance.volume = options.volume || this.settings.speechVolume;
            utterance.lang = options.language || this.settings.language;
            
            // Set voice if specified
            if (options.voiceName || this.settings.voiceName) {
                const voices = this.speechSynthesis.getVoices();
                const voice = voices.find(v => 
                    v.name === (options.voiceName || this.settings.voiceName) ||
                    v.name.toLowerCase().includes((options.voiceName || this.settings.voiceName).toLowerCase())
                );
                if (voice) utterance.voice = voice;
            }
            
            utterance.onstart = () => {
                this.updateVoiceStatus('🗣️ AI SPEAKING...', '#00ff88');
            };
            
            utterance.onend = () => {
                this.updateVoiceStatus('🤖 AI READY', '#00ff00');
                this.currentUtterance = null;
            };
            
            utterance.onerror = (event) => {
                console.error('Speech synthesis error:', event.error);
                this.currentUtterance = null;
            };
            
            this.currentUtterance = utterance;
            this.speechSynthesis.speak(utterance);
        }
        
        // Speech Recognition Methods
        
        startListening(callback = null) {
            if (!this.speechRecognition) {
                console.warn('Speech recognition not available');
                return false;
            }
            
            if (callback) this.onVoiceResult = callback;
            
            try {
                this.speechRecognition.start();
                document.getElementById('mcp-voice-toggle').textContent = 'STOP LISTENING';
                return true;
            } catch (error) {
                console.error('Failed to start voice recognition:', error);
                return false;
            }
        }
        
        stopListening() {
            if (this.speechRecognition && this.isListening) {
                this.speechRecognition.stop();
                document.getElementById('mcp-voice-toggle').textContent = 'START LISTENING';
            }
        }
        
        // UI Update Methods
        
        showVoicePanel() {
            if (this.voicePanel) {
                this.voicePanel.style.display = 'block';
            }
        }
        
        hideVoicePanel() {
            this.stopListening();
            if (this.voicePanel) {
                this.voicePanel.style.display = 'none';
            }
        }
        
        updateVoiceStatus(status, color) {
            const statusElement = document.getElementById('mcp-voice-status');
            if (statusElement) {
                statusElement.textContent = status;
                statusElement.style.color = color;
            }
        }
        
        updateTranscript(finalText, interimText) {
            const display = document.getElementById('mcp-transcript-display');
            if (!display) return;
            
            let content = '';
            if (finalText) {
                content += `<div style="color: #00ff00; margin-bottom: 4px;">YOU: ${finalText}</div>`;
            }
            if (interimText) {
                content += `<div style="color: #888; font-style: italic;">...${interimText}</div>`;
            }
            
            display.innerHTML = content || '<div style="color: #888; font-style: italic;">Voice transcript will appear here...</div>';
            display.scrollTop = display.scrollHeight;
        }
        
        // Settings and Configuration
        
        updateSettings(newSettings) {
            this.settings = { ...this.settings, ...newSettings };
            
            if (this.speechRecognition) {
                this.speechRecognition.lang = this.settings.language;
                this.speechRecognition.continuous = this.settings.continuousListening;
            }
        }
        
        showVoiceSettings() {
            const voices = this.speechSynthesis.getVoices();
            const voiceOptions = voices.map(v => `<option value="${v.name}">${v.name} (${v.lang})</option>`).join('');
            
            const settingsHTML = `
                <div style="margin-bottom: 12px;">
                    <label style="display: block; margin-bottom: 4px; font-size: 11px;">Speech Rate:</label>
                    <input type="range" min="0.1" max="2" step="0.1" value="${this.settings.speechRate}" 
                           id="voice-rate" style="width: 100%;">
                    <div style="font-size: 10px; color: #888;">${this.settings.speechRate}x</div>
                </div>
                
                <div style="margin-bottom: 12px;">
                    <label style="display: block; margin-bottom: 4px; font-size: 11px;">Voice:</label>
                    <select id="voice-select" style="width: 100%; background: #000; color: #00ff00; border: 1px solid #004400;">
                        <option value="">Default Voice</option>
                        ${voiceOptions}
                    </select>
                </div>
                
                <div style="margin-bottom: 12px;">
                    <label style="display: flex; align-items: center; font-size: 11px;">
                        <input type="checkbox" id="continuous-listening" ${this.settings.continuousListening ? 'checked' : ''}>
                        <span style="margin-left: 6px;">Continuous Listening</span>
                    </label>
                </div>
                
                <button onclick="this.parentElement.remove()" style="
                    background: rgba(0, 255, 0, 0.1);
                    border: 1px solid #00ff00;
                    color: #00ff00;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-family: inherit;
                    font-size: 11px;
                    cursor: pointer;
                ">APPLY SETTINGS</button>
            `;
            
            const settingsPanel = document.createElement('div');
            settingsPanel.style.cssText = `
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: rgba(0, 0, 0, 0.95);
                border: 2px solid #ffaa00;
                border-radius: 12px;
                padding: 20px;
                color: #ffaa00;
                font-family: 'Courier New', monospace;
                z-index: 1000000;
                box-shadow: 0 0 30px rgba(255, 170, 0, 0.4);
            `;
            
            settingsPanel.innerHTML = `
                <div style="font-weight: bold; margin-bottom: 16px; font-size: 14px;">🎚️ VOICE SETTINGS</div>
                ${settingsHTML}
            `;
            
            document.body.appendChild(settingsPanel);
        }
        
        // Available Voices
        
        getAvailableVoices() {
            return this.speechSynthesis.getVoices().map(voice => ({
                name: voice.name,
                lang: voice.lang,
                gender: voice.name.toLowerCase().includes('female') ? 'female' : 'male',
                local: voice.localService
            }));
        }
    }
    
    // Global voice system instance
    window.mcpVoice = new MCPVoiceSystem();

    console.log('🗣️ MCP Voice Communication System initialized');
}
"""

    async def initialize(self, page: Page) -> None:
        """Initialize the voice communication system using V8 context injection"""
        try:
            # Use addInitScript for V8 context injection - safer and more reliable
            await page.add_init_script(self.VOICE_SCRIPT)
            
            # Verify initialization with timeout
            await page.wait_for_function(
                "() => typeof window.mcpVoice === 'object' && window.mcpVoice.speak",
                timeout=5000
            )
        except Exception as e:
            print(f"Warning: Failed to initialize voice system: {e}")
            # Voice system gracefully degrades if Web Speech API unavailable
        
    async def speak_to_user(
        self, 
        page: Page, 
        text: str,
        settings: Optional[VoiceSettings] = None
    ) -> None:
        """Have the AI speak text aloud to the user"""
        
        voice_options = {}
        if settings:
            voice_options = {
                "rate": settings.speech_rate,
                "pitch": settings.speech_pitch,
                "volume": settings.speech_volume,
                "language": settings.language
            }
            if settings.voice_name:
                voice_options["voiceName"] = settings.voice_name
                
        await page.evaluate(
            "mcpVoice.speak(arguments[0], arguments[1])",
            text, voice_options
        )
        
    async def listen_for_response(
        self, 
        page: Page,
        timeout: int = 30000
    ) -> Optional[Dict[str, Any]]:
        """
        Listen for user voice response and return transcript.
        
        Returns:
            Dictionary with transcript, confidence, and timestamp, or None if no response
        """
        
        try:
            # Show voice panel and start listening
            await page.evaluate("mcpVoice.showVoicePanel()")
            
            # Wait for voice response
            result = await page.evaluate(f"""
                new Promise((resolve) => {{
                    const timeoutId = setTimeout(() => {{
                        mcpVoice.stopListening();
                        resolve(null);
                    }}, {timeout});
                    
                    mcpVoice.startListening((voiceResult) => {{
                        clearTimeout(timeoutId);
                        mcpVoice.stopListening();
                        resolve(voiceResult);
                    }});
                }})
            """)
            
            return result
            
        except Exception as e:
            return None
            
    async def ask_voice_question(
        self,
        page: Page,
        question: str,
        settings: Optional[VoiceSettings] = None
    ) -> Optional[str]:
        """
        Ask a question aloud and wait for voice response.
        
        Returns:
            User's voice response as text, or None if no response
        """
        
        # Speak the question
        await self.speak_to_user(page, question, settings)
        
        # Wait a moment for speech to complete
        await page.wait_for_timeout(1000)
        
        # Listen for response
        voice_result = await self.listen_for_response(page)
        
        if voice_result:
            return voice_result.get('transcript', '').strip()
        
        return None
        
    async def show_voice_controls(self, page: Page) -> None:
        """Show the voice control panel to the user"""
        await page.evaluate("mcpVoice.showVoicePanel()")
        
    async def hide_voice_controls(self, page: Page) -> None:
        """Hide the voice control panel"""
        await page.evaluate("mcpVoice.hideVoicePanel()")
        
    async def get_available_voices(self, page: Page) -> list[Dict[str, Any]]:
        """Get list of available text-to-speech voices"""
        voices = await page.evaluate("mcpVoice.getAvailableVoices()")
        return voices or []