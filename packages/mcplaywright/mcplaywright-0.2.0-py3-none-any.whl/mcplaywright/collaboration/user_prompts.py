"""
Interactive user confirmation system for AI-Human collaboration.

Provides JavaScript functions for models to request user confirmations:
- mcpPrompt() - Interactive confirmation dialogs
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel
from playwright.async_api import Page
import asyncio

class PromptOptions(BaseModel):
    """Configuration options for user prompts"""
    title: Optional[str] = None
    confirm_text: str = "CONFIRM"
    cancel_text: str = "CANCEL"
    timeout: int = 30000  # 30 seconds default timeout

class UserPrompts:
    """
    Interactive user confirmation system enabling AI models to request
    user input and confirmations during browser automation.
    
    Features cyberpunk-themed modal dialogs with ESC key support.
    """
    
    PROMPT_SCRIPT = """
// MCP User Confirmation System
// Interactive prompts with cyberpunk styling

if (typeof window.mcpPromptInit === 'undefined') {
    window.mcpPromptInit = true;
    
    // Promise-based prompt system
    window.mcpPrompt = async (message, options = {}) => {
        return new Promise((resolve) => {
            const {
                title = null,
                confirmText = 'CONFIRM',
                cancelText = 'CANCEL',
                timeout = 30000
            } = options;
            
            // Create modal backdrop
            const backdrop = document.createElement('div');
            backdrop.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                background: rgba(0, 0, 0, 0.8);
                backdrop-filter: blur(4px);
                z-index: 1000000;
                display: flex;
                align-items: center;
                justify-content: center;
                font-family: 'Courier New', monospace;
                animation: mcpFadeIn 0.3s ease-out;
            `;
            
            // Create modal dialog
            const modal = document.createElement('div');
            modal.style.cssText = `
                background: rgba(0, 0, 0, 0.95);
                border: 2px solid #00ff00;
                border-radius: 12px;
                padding: 24px;
                max-width: 500px;
                min-width: 350px;
                color: #00ff00;
                box-shadow: 0 0 30px rgba(0, 255, 0, 0.4);
                animation: mcpScaleIn 0.3s ease-out;
                position: relative;
            `;
            
            // Build modal content
            let content = '';
            
            if (title) {
                content += `
                    <div style="
                        font-size: 18px; 
                        font-weight: bold; 
                        margin-bottom: 16px; 
                        text-align: center;
                        color: #00ff88;
                        text-shadow: 0 0 10px rgba(0, 255, 136, 0.6);
                    ">${title}</div>
                `;
            }
            
            content += `
                <div style="
                    font-size: 14px; 
                    line-height: 1.5; 
                    margin-bottom: 24px;
                    text-align: center;
                ">${message}</div>
                
                <div style="
                    display: flex; 
                    gap: 12px; 
                    justify-content: center;
                ">
                    <button id="mcp-prompt-confirm" style="
                        background: rgba(0, 255, 0, 0.1);
                        border: 1px solid #00ff00;
                        color: #00ff00;
                        padding: 10px 20px;
                        border-radius: 6px;
                        font-family: 'Courier New', monospace;
                        font-size: 12px;
                        font-weight: bold;
                        cursor: pointer;
                        transition: all 0.2s ease;
                        text-transform: uppercase;
                    ">${confirmText}</button>
                    
                    <button id="mcp-prompt-cancel" style="
                        background: rgba(255, 68, 68, 0.1);
                        border: 1px solid #ff4444;
                        color: #ff4444;
                        padding: 10px 20px;
                        border-radius: 6px;
                        font-family: 'Courier New', monospace;
                        font-size: 12px;
                        font-weight: bold;
                        cursor: pointer;
                        transition: all 0.2s ease;
                        text-transform: uppercase;
                    ">${cancelText}</button>
                </div>
            `;
            
            modal.innerHTML = content;
            backdrop.appendChild(modal);
            
            // Add modal animations
            if (!document.getElementById('mcp-prompt-styles')) {
                const styleSheet = document.createElement('style');
                styleSheet.id = 'mcp-prompt-styles';
                styleSheet.innerHTML = `
                    @keyframes mcpFadeIn {
                        from { opacity: 0; }
                        to { opacity: 1; }
                    }
                    @keyframes mcpScaleIn {
                        from { transform: scale(0.8); opacity: 0; }
                        to { transform: scale(1); opacity: 1; }
                    }
                    @keyframes mcpFadeOut {
                        from { opacity: 1; }
                        to { opacity: 0; }
                    }
                    #mcp-prompt-confirm:hover {
                        background: rgba(0, 255, 0, 0.2) !important;
                        box-shadow: 0 0 15px rgba(0, 255, 0, 0.3) !important;
                    }
                    #mcp-prompt-cancel:hover {
                        background: rgba(255, 68, 68, 0.2) !important;
                        box-shadow: 0 0 15px rgba(255, 68, 68, 0.3) !important;
                    }
                `;
                document.head.appendChild(styleSheet);
            }
            
            document.body.appendChild(backdrop);
            
            // Event handlers
            const cleanup = () => {
                backdrop.style.animation = 'mcpFadeOut 0.3s ease-in';
                setTimeout(() => {
                    if (backdrop.parentNode) {
                        backdrop.parentNode.removeChild(backdrop);
                    }
                }, 300);
            };
            
            const confirmButton = backdrop.querySelector('#mcp-prompt-confirm');
            const cancelButton = backdrop.querySelector('#mcp-prompt-cancel');
            
            confirmButton.addEventListener('click', () => {
                cleanup();
                resolve(true);
            });
            
            cancelButton.addEventListener('click', () => {
                cleanup();
                resolve(false);
            });
            
            // ESC key support
            const handleEsc = (e) => {
                if (e.key === 'Escape') {
                    cleanup();
                    resolve(false);
                    document.removeEventListener('keydown', handleEsc);
                }
            };
            document.addEventListener('keydown', handleEsc);
            
            // Timeout handling
            if (timeout > 0) {
                setTimeout(() => {
                    if (backdrop.parentNode) {
                        cleanup();
                        resolve(false);
                        document.removeEventListener('keydown', handleEsc);
                    }
                }, timeout);
            }
            
            // Focus first button for keyboard navigation
            confirmButton.focus();
        });
    };

    console.log('🤖 MCP User Prompt System initialized');
}
"""

    async def initialize(self, page: Page) -> None:
        """Initialize the user prompt system using V8 context injection"""
        try:
            # Use addInitScript for V8 context injection - safer and more reliable
            await page.add_init_script(self.PROMPT_SCRIPT)
            
            # Verify initialization
            await page.wait_for_function(
                "() => typeof window.mcpPrompt === 'function'",
                timeout=5000
            )
        except Exception as e:
            print(f"Warning: Failed to initialize prompts system: {e}")
            # Fall back to secure V8 implementation
            from .secure_v8_scripts import SecureV8CollaborationAPI
            secure_api = SecureV8CollaborationAPI()
            await secure_api.initialize_secure_prompts(page)
        
    async def confirm(
        self, 
        page: Page, 
        message: str,
        title: Optional[str] = None,
        confirm_text: str = "CONFIRM",
        cancel_text: str = "CANCEL",
        timeout: int = 30000
    ) -> bool:
        """
        Show a confirmation dialog to the user and return their choice.
        
        Returns:
            True if user confirmed, False if cancelled or timed out
        """
        try:
            result = await page.evaluate("""
                async (args) => {
                    const [message, options] = args;
                    return await mcpPrompt(message, options);
                }
            """, [message, {
                "title": title,
                "confirmText": confirm_text,
                "cancelText": cancel_text,
                "timeout": timeout
            }])
            
            return bool(result)
            
        except Exception as e:
            # If prompt fails (e.g., page navigated away), default to False
            return False
            
    async def ask_permission(
        self,
        page: Page,
        action_description: str,
        danger_level: str = "normal"
    ) -> bool:
        """
        Ask user for permission to perform an action.
        
        Args:
            action_description: Description of the action to perform
            danger_level: "safe", "normal", "destructive"
        """
        
        danger_configs = {
            "safe": {
                "title": "🔍 CONFIRM ACTION",
                "confirm_text": "PROCEED",
                "cancel_text": "SKIP"
            },
            "normal": {
                "title": "⚡ CONFIRM ACTION",
                "confirm_text": "YES, CONTINUE",
                "cancel_text": "CANCEL"
            },
            "destructive": {
                "title": "⚠️ DESTRUCTIVE ACTION",
                "confirm_text": "YES, I UNDERSTAND",
                "cancel_text": "CANCEL"
            }
        }
        
        config = danger_configs.get(danger_level, danger_configs["normal"])
        
        return await self.confirm(
            page,
            f"I want to: {action_description}\\n\\nShould I proceed?",
            title=config["title"],
            confirm_text=config["confirm_text"],
            cancel_text=config["cancel_text"]
        )