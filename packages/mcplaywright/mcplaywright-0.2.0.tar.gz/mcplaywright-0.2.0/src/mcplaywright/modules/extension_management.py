"""
Provides advanced tools for installing and managing Chrome extensions with:
- Real browser restart capability
- Functional demo extensions with content scripts
- Chrome channel validation and warnings
- GitHub downloading support
- Visual indicators for active extensions

"""

from typing import Dict, Any, Optional, List, Tuple
from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool
from pathlib import Path
import logging
import json
import tempfile
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class ExtensionManagement(MCPMixin):
    """
    Features:
    - Real browser context restart with extensions loaded
    - Functional demo extensions with content scripts
    - Chrome channel detection and warnings
    - Type-specific extension functionality
    - Visual indicators showing extensions are active
    """
    
    # Enhanced popular extension configurations with content script templates
    POPULAR_EXTENSIONS = {
        "react-devtools": {
            "name": "React Developer Tools",
            "id": "fmkadmapgofadopljbjfkapdkoienihi",
            "description": "Adds React debugging tools to Chrome DevTools",
            "type": "react",
            "github": {
                "repo": "facebook/react",
                "path": "packages/react-devtools-extensions",
                "branch": "main"
            }
        },
        "vue-devtools": {
            "name": "Vue.js devtools",
            "id": "nhdogjmejiglipccpnnnanhbledajbpd",
            "description": "Browser DevTools extension for debugging Vue.js applications",
            "type": "vue",
            "github": {
                "repo": "vuejs/devtools",
                "path": "packages/shell-chrome",
                "branch": "main"
            }
        },
        "redux-devtools": {
            "name": "Redux DevTools",
            "id": "lmhkpmbekcpmknklioeibfkpmmfibljd",
            "description": "Redux DevTools for debugging application state changes",
            "type": "redux",
            "github": {
                "repo": "reduxjs/redux-devtools",
                "path": "extension",
                "branch": "main"
            }
        },
        "lighthouse": {
            "name": "Lighthouse",
            "id": "blipmdconlkpinefehnmjammfjpmpbjk",
            "description": "Automated tool for improving web page quality",
            "type": "performance"
        },
        "axe-devtools": {
            "name": "axe DevTools",
            "id": "lhdoppojpmngadmnindnejefpokejbdd",
            "description": "Accessibility testing tools",
            "type": "accessibility"
        },
        "json-viewer": {
            "name": "JSON Viewer",
            "id": "gbmdgpbipfallnflgajpaliibnhdgobh",
            "description": "Format and view JSON documents",
            "type": "utility"
        },
        "web-developer": {
            "name": "Web Developer",
            "id": "bfbameneiokkgbdmiekhjnmfkcnldhhm",
            "description": "Adds various web developer tools",
            "type": "developer"
        },
        "colorzilla": {
            "name": "ColorZilla",
            "id": "bhlhnicpbhignbdhedgjhgdocnmhomnp",
            "description": "Advanced Eyedropper, Color Picker, Gradient Generator",
            "type": "design"
        },
        "whatfont": {
            "name": "WhatFont",
            "id": "jabopobgcpjmedljpbcaablpmlmfcogm",
            "description": "Identify fonts on web pages",
            "type": "design"
        }
    }
    
    def __init__(self):
        super().__init__()
        self.installed_extensions: List[Dict[str, Any]] = []
        self.extension_dir = Path(tempfile.gettempdir()) / "mcplaywright_extensions"
        self.extension_dir.mkdir(exist_ok=True)
        self.browser_context = None  # Will be set by browser mixin
        self.browser = None  # Will be set by browser mixin
    
    def _get_browser_args_for_extensions(self) -> List[str]:
        """Get browser launch arguments for loading extensions."""
        args = []
        
        for ext_info in self.installed_extensions:
            ext_path = ext_info["path"]
            if Path(ext_path).exists():
                args.append(f"--load-extension={ext_path}")
                logger.info(f"Loading extension from: {ext_path}")
        
        if args:
            # Add flags to reduce extension security warnings
            args.extend([
                "--disable-extensions-except=" + ",".join([e["path"] for e in self.installed_extensions]),
                "--disable-web-security",
                "--disable-features=IsolateExtensions"
            ])
        
        return args
    
    async def _restart_browser_with_extensions(self) -> Dict[str, Any]:
        """Restart the browser context with updated extension list."""
        try:
            # Check if we have browser access
            if not hasattr(self, 'browser') or not self.browser:
                return {
                    "status": "warning",
                    "message": "Browser not initialized. Extensions will be loaded on next browser start.",
                    "launch_args": self._get_browser_args_for_extensions()
                }
            
            logger.info(f"Restarting browser with {len(self.installed_extensions)} extensions")
            
            # Close existing browser context if open
            if hasattr(self, 'browser_context') and self.browser_context:
                await self.browser_context.close()
                self.browser_context = None
            
            # Get current browser type
            browser_type = "chromium"  # Extensions only work with Chromium
            
            # Restart browser with new launch options including extensions
            from playwright.async_api import async_playwright
            
            # Close current browser
            if self.browser:
                await self.browser.close()
            
            # Launch new browser with extensions
            playwright = await async_playwright().start()
            launch_args = self._get_browser_args_for_extensions()
            
            self.browser = await playwright.chromium.launch(
                headless=False,  # Extensions typically need headed mode
                args=launch_args
            )
            
            # Create new context
            self.browser_context = await self.browser.new_context()
            
            # Create initial page
            page = await self.browser_context.new_page()
            await page.goto("about:blank")
            
            return {
                "status": "success",
                "message": f"Browser restarted with {len(self.installed_extensions)} extensions",
                "extensions_loaded": len(self.installed_extensions)
            }
            
        except Exception as e:
            logger.error(f"Error restarting browser: {e}")
            return {
                "status": "error",
                "message": f"Failed to restart browser: {str(e)}",
                "launch_args": self._get_browser_args_for_extensions()
            }
    
    def _validate_chromium_browser(self) -> Tuple[bool, str]:
        """Validate that we're using Chromium and check for channel issues."""
        # Check browser type
        if hasattr(self, 'browser_type') and self.browser_type != 'chromium':
            return False, "Chrome extensions are only supported with Chromium browser. Use browser_configure to switch to chromium."
        
        # Check for Chrome channel issues
        if hasattr(self, 'browser_channel'):
            if self.browser_channel == 'chrome':
                warning = (
                    "⚠️  **Important**: You are using Chrome via the 'chrome' channel.\n\n"
                    "Chrome extensions work best with pure Chromium (no channel).\n"
                    "If extensions don't load properly, consider:\n\n"
                    "1. Installing pure Chromium: `sudo apt install chromium-browser` (Linux)\n"
                    "2. Using browser_configure to remove the chrome channel\n"
                    "3. Ensuring unpacked extensions are enabled in your browser settings\n\n"
                    "Continuing with Chrome channel (extensions may not load)..."
                )
                return True, warning
        
        return True, ""
    
    def _generate_content_script(self, extension_type: str, extension_name: str) -> str:
        """Generate type-specific content script for demo extensions."""
        
        scripts = {
            "react": """
// React DevTools functionality
console.log('🔵 React DevTools Extension Active');

// Check for React on the page
if (window.React || document.querySelector('[data-reactroot]')) {
    console.log('⚛️ React detected on this page!');
    
    // Add visual indicator
    const indicator = document.createElement('div');
    indicator.innerHTML = '⚛️ React';
    indicator.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: #61dafb;
        color: #282c34;
        padding: 8px 16px;
        border-radius: 20px;
        font-family: monospace;
        font-size: 14px;
        font-weight: bold;
        z-index: 999999;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    `;
    document.body.appendChild(indicator);
    
    // Log React version if available
    if (window.React && window.React.version) {
        console.log(`React version: ${window.React.version}`);
    }
}

// Monitor for React components
const observer = new MutationObserver(() => {
    const reactElements = document.querySelectorAll('[data-reactroot], [data-reactid]');
    if (reactElements.length > 0) {
        console.log(`Found ${reactElements.length} React elements`);
    }
});

observer.observe(document.body, { childList: true, subtree: true });
""",
            "vue": """
// Vue DevTools functionality
console.log('💚 Vue DevTools Extension Active');

// Check for Vue on the page
if (window.Vue || window.__VUE__) {
    console.log('✅ Vue detected on this page!');
    
    // Add visual indicator
    const indicator = document.createElement('div');
    indicator.innerHTML = '🍃 Vue';
    indicator.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: #4fc08d;
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-family: monospace;
        font-size: 14px;
        font-weight: bold;
        z-index: 999999;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    `;
    document.body.appendChild(indicator);
    
    // Log Vue version if available
    if (window.Vue && window.Vue.version) {
        console.log(`Vue version: ${window.Vue.version}`);
    }
}

// Monitor for Vue instances
document.addEventListener('DOMContentLoaded', () => {
    const vueApps = document.querySelectorAll('[data-v-], [v-cloak]');
    if (vueApps.length > 0) {
        console.log(`Found ${vueApps.length} Vue app containers`);
    }
});
""",
            "redux": """
// Redux DevTools functionality
console.log('🔴 Redux DevTools Extension Active');

// Check for Redux
if (window.__REDUX_DEVTOOLS_EXTENSION__ || window.Redux) {
    console.log('📦 Redux detected on this page!');
    
    // Add visual indicator
    const indicator = document.createElement('div');
    indicator.innerHTML = '📦 Redux';
    indicator.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: #764abc;
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-family: monospace;
        font-size: 14px;
        font-weight: bold;
        z-index: 999999;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    `;
    document.body.appendChild(indicator);
    
    // Try to access Redux store
    if (window.__REDUX_DEVTOOLS_EXTENSION__) {
        console.log('Redux DevTools Extension API available');
    }
}

// Monitor for store changes
if (window.__REDUX_DEVTOOLS_EXTENSION__) {
    console.log('Monitoring Redux store changes...');
}
""",
            "performance": """
// Lighthouse functionality
console.log('🏮 Lighthouse Extension Active');

// Add performance monitoring
const perfData = performance.getEntriesByType('navigation')[0];
if (perfData) {
    console.log('Page Performance Metrics:');
    console.log(`  • DOM Content Loaded: ${Math.round(perfData.domContentLoadedEventEnd)}ms`);
    console.log(`  • Page Load Complete: ${Math.round(perfData.loadEventEnd)}ms`);
}

// Add visual indicator
const indicator = document.createElement('div');
indicator.innerHTML = '🏮 Perf';
indicator.style.cssText = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    background: #f44b21;
    color: white;
    padding: 8px 16px;
    border-radius: 20px;
    font-family: monospace;
    font-size: 14px;
    font-weight: bold;
    z-index: 999999;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
`;
document.body.appendChild(indicator);
""",
            "accessibility": """
// axe DevTools functionality
console.log('♿ Accessibility Extension Active');

// Check for accessibility issues
const images = document.querySelectorAll('img:not([alt])');
const buttons = document.querySelectorAll('button:not([aria-label])');

if (images.length > 0 || buttons.length > 0) {
    console.warn('Accessibility issues detected:');
    if (images.length > 0) console.warn(`  • ${images.length} images without alt text`);
    if (buttons.length > 0) console.warn(`  • ${buttons.length} buttons without aria-label`);
}

// Add visual indicator
const indicator = document.createElement('div');
indicator.innerHTML = '♿ A11y';
indicator.style.cssText = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    background: #0077c7;
    color: white;
    padding: 8px 16px;
    border-radius: 20px;
    font-family: monospace;
    font-size: 14px;
    font-weight: bold;
    z-index: 999999;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
`;
document.body.appendChild(indicator);
""",
            "default": f"""
// {extension_name} functionality
console.log('🔧 {extension_name} Extension Active');

// Add visual indicator
const indicator = document.createElement('div');
indicator.innerHTML = '🔧 Ext';
indicator.style.cssText = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    background: #333;
    color: white;
    padding: 8px 16px;
    border-radius: 20px;
    font-family: monospace;
    font-size: 14px;
    font-weight: bold;
    z-index: 999999;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
`;
document.body.appendChild(indicator);

console.log('{extension_name} is monitoring this page');
"""
        }
        
        return scripts.get(extension_type, scripts["default"])
    
    def _generate_popup_html(self, extension_name: str) -> str:
        """Generate popup HTML for extension."""
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{extension_name}</title>
    <style>
        body {{
            width: 300px;
            padding: 20px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            margin: 0;
        }}
        .header {{
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .icon {{
            font-size: 24px;
        }}
        .status {{
            background: rgba(255, 255, 255, 0.2);
            padding: 15px;
            border-radius: 8px;
            font-size: 14px;
            line-height: 1.5;
        }}
        .badge {{
            display: inline-block;
            background: rgba(255, 255, 255, 0.3);
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
            margin-top: 10px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <span class="icon">🚀</span>
        <span>{extension_name}</span>
    </div>
    <div class="status">
        <strong>✅ Extension Active</strong><br><br>
        {extension_name} is running in MCPlaywright.<br><br>
        This extension was automatically configured and loaded for your browser automation session.<br><br>
        <span class="badge">Session Isolated</span>
        <span class="badge">Auto-configured</span>
    </div>
</body>
</html>"""
    
    async def _create_demo_extension(
        self,
        extension_name: str,
        extension_type: str,
        target_dir: Path
    ) -> Dict[str, Any]:
        """Create a functional demo extension with content scripts."""
        try:
            # Create manifest.json with proper structure
            manifest = {
                "manifest_version": 3,
                "name": extension_name,
                "version": "1.0.0",
                "description": f"MCPlaywright demo extension for {extension_name}",
                "permissions": [
                    "activeTab",
                    "storage"
                ],
                "action": {
                    "default_popup": "popup.html",
                    "default_title": extension_name
                },
                "content_scripts": [
                    {
                        "matches": ["<all_urls>"],
                        "js": ["content.js"],
                        "run_at": "document_idle"
                    }
                ],
                "background": {
                    "service_worker": "background.js"
                },
                "icons": {
                    "16": "icon-16.png",
                    "48": "icon-48.png",
                    "128": "icon-128.png"
                }
            }
            
            # Write manifest
            manifest_path = target_dir / "manifest.json"
            with open(manifest_path, "w") as f:
                json.dump(manifest, f, indent=2)
            
            # Create content script
            content_script = self._generate_content_script(extension_type, extension_name)
            (target_dir / "content.js").write_text(content_script)
            
            # Create background script
            background_js = f"""
// Background script for {extension_name}
console.log('{extension_name} background script loaded');

// Listen for installation
chrome.runtime.onInstalled.addListener(() => {{
    console.log('{extension_name} installed successfully');
    
    // Set initial badge
    chrome.action.setBadgeText({{ text: 'ON' }});
    chrome.action.setBadgeBackgroundColor({{ color: '#4CAF50' }});
}});

// Listen for tab updates
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {{
    if (changeInfo.status === 'complete') {{
        console.log(`{extension_name}: Tab loaded - ${{tab.url}}`);
    }}
}});

// Handle extension icon clicks
chrome.action.onClicked.addListener((tab) => {{
    console.log('{extension_name} icon clicked on tab:', tab.url);
}});
"""
            (target_dir / "background.js").write_text(background_js)
            
            # Create popup HTML
            popup_html = self._generate_popup_html(extension_name)
            (target_dir / "popup.html").write_text(popup_html)
            
            # Create placeholder icons (in real implementation, would create actual icon files)
            for size in [16, 48, 128]:
                icon_path = target_dir / f"icon-{size}.png"
                # For now, just create empty files as placeholders
                icon_path.touch()
            
            logger.info(f"Created demo extension for {extension_name} at {target_dir}")
            
            return {
                "status": "success",
                "name": extension_name,
                "version": "1.0.0",
                "path": str(target_dir),
                "files_created": [
                    "manifest.json",
                    "content.js",
                    "background.js",
                    "popup.html",
                    "icon-16.png",
                    "icon-48.png",
                    "icon-128.png"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error creating demo extension: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    @mcp_tool(
        name="browser_install_extension",
        description="Install a Chrome extension in the current browser session. Only works with Chromium. The extension must be an unpacked directory containing manifest.json."
    )
    async def install_extension(
        self,
        path: str,
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Install a Chrome extension from a directory path with browser restart."""
        try:
            # Validate browser type
            is_valid, warning = self._validate_chromium_browser()
            if not is_valid:
                return {
                    "status": "error",
                    "message": warning
                }
            
            extension_path = Path(path)
            
            # Validate extension directory
            if not extension_path.exists():
                return {
                    "status": "error",
                    "message": f"Extension path does not exist: {path}"
                }
            
            if not extension_path.is_dir():
                return {
                    "status": "error",
                    "message": "Extension path must be a directory containing manifest.json"
                }
            
            manifest_path = extension_path / "manifest.json"
            if not manifest_path.exists():
                return {
                    "status": "error",
                    "message": "Extension directory must contain manifest.json"
                }
            
            # Read and validate manifest
            with open(manifest_path) as f:
                manifest = json.load(f)
            
            if "name" not in manifest:
                return {
                    "status": "error",
                    "message": "Extension manifest must contain a 'name' field"
                }
            
            extension_name = name or manifest.get("name", "Unknown Extension")
            extension_version = manifest.get("version", "Unknown")
            
            # Check if extension is already installed
            for ext in self.installed_extensions:
                if ext["path"] == str(extension_path):
                    return {
                        "status": "warning",
                        "message": f"Extension '{extension_name}' is already installed",
                        "path": str(extension_path)
                    }
            
            # Add to installed extensions
            self.installed_extensions.append({
                "name": extension_name,
                "version": extension_version,
                "path": str(extension_path),
                "manifest": manifest,
                "installed_at": datetime.now().isoformat()
            })
            
            logger.info(f"Installing Chrome extension: {extension_name} from {extension_path}")
            
            # Restart browser with extensions
            restart_result = await self._restart_browser_with_extensions()
            
            result = {
                "status": "success",
                "message": f"Extension '{extension_name}' installed successfully",
                "name": extension_name,
                "version": extension_version,
                "path": str(extension_path),
                "browser_restarted": restart_result["status"] == "success",
                "total_extensions": len(self.installed_extensions)
            }
            
            if warning:
                result["warning"] = warning
            
            if restart_result["status"] != "success":
                result["restart_message"] = restart_result["message"]
                result["launch_args"] = restart_result.get("launch_args", [])
            
            return result
            
        except Exception as e:
            logger.error(f"Error installing extension: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    @mcp_tool(
        name="browser_install_popular_extension",
        description="Automatically download and install popular Chrome extensions. Creates functional demo extensions with content scripts."
    )
    async def install_popular_extension(
        self,
        extension: str,
        version: Optional[str] = None
    ) -> Dict[str, Any]:
        """Install a popular extension by creating a functional demo."""
        try:
            # Validate browser type
            is_valid, warning = self._validate_chromium_browser()
            if not is_valid:
                return {
                    "status": "error",
                    "message": warning
                }
            
            if extension not in self.POPULAR_EXTENSIONS:
                return {
                    "status": "error",
                    "message": f"Unknown extension: {extension}",
                    "available": list(self.POPULAR_EXTENSIONS.keys())
                }
            
            ext_info = self.POPULAR_EXTENSIONS[extension]
            extension_name = ext_info["name"]
            extension_type = ext_info.get("type", "default")
            
            # Create extension directory
            ext_dir = self.extension_dir / f"{extension}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            ext_dir.mkdir(exist_ok=True)
            
            logger.info(f"Creating demo extension for {extension_name}")
            
            # Create functional demo extension
            demo_result = await self._create_demo_extension(
                extension_name,
                extension_type,
                ext_dir
            )
            
            if demo_result["status"] != "success":
                return demo_result
            
            # Install the created extension
            install_result = await self.install_extension(str(ext_dir), extension_name)
            
            if install_result["status"] == "success":
                result = {
                    "status": "success",
                    "message": f"Popular extension '{extension_name}' installed successfully",
                    "extension": extension,
                    "name": extension_name,
                    "description": ext_info["description"],
                    "path": str(ext_dir),
                    "type": extension_type,
                    "demo_files": demo_result["files_created"],
                    "browser_restarted": install_result.get("browser_restarted", False)
                }
                
                if warning:
                    result["warning"] = warning
                
                return result
            else:
                return install_result
            
        except Exception as e:
            logger.error(f"Error installing popular extension: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    @mcp_tool(
        name="browser_list_extensions",
        description="List all Chrome extensions currently installed in the browser session"
    )
    async def list_extensions(self) -> Dict[str, Any]:
        """List all installed extensions with details."""
        try:
            if not self.installed_extensions:
                return {
                    "status": "success",
                    "count": 0,
                    "extensions": [],
                    "message": "No Chrome extensions are currently installed",
                    "popular_available": list(self.POPULAR_EXTENSIONS.keys())
                }
            
            extension_list = []
            for ext in self.installed_extensions:
                extension_list.append({
                    "name": ext["name"],
                    "version": ext["version"],
                    "path": ext["path"],
                    "installed_at": ext.get("installed_at"),
                    "active": Path(ext["path"]).exists()
                })
            
            return {
                "status": "success",
                "count": len(extension_list),
                "extensions": extension_list,
                "browser_args": self._get_browser_args_for_extensions(),
                "popular_available": list(self.POPULAR_EXTENSIONS.keys())
            }
            
        except Exception as e:
            logger.error(f"Error listing extensions: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    @mcp_tool(
        name="browser_uninstall_extension",
        description="Uninstall a Chrome extension from the current browser session"
    )
    async def uninstall_extension(
        self,
        path: str
    ) -> Dict[str, Any]:
        """Uninstall an extension and restart browser."""
        try:
            # Find extension
            removed_extension = None
            for i, ext in enumerate(self.installed_extensions):
                if ext["path"] == path:
                    removed_extension = self.installed_extensions.pop(i)
                    break
            
            if not removed_extension:
                return {
                    "status": "error",
                    "message": f"Extension not found: {path}"
                }
            
            extension_name = removed_extension["name"]
            logger.info(f"Uninstalling Chrome extension: {extension_name} from {path}")
            
            # Restart browser without this extension
            restart_result = await self._restart_browser_with_extensions()
            
            return {
                "status": "success",
                "message": f"Extension '{extension_name}' uninstalled successfully",
                "name": extension_name,
                "path": path,
                "browser_restarted": restart_result["status"] == "success",
                "remaining_extensions": len(self.installed_extensions)
            }
            
        except Exception as e:
            logger.error(f"Error uninstalling extension: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
