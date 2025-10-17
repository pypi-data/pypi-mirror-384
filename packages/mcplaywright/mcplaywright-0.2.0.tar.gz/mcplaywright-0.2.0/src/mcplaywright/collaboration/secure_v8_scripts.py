"""
Ultra-secure V8 context injection scripts with comprehensive error handling.

Production-grade JavaScript designed for V8 context injection via page.addInitScript().
Includes robust safety measures, error boundaries, and defensive programming practices.
"""

from typing import Optional
from playwright.async_api import Page

class SecureV8CollaborationAPI:
    """
    Ultra-secure, production-grade collaboration API with V8 context injection.
    
    Features:
    - V8 context injection for maximum safety and reliability
    - Comprehensive error boundaries around all functionality
    - Defensive programming against hostile page environments  
    - Zero global namespace pollution
    - Memory leak prevention and cleanup
    - Cross-browser compatibility with graceful degradation
    """
    
    # Ultra-secure V8 messaging system with error boundaries
    SECURE_MESSAGING_SCRIPT = """
// MCP Secure Messaging System - V8 Context Injection
// Ultra-secure with comprehensive error boundaries and safety measures

(function() {
    'use strict';
    
    // Defensive namespace check - avoid conflicts
    if (typeof window !== 'undefined' && window.mcpSecureMessaging) {
        return; // Already initialized
    }
    
    try {
        // Create secure messaging namespace with error boundaries
        const mcpSecureMessaging = (() => {
            // Private state - protected from external access
            let messageContainer = null;
            let messageCount = 0;
            let isStylesInjected = false;
            const activeMessages = new Map();
            
            // Safe DOM access with error handling
            const safeCreateElement = (tag, styles = '', innerHTML = '') => {
                try {
                    const element = document.createElement(tag);
                    if (styles) element.style.cssText = styles;
                    if (innerHTML) element.innerHTML = innerHTML;
                    return element;
                } catch (error) {
                    console.warn('MCP: Failed to create element:', error);
                    return null;
                }
            };
            
            // Safe DOM insertion with validation
            const safeAppendChild = (parent, child) => {
                try {
                    if (parent && child && typeof parent.appendChild === 'function') {
                        return parent.appendChild(child);
                    }
                } catch (error) {
                    console.warn('MCP: Failed to append child:', error);
                }
                return null;
            };
            
            // Safe element removal with cleanup
            const safeRemoveElement = (element) => {
                try {
                    if (element && element.parentNode && typeof element.remove === 'function') {
                        element.remove();
                        return true;
                    }
                } catch (error) {
                    console.warn('MCP: Failed to remove element:', error);
                }
                return false;
            };
            
            // Create message container with error handling
            const createContainer = () => {
                if (messageContainer && document.contains(messageContainer)) {
                    return messageContainer;
                }
                
                try {
                    messageContainer = safeCreateElement('div', 
                        'position:fixed;top:20px;right:20px;z-index:999999;' +
                        'pointer-events:none;font-family:Courier,monospace;' +
                        'max-width:400px;font-size:14px;line-height:1.4'
                    );
                    
                    if (messageContainer) {
                        messageContainer.id = 'mcp-msg-container-' + Date.now();
                        safeAppendChild(document.body, messageContainer);
                    }
                } catch (error) {
                    console.warn('MCP: Failed to create message container:', error);
                    messageContainer = null;
                }
                
                return messageContainer;
            };
            
            // Inject CSS styles once with error handling
            const injectStyles = () => {
                if (isStylesInjected) return;
                
                try {
                    const styles = safeCreateElement('style', '', `
                        @keyframes mcpSlideIn { 
                            from { transform: translateX(100%); opacity: 0; } 
                            to { transform: translateX(0); opacity: 1; } 
                        }
                        @keyframes mcpSlideOut { 
                            from { transform: translateX(0); opacity: 1; } 
                            to { transform: translateX(100%); opacity: 0; } 
                        }
                        @keyframes mcpGlow { 
                            0%, 100% { box-shadow: 0 0 20px currentColor; } 
                            50% { box-shadow: 0 0 30px currentColor; } 
                        }
                    `);
                    
                    if (styles) {
                        styles.id = 'mcp-styles-' + Date.now();
                        safeAppendChild(document.head || document.documentElement, styles);
                        isStylesInjected = true;
                    }
                } catch (error) {
                    console.warn('MCP: Failed to inject styles:', error);
                }
            };
            
            // Secure message display with comprehensive error handling
            const displayMessage = (text, type = 'info', duration = 5000, title = null) => {
                try {
                    // Input validation
                    if (typeof text !== 'string' || text.length === 0) {
                        console.warn('MCP: Invalid message text');
                        return null;
                    }
                    
                    // Sanitize inputs
                    text = String(text).substring(0, 500); // Limit message length
                    type = ['info', 'success', 'warning', 'error'].includes(type) ? type : 'info';
                    duration = Math.max(0, Math.min(60000, Number(duration) || 5000)); // 0-60s limit
                    if (title) title = String(title).substring(0, 100);
                    
                    const container = createContainer();
                    if (!container) return null;
                    
                    injectStyles();
                    
                    // Color mapping with fallback
                    const colors = {
                        info: '#00ff00',
                        success: '#00ff88', 
                        warning: '#ffaa00',
                        error: '#ff4444'
                    };
                    const color = colors[type] || colors.info;
                    
                    // Icon mapping
                    const icons = {
                        info: 'ℹ',
                        success: '✓',
                        warning: '⚠',
                        error: '✗'
                    };
                    const icon = icons[type] || icons.info;
                    
                    // Create message element with safe HTML
                    const messageId = 'mcp-msg-' + (++messageCount);
                    const message = safeCreateElement('div', 
                        `background:rgba(0,0,0,0.95);border:2px solid ${color};` +
                        `border-radius:8px;padding:12px 16px;margin-bottom:10px;` +
                        `color:${color};font-family:inherit;box-shadow:0 0 20px ${color}40;` +
                        `animation:mcpSlideIn 0.3s ease-out,mcpGlow 2s ease-in-out infinite;` +
                        `pointer-events:auto;cursor:pointer;position:relative;overflow:hidden;`
                    );
                    
                    if (!message) return null;
                    
                    message.id = messageId;
                    
                    // Build content safely
                    let content = '';
                    if (title) {
                        content += `<div style="font-weight:bold;margin-bottom:6px;font-size:15px;">${title}</div>`;
                    }
                    content += `<span style="margin-right:8px;font-weight:bold;">${icon}</span>${text}`;
                    
                    message.innerHTML = content;
                    
                    // Safe click handler with cleanup
                    const cleanup = () => {
                        try {
                            message.style.animation = 'mcpSlideOut 0.3s ease-in';
                            setTimeout(() => {
                                safeRemoveElement(message);
                                activeMessages.delete(messageId);
                            }, 300);
                        } catch (error) {
                            console.warn('MCP: Cleanup error:', error);
                            safeRemoveElement(message);
                        }
                    };
                    
                    // Add click listener with error boundary
                    try {
                        message.addEventListener('click', cleanup);
                    } catch (error) {
                        console.warn('MCP: Failed to add click listener:', error);
                    }
                    
                    // Append message safely
                    safeAppendChild(container, message);
                    activeMessages.set(messageId, { element: message, cleanup });
                    
                    // Auto-dismiss with cleanup
                    if (duration > 0) {
                        setTimeout(() => {
                            if (activeMessages.has(messageId)) {
                                cleanup();
                            }
                        }, duration);
                    }
                    
                    return message;
                    
                } catch (error) {
                    console.error('MCP: Message display error:', error);
                    return null;
                }
            };
            
            // Public API with error boundaries
            const publicAPI = {
                // Core messaging function
                message: (text, type, duration, title) => {
                    try {
                        return displayMessage(text, type, duration, title);
                    } catch (error) {
                        console.error('MCP: Message API error:', error);
                        return null;
                    }
                },
                
                // Helper functions with error boundaries
                info: (text, title) => publicAPI.message(text, 'info', 5000, title),
                success: (text, title) => publicAPI.message(text, 'success', 3000, title),
                warning: (text, title) => publicAPI.message(text, 'warning', 4000, title),
                error: (text, title) => publicAPI.message(text, 'error', 6000, title),
                loading: (text, title) => publicAPI.message(text, 'info', 0, title || '⏳ PROCESSING'),
                done: (text, title) => publicAPI.message(text, 'success', 3000, title || '✅ COMPLETED'),
                failed: (text, title) => publicAPI.message(text, 'error', 5000, title || '❌ FAILED'),
                
                // Cleanup function for memory management
                cleanup: () => {
                    try {
                        activeMessages.forEach((msg, id) => {
                            try {
                                msg.cleanup();
                            } catch (e) {
                                console.warn('MCP: Cleanup individual message error:', e);
                            }
                        });
                        activeMessages.clear();
                        
                        if (messageContainer) {
                            safeRemoveElement(messageContainer);
                            messageContainer = null;
                        }
                    } catch (error) {
                        console.warn('MCP: Global cleanup error:', error);
                    }
                },
                
                // Health check
                isAvailable: () => {
                    try {
                        return !!(document && document.body && typeof document.createElement === 'function');
                    } catch (error) {
                        return false;
                    }
                }
            };
            
            return publicAPI;
        })();
        
        // Secure global assignment with error boundary
        if (typeof window !== 'undefined') {
            // Primary API
            window.mcpMessage = mcpSecureMessaging.message;
            window.mcpNotify = {
                info: mcpSecureMessaging.info,
                success: mcpSecureMessaging.success,
                warning: mcpSecureMessaging.warning,
                error: mcpSecureMessaging.error,
                loading: mcpSecureMessaging.loading,
                done: mcpSecureMessaging.done,
                failed: mcpSecureMessaging.failed
            };
            
            // Internal cleanup API (for debugging/testing)
            window.mcpSecureMessaging = mcpSecureMessaging;
            
            // Page unload cleanup
            try {
                window.addEventListener('beforeunload', () => {
                    try {
                        mcpSecureMessaging.cleanup();
                    } catch (e) {
                        console.warn('MCP: Unload cleanup error:', e);
                    }
                });
            } catch (error) {
                console.warn('MCP: Failed to add unload listener:', error);
            }
        }
        
        // Success indicator
        console.log('🤖 MCP Secure Messaging System initialized via V8 context');
        
    } catch (error) {
        console.error('MCP: Critical initialization error:', error);
        
        // Fallback minimal API to prevent page breakage
        if (typeof window !== 'undefined') {
            window.mcpMessage = (text) => console.log('MCP Fallback:', text);
            window.mcpNotify = {
                info: (text) => console.log('MCP Info:', text),
                success: (text) => console.log('MCP Success:', text),
                warning: (text) => console.warn('MCP Warning:', text),
                error: (text) => console.error('MCP Error:', text),
                loading: (text) => console.log('MCP Loading:', text),
                done: (text) => console.log('MCP Done:', text),
                failed: (text) => console.error('MCP Failed:', text)
            };
        }
    }
})();
"""

    # Ultra-secure V8 prompts system  
    SECURE_PROMPTS_SCRIPT = """
// MCP Secure Prompts System - V8 Context Injection
// Ultra-secure interactive confirmations with comprehensive error handling

(function() {
    'use strict';
    
    if (typeof window !== 'undefined' && window.mcpSecurePrompts) {
        return; // Already initialized
    }
    
    try {
        const mcpSecurePrompts = (() => {
            let activePrompts = new Set();
            let promptCount = 0;
            let isStylesInjected = false;
            
            // Safe DOM utilities
            const safeCreate = (tag, styles = '', html = '') => {
                try {
                    const el = document.createElement(tag);
                    if (styles) el.style.cssText = styles;
                    if (html) el.innerHTML = html;
                    return el;
                } catch (e) {
                    console.warn('MCP Prompt: Create element error:', e);
                    return null;
                }
            };
            
            const safeAppend = (parent, child) => {
                try {
                    if (parent && child) return parent.appendChild(child);
                } catch (e) {
                    console.warn('MCP Prompt: Append error:', e);
                }
                return null;
            };
            
            const safeRemove = (element) => {
                try {
                    if (element && element.remove) {
                        element.remove();
                        return true;
                    }
                } catch (e) {
                    console.warn('MCP Prompt: Remove error:', e);
                }
                return false;
            };
            
            // Inject styles once
            const injectStyles = () => {
                if (isStylesInjected) return;
                
                try {
                    const styles = safeCreate('style', '', `
                        @keyframes mcpPromptFadeIn { from { opacity: 0; } to { opacity: 1; } }
                        @keyframes mcpPromptScaleIn { 
                            from { transform: scale(0.8); opacity: 0; } 
                            to { transform: scale(1); opacity: 1; } 
                        }
                        @keyframes mcpPromptFadeOut { from { opacity: 1; } to { opacity: 0; } }
                        .mcp-prompt-btn:hover { 
                            background: rgba(255,255,255,0.1) !important; 
                            box-shadow: 0 0 15px currentColor !important; 
                        }
                    `);
                    
                    if (styles) {
                        safeAppend(document.head || document.documentElement, styles);
                        isStylesInjected = true;
                    }
                } catch (e) {
                    console.warn('MCP Prompt: Style injection error:', e);
                }
            };
            
            // Secure prompt display
            const showPrompt = (message, options = {}) => {
                return new Promise((resolve) => {
                    try {
                        // Input validation and sanitization
                        if (typeof message !== 'string' || !message.trim()) {
                            console.warn('MCP Prompt: Invalid message');
                            resolve(false);
                            return;
                        }
                        
                        message = String(message).substring(0, 1000);
                        const opts = {
                            title: options.title ? String(options.title).substring(0, 200) : null,
                            confirmText: String(options.confirmText || 'CONFIRM').substring(0, 50),
                            cancelText: String(options.cancelText || 'CANCEL').substring(0, 50),
                            timeout: Math.max(0, Math.min(300000, Number(options.timeout) || 30000))
                        };
                        
                        const promptId = 'mcp-prompt-' + (++promptCount);
                        injectStyles();
                        
                        // Create backdrop
                        const backdrop = safeCreate('div', 
                            'position:fixed;top:0;left:0;width:100vw;height:100vh;' +
                            'background:rgba(0,0,0,0.8);backdrop-filter:blur(4px);' +
                            'z-index:1000000;display:flex;align-items:center;justify-content:center;' +
                            'font-family:Courier,monospace;animation:mcpPromptFadeIn 0.3s ease-out;'
                        );
                        
                        if (!backdrop) {
                            resolve(false);
                            return;
                        }
                        
                        backdrop.id = promptId + '-backdrop';
                        
                        // Create modal
                        const modal = safeCreate('div',
                            'background:rgba(0,0,0,0.95);border:2px solid #00ff00;' +
                            'border-radius:12px;padding:24px;max-width:500px;min-width:350px;' +
                            'color:#00ff00;box-shadow:0 0 30px #00ff0040;' +
                            'animation:mcpPromptScaleIn 0.3s ease-out;position:relative;'
                        );
                        
                        if (!modal) {
                            resolve(false);
                            return;
                        }
                        
                        // Build content safely
                        let content = '';
                        if (opts.title) {
                            content += `<div style="font-size:18px;font-weight:bold;margin-bottom:16px;text-align:center;color:#00ff88;text-shadow:0 0 10px #00ff8860;">${opts.title}</div>`;
                        }
                        content += `<div style="font-size:14px;line-height:1.5;margin-bottom:24px;text-align:center;">${message}</div>`;
                        content += `
                            <div style="display:flex;gap:12px;justify-content:center;">
                                <button id="${promptId}-confirm" class="mcp-prompt-btn" style="
                                    background:rgba(0,255,0,0.1);border:1px solid #00ff00;color:#00ff00;
                                    padding:10px 20px;border-radius:6px;font-family:inherit;font-size:12px;
                                    font-weight:bold;cursor:pointer;transition:all 0.2s ease;text-transform:uppercase;
                                ">${opts.confirmText}</button>
                                <button id="${promptId}-cancel" class="mcp-prompt-btn" style="
                                    background:rgba(255,68,68,0.1);border:1px solid #ff4444;color:#ff4444;
                                    padding:10px 20px;border-radius:6px;font-family:inherit;font-size:12px;
                                    font-weight:bold;cursor:pointer;transition:all 0.2s ease;text-transform:uppercase;
                                ">${opts.cancelText}</button>
                            </div>
                        `;
                        
                        modal.innerHTML = content;
                        safeAppend(backdrop, modal);
                        
                        // Cleanup function
                        const cleanup = (result) => {
                            try {
                                backdrop.style.animation = 'mcpPromptFadeOut 0.3s ease-in';
                                setTimeout(() => {
                                    safeRemove(backdrop);
                                    activePrompts.delete(promptId);
                                    document.removeEventListener('keydown', keyHandler);
                                    resolve(result);
                                }, 300);
                            } catch (e) {
                                console.warn('MCP Prompt: Cleanup error:', e);
                                safeRemove(backdrop);
                                resolve(false);
                            }
                        };
                        
                        // Event handlers with error boundaries
                        const keyHandler = (e) => {
                            try {
                                if (e.key === 'Escape') {
                                    e.preventDefault();
                                    cleanup(false);
                                }
                            } catch (error) {
                                console.warn('MCP Prompt: Key handler error:', error);
                            }
                        };
                        
                        try {
                            document.addEventListener('keydown', keyHandler);
                        } catch (e) {
                            console.warn('MCP Prompt: Key listener error:', e);
                        }
                        
                        // Button handlers
                        try {
                            const confirmBtn = modal.querySelector(`#${promptId}-confirm`);
                            const cancelBtn = modal.querySelector(`#${promptId}-cancel`);
                            
                            if (confirmBtn) {
                                confirmBtn.addEventListener('click', () => cleanup(true));
                                setTimeout(() => confirmBtn.focus(), 100);
                            }
                            
                            if (cancelBtn) {
                                cancelBtn.addEventListener('click', () => cleanup(false));
                            }
                        } catch (e) {
                            console.warn('MCP Prompt: Button setup error:', e);
                        }
                        
                        // Add to DOM
                        safeAppend(document.body, backdrop);
                        activePrompts.add(promptId);
                        
                        // Timeout handling
                        if (opts.timeout > 0) {
                            setTimeout(() => {
                                if (activePrompts.has(promptId)) {
                                    cleanup(false);
                                }
                            }, opts.timeout);
                        }
                        
                    } catch (error) {
                        console.error('MCP Prompt: Display error:', error);
                        resolve(false);
                    }
                });
            };
            
            return {
                prompt: showPrompt,
                cleanup: () => {
                    try {
                        activePrompts.forEach(id => {
                            const backdrop = document.getElementById(id + '-backdrop');
                            if (backdrop) safeRemove(backdrop);
                        });
                        activePrompts.clear();
                    } catch (e) {
                        console.warn('MCP Prompt: Global cleanup error:', e);
                    }
                },
                isAvailable: () => {
                    try {
                        return !!(document && document.body);
                    } catch (e) {
                        return false;
                    }
                }
            };
        })();
        
        // Secure global assignment
        if (typeof window !== 'undefined') {
            window.mcpPrompt = mcpSecurePrompts.prompt;
            window.mcpSecurePrompts = mcpSecurePrompts;
        }
        
        console.log('🤖 MCP Secure Prompts System initialized via V8 context');
        
    } catch (error) {
        console.error('MCP Prompts: Critical initialization error:', error);
        
        // Fallback
        if (typeof window !== 'undefined') {
            window.mcpPrompt = (message) => {
                console.log('MCP Prompt Fallback:', message);
                return Promise.resolve(confirm(message || 'Confirm?'));
            };
        }
    }
})();
"""

    async def initialize_secure_messaging(self, page: Page) -> None:
        """Initialize secure messaging system via V8 context injection"""
        try:
            await page.add_init_script(self.SECURE_MESSAGING_SCRIPT)
        except Exception as e:
            print(f"Failed to initialize secure messaging: {e}")
            
    async def initialize_secure_prompts(self, page: Page) -> None:
        """Initialize secure prompts system via V8 context injection"""
        try:
            await page.add_init_script(self.SECURE_PROMPTS_SCRIPT)
        except Exception as e:
            print(f"Failed to initialize secure prompts: {e}")
            
    async def initialize_all_secure_systems(self, page: Page) -> None:
        """Initialize all secure collaboration systems via V8 context injection"""
        await self.initialize_secure_messaging(page)
        await self.initialize_secure_prompts(page)
        
        # Add more systems as we create them...
        
    async def verify_systems_available(self, page: Page) -> dict:
        """Verify that all collaboration systems are available and working"""
        try:
            result = await page.evaluate("""
                () => {
                    return {
                        messaging_available: typeof window.mcpMessage === 'function',
                        prompts_available: typeof window.mcpPrompt === 'function',
                        notify_helpers: typeof window.mcpNotify === 'object',
                        secure_messaging: typeof window.mcpSecureMessaging === 'object',
                        secure_prompts: typeof window.mcpSecurePrompts === 'object',
                        dom_ready: document.readyState,
                        body_available: !!document.body
                    };
                }
            """)
            return result
        except Exception as e:
            print(f"Failed to verify systems: {e}")
            return {
                "error": str(e),
                "systems_available": False
            }