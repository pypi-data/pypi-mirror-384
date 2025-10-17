"""
Interactive element selection system for AI-Human collaboration.

Provides JavaScript functions for models to request user element selection:
- mcpInspector.start() - Interactive element selection with visual feedback
- mcpInspector.stop() - Stop inspection programmatically
"""

from typing import Dict, Any, Optional, Callable, Union
from pydantic import BaseModel
from playwright.async_api import Page
import json

class ElementDetails(BaseModel):
    """Detailed information about a user-selected element"""
    tag_name: str
    id: Optional[str] = None
    class_name: Optional[str] = None
    text_content: Optional[str] = None
    xpath: str
    attributes: Dict[str, Any]
    bounding_rect: Dict[str, float]
    visible: bool

class ElementInspector:
    """
    Interactive element selection system enabling AI models to request
    users to click on specific elements for precise automation.
    
    Features visual element highlighting and detailed element information extraction.
    """
    
    INSPECTOR_SCRIPT = """
// MCP Interactive Element Inspector System
// Visual element selection with detailed information extraction

if (typeof window.mcpInspectorInit === 'undefined') {
    window.mcpInspectorInit = true;
    
    class MCPElementInspector {
        constructor() {
            this.isActive = false;
            this.callback = null;
            this.instructions = null;
            this.highlightedElement = null;
            this.overlay = null;
            this.messageBox = null;
        }
        
        start(instructions, callback) {
            if (this.isActive) {
                this.stop();
            }
            
            this.isActive = true;
            this.instructions = instructions;
            this.callback = callback;
            
            this.createInspectorUI();
            this.attachEventListeners();
            
            console.log('🔍 MCP Element Inspector started:', instructions);
        }
        
        stop() {
            if (!this.isActive) return;
            
            this.isActive = false;
            this.callback = null;
            this.instructions = null;
            
            this.removeHighlight();
            this.removeInspectorUI();
            this.detachEventListeners();
            
            console.log('🔍 MCP Element Inspector stopped');
        }
        
        createInspectorUI() {
            // Create overlay for visual feedback
            this.overlay = document.createElement('div');
            this.overlay.id = 'mcp-inspector-overlay';
            this.overlay.style.cssText = `
                position: absolute;
                pointer-events: none;
                border: 2px solid #00ff00;
                background: rgba(0, 255, 0, 0.1);
                border-radius: 4px;
                z-index: 999998;
                transition: all 0.1s ease;
                box-shadow: 0 0 15px rgba(0, 255, 0, 0.5);
            `;
            document.body.appendChild(this.overlay);
            
            // Create instruction message box
            this.messageBox = document.createElement('div');
            this.messageBox.id = 'mcp-inspector-message';
            this.messageBox.style.cssText = `
                position: fixed;
                top: 20px;
                left: 50%;
                transform: translateX(-50%);
                background: rgba(0, 0, 0, 0.95);
                border: 2px solid #00ff00;
                border-radius: 8px;
                padding: 16px 20px;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                font-size: 14px;
                font-weight: bold;
                z-index: 999999;
                box-shadow: 0 0 25px rgba(0, 255, 0, 0.4);
                max-width: 90vw;
                text-align: center;
                animation: mcpInspectorPulse 2s ease-in-out infinite;
            `;
            
            this.messageBox.innerHTML = `
                <div style="margin-bottom: 8px;">🔍 ELEMENT INSPECTOR ACTIVE</div>
                <div style="font-size: 12px; color: #88ff88;">${this.instructions}</div>
                <div style="font-size: 11px; color: #66cc66; margin-top: 8px;">Press ESC to cancel</div>
            `;
            
            document.body.appendChild(this.messageBox);
            
            // Add inspector styles
            if (!document.getElementById('mcp-inspector-styles')) {
                const styleSheet = document.createElement('style');
                styleSheet.id = 'mcp-inspector-styles';
                styleSheet.innerHTML = `
                    @keyframes mcpInspectorPulse {
                        0%, 100% { box-shadow: 0 0 25px rgba(0, 255, 0, 0.4); }
                        50% { box-shadow: 0 0 35px rgba(0, 255, 0, 0.6); }
                    }
                    
                    .mcp-inspector-cursor {
                        cursor: crosshair !important;
                    }
                `;
                document.head.appendChild(styleSheet);
            }
            
            // Add cursor style
            document.body.classList.add('mcp-inspector-cursor');
        }
        
        removeInspectorUI() {
            if (this.overlay && this.overlay.parentNode) {
                this.overlay.parentNode.removeChild(this.overlay);
            }
            if (this.messageBox && this.messageBox.parentNode) {
                this.messageBox.parentNode.removeChild(this.messageBox);
            }
            
            document.body.classList.remove('mcp-inspector-cursor');
            
            this.overlay = null;
            this.messageBox = null;
        }
        
        attachEventListeners() {
            this.handleMouseMove = this.handleMouseMove.bind(this);
            this.handleClick = this.handleClick.bind(this);
            this.handleKeydown = this.handleKeydown.bind(this);
            
            document.addEventListener('mousemove', this.handleMouseMove, true);
            document.addEventListener('click', this.handleClick, true);
            document.addEventListener('keydown', this.handleKeydown, true);
        }
        
        detachEventListeners() {
            document.removeEventListener('mousemove', this.handleMouseMove, true);
            document.removeEventListener('click', this.handleClick, true);
            document.removeEventListener('keydown', this.handleKeydown, true);
        }
        
        handleMouseMove(event) {
            if (!this.isActive) return;
            
            const element = event.target;
            if (element === this.overlay || element === this.messageBox) return;
            
            this.highlightElement(element);
        }
        
        handleClick(event) {
            if (!this.isActive) return;
            
            event.preventDefault();
            event.stopPropagation();
            
            const element = event.target;
            if (element === this.overlay || element === this.messageBox) return;
            
            const elementDetails = this.extractElementDetails(element);
            
            this.stop();
            
            if (this.callback) {
                this.callback(elementDetails);
            }
        }
        
        handleKeydown(event) {
            if (!this.isActive) return;
            
            if (event.key === 'Escape') {
                event.preventDefault();
                this.stop();
                
                // Call callback with null to indicate cancellation
                if (this.callback) {
                    this.callback(null);
                }
            }
        }
        
        highlightElement(element) {
            if (!this.overlay || element === this.highlightedElement) return;
            
            this.highlightedElement = element;
            
            const rect = element.getBoundingClientRect();
            const scrollX = window.pageXOffset || document.documentElement.scrollLeft;
            const scrollY = window.pageYOffset || document.documentElement.scrollTop;
            
            this.overlay.style.left = (rect.left + scrollX - 2) + 'px';
            this.overlay.style.top = (rect.top + scrollY - 2) + 'px';
            this.overlay.style.width = (rect.width + 4) + 'px';
            this.overlay.style.height = (rect.height + 4) + 'px';
            this.overlay.style.display = 'block';
        }
        
        removeHighlight() {
            if (this.overlay) {
                this.overlay.style.display = 'none';
            }
            this.highlightedElement = null;
        }
        
        extractElementDetails(element) {
            // Generate XPath for element
            const generateXPath = (element) => {
                if (element.id !== '') {
                    return `//*[@id="${element.id}"]`;
                }
                
                if (element === document.body) {
                    return '/html/body';
                }
                
                let ix = 0;
                const siblings = element.parentNode.childNodes;
                for (let i = 0; i < siblings.length; i++) {
                    const sibling = siblings[i];
                    if (sibling === element) {
                        return generateXPath(element.parentNode) + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
                    }
                    if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
                        ix++;
                    }
                }
            };
            
            // Extract all attributes
            const attributes = {};
            if (element.attributes) {
                for (let i = 0; i < element.attributes.length; i++) {
                    const attr = element.attributes[i];
                    attributes[attr.name] = attr.value;
                }
            }
            
            // Get bounding rectangle
            const rect = element.getBoundingClientRect();
            const boundingRect = {
                x: rect.x,
                y: rect.y,
                width: rect.width,
                height: rect.height,
                top: rect.top,
                right: rect.right,
                bottom: rect.bottom,
                left: rect.left
            };
            
            // Extract text content (truncated to 100 chars)
            let textContent = element.textContent || element.innerText || '';
            textContent = textContent.trim();
            if (textContent.length > 100) {
                textContent = textContent.substring(0, 100) + '...';
            }
            
            return {
                tagName: element.tagName.toLowerCase(),
                id: element.id || null,
                className: element.className || null,
                textContent: textContent || null,
                xpath: generateXPath(element),
                attributes: attributes,
                boundingRect: boundingRect,
                visible: rect.width > 0 && rect.height > 0 && 
                        getComputedStyle(element).visibility !== 'hidden'
            };
        }
    }
    
    // Global inspector instance
    window.mcpInspector = new MCPElementInspector();

    console.log('🔍 MCP Element Inspector System initialized');
}
"""

    async def initialize(self, page: Page) -> None:
        """Initialize the element inspector system using V8 context injection"""
        try:
            # Use addInitScript for V8 context injection - safer and more reliable
            await page.add_init_script(self.INSPECTOR_SCRIPT)
            
            # Verify initialization
            await page.wait_for_function(
                "() => typeof window.mcpInspector === 'object' && window.mcpInspector.start",
                timeout=5000
            )
        except Exception as e:
            print(f"Warning: Failed to initialize inspector system: {e}")
            # Could add secure fallback here if needed
        
    async def start_inspection(
        self, 
        page: Page, 
        instructions: str,
        timeout: int = 60000
    ) -> Optional[ElementDetails]:
        """
        Start interactive element selection and wait for user to click an element.
        
        Args:
            page: Playwright page instance
            instructions: Instructions to show the user
            timeout: Maximum time to wait for selection (ms)
            
        Returns:
            ElementDetails if element was selected, None if cancelled/timeout
        """
        
        try:
            # Start the inspector and wait for element selection
            result = await page.evaluate(f"""
                new Promise((resolve, reject) => {{
                    const timeoutId = setTimeout(() => {{
                        mcpInspector.stop();
                        resolve(null);
                    }}, {timeout});
                    
                    mcpInspector.start('{instructions}', (elementDetails) => {{
                        clearTimeout(timeoutId);
                        resolve(elementDetails);
                    }});
                }})
            """)
            
            if result is None:
                return None
                
            # Convert JavaScript result to Python ElementDetails
            return ElementDetails(
                tag_name=result.get('tagName', 'unknown'),
                id=result.get('id'),
                class_name=result.get('className'),
                text_content=result.get('textContent'),
                xpath=result.get('xpath', ''),
                attributes=result.get('attributes', {}),
                bounding_rect=result.get('boundingRect', {}),
                visible=result.get('visible', False)
            )
            
        except Exception as e:
            # If inspection fails, stop inspector and return None
            await self.stop_inspection(page)
            return None
            
    async def stop_inspection(self, page: Page) -> None:
        """Stop the element inspector programmatically"""
        await page.evaluate("mcpInspector.stop()")
        
    async def request_element_selection(
        self,
        page: Page,
        element_description: str,
        purpose: str = ""
    ) -> Optional[ElementDetails]:
        """
        High-level helper to request user to select a specific type of element.
        
        Args:
            element_description: What type of element to select (e.g., "login button")
            purpose: What you plan to do with it (e.g., "to log in")
        """
        
        instructions = f"Please click on the {element_description}"
        if purpose:
            instructions += f" {purpose}"
            
        return await self.start_inspection(page, instructions)
        
    async def collaborative_form_filling(
        self,
        page: Page,
        form_fields: list[str]
    ) -> Dict[str, Optional[ElementDetails]]:
        """
        Guide user through selecting multiple form fields in sequence.
        
        Returns:
            Dictionary mapping field names to their ElementDetails
        """
        
        results = {}
        
        for field_name in form_fields:
            element = await self.request_element_selection(
                page,
                f"{field_name} field",
                f"so I can enter the {field_name}"
            )
            
            if element is None:
                # User cancelled, stop the process
                break
                
            results[field_name] = element
            
        return results