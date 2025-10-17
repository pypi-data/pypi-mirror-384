"""
Provides a Django-style debug toolbar for identifying which MCP client is controlling
the browser. This solves the problem of running multiple MCP clients in parallel.
"""

from typing import Dict, Any, Optional, List
from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool
import json
import base64
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ClientIdentification(MCPMixin):
    """
    Provides a visual toolbar to identify which MCP client is controlling the browser,
    along with custom code injection capabilities for enhanced debugging.
    """
    
    def __init__(self):
        super().__init__()
        self.injections: Dict[str, Dict[str, Any]] = {}
        self.toolbar_enabled = False
        self.toolbar_config = {
            "position": "bottom-right",
            "theme": "dark",
            "opacity": 0.9,
            "minimized": False,
            "showDetails": True,
            "projectName": "MCPlaywright"
        }
        self.auto_inject = True
        
    def _generate_debug_toolbar_html(self) -> str:
        """Generate the HTML for the debug toolbar."""
        config = self.toolbar_config
        
        # Generate unique session ID
        session_id = f"mcp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        toolbar_html = f"""
        <!-- MCP Client Debug Toolbar -->
        <div id="mcp-debug-toolbar" data-session="{session_id}" style="
            position: fixed;
            {config['position'].split('-')[0]}: 20px;
            {config['position'].split('-')[1]}: 20px;
            background: {'#1a1a1a' if config['theme'] == 'dark' else '#ffffff'};
            color: {'#ffffff' if config['theme'] == 'dark' else '#000000'};
            border: 2px solid {'#4CAF50' if config['theme'] == 'dark' else '#2196F3'};
            border-radius: 8px;
            padding: 10px 15px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 12px;
            z-index: 999999;
            opacity: {config['opacity']};
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            transition: all 0.3s ease;
            min-width: 200px;
        ">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center;">
                    <span style="
                        display: inline-block;
                        width: 10px;
                        height: 10px;
                        background: #4CAF50;
                        border-radius: 50%;
                        margin-right: 8px;
                        animation: pulse 2s infinite;
                    "></span>
                    <strong>{config['projectName']}</strong>
                </div>
                <button onclick="toggleMCPToolbar()" style="
                    background: none;
                    border: none;
                    color: inherit;
                    cursor: pointer;
                    font-size: 16px;
                    padding: 0;
                    margin-left: 10px;
                ">{'▼' if not config['minimized'] else '▲'}</button>
            </div>
            
            <div id="mcp-toolbar-details" style="{'display: none;' if config['minimized'] else 'display: block;'} margin-top: 10px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.2);">
                <div style="margin: 5px 0;">
                    <span style="opacity: 0.7;">Session:</span> {session_id}
                </div>
                <div style="margin: 5px 0;">
                    <span style="opacity: 0.7;">Client:</span> Python MCPlaywright
                </div>
                <div style="margin: 5px 0;">
                    <span style="opacity: 0.7;">Time:</span> <span id="mcp-time">{datetime.now().strftime('%H:%M:%S')}</span>
                </div>
                <div style="margin: 5px 0;">
                    <span style="opacity: 0.7;">Injections:</span> <span id="mcp-injection-count">{len(self.injections)}</span>
                </div>
            </div>
        </div>
        
        <style>
            @keyframes pulse {{
                0% {{ opacity: 1; }}
                50% {{ opacity: 0.5; }}
                100% {{ opacity: 1; }}
            }}
            
            #mcp-debug-toolbar:hover {{
                opacity: 1 !important;
                box-shadow: 0 6px 20px rgba(76, 175, 80, 0.4);
            }}
        </style>
        
        <script>
            function toggleMCPToolbar() {{
                const details = document.getElementById('mcp-toolbar-details');
                const toolbar = document.getElementById('mcp-debug-toolbar');
                if (details.style.display === 'none') {{
                    details.style.display = 'block';
                    toolbar.style.minWidth = '250px';
                }} else {{
                    details.style.display = 'none';
                    toolbar.style.minWidth = '200px';
                }}
            }}
            
            // Update time every second
            setInterval(() => {{
                const timeEl = document.getElementById('mcp-time');
                if (timeEl) {{
                    timeEl.textContent = new Date().toLocaleTimeString();
                }}
            }}, 1000);
            
            // Log toolbar activation
            console.log('%c🎭 MCP Client Debug Toolbar Active', 'color: #4CAF50; font-size: 14px; font-weight: bold;');
            console.log('Session: {session_id}');
            console.log('Client: {config["projectName"]}');
        </script>
        """
        
        return toolbar_html
    
    def _wrap_for_llm_safety(self, html: str) -> str:
        """Wrap HTML in comments to prevent LLM interpretation."""
        return f"<!-- MCP_INJECTION_START -->\n{html}\n<!-- MCP_INJECTION_END -->"
    
    @mcp_tool(
        name="browser_enable_debug_toolbar",
        description="Enable the debug toolbar to identify which MCP client is controlling the browser"
    )
    async def enable_debug_toolbar(
        self,
        position: str = "bottom-right",
        theme: str = "dark",
        opacity: float = 0.9,
        minimized: bool = False,
        show_details: bool = True,
        project_name: str = "MCPlaywright"
    ) -> Dict[str, Any]:
        """Enable the MCP client debug toolbar."""
        try:
            # Update toolbar configuration
            self.toolbar_config.update({
                "position": position,
                "theme": theme,
                "opacity": opacity,
                "minimized": minimized,
                "showDetails": show_details,
                "projectName": project_name
            })
            
            # Generate toolbar HTML
            toolbar_html = self._generate_debug_toolbar_html()
            
            # Inject into current page
            page = await self.get_current_page()
            
            # Inject toolbar HTML
            await page.evaluate(f"""
                (() => {{
                    // Remove existing toolbar if present
                    const existing = document.getElementById('mcp-debug-toolbar');
                    if (existing) {{
                        existing.remove();
                    }}
                    
                    // Create container and inject HTML
                    const container = document.createElement('div');
                    container.innerHTML = `{toolbar_html}`;
                    document.body.appendChild(container.firstElementChild);
                    
                    return true;
                }})();
            """)
            
            self.toolbar_enabled = True
            
            # Store in injections
            self.injections["debug_toolbar"] = {
                "type": "toolbar",
                "name": "Debug Toolbar",
                "config": self.toolbar_config,
                "auto_inject": True,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Debug toolbar enabled: {project_name}")
            
            return {
                "status": "success",
                "message": "Debug toolbar enabled",
                "config": self.toolbar_config,
                "session": f"mcp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
            
        except Exception as e:
            logger.error(f"Error enabling debug toolbar: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    @mcp_tool(
        name="browser_inject_custom_code",
        description="Inject custom JavaScript or CSS code into all pages in the current session"
    )
    async def inject_custom_code(
        self,
        name: str,
        code: str,
        type: str = "javascript",
        auto_inject: bool = True,
        persistent: bool = False
    ) -> Dict[str, Any]:
        """Inject custom JavaScript or CSS code."""
        try:
            page = await self.get_current_page()
            
            if type == "javascript":
                # Wrap JavaScript in IIFE for safety
                wrapped_code = f"""
                    (function() {{
                        try {{
                            {code}
                            console.log('MCP Injection "{name}" executed successfully');
                        }} catch (e) {{
                            console.error('MCP Injection "{name}" error:', e);
                        }}
                    }})();
                """
                await page.evaluate(wrapped_code)
                
            elif type == "css":
                # Inject CSS via style tag
                wrapped_code = f"""
                    (() => {{
                        const style = document.createElement('style');
                        style.setAttribute('data-mcp-injection', '{name}');
                        style.textContent = `{code}`;
                        document.head.appendChild(style);
                        return true;
                    }})();
                """
                await page.evaluate(wrapped_code)
            
            else:
                return {
                    "status": "error",
                    "message": f"Invalid type: {type}. Must be 'javascript' or 'css'"
                }
            
            # Store injection for persistence
            self.injections[name] = {
                "name": name,
                "type": type,
                "code": code,
                "auto_inject": auto_inject,
                "persistent": persistent,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Custom {type} injection '{name}' applied")
            
            return {
                "status": "success",
                "message": f"Custom {type} injected successfully",
                "name": name,
                "auto_inject": auto_inject,
                "injection_count": len(self.injections)
            }
            
        except Exception as e:
            logger.error(f"Error injecting custom code: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    @mcp_tool(
        name="browser_list_injections",
        description="List all active code injections for the current session",
        annotations={"readOnlyHint": True}
    )
    async def list_injections(self) -> Dict[str, Any]:
        """List all active code injections."""
        try:
            injection_list = []
            
            for key, injection in self.injections.items():
                injection_list.append({
                    "key": key,
                    "name": injection.get("name"),
                    "type": injection.get("type"),
                    "auto_inject": injection.get("auto_inject", False),
                    "persistent": injection.get("persistent", False),
                    "timestamp": injection.get("timestamp")
                })
            
            return {
                "status": "success",
                "toolbar_enabled": self.toolbar_enabled,
                "injection_count": len(injection_list),
                "injections": injection_list
            }
            
        except Exception as e:
            logger.error(f"Error listing injections: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    @mcp_tool(
        name="browser_disable_debug_toolbar",
        description="Disable the debug toolbar for the current session"
    )
    async def disable_debug_toolbar(self) -> Dict[str, Any]:
        """Disable the debug toolbar."""
        try:
            page = await self.get_current_page()
            
            # Remove toolbar from page
            await page.evaluate("""
                (() => {
                    const toolbar = document.getElementById('mcp-debug-toolbar');
                    if (toolbar) {
                        toolbar.remove();
                        return true;
                    }
                    return false;
                })();
            """)
            
            # Remove from injections
            if "debug_toolbar" in self.injections:
                del self.injections["debug_toolbar"]
            
            self.toolbar_enabled = False
            
            logger.info("Debug toolbar disabled")
            
            return {
                "status": "success",
                "message": "Debug toolbar disabled"
            }
            
        except Exception as e:
            logger.error(f"Error disabling debug toolbar: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    @mcp_tool(
        name="browser_clear_injections",
        description="Remove all custom code injections (keeps debug toolbar)"
    )
    async def clear_injections(
        self,
        include_toolbar: bool = False
    ) -> Dict[str, Any]:
        """Clear all code injections."""
        try:
            page = await self.get_current_page()
            
            # Remove all injection elements from page
            await page.evaluate("""
                (() => {
                    // Remove injected styles
                    const styles = document.querySelectorAll('style[data-mcp-injection]');
                    styles.forEach(s => s.remove());
                    
                    // Log cleanup
                    console.log('MCP injections cleared');
                    
                    return styles.length;
                })();
            """)
            
            # Clear injection registry
            cleared_count = 0
            keys_to_remove = []
            
            for key in self.injections.keys():
                if key != "debug_toolbar" or include_toolbar:
                    keys_to_remove.append(key)
                    cleared_count += 1
            
            for key in keys_to_remove:
                del self.injections[key]
            
            if include_toolbar:
                await self.disable_debug_toolbar()
            
            logger.info(f"Cleared {cleared_count} injections")
            
            return {
                "status": "success",
                "message": f"Cleared {cleared_count} injections",
                "remaining": len(self.injections)
            }
            
        except Exception as e:
            logger.error(f"Error clearing injections: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _auto_inject_on_navigation(self, page):
        """Automatically inject persistent code on new pages."""
        if not self.auto_inject:
            return
        
        for injection in self.injections.values():
            if injection.get("auto_inject", False):
                if injection["type"] == "toolbar":
                    # Re-inject toolbar
                    toolbar_html = self._generate_debug_toolbar_html()
                    await page.evaluate(f"""
                        (() => {{
                            const container = document.createElement('div');
                            container.innerHTML = `{toolbar_html}`;
                            document.body.appendChild(container.firstElementChild);
                        }})();
                    """)
                elif injection["type"] == "javascript":
                    await page.evaluate(injection["code"])
                elif injection["type"] == "css":
                    await page.evaluate(f"""
                        (() => {{
                            const style = document.createElement('style');
                            style.setAttribute('data-mcp-injection', '{injection["name"]}');
                            style.textContent = `{injection["code"]}`;
                            document.head.appendChild(style);
                        }})();
                    """)
        
        logger.info(f"Auto-injected {len(self.injections)} items on new page")
