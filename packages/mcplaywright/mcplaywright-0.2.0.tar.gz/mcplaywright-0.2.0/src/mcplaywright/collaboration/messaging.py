"""
Real-time messaging system for AI-Human collaboration.

Provides JavaScript functions for models to communicate with users:
- mcpMessage() - Basic messaging with auto-dismiss
- mcpNotify.* - Helper functions for different message types
"""

from typing import Dict, Any, Optional, Literal
from pydantic import BaseModel
from playwright.async_api import Page

MessageType = Literal["info", "success", "warning", "error"]

class CollaborationMessage(BaseModel):
    """Message data structure for AI-Human communication"""
    text: str
    type: MessageType = "info"
    duration: int = 5000  # milliseconds, 0 = persistent
    title: Optional[str] = None
    
class CollaborationMessaging:
    """
    Real-time messaging system enabling AI models to communicate with users
    during browser automation sessions.
    
    Provides cyberpunk-themed notifications with auto-dismiss functionality.
    """
    
    COLLABORATION_SCRIPT = """
// MCP Model-User Collaboration Messaging System
// Cyberpunk "hacker matrix" theme with neon green styling

if (typeof window.mcpCollaborationInit === 'undefined') {
    window.mcpCollaborationInit = true;
    
    // Create notification container
    const createNotificationContainer = () => {
        let container = document.getElementById('mcp-notification-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'mcp-notification-container';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 999999;
                pointer-events: none;
                font-family: 'Courier New', monospace;
                max-width: 400px;
            `;
            document.body.appendChild(container);
        }
        return container;
    };

    // Core messaging function
    window.mcpMessage = (text, type = 'info', duration = 5000, title = null) => {
        const container = createNotificationContainer();
        
        const notification = document.createElement('div');
        notification.style.cssText = `
            background: rgba(0, 0, 0, 0.95);
            border: 2px solid #00ff00;
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 10px;
            color: #00ff00;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.4;
            box-shadow: 0 0 20px rgba(0, 255, 0, 0.3);
            animation: mcpSlideIn 0.3s ease-out;
            pointer-events: auto;
            cursor: pointer;
            position: relative;
            overflow: hidden;
        `;
        
        // Color variations by message type
        const colors = {
            info: { border: '#00ff00', color: '#00ff00', glow: 'rgba(0, 255, 0, 0.3)' },
            success: { border: '#00ff88', color: '#00ff88', glow: 'rgba(0, 255, 136, 0.3)' },
            warning: { border: '#ffaa00', color: '#ffaa00', glow: 'rgba(255, 170, 0, 0.3)' },
            error: { border: '#ff4444', color: '#ff4444', glow: 'rgba(255, 68, 68, 0.3)' }
        };
        
        const themeColors = colors[type] || colors.info;
        notification.style.borderColor = themeColors.border;
        notification.style.color = themeColors.color;
        notification.style.boxShadow = `0 0 20px ${themeColors.glow}`;
        
        // Build notification content
        let content = '';
        if (title) {
            content += `<div style="font-weight: bold; margin-bottom: 6px; font-size: 15px;">${title}</div>`;
        }
        content += `<div>${text}</div>`;
        
        // Add type indicator
        const indicators = { info: 'ℹ', success: '✓', warning: '⚠', error: '✗' };
        content = `<span style="margin-right: 8px; font-weight: bold;">${indicators[type] || indicators.info}</span>` + content;
        
        notification.innerHTML = content;
        
        // Glowing border animation
        const glowKeyframes = `
            @keyframes mcpGlow {
                0%, 100% { box-shadow: 0 0 20px ${themeColors.glow}; }
                50% { box-shadow: 0 0 30px ${themeColors.glow}, 0 0 40px ${themeColors.glow}; }
            }
        `;
        
        if (!document.getElementById('mcp-glow-styles')) {
            const styleSheet = document.createElement('style');
            styleSheet.id = 'mcp-glow-styles';
            styleSheet.innerHTML = `
                @keyframes mcpSlideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                @keyframes mcpSlideOut {
                    from { transform: translateX(0); opacity: 1; }
                    to { transform: translateX(100%); opacity: 0; }
                }
                ${glowKeyframes}
            `;
            document.head.appendChild(styleSheet);
        }
        
        // Add pulsing glow effect
        notification.style.animation = 'mcpSlideIn 0.3s ease-out, mcpGlow 2s ease-in-out infinite';
        
        // Click to dismiss
        notification.addEventListener('click', () => {
            notification.style.animation = 'mcpSlideOut 0.3s ease-in';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        });
        
        container.appendChild(notification);
        
        // Auto-dismiss after duration (if not persistent)
        if (duration > 0) {
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.style.animation = 'mcpSlideOut 0.3s ease-in';
                    setTimeout(() => {
                        if (notification.parentNode) {
                            notification.parentNode.removeChild(notification);
                        }
                    }, 300);
                }
            }, duration);
        }
        
        return notification;
    };

    // Helper notification functions
    window.mcpNotify = {
        info: (text, title = null) => window.mcpMessage(text, 'info', 5000, title),
        success: (text, title = null) => window.mcpMessage(text, 'success', 3000, title),
        warning: (text, title = null) => window.mcpMessage(text, 'warning', 4000, title),
        error: (text, title = null) => window.mcpMessage(text, 'error', 6000, title),
        loading: (text, title = null) => window.mcpMessage(text, 'info', 0, title || '⏳ PROCESSING'),
        done: (text, title = null) => window.mcpMessage(text, 'success', 3000, title || '✅ COMPLETED'),
        failed: (text, title = null) => window.mcpMessage(text, 'error', 5000, title || '❌ FAILED')
    };

    console.log('🤖 MCP Collaboration Messaging System initialized');
}
"""

    async def initialize(self, page: Page) -> None:
        """Initialize the collaboration messaging system using V8 context injection"""
        try:
            # Use addInitScript for V8 context injection - safer and more reliable
            await page.add_init_script(self.COLLABORATION_SCRIPT)
            
            # Verify initialization
            await page.wait_for_function(
                "() => typeof window.mcpMessage === 'function'",
                timeout=5000
            )
        except Exception as e:
            print(f"Warning: Failed to initialize messaging system: {e}")
            # Fall back to secure V8 implementation
            from .secure_v8_scripts import SecureV8CollaborationAPI
            secure_api = SecureV8CollaborationAPI()
            await secure_api.initialize_secure_messaging(page)
        
    async def send_message(
        self, 
        page: Page, 
        text: str, 
        message_type: MessageType = "info",
        duration: int = 5000,
        title: Optional[str] = None
    ) -> None:
        """Send a message to the user"""
        await page.evaluate(
            "mcpMessage(arguments[0], arguments[1], arguments[2], arguments[3])",
            text, message_type, duration, title
        )
        
    async def notify_info(self, page: Page, text: str, title: Optional[str] = None) -> None:
        """Send an info notification (5s auto-dismiss)"""
        await page.evaluate("mcpNotify.info(arguments[0], arguments[1])", text, title)
        
    async def notify_success(self, page: Page, text: str, title: Optional[str] = None) -> None:
        """Send a success notification (3s auto-dismiss)"""
        await page.evaluate("mcpNotify.success(arguments[0], arguments[1])", text, title)
        
    async def notify_warning(self, page: Page, text: str, title: Optional[str] = None) -> None:
        """Send a warning notification (4s auto-dismiss)"""
        await page.evaluate("mcpNotify.warning(arguments[0], arguments[1])", text, title)
        
    async def notify_error(self, page: Page, text: str, title: Optional[str] = None) -> None:
        """Send an error notification (6s auto-dismiss)"""
        await page.evaluate("mcpNotify.error(arguments[0], arguments[1])", text, title)
        
    async def notify_loading(self, page: Page, text: str, title: Optional[str] = None) -> None:
        """Send a persistent loading notification"""
        await page.evaluate("mcpNotify.loading(arguments[0], arguments[1])", text, title)
        
    async def notify_done(self, page: Page, text: str, title: Optional[str] = None) -> None:
        """Send a completion notification (3s auto-dismiss)"""
        await page.evaluate("mcpNotify.done(arguments[0], arguments[1])", text, title)
        
    async def notify_failed(self, page: Page, text: str, title: Optional[str] = None) -> None:
        """Send a failure notification (5s auto-dismiss)"""
        await page.evaluate("mcpNotify.failed(arguments[0], arguments[1])", text, title)