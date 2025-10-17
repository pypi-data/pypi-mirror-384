"""
Network Condition Simulation for MCPlaywright

Advanced network throttling and condition simulation using Chrome DevTools Protocol (CDP).
Provides realistic network condition testing for performance and reliability validation.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from pydantic import BaseModel, Field
from dataclasses import dataclass

from ..session_manager import get_session_manager
from ..state.devtools_state import get_devtools_state

logger = logging.getLogger(__name__)


class NetworkConnectionType(Enum):
    """Predefined network connection types with realistic parameters"""
    NONE = "none"
    OFFLINE = "offline"
    SLOW_2G = "slow2g"
    FAST_2G = "fast2g" 
    SLOW_3G = "slow3g"
    FAST_3G = "fast3g"
    SLOW_4G = "slow4g"
    FAST_4G = "fast4g"
    WIFI = "wifi"
    ETHERNET = "ethernet"
    CUSTOM = "custom"


@dataclass
class NetworkCondition:
    """Network condition configuration"""
    name: str
    offline: bool
    downloadThroughput: float  # bytes per second
    uploadThroughput: float    # bytes per second
    latency: float            # milliseconds
    description: str = ""
    
    def to_cdp_params(self) -> Dict[str, Any]:
        """Convert to CDP Network.emulateNetworkConditions parameters"""
        return {
            "offline": self.offline,
            "downloadThroughput": int(self.downloadThroughput),
            "uploadThroughput": int(self.uploadThroughput),
            "latency": int(self.latency)
        }


# Predefined realistic network conditions based on real-world measurements
NETWORK_PRESETS = {
    NetworkConnectionType.OFFLINE: NetworkCondition(
        name="Offline",
        offline=True,
        downloadThroughput=0,
        uploadThroughput=0,
        latency=0,
        description="No network connection"
    ),
    
    NetworkConnectionType.SLOW_2G: NetworkCondition(
        name="Slow 2G",
        offline=False,
        downloadThroughput=28 * 1024 / 8,  # 28 kbit/s = 3.5 KB/s
        uploadThroughput=14 * 1024 / 8,    # 14 kbit/s = 1.75 KB/s
        latency=3000,  # 3 seconds
        description="Slow 2G connection (GPRS)"
    ),
    
    NetworkConnectionType.FAST_2G: NetworkCondition(
        name="Fast 2G", 
        offline=False,
        downloadThroughput=128 * 1024 / 8,  # 128 kbit/s = 16 KB/s
        uploadThroughput=64 * 1024 / 8,     # 64 kbit/s = 8 KB/s
        latency=1500,  # 1.5 seconds
        description="Fast 2G connection (EDGE)"
    ),
    
    NetworkConnectionType.SLOW_3G: NetworkCondition(
        name="Slow 3G",
        offline=False,
        downloadThroughput=400 * 1024 / 8,  # 400 kbit/s = 50 KB/s
        uploadThroughput=150 * 1024 / 8,    # 150 kbit/s = 18.75 KB/s
        latency=800,   # 800ms
        description="Slow 3G connection"
    ),
    
    NetworkConnectionType.FAST_3G: NetworkCondition(
        name="Fast 3G",
        offline=False,
        downloadThroughput=1500 * 1024 / 8,  # 1.5 Mbit/s = 187.5 KB/s
        uploadThroughput=750 * 1024 / 8,     # 750 kbit/s = 93.75 KB/s
        latency=400,   # 400ms
        description="Fast 3G connection (HSDPA)"
    ),
    
    NetworkConnectionType.SLOW_4G: NetworkCondition(
        name="Slow 4G",
        offline=False,
        downloadThroughput=4 * 1024 * 1024 / 8,  # 4 Mbit/s = 512 KB/s
        uploadThroughput=1 * 1024 * 1024 / 8,    # 1 Mbit/s = 128 KB/s
        latency=150,   # 150ms
        description="Slow 4G LTE connection"
    ),
    
    NetworkConnectionType.FAST_4G: NetworkCondition(
        name="Fast 4G",
        offline=False,
        downloadThroughput=20 * 1024 * 1024 / 8,  # 20 Mbit/s = 2.5 MB/s
        uploadThroughput=10 * 1024 * 1024 / 8,    # 10 Mbit/s = 1.25 MB/s
        latency=75,    # 75ms
        description="Fast 4G LTE connection"
    ),
    
    NetworkConnectionType.WIFI: NetworkCondition(
        name="WiFi",
        offline=False,
        downloadThroughput=50 * 1024 * 1024 / 8,  # 50 Mbit/s = 6.25 MB/s
        uploadThroughput=25 * 1024 * 1024 / 8,    # 25 Mbit/s = 3.125 MB/s
        latency=30,    # 30ms
        description="Typical WiFi connection"
    ),
    
    NetworkConnectionType.ETHERNET: NetworkCondition(
        name="Ethernet",
        offline=False,
        downloadThroughput=100 * 1024 * 1024 / 8,  # 100 Mbit/s = 12.5 MB/s
        uploadThroughput=100 * 1024 * 1024 / 8,    # 100 Mbit/s = 12.5 MB/s
        latency=5,     # 5ms
        description="Fast Ethernet connection"
    )
}


class NetworkConditionParams(BaseModel):
    """Parameters for setting network conditions"""
    session_id: Optional[str] = Field(None, description="Session ID")
    connection_type: Optional[str] = Field(None, description="Predefined connection type")
    
    # Custom network condition parameters
    offline: Optional[bool] = Field(None, description="Set offline mode")
    download_throughput: Optional[float] = Field(None, description="Download speed in bytes/sec")
    upload_throughput: Optional[float] = Field(None, description="Upload speed in bytes/sec")
    latency: Optional[float] = Field(None, description="Network latency in milliseconds")
    
    # Advanced options
    apply_to_all_pages: bool = Field(True, description="Apply to all pages in session")
    simulate_packet_loss: Optional[float] = Field(None, description="Packet loss percentage (0-100)")


class NetworkTestingParams(BaseModel):
    """Parameters for network testing scenarios"""
    session_id: Optional[str] = Field(None, description="Session ID")
    test_scenario: str = Field(description="Test scenario name")
    duration_seconds: Optional[int] = Field(60, description="Test duration in seconds")
    conditions: List[str] = Field(description="List of network conditions to cycle through")
    metrics_collection: bool = Field(True, description="Enable performance metrics collection")


class NetworkMetricsParams(BaseModel):
    """Parameters for network metrics collection"""
    session_id: Optional[str] = Field(None, description="Session ID")
    reset_metrics: bool = Field(False, description="Reset metrics before collection")


async def browser_set_network_conditions(params: NetworkConditionParams) -> Dict[str, Any]:
    """
    Set network conditions for realistic network testing.
    
    Simulates various network conditions including mobile connections (2G, 3G, 4G),
    WiFi, Ethernet, and offline states using Chrome DevTools Protocol.
    
    Features:
    - Predefined realistic network profiles based on real-world measurements
    - Custom network condition configuration
    - Session-wide or page-specific application
    - Performance impact simulation with accurate latency and throughput
    
    Returns:
        Network condition configuration result with performance expectations
    """
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_or_create_session(params.session_id)
        
        # Determine network condition to apply
        network_condition = None
        
        if params.connection_type:
            # Use predefined connection type
            try:
                connection_type = NetworkConnectionType(params.connection_type.lower())
                network_condition = NETWORK_PRESETS[connection_type]
            except ValueError:
                return {
                    "success": False,
                    "error": f"Unknown connection type: {params.connection_type}",
                    "available_types": [t.value for t in NetworkConnectionType]
                }
        
        elif any([params.offline is not None, params.download_throughput, params.upload_throughput, params.latency]):
            # Use custom network condition
            network_condition = NetworkCondition(
                name="Custom",
                offline=params.offline or False,
                downloadThroughput=params.download_throughput or (50 * 1024 * 1024 / 8),  # Default 50 Mbit/s
                uploadThroughput=params.upload_throughput or (25 * 1024 * 1024 / 8),      # Default 25 Mbit/s  
                latency=params.latency or 30,  # Default 30ms
                description="Custom network condition"
            )
        
        else:
            return {
                "success": False,
                "error": "Must specify either connection_type or custom network parameters"
            }
        
        # Get current page
        page = await context.get_current_page()
        
        # Get CDP session
        client = await page.context.new_cdp_session(page)
        
        # Enable Network domain
        await client.send("Network.enable")
        
        # Apply network condition via CDP
        cdp_params = network_condition.to_cdp_params()
        await client.send("Network.emulateNetworkConditions", cdp_params)
        
        logger.info(f"Applied network condition: {network_condition.name} for session {context.session_id}")
        
        # Calculate expected performance impact
        expected_impact = _calculate_performance_impact(network_condition)
        
        return {
            "success": True,
            "network_condition": {
                "name": network_condition.name,
                "description": network_condition.description,
                "offline": network_condition.offline,
                "download_speed": f"{network_condition.downloadThroughput / 1024:.1f} KB/s",
                "upload_speed": f"{network_condition.uploadThroughput / 1024:.1f} KB/s", 
                "latency": f"{network_condition.latency}ms"
            },
            "expected_impact": expected_impact,
            "session_id": context.session_id,
            "applied_to": "current_page" if not params.apply_to_all_pages else "all_pages"
        }
        
    except Exception as e:
        logger.error(f"Error setting network conditions: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def browser_clear_network_conditions(session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Clear network conditions and restore normal network behavior.
    
    Returns:
        Network restoration result
    """
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_or_create_session(session_id)
        
        page = await context.get_current_page()
        client = await page.context.new_cdp_session(page)
        
        # Disable network emulation by setting unlimited conditions
        await client.send("Network.emulateNetworkConditions", {
            "offline": False,
            "downloadThroughput": -1,  # Unlimited
            "uploadThroughput": -1,    # Unlimited
            "latency": 0
        })
        
        logger.info(f"Cleared network conditions for session {context.session_id}")
        
        return {
            "success": True,
            "message": "Network conditions cleared - normal network behavior restored",
            "session_id": context.session_id
        }
        
    except Exception as e:
        logger.error(f"Error clearing network conditions: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def browser_list_network_presets() -> Dict[str, Any]:
    """
    List all available network condition presets with descriptions.
    
    Returns:
        Available network presets with detailed specifications
    """
    try:
        presets = {}
        
        for connection_type, condition in NETWORK_PRESETS.items():
            presets[connection_type.value] = {
                "name": condition.name,
                "description": condition.description,
                "offline": condition.offline,
                "download_speed": f"{condition.downloadThroughput / 1024:.1f} KB/s",
                "upload_speed": f"{condition.uploadThroughput / 1024:.1f} KB/s",
                "latency": f"{condition.latency}ms",
                "typical_use_cases": _get_use_cases(connection_type)
            }
        
        return {
            "success": True,
            "presets": presets,
            "total_presets": len(presets),
            "usage_example": {
                "connection_type": "slow3g",
                "description": "Simulate slow 3G mobile connection for performance testing"
            }
        }
        
    except Exception as e:
        logger.error(f"Error listing network presets: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def browser_test_network_conditions(params: NetworkTestingParams) -> Dict[str, Any]:
    """
    Run automated network condition testing scenarios.
    
    Cycles through different network conditions to test application behavior
    under various network constraints with performance metrics collection.
    
    Returns:
        Network testing results with performance analysis
    """
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_or_create_session(params.session_id)
        
        test_results = {
            "scenario": params.test_scenario,
            "start_time": asyncio.get_event_loop().time(),
            "conditions_tested": [],
            "metrics": {},
            "recommendations": []
        }
        
        page = await context.get_current_page()
        client = await page.context.new_cdp_session(page)
        await client.send("Network.enable")
        
        # Enable performance monitoring if requested
        if params.metrics_collection:
            await client.send("Performance.enable")
        
        duration_per_condition = params.duration_seconds // len(params.conditions)
        
        for i, condition_type in enumerate(params.conditions):
            logger.info(f"Testing condition {i+1}/{len(params.conditions)}: {condition_type}")
            
            # Apply network condition
            if condition_type in [t.value for t in NetworkConnectionType]:
                connection_type = NetworkConnectionType(condition_type)
                condition = NETWORK_PRESETS[connection_type]
                
                await client.send("Network.emulateNetworkConditions", condition.to_cdp_params())
                
                # Collect metrics for this condition
                condition_start = asyncio.get_event_loop().time()
                
                if params.metrics_collection:
                    # Wait and collect performance metrics
                    await asyncio.sleep(duration_per_condition)
                    
                    # Get performance metrics
                    metrics = await client.send("Performance.getMetrics")
                    
                    condition_metrics = {
                        "condition": condition.name,
                        "duration": duration_per_condition,
                        "performance_metrics": _process_performance_metrics(metrics.get("metrics", []))
                    }
                    
                    test_results["conditions_tested"].append(condition_metrics)
                    test_results["metrics"][condition_type] = condition_metrics
        
        # Clear network conditions
        await client.send("Network.emulateNetworkConditions", {
            "offline": False,
            "downloadThroughput": -1,
            "uploadThroughput": -1, 
            "latency": 0
        })
        
        test_results["end_time"] = asyncio.get_event_loop().time()
        test_results["total_duration"] = test_results["end_time"] - test_results["start_time"]
        test_results["recommendations"] = _generate_network_recommendations(test_results)
        
        logger.info(f"Completed network testing scenario: {params.test_scenario}")
        
        return {
            "success": True,
            "test_results": test_results,
            "session_id": context.session_id
        }
        
    except Exception as e:
        logger.error(f"Error in network testing: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def _calculate_performance_impact(condition: NetworkCondition) -> Dict[str, Any]:
    """Calculate expected performance impact of network condition"""
    
    # Estimate page load time impact based on network condition
    baseline_load_time = 2.0  # seconds for typical page
    
    if condition.offline:
        impact_factor = float('inf')
        impact_description = "Complete network failure - pages will not load"
    elif condition.latency > 2000:  # > 2 seconds
        impact_factor = 5.0
        impact_description = "Severe performance impact - very slow loading"
    elif condition.latency > 800:   # > 800ms
        impact_factor = 3.0
        impact_description = "Significant performance impact - slow loading"
    elif condition.latency > 300:   # > 300ms
        impact_factor = 1.8
        impact_description = "Moderate performance impact - noticeable delays"
    elif condition.latency > 100:   # > 100ms
        impact_factor = 1.3
        impact_description = "Minor performance impact - slight delays"
    else:
        impact_factor = 1.0
        impact_description = "Minimal performance impact - fast loading"
    
    estimated_load_time = baseline_load_time * impact_factor
    
    return {
        "estimated_page_load_time": f"{estimated_load_time:.1f}s",
        "impact_factor": f"{impact_factor}x",
        "impact_description": impact_description,
        "recommendations": _get_condition_recommendations(condition)
    }


def _get_use_cases(connection_type: NetworkConnectionType) -> List[str]:
    """Get typical use cases for network condition"""
    use_cases = {
        NetworkConnectionType.OFFLINE: [
            "Test offline functionality",
            "Validate service worker behavior", 
            "Test error handling for network failures"
        ],
        NetworkConnectionType.SLOW_2G: [
            "Test performance on very slow connections",
            "Validate progressive loading strategies",
            "Test timeout handling"
        ],
        NetworkConnectionType.SLOW_3G: [
            "Test mobile performance in poor coverage areas",
            "Validate critical resource prioritization",
            "Test user experience on slow connections"
        ],
        NetworkConnectionType.FAST_3G: [
            "Test typical mobile performance",
            "Validate mobile-optimized loading",
            "Test responsive design performance"
        ],
        NetworkConnectionType.SLOW_4G: [
            "Test performance on congested networks",
            "Validate resource loading strategies",
            "Test video/media performance"
        ],
        NetworkConnectionType.FAST_4G: [
            "Test modern mobile performance",
            "Validate rich media experiences",
            "Test real-time features"
        ],
        NetworkConnectionType.WIFI: [
            "Test desktop-like mobile performance",
            "Validate high-bandwidth features",
            "Test concurrent operations"
        ],
        NetworkConnectionType.ETHERNET: [
            "Test optimal performance scenarios",
            "Validate all features work smoothly",
            "Baseline performance testing"
        ]
    }
    
    return use_cases.get(connection_type, ["General network testing"])


def _get_condition_recommendations(condition: NetworkCondition) -> List[str]:
    """Get recommendations based on network condition"""
    recommendations = []
    
    if condition.offline:
        recommendations.extend([
            "Implement robust offline functionality",
            "Use service workers for caching",
            "Provide clear offline status indicators"
        ])
    elif condition.latency > 1000:
        recommendations.extend([
            "Minimize initial page load requirements",
            "Implement progressive loading",
            "Use skeleton screens for perceived performance",
            "Optimize critical rendering path"
        ])
    elif condition.downloadThroughput < 50 * 1024:  # < 50 KB/s
        recommendations.extend([
            "Compress all assets aggressively",
            "Implement lazy loading for images",
            "Minimize JavaScript bundle size",
            "Use WebP or AVIF image formats"
        ])
    
    return recommendations


def _process_performance_metrics(metrics: List[Dict]) -> Dict[str, float]:
    """Process CDP performance metrics"""
    processed = {}
    
    for metric in metrics:
        name = metric.get("name", "")
        value = metric.get("value", 0)
        
        if name in ["Timestamp", "JSHeapUsedSize", "JSHeapTotalSize", "FirstMeaningfulPaint"]:
            processed[name] = value
    
    return processed


def _generate_network_recommendations(test_results: Dict[str, Any]) -> List[str]:
    """Generate recommendations based on network testing results"""
    recommendations = []
    
    conditions_tested = test_results.get("conditions_tested", [])
    
    if len(conditions_tested) > 0:
        recommendations.append("Consider implementing adaptive loading based on connection speed")
        recommendations.append("Test critical user journeys on slower connections")
        
        # Check if slow conditions were problematic
        slow_conditions = [c for c in conditions_tested if "slow" in c["condition"].lower()]
        if slow_conditions:
            recommendations.append("Optimize for mobile and slow connections - these are critical user scenarios")
    
    return recommendations