#!/usr/bin/env python3
"""
MCPlaywright Demo Script

Demonstrates the core capabilities of MCPlaywright including browser automation,
session management, UI customization, and advanced features.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mcplaywright-demo")

# Add src to path
import sys
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import MCPlaywright components
from mcplaywright.server import health_check, server_info, test_playwright_installation
from mcplaywright.session_manager import initialize_session_manager, cleanup_session_manager
from mcplaywright.tools.browser import (
    browser_navigate, NavigateParams,
    browser_screenshot, ScreenshotParams,
    browser_click, ClickParams,
    browser_get_page_info,
    browser_close_session, CloseSessionParams
)
from mcplaywright.tools.configure import (
    browser_configure, BrowserConfigureParams,
    browser_list_sessions, SessionListParams,
    browser_get_session_info
)


async def demo_server_health():
    """Demonstrate server health and info endpoints"""
    print("\n🏥 Server Health & Information")
    print("=" * 40)
    
    # Check server health
    health = await health_check()
    print(f"✅ Health Status: {health['status']}")
    print(f"📋 Version: {health['version']}")
    print(f"⏰ Uptime: {health['uptime']}")
    print(f"🎭 Playwright Available: {health['playwright_available']}")
    
    # Get server information
    info = await server_info()
    print(f"\n📊 Server: {info['name']} v{info['version']}")
    print(f"🐍 Python: {info['python_version']}")
    print(f"🌐 Browsers: {', '.join(info['supported_browsers'])}")
    print(f"⚡ Capabilities: {len(info['capabilities'])} features")
    
    # Test Playwright installation
    playwright_test = await test_playwright_installation()
    if playwright_test['success']:
        browsers = playwright_test['available_browsers']
        print(f"🎭 Playwright: {len(browsers)} browser(s) available - {', '.join(browsers)}")
    else:
        print(f"❌ Playwright Test Failed: {playwright_test['error']}")


async def demo_browser_configuration():
    """Demonstrate advanced browser configuration"""
    print("\n🔧 Browser Configuration")
    print("=" * 40)
    
    # Configure browser with UI customization features
    print("🎨 Configuring browser with UI customization...")
    config_result = await browser_configure(
        BrowserConfigureParams(
            headless=True,  # For demo purposes
            viewport_width=1920,
            viewport_height=1080,
            slow_mo=200,  # Visual delays for demonstration
            args=[
                "--force-color-profile=srgb",
                "--disable-web-security"
            ],
            locale="en-US",
            timezone="America/New_York",
            permissions=["geolocation"]
        )
    )
    
    if config_result['success']:
        session_id = config_result['session_id']
        print(f"✅ Browser configured successfully!")
        print(f"📱 Session ID: {session_id}")
        print(f"🔧 Updates Applied: {', '.join(config_result['updates_applied'])}")
        
        if 'slow_mo_info' in config_result:
            print(f"🎬 {config_result['slow_mo_info']}")
        
        return session_id
    else:
        print(f"❌ Configuration failed: {config_result['error']}")
        return None


async def demo_browser_automation(session_id: str):
    """Demonstrate browser automation capabilities"""
    print("\n🌐 Browser Automation")
    print("=" * 40)
    
    # Navigate to a test page
    print("🧭 Navigating to example.com...")
    nav_result = await browser_navigate(
        NavigateParams(
            url="https://example.com",
            session_id=session_id,
            wait_until="networkidle"
        )
    )
    
    if nav_result['success']:
        print(f"✅ Navigation successful!")
        print(f"📄 Page Title: {nav_result['title']}")
        print(f"🔗 Final URL: {nav_result['url']}")
    else:
        print(f"❌ Navigation failed: {nav_result['error']}")
        return False
    
    # Get page information
    print("\n📋 Getting page information...")
    page_info = await browser_get_page_info(session_id)
    
    if page_info['success']:
        print(f"✅ Page Info Retrieved:")
        print(f"   Title: {page_info['title']}")
        print(f"   URL: {page_info['url']}")
        print(f"   Viewport: {page_info['viewport']['width']}x{page_info['viewport']['height']}")
        print(f"   Ready State: {page_info['ready_state']}")
    
    # Take a screenshot
    print("\n📸 Taking screenshot...")
    screenshot_result = await browser_screenshot(
        ScreenshotParams(
            session_id=session_id,
            filename="demo-example-page.png",
            full_page=True,
            format="png"
        )
    )
    
    if screenshot_result['success']:
        print(f"✅ Screenshot saved successfully!")
        print(f"📁 File: {screenshot_result['filename']}")
        print(f"📏 Size: {screenshot_result['size_bytes']} bytes")
        print(f"📍 Path: {screenshot_result['path']}")
    else:
        print(f"❌ Screenshot failed: {screenshot_result['error']}")
    
    return True


async def demo_session_management():
    """Demonstrate session management capabilities"""
    print("\n👥 Session Management")
    print("=" * 40)
    
    # List all active sessions
    sessions_result = await browser_list_sessions(
        SessionListParams(include_details=True)
    )
    
    if sessions_result['success']:
        print(f"📊 Active Sessions: {sessions_result['session_count']}")
        print(f"📈 Statistics:")
        stats = sessions_result['statistics']
        print(f"   Max Concurrent: {stats['max_concurrent_sessions']}")
        print(f"   Session Timeout: {stats['session_timeout']}s")
        print(f"   Video Recording Sessions: {stats['video_recording_sessions']}")
        print(f"   Request Monitoring Sessions: {stats['request_monitoring_sessions']}")
        
        # Show session details
        for session in sessions_result['sessions']:
            print(f"\n🔍 Session: {session['session_id']}")
            print(f"   Browser: {session.get('browser_type', 'Unknown')}")
            print(f"   Created: {session.get('created_at', 'Unknown')}")
            print(f"   Pages: {session.get('pages', 0)}")
            print(f"   Video Recording: {session.get('video_recording', False)}")
            print(f"   Request Monitoring: {session.get('request_monitoring', False)}")


async def demo_advanced_configuration():
    """Demonstrate advanced configuration features"""
    print("\n⚡ Advanced Configuration")
    print("=" * 40)
    
    # Create a session with advanced UI customization
    print("🎯 Creating session with advanced features...")
    config_result = await browser_configure(
        BrowserConfigureParams(
            headless=True,
            slow_mo=500,  # For professional demo recordings
            devtools=False,  # Clean interface for recording
            args=[
                "--force-dark-mode",
                "--enable-features=WebUIDarkMode",
                "--start-maximized"
            ],
            chromium_sandbox=False,  # Container-friendly
            viewport_width=1280,
            viewport_height=720,
            latitude=40.7128,  # New York
            longitude=-74.0060,
            accuracy=100,
            permissions=["geolocation", "notifications"],
            color_scheme="dark"
        )
    )
    
    if config_result['success']:
        session_id = config_result['session_id']
        print(f"✅ Advanced configuration successful!")
        print(f"📱 Session ID: {session_id}")
        
        # Show helpful information
        if 'slow_mo_info' in config_result:
            print(f"🎬 {config_result['slow_mo_info']}")
        if 'args_info' in config_result:
            print(f"🔧 {config_result['args_info']}")
        
        # Get detailed session info
        session_info = await browser_get_session_info(session_id)
        if session_info['success']:
            config = session_info['configuration']
            print(f"\n🔍 Session Configuration:")
            print(f"   SlowMo: {config['slow_mo']}ms")
            print(f"   Viewport: {config['viewport']['width']}x{config['viewport']['height']}")
            print(f"   Geolocation: {config.get('geolocation', 'Not set')}")
            print(f"   Color Scheme: {config.get('color_scheme', 'Not set')}")
            print(f"   Custom Args: {len(config.get('args', []))} arguments")
        
        return session_id
    else:
        print(f"❌ Advanced configuration failed: {config_result['error']}")
        return None


async def demo_cleanup(session_ids: list):
    """Demonstrate session cleanup"""
    print("\n🧹 Session Cleanup")
    print("=" * 40)
    
    for session_id in session_ids:
        if session_id:
            print(f"🗑️ Closing session {session_id[:8]}...")
            close_result = await browser_close_session(
                CloseSessionParams(session_id=session_id)
            )
            
            if close_result['success']:
                print(f"✅ Session closed successfully")
                if close_result.get('video_files'):
                    print(f"🎬 Video files: {len(close_result['video_files'])}")
            else:
                print(f"❌ Session close failed: {close_result['error']}")
    
    # Verify all sessions are cleaned up
    final_sessions = await browser_list_sessions(
        SessionListParams(include_details=False)
    )
    
    if final_sessions['success']:
        print(f"📊 Final session count: {final_sessions['session_count']}")


async def main():
    """Run the complete MCPlaywright demo"""
    print("🎭 MCPlaywright Demo")
    print("=" * 50)
    print("Demonstrating advanced browser automation with FastMCP 2.0")
    print("=" * 50)
    
    session_ids = []
    
    try:
        # Initialize session manager
        print("\n🚀 Initializing MCPlaywright...")
        await initialize_session_manager(
            session_timeout=300,  # 5 minutes
            max_concurrent_sessions=5
        )
        print("✅ Session manager initialized")
        
        # Demo server health
        await demo_server_health()
        
        # Demo browser configuration
        session_id = await demo_browser_configuration()
        if session_id:
            session_ids.append(session_id)
        
        # Demo browser automation
        if session_id:
            automation_success = await demo_browser_automation(session_id)
            if not automation_success:
                print("⚠️ Browser automation had issues, continuing with other demos...")
        
        # Demo session management
        await demo_session_management()
        
        # Demo advanced configuration
        advanced_session_id = await demo_advanced_configuration()
        if advanced_session_id:
            session_ids.append(advanced_session_id)
        
        print("\n🎉 Demo completed successfully!")
        print("=" * 50)
        print("Key Features Demonstrated:")
        print("✅ Server health monitoring and information")
        print("✅ Advanced browser configuration with UI customization")
        print("✅ Browser automation (navigation, screenshots)")
        print("✅ Session management and isolation")
        print("✅ Advanced features (geolocation, custom args, themes)")
        print("✅ Resource cleanup and session management")
        print("=" * 50)
        
    except Exception as e:
        logger.error(f"Demo failed: {str(e)}", exc_info=True)
        print(f"\n❌ Demo failed: {str(e)}")
        
    finally:
        # Cleanup
        await demo_cleanup(session_ids)
        
        # Cleanup session manager
        print("\n🧹 Cleaning up session manager...")
        await cleanup_session_manager()
        print("✅ Cleanup completed")


if __name__ == "__main__":
    print("🎭 Starting MCPlaywright Demo...")
    print("⚠️  Note: This demo requires Playwright browsers to be installed.")
    print("   Run: playwright install chromium\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n💥 Demo crashed: {str(e)}")
        sys.exit(1)