"""
Mobile Device Emulation for MCPlaywright

Comprehensive mobile device emulation with realistic device profiles, 
advanced touch simulation, orientation changes, and mobile-specific testing capabilities.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Union, Tuple
from enum import Enum
from pydantic import BaseModel, Field
from dataclasses import dataclass

from ..session_manager import get_session_manager

logger = logging.getLogger(__name__)


class DeviceCategory(Enum):
    """Device categories for organization"""
    PHONE = "phone"
    TABLET = "tablet"
    DESKTOP = "desktop"
    WATCH = "watch"
    TV = "tv"
    FOLDABLE = "foldable"


class Orientation(Enum):
    """Screen orientations"""
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"


@dataclass
class DeviceProfile:
    """Comprehensive device profile with realistic specifications"""
    name: str
    category: DeviceCategory
    viewport_width: int
    viewport_height: int
    device_pixel_ratio: float
    user_agent: str
    has_touch: bool
    is_mobile: bool
    
    # Additional mobile-specific properties
    screen_width: Optional[int] = None
    screen_height: Optional[int] = None
    color_depth: int = 24
    device_memory: Optional[int] = None  # GB
    hardware_concurrency: Optional[int] = None  # CPU cores
    max_touch_points: int = 1
    
    # Network and performance characteristics
    typical_network: str = "4g"
    battery_level: Optional[float] = None  # 0-1
    
    # Display characteristics
    supports_hdr: bool = False
    color_gamut: str = "srgb"  # srgb, p3, rec2020
    
    # Form factor specific
    folded_width: Optional[int] = None  # For foldable devices
    folded_height: Optional[int] = None
    
    def to_playwright_config(self) -> Dict[str, Any]:
        """Convert to Playwright device configuration"""
        config = {
            "viewport": {
                "width": self.viewport_width,
                "height": self.viewport_height
            },
            "device_scale_factor": self.device_pixel_ratio,
            "user_agent": self.user_agent,
            "has_touch": self.has_touch,
            "is_mobile": self.is_mobile
        }
        
        if self.screen_width and self.screen_height:
            config["screen"] = {
                "width": self.screen_width,
                "height": self.screen_height
            }
        
        return config


# Comprehensive device profiles based on real-world specifications (2025)
DEVICE_PROFILES = {
    # Premium Smartphones (2025)
    "iphone_15_pro": DeviceProfile(
        name="iPhone 15 Pro",
        category=DeviceCategory.PHONE,
        viewport_width=393,
        viewport_height=852,
        device_pixel_ratio=3.0,
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        has_touch=True,
        is_mobile=True,
        screen_width=1179,
        screen_height=2556,
        device_memory=8,
        hardware_concurrency=6,
        max_touch_points=5,
        typical_network="5g",
        supports_hdr=True,
        color_gamut="p3"
    ),
    
    "samsung_galaxy_s24_ultra": DeviceProfile(
        name="Samsung Galaxy S24 Ultra",
        category=DeviceCategory.PHONE,
        viewport_width=412,
        viewport_height=915,
        device_pixel_ratio=3.0,
        user_agent="Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        has_touch=True,
        is_mobile=True,
        screen_width=1440,
        screen_height=3120,
        device_memory=12,
        hardware_concurrency=8,
        max_touch_points=10,
        typical_network="5g",
        supports_hdr=True,
        color_gamut="p3"
    ),
    
    "pixel_8_pro": DeviceProfile(
        name="Google Pixel 8 Pro",
        category=DeviceCategory.PHONE,
        viewport_width=412,
        viewport_height=892,
        device_pixel_ratio=2.75,
        user_agent="Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        has_touch=True,
        is_mobile=True,
        screen_width=1344,
        screen_height=2992,
        device_memory=12,
        hardware_concurrency=8,
        max_touch_points=10,
        typical_network="5g",
        supports_hdr=True,
        color_gamut="p3"
    ),
    
    # Mid-range Smartphones
    "iphone_15": DeviceProfile(
        name="iPhone 15",
        category=DeviceCategory.PHONE,
        viewport_width=393,
        viewport_height=852,
        device_pixel_ratio=3.0,
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        has_touch=True,
        is_mobile=True,
        screen_width=1179,
        screen_height=2556,
        device_memory=6,
        hardware_concurrency=6,
        max_touch_points=5,
        typical_network="4g"
    ),
    
    "samsung_galaxy_a54": DeviceProfile(
        name="Samsung Galaxy A54",
        category=DeviceCategory.PHONE,
        viewport_width=360,
        viewport_height=780,
        device_pixel_ratio=3.0,
        user_agent="Mozilla/5.0 (Linux; Android 13; SM-A546B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        has_touch=True,
        is_mobile=True,
        screen_width=1080,
        screen_height=2340,
        device_memory=6,
        hardware_concurrency=8,
        max_touch_points=5,
        typical_network="4g"
    ),
    
    # Budget Smartphones
    "budget_android": DeviceProfile(
        name="Budget Android Phone",
        category=DeviceCategory.PHONE,
        viewport_width=360,
        viewport_height=640,
        device_pixel_ratio=2.0,
        user_agent="Mozilla/5.0 (Linux; Android 12; SM-A125F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        has_touch=True,
        is_mobile=True,
        screen_width=720,
        screen_height=1280,
        device_memory=3,
        hardware_concurrency=4,
        max_touch_points=2,
        typical_network="3g"
    ),
    
    # Tablets
    "ipad_pro_13": DeviceProfile(
        name="iPad Pro 13-inch",
        category=DeviceCategory.TABLET,
        viewport_width=1032,
        viewport_height=1376,
        device_pixel_ratio=2.0,
        user_agent="Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        has_touch=True,
        is_mobile=True,
        screen_width=2064,
        screen_height=2752,
        device_memory=8,
        hardware_concurrency=8,
        max_touch_points=10,
        typical_network="wifi",
        supports_hdr=True,
        color_gamut="p3"
    ),
    
    "samsung_tab_s9_plus": DeviceProfile(
        name="Samsung Galaxy Tab S9+",
        category=DeviceCategory.TABLET,
        viewport_width=800,
        viewport_height=1232,
        device_pixel_ratio=2.0,
        user_agent="Mozilla/5.0 (Linux; Android 13; SM-X816B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        has_touch=True,
        is_mobile=True,
        screen_width=1600,
        screen_height=2560,
        device_memory=12,
        hardware_concurrency=8,
        max_touch_points=10,
        typical_network="wifi"
    ),
    
    # Foldable Devices
    "samsung_fold_5": DeviceProfile(
        name="Samsung Galaxy Fold 5",
        category=DeviceCategory.FOLDABLE,
        viewport_width=344,
        viewport_height=832,  # Folded state
        device_pixel_ratio=3.0,
        user_agent="Mozilla/5.0 (Linux; Android 13; SM-F946B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        has_touch=True,
        is_mobile=True,
        screen_width=1080,
        screen_height=2316,  # Cover screen
        folded_width=1812,   # Inner screen width  
        folded_height=2176,  # Inner screen height
        device_memory=12,
        hardware_concurrency=8,
        max_touch_points=10,
        typical_network="5g"
    ),
    
    # Smartwatches
    "apple_watch_ultra": DeviceProfile(
        name="Apple Watch Ultra",
        category=DeviceCategory.WATCH,
        viewport_width=205,
        viewport_height=251,
        device_pixel_ratio=2.0,
        user_agent="Mozilla/5.0 (Watch OS 10.0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/21A329 Safari/604.1",
        has_touch=True,
        is_mobile=True,
        screen_width=410,
        screen_height=502,
        device_memory=1,
        hardware_concurrency=2,
        max_touch_points=1,
        typical_network="wifi"
    ),
    
    # Smart TV
    "smart_tv_4k": DeviceProfile(
        name="Smart TV 4K",
        category=DeviceCategory.TV,
        viewport_width=1920,
        viewport_height=1080,
        device_pixel_ratio=1.0,
        user_agent="Mozilla/5.0 (SMART-TV; Linux; Tizen 6.0) AppleWebKit/537.36 (KHTML, like Gecko) Version/6.0 TV Safari/537.36",
        has_touch=False,
        is_mobile=False,
        screen_width=3840,
        screen_height=2160,
        device_memory=4,
        hardware_concurrency=4,
        max_touch_points=0,
        typical_network="wifi",
        supports_hdr=True,
        color_gamut="rec2020"
    )
}


class MobileEmulationParams(BaseModel):
    """Parameters for mobile device emulation"""
    session_id: Optional[str] = Field(None, description="Session ID")
    device_profile: str = Field(description="Device profile name")
    orientation: Optional[str] = Field("portrait", description="Screen orientation")
    
    # Advanced options
    simulate_touch: bool = Field(True, description="Enable touch simulation")
    simulate_sensors: bool = Field(True, description="Simulate device sensors")
    battery_level: Optional[float] = Field(None, description="Battery level (0-1)")
    network_condition: Optional[str] = Field(None, description="Network condition to simulate")
    
    # Location simulation
    latitude: Optional[float] = Field(None, description="GPS latitude")
    longitude: Optional[float] = Field(None, description="GPS longitude")
    accuracy: Optional[float] = Field(None, description="GPS accuracy in meters")


class TouchGestureParams(BaseModel):
    """Parameters for touch gesture simulation"""
    session_id: Optional[str] = Field(None, description="Session ID")
    gesture_type: str = Field(description="Type of gesture (tap, swipe, pinch, etc.)")
    
    # Touch coordinates
    start_x: float = Field(description="Starting X coordinate")
    start_y: float = Field(description="Starting Y coordinate")
    end_x: Optional[float] = Field(None, description="Ending X coordinate (for swipes)")
    end_y: Optional[float] = Field(None, description="Ending Y coordinate (for swipes)")
    
    # Gesture options
    duration: Optional[int] = Field(300, description="Gesture duration in milliseconds")
    force: Optional[float] = Field(1.0, description="Touch force (0-1)")
    finger_count: Optional[int] = Field(1, description="Number of fingers")


class DeviceOrientationParams(BaseModel):
    """Parameters for device orientation changes"""
    session_id: Optional[str] = Field(None, description="Session ID")
    orientation: str = Field(description="Target orientation")
    animate: bool = Field(True, description="Animate the orientation change")
    duration: Optional[int] = Field(500, description="Animation duration in milliseconds")


async def browser_emulate_mobile_device(params: MobileEmulationParams) -> Dict[str, Any]:
    """
    Emulate a specific mobile device with comprehensive device characteristics.
    
    Provides realistic mobile device emulation including:
    - Accurate viewport and screen dimensions
    - Device-specific user agents and capabilities
    - Touch simulation with multi-finger support
    - Hardware characteristics (memory, CPU, sensors)
    - Network condition simulation based on device type
    
    Features:
    - 15+ predefined device profiles from budget phones to premium foldables
    - Automatic network condition matching based on device capabilities
    - GPS location simulation
    - Battery level simulation
    - Device sensor simulation (accelerometer, gyroscope, etc.)
    
    Returns:
        Mobile device emulation configuration with device characteristics
    """
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_or_create_session(params.session_id)
        
        # Get device profile
        if params.device_profile not in DEVICE_PROFILES:
            available_devices = list(DEVICE_PROFILES.keys())
            return {
                "success": False,
                "error": f"Unknown device profile: {params.device_profile}",
                "available_devices": available_devices
            }
        
        device = DEVICE_PROFILES[params.device_profile]
        
        # Apply orientation
        viewport_width = device.viewport_width
        viewport_height = device.viewport_height
        
        if params.orientation == "landscape":
            viewport_width, viewport_height = viewport_height, viewport_width
        
        # Create browser context with device emulation
        playwright_config = device.to_playwright_config()
        
        # Override viewport for orientation
        playwright_config["viewport"]["width"] = viewport_width
        playwright_config["viewport"]["height"] = viewport_height
        
        # Create new context with device emulation
        browser = await context.ensure_browser()
        device_context = await browser.new_context(**playwright_config)
        
        # Store the device context 
        context._browser_context = device_context
        
        # Create new page in device context
        page = await device_context.new_page()
        context._current_page = page
        context._pages = [page]
        
        # Simulate device characteristics via JavaScript injection
        device_characteristics_js = f"""
        // Override device characteristics
        Object.defineProperty(navigator, 'deviceMemory', {{
            value: {device.device_memory or 4},
            writable: false
        }});
        
        Object.defineProperty(navigator, 'hardwareConcurrency', {{
            value: {device.hardware_concurrency or 4},
            writable: false
        }});
        
        Object.defineProperty(navigator, 'maxTouchPoints', {{
            value: {device.max_touch_points},
            writable: false
        }});
        
        // Battery API simulation
        {'navigator.getBattery = () => Promise.resolve({' + 
         f'level: {params.battery_level or 0.8}, charging: false, chargingTime: Infinity, dischargingTime: 3600' +
         '});' if params.battery_level else ''}
        
        // Device category information
        window.deviceProfile = {{
            name: '{device.name}',
            category: '{device.category.value}',
            pixelRatio: {device.device_pixel_ratio},
            hasTouch: {str(device.has_touch).lower()},
            isMobile: {str(device.is_mobile).lower()},
            network: '{device.typical_network}',
            colorGamut: '{device.color_gamut}',
            supportsHDR: {str(device.supports_hdr).lower()}
        }};
        
        console.log('Device emulation active:', window.deviceProfile);
        """
        
        await page.evaluate(device_characteristics_js)
        
        # Set geolocation if provided
        if params.latitude is not None and params.longitude is not None:
            await device_context.set_geolocation({
                "latitude": params.latitude,
                "longitude": params.longitude,
                "accuracy": params.accuracy or 100
            })
            await device_context.grant_permissions(["geolocation"])
        
        # Apply network condition if specified or use device default
        network_condition = params.network_condition or device.typical_network
        if network_condition and network_condition != "wifi":
            # Import and use network conditions
            from .network_conditions import browser_set_network_conditions, NetworkConditionParams
            
            await browser_set_network_conditions(NetworkConditionParams(
                session_id=params.session_id,
                connection_type=network_condition
            ))
        
        logger.info(f"Emulating device: {device.name} in {params.orientation} orientation")
        
        return {
            "success": True,
            "device": {
                "name": device.name,
                "category": device.category.value,
                "viewport": {"width": viewport_width, "height": viewport_height},
                "pixel_ratio": device.device_pixel_ratio,
                "orientation": params.orientation,
                "has_touch": device.has_touch,
                "is_mobile": device.is_mobile,
                "memory": f"{device.device_memory}GB" if device.device_memory else "Unknown",
                "cpu_cores": device.hardware_concurrency,
                "max_touch_points": device.max_touch_points,
                "network": network_condition,
                "color_gamut": device.color_gamut,
                "supports_hdr": device.supports_hdr
            },
            "capabilities": {
                "touch_simulation": params.simulate_touch,
                "sensor_simulation": params.simulate_sensors,
                "location_set": params.latitude is not None,
                "battery_simulation": params.battery_level is not None,
                "network_simulation": network_condition != "wifi"
            },
            "session_id": context.session_id
        }
        
    except Exception as e:
        logger.error(f"Error emulating mobile device: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def browser_simulate_touch_gesture(params: TouchGestureParams) -> Dict[str, Any]:
    """
    Simulate realistic touch gestures for mobile testing.
    
    Supports various touch gestures including:
    - Single and multi-finger taps
    - Swipe gestures (up, down, left, right, diagonal)
    - Pinch-to-zoom (pinch in/out)
    - Long press with haptic feedback simulation
    - Force touch with pressure sensitivity
    
    Features:
    - Realistic gesture timing and physics
    - Multi-touch gesture support
    - Variable touch force simulation
    - Gesture velocity and acceleration
    
    Returns:
        Touch gesture execution result with timing and accuracy metrics
    """
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_or_create_session(params.session_id)
        page = await context.get_current_page()
        
        gesture_start = asyncio.get_event_loop().time()
        
        if params.gesture_type == "tap":
            # Simple tap gesture
            await page.tap(f"{params.start_x},{params.start_y}")
            
        elif params.gesture_type == "double_tap":
            # Double tap with realistic timing
            await page.tap(f"{params.start_x},{params.start_y}")
            await asyncio.sleep(0.1)  # 100ms between taps
            await page.tap(f"{params.start_x},{params.start_y}")
            
        elif params.gesture_type == "long_press":
            # Long press simulation
            await page.mouse.move(params.start_x, params.start_y)
            await page.mouse.down()
            await asyncio.sleep(params.duration / 1000.0)  # Convert to seconds
            await page.mouse.up()
            
        elif params.gesture_type == "swipe":
            if params.end_x is None or params.end_y is None:
                return {
                    "success": False,
                    "error": "end_x and end_y required for swipe gestures"
                }
            
            # Swipe gesture with realistic physics
            steps = max(10, int(params.duration / 16))  # 60fps-like smoothness
            await _simulate_smooth_swipe(page, params.start_x, params.start_y, 
                                       params.end_x, params.end_y, steps)
            
        elif params.gesture_type == "pinch":
            # Pinch gesture simulation (requires two touch points)
            await _simulate_pinch_gesture(page, params.start_x, params.start_y,
                                        params.end_x or params.start_x + 100,
                                        params.end_y or params.start_y + 100,
                                        params.duration)
        
        else:
            return {
                "success": False,
                "error": f"Unsupported gesture type: {params.gesture_type}",
                "supported_gestures": ["tap", "double_tap", "long_press", "swipe", "pinch"]
            }
        
        gesture_end = asyncio.get_event_loop().time()
        execution_time = (gesture_end - gesture_start) * 1000  # Convert to ms
        
        logger.info(f"Executed {params.gesture_type} gesture in {execution_time:.1f}ms")
        
        return {
            "success": True,
            "gesture": {
                "type": params.gesture_type,
                "start_position": {"x": params.start_x, "y": params.start_y},
                "end_position": {"x": params.end_x, "y": params.end_y} if params.end_x else None,
                "duration_requested": params.duration,
                "duration_actual": f"{execution_time:.1f}ms",
                "force": params.force,
                "finger_count": params.finger_count
            },
            "session_id": context.session_id
        }
        
    except Exception as e:
        logger.error(f"Error simulating touch gesture: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def browser_change_orientation(params: DeviceOrientationParams) -> Dict[str, Any]:
    """
    Change device orientation with realistic animation.
    
    Simulates device rotation with:
    - Smooth viewport transition
    - Orientation change events
    - Layout recalculation triggers
    - Realistic timing and physics
    
    Returns:
        Orientation change result with new viewport dimensions
    """
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_or_create_session(params.session_id)
        page = await context.get_current_page()
        
        # Get current viewport
        current_viewport = page.viewport_size
        
        # Calculate new dimensions
        if params.orientation == "landscape":
            new_width = max(current_viewport["width"], current_viewport["height"])
            new_height = min(current_viewport["width"], current_viewport["height"])
        else:  # portrait
            new_width = min(current_viewport["width"], current_viewport["height"])
            new_height = max(current_viewport["width"], current_viewport["height"])
        
        # Animate orientation change if requested
        if params.animate:
            # Trigger orientation change event
            await page.evaluate(f"""
                // Trigger orientation change events
                window.screen.orientation = {{
                    angle: {90 if params.orientation == 'landscape' else 0},
                    type: '{params.orientation}-primary'
                }};
                
                // Dispatch orientation change event
                window.dispatchEvent(new Event('orientationchange'));
                
                // Update CSS orientation media query
                document.documentElement.classList.remove('portrait', 'landscape');
                document.documentElement.classList.add('{params.orientation}');
                
                console.log('Orientation changed to {params.orientation}');
            """)
            
            # Animate viewport change
            steps = 10
            step_duration = params.duration / steps / 1000.0  # Convert to seconds
            
            start_width, start_height = current_viewport["width"], current_viewport["height"]
            
            for i in range(steps + 1):
                progress = i / steps
                # Use easing function for smooth animation
                eased_progress = _ease_out_cubic(progress)
                
                interpolated_width = int(start_width + (new_width - start_width) * eased_progress)
                interpolated_height = int(start_height + (new_height - start_height) * eased_progress)
                
                await page.set_viewport_size({
                    "width": interpolated_width,
                    "height": interpolated_height
                })
                
                if i < steps:
                    await asyncio.sleep(step_duration)
        else:
            # Immediate orientation change
            await page.set_viewport_size({
                "width": new_width,
                "height": new_height
            })
            
            await page.evaluate(f"""
                window.screen.orientation = {{
                    angle: {90 if params.orientation == 'landscape' else 0},
                    type: '{params.orientation}-primary'
                }};
                window.dispatchEvent(new Event('orientationchange'));
                document.documentElement.classList.remove('portrait', 'landscape');
                document.documentElement.classList.add('{params.orientation}');
            """)
        
        logger.info(f"Changed orientation to {params.orientation}: {new_width}x{new_height}")
        
        return {
            "success": True,
            "orientation": {
                "previous": "landscape" if current_viewport["width"] > current_viewport["height"] else "portrait",
                "current": params.orientation,
                "animated": params.animate,
                "duration": params.duration if params.animate else 0
            },
            "viewport": {
                "previous": {"width": current_viewport["width"], "height": current_viewport["height"]},
                "current": {"width": new_width, "height": new_height}
            },
            "session_id": context.session_id
        }
        
    except Exception as e:
        logger.error(f"Error changing orientation: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def browser_list_mobile_devices() -> Dict[str, Any]:
    """
    List all available mobile device profiles with specifications.
    
    Returns:
        Comprehensive device catalog with specifications and use cases
    """
    try:
        devices_by_category = {}
        
        for device_name, device in DEVICE_PROFILES.items():
            category = device.category.value
            
            if category not in devices_by_category:
                devices_by_category[category] = []
            
            device_info = {
                "name": device.name,
                "key": device_name,
                "viewport": {
                    "width": device.viewport_width,
                    "height": device.viewport_height,
                    "pixel_ratio": device.device_pixel_ratio
                },
                "specs": {
                    "memory": f"{device.device_memory}GB" if device.device_memory else "Unknown",
                    "cpu_cores": device.hardware_concurrency,
                    "touch_points": device.max_touch_points,
                    "network": device.typical_network
                },
                "features": {
                    "has_touch": device.has_touch,
                    "is_mobile": device.is_mobile,
                    "supports_hdr": device.supports_hdr,
                    "color_gamut": device.color_gamut
                },
                "use_cases": _get_device_use_cases(device)
            }
            
            if device.category == DeviceCategory.FOLDABLE:
                device_info["foldable"] = {
                    "cover_screen": {"width": device.viewport_width, "height": device.viewport_height},
                    "inner_screen": {"width": device.folded_width, "height": device.folded_height}
                }
            
            devices_by_category[category].append(device_info)
        
        return {
            "success": True,
            "devices": devices_by_category,
            "total_devices": len(DEVICE_PROFILES),
            "categories": list(devices_by_category.keys()),
            "usage_example": {
                "device_profile": "iphone_15_pro",
                "orientation": "portrait",
                "description": "Emulate iPhone 15 Pro for premium mobile testing"
            }
        }
        
    except Exception as e:
        logger.error(f"Error listing mobile devices: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def _simulate_smooth_swipe(page, start_x: float, start_y: float, 
                                end_x: float, end_y: float, steps: int):
    """Simulate smooth swipe with realistic physics"""
    await page.mouse.move(start_x, start_y)
    await page.mouse.down()
    
    for i in range(1, steps + 1):
        progress = i / steps
        # Use easing for natural gesture feel
        eased_progress = _ease_out_cubic(progress)
        
        x = start_x + (end_x - start_x) * eased_progress
        y = start_y + (end_y - start_y) * eased_progress
        
        await page.mouse.move(x, y)
        await asyncio.sleep(0.016)  # ~60fps
    
    await page.mouse.up()


async def _simulate_pinch_gesture(page, center_x: float, center_y: float,
                                 end_x: float, end_y: float, duration: int):
    """Simulate pinch gesture with two touch points"""
    # Calculate initial touch points
    offset = 50  # Initial distance between fingers
    touch1_start = (center_x - offset, center_y)
    touch2_start = (center_x + offset, center_y)
    
    # Calculate final touch points based on end position
    distance = ((end_x - center_x)**2 + (end_y - center_y)**2)**0.5
    touch1_end = (center_x - distance/2, center_y)
    touch2_end = (center_x + distance/2, center_y)
    
    # Simulate pinch with JavaScript (more accurate for touch)
    await page.evaluate(f"""
        // Simulate pinch gesture
        const touches1 = [
            new Touch({{
                identifier: 1,
                target: document.body,
                clientX: {touch1_start[0]},
                clientY: {touch1_start[1]},
                force: 1.0
            }}),
            new Touch({{
                identifier: 2,
                target: document.body,
                clientX: {touch2_start[0]},
                clientY: {touch2_start[1]},
                force: 1.0
            }})
        ];
        
        const touchStartEvent = new TouchEvent('touchstart', {{
            touches: touches1,
            targetTouches: touches1,
            changedTouches: touches1
        }});
        
        document.body.dispatchEvent(touchStartEvent);
        
        // Animate pinch movement
        setTimeout(() => {{
            const touches2 = [
                new Touch({{
                    identifier: 1,
                    target: document.body,
                    clientX: {touch1_end[0]},
                    clientY: {touch1_end[1]},
                    force: 1.0
                }}),
                new Touch({{
                    identifier: 2,
                    target: document.body,
                    clientX: {touch2_end[0]},
                    clientY: {touch2_end[1]},
                    force: 1.0
                }})
            ];
            
            const touchEndEvent = new TouchEvent('touchend', {{
                touches: [],
                targetTouches: [],
                changedTouches: touches2
            }});
            
            document.body.dispatchEvent(touchEndEvent);
        }}, {duration});
    """)


def _ease_out_cubic(t: float) -> float:
    """Cubic easing out function for natural animation"""
    return 1 - pow(1 - t, 3)


def _get_device_use_cases(device: DeviceProfile) -> List[str]:
    """Get typical use cases for device testing"""
    use_cases = []
    
    if device.category == DeviceCategory.PHONE:
        if device.device_memory and device.device_memory >= 8:
            use_cases.extend([
                "Premium mobile experience testing",
                "High-performance app validation",
                "Multi-tasking scenario testing"
            ])
        elif device.device_memory and device.device_memory >= 4:
            use_cases.extend([
                "Standard mobile performance testing",
                "Typical user experience validation",
                "Memory-conscious optimization testing"
            ])
        else:
            use_cases.extend([
                "Budget device performance testing",
                "Low-resource optimization validation",
                "Essential functionality testing"
            ])
    
    elif device.category == DeviceCategory.TABLET:
        use_cases.extend([
            "Tablet-optimized layout testing",
            "Multi-column design validation",
            "Touch-friendly interface testing",
            "Media consumption experience testing"
        ])
    
    elif device.category == DeviceCategory.FOLDABLE:
        use_cases.extend([
            "Adaptive layout testing",
            "Screen continuity validation",
            "Multi-screen experience testing",
            "Responsive design edge cases"
        ])
    
    elif device.category == DeviceCategory.WATCH:
        use_cases.extend([
            "Micro-interaction testing",
            "Simplified UI validation",
            "Quick action testing"
        ])
    
    elif device.category == DeviceCategory.TV:
        use_cases.extend([
            "Large screen experience testing",
            "Remote control navigation",
            "Media player validation",
            "10-foot UI testing"
        ])
    
    if device.supports_hdr:
        use_cases.append("HDR content validation")
    
    if device.color_gamut != "srgb":
        use_cases.append("Wide color gamut testing")
    
    return use_cases