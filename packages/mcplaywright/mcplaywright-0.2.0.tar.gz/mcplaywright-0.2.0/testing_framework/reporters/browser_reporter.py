#!/usr/bin/env python3
"""
Browser Test Reporter - Specialized reporter for MCPlaywright browser automation tests.

Provides comprehensive browser-specific test reporting including screenshots,
video analysis, network monitoring, and dynamic tool visibility tracking.
"""

import html
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import time

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from .base_reporter import BaseReporter
from utilities.syntax_highlighter import SyntaxHighlighter
from utilities.quality_metrics import QualityMetrics


class BrowserTestReporter(BaseReporter):
    """
    Specialized test reporter for browser automation testing.
    
    Features:
    - Screenshot integration with quality assessment
    - Video recording analysis and validation
    - Network request monitoring and analysis  
    - Dynamic tool visibility timeline tracking
    - Browser action logging with timing
    - MCPlaywright-specific quality metrics
    """
    
    def __init__(self, test_name: str, browser_context: str = "chromium"):
        """Initialize browser test reporter."""
        super().__init__(test_name)
        
        self.browser_context = browser_context
        self.syntax_highlighter = SyntaxHighlighter()
        self.quality_metrics = QualityMetrics()
        
        # Browser-specific data
        self.browser_actions = []
        self.screenshots = []
        self.video_segments = []
        self.network_requests = []
        self.tool_visibility_timeline = []
        
        # Performance tracking
        self.action_timings = []
        self.last_action_time = time.time()
        
        # Test lifecycle tracking
        self.test_steps = []
        self.test_started = False
        self.test_completed = False
        
        # Session tracking
        self.session_id = f"mcplaywright_{test_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def log_test_start(self, test_name: str, description: str = "") -> None:
        """Log the start of a test."""
        self.test_started = True
        self.data["test_info"] = {
            "name": test_name,
            "description": description,
            "start_time": datetime.now().isoformat(),
            "browser_context": self.browser_context
        }
    
    def log_test_step(self, step_name: str, description: str = "") -> None:
        """Log a test step."""
        step_entry = {
            "name": step_name,
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "success": True  # Will be updated if errors occur
        }
        self.test_steps.append(step_entry)
    
    def log_test_completion(self, success: bool) -> None:
        """Log test completion."""
        self.test_completed = True
        end_time = time.time()
        duration = end_time - self.start_time
        
        if "test_info" not in self.data:
            self.data["test_info"] = {}
        
        self.data["test_info"].update({
            "end_time": datetime.now().isoformat(),
            "duration": duration,
            "success": success,
            "steps": self.test_steps
        })
        
    def get_test_data(self) -> Dict[str, Any]:
        """Get complete test data for analysis."""
        return {
            **self.data,
            "session_id": getattr(self, 'session_id', 'unknown'),
            "browser_data": {
                "actions": self.browser_actions,
                "screenshots": self.screenshots,
                "video_segments": self.video_segments,
                "network_requests": self.network_requests,
                "tool_visibility_timeline": self.tool_visibility_timeline
            },
            "timestamp": datetime.now().isoformat()
        }

    def log_browser_action(self, action: str, selector: Optional[str], 
                          result: Any, duration_ms: Optional[float] = None) -> None:
        """Log browser interaction with timing and results."""
        current_time = time.time()
        
        if duration_ms is None:
            duration_ms = (current_time - self.last_action_time) * 1000
        
        action_entry = {
            "action": action,
            "selector": selector,
            "result": result,
            "duration_ms": duration_ms,
            "timestamp": datetime.now().isoformat(),
            "success": self._determine_action_success(result)
        }
        
        self.browser_actions.append(action_entry)
        self.action_timings.append(duration_ms)
        self.last_action_time = current_time
        
        # Log as processing step for base reporter
        self.log_processing_step(
            f"Browser: {action}",
            action_entry,
            duration_ms / 1000  # Convert to seconds
        )
    
    def log_screenshot(self, name: str, screenshot_path: str, 
                      description: str = "", quality_score: Optional[float] = None) -> None:
        """Log screenshot with quality assessment."""
        # Ensure path is relative to reports directory
        if screenshot_path.startswith("/"):
            screenshot_path = os.path.relpath(screenshot_path, "/app/reports")
        
        screenshot_entry = {
            "name": name,
            "path": screenshot_path,
            "description": description,
            "quality_score": quality_score,
            "timestamp": datetime.now().isoformat(),
            "exists": os.path.exists(f"/app/reports/{screenshot_path}")
        }
        
        self.screenshots.append(screenshot_entry)
        
        # Log as output for base reporter
        self.log_output(
            f"screenshot_{name}",
            screenshot_entry,
            f"Screenshot: {description}",
            quality_score
        )
    
    def log_video_segment(self, name: str, video_path: str, duration: float,
                         quality_score: Optional[float] = None) -> None:
        """Log video recording segment with analysis."""
        # Ensure path is relative to reports directory
        if video_path.startswith("/"):
            video_path = os.path.relpath(video_path, "/app/reports")
        
        video_entry = {
            "name": name,
            "path": video_path,
            "duration": duration,
            "quality_score": quality_score,
            "timestamp": datetime.now().isoformat(),
            "exists": os.path.exists(f"/app/reports/{video_path}"),
            "size_mb": self._get_file_size_mb(f"/app/reports/{video_path}")
        }
        
        self.video_segments.append(video_entry)
        
        # Log as output for base reporter
        self.log_output(
            f"video_{name}",
            video_entry,
            f"Video: {name} ({duration:.1f}s)",
            quality_score
        )
    
    def log_network_requests(self, requests: List[Dict], description: str = "") -> None:
        """Log network requests for analysis."""
        network_entry = {
            "requests": requests,
            "count": len(requests),
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "success_rate": self._calculate_request_success_rate(requests),
            "average_response_time": self._calculate_average_response_time(requests)
        }
        
        self.network_requests.append(network_entry)
        
        # Log as output for base reporter
        self.log_output(
            "network_requests",
            network_entry,
            f"Network: {description} ({len(requests)} requests)"
        )
    
    def log_tool_visibility(self, visible_tools: List[str], hidden_tools: List[str],
                           description: str = "") -> None:
        """Track dynamic tool visibility changes."""
        visibility_entry = {
            "visible_tools": visible_tools,
            "hidden_tools": hidden_tools,
            "visible_count": len(visible_tools),
            "hidden_count": len(hidden_tools),
            "description": description,
            "timestamp": datetime.now().isoformat()
        }
        
        self.tool_visibility_timeline.append(visibility_entry)
        
        # Log as processing step for base reporter
        self.log_processing_step(
            "Tool Visibility",
            visibility_entry
        )
    
    async def finalize_browser_test(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive browser test report."""
        return await self.finalize(output_path)
    
    async def finalize(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Generate final browser test report with HTML output."""
        end_time = time.time()
        duration = end_time - self.start_time
        
        # Calculate overall quality metrics
        overall_quality_score = self._calculate_overall_quality_score()
        overall_passed = self._calculate_overall_status()
        
        # Build final result
        result = {
            "test_name": self.test_name,
            "browser_context": self.browser_context,
            "duration": duration,
            "passed": overall_passed,
            "overall_quality_score": overall_quality_score,
            "timestamp": datetime.now().isoformat(),
            "data": self.data,
            "browser_data": {
                "actions": self.browser_actions,
                "screenshots": self.screenshots,
                "video_segments": self.video_segments,
                "network_requests": self.network_requests,
                "tool_visibility_timeline": self.tool_visibility_timeline
            },
            "performance_metrics": {
                "action_count": len(self.browser_actions),
                "successful_actions": sum(1 for a in self.browser_actions if a["success"]),
                "average_action_time": sum(self.action_timings) / len(self.action_timings) if self.action_timings else 0,
                "screenshot_count": len(self.screenshots),
                "video_count": len(self.video_segments),
                "network_request_count": sum(nr["count"] for nr in self.network_requests)
            },
            "summary": self._get_summary_stats()
        }
        
        # Generate HTML report if path provided
        if output_path:
            html_content = self._generate_browser_html_report(result)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
        
        return result
    
    def _determine_action_success(self, result: Any) -> bool:
        """Determine if a browser action was successful."""
        if isinstance(result, dict):
            return result.get("success", True) and not result.get("error")
        if isinstance(result, bool):
            return result
        return True  # Default to success
    
    def _calculate_request_success_rate(self, requests: List[Dict]) -> float:
        """Calculate HTTP request success rate."""
        if not requests:
            return 0.0
        
        successful = sum(1 for r in requests 
                        if 200 <= r.get("status", 0) < 400)
        return (successful / len(requests)) * 100
    
    def _calculate_average_response_time(self, requests: List[Dict]) -> float:
        """Calculate average response time for requests."""
        if not requests:
            return 0.0
        
        times = [r.get("response_time", 0) for r in requests if "response_time" in r]
        return sum(times) / len(times) if times else 0.0
    
    def _get_file_size_mb(self, file_path: str) -> float:
        """Get file size in megabytes."""
        try:
            if os.path.exists(file_path):
                return os.path.getsize(file_path) / (1024 * 1024)
        except:
            pass
        return 0.0
    
    def _calculate_overall_quality_score(self) -> float:
        """Calculate overall quality score for browser test."""
        scores = []
        
        # Action success rate
        if self.browser_actions:
            success_rate = sum(1 for a in self.browser_actions if a["success"]) / len(self.browser_actions)
            scores.append(success_rate * 10)  # Scale to 0-10
        
        # Screenshot quality
        screenshot_scores = [s["quality_score"] for s in self.screenshots 
                           if s["quality_score"] is not None]
        if screenshot_scores:
            scores.append(sum(screenshot_scores) / len(screenshot_scores))
        
        # Video quality
        video_scores = [v["quality_score"] for v in self.video_segments 
                       if v["quality_score"] is not None]
        if video_scores:
            scores.append(sum(video_scores) / len(video_scores))
        
        # Quality metrics from base reporter
        quality_metrics_scores = [
            m["value"] for m in self.data["quality_metrics"].values()
            if isinstance(m["value"], (int, float)) and m["passed"]
        ]
        scores.extend(quality_metrics_scores)
        
        return sum(scores) / len(scores) if scores else 7.0  # Default score
    
    def _generate_browser_html_report(self, result: Dict[str, Any]) -> str:
        """Generate beautiful HTML report with MCPlaywright theme."""
        status_class = "success" if result["passed"] else "failure"
        status_text = "PASSED" if result["passed"] else "FAILED"
        
        # Build sections
        overview_html = self._build_overview_section(result)
        inputs_html = self._build_inputs_section(result["data"]["inputs"])
        outputs_html = self._build_outputs_section(result["data"]["outputs"])
        actions_html = self._build_actions_section(result["browser_data"]["actions"])
        screenshots_html = self._build_screenshots_section(result["browser_data"]["screenshots"])
        videos_html = self._build_videos_section(result["browser_data"]["video_segments"])
        network_html = self._build_network_section(result["browser_data"]["network_requests"])
        tools_html = self._build_tools_timeline_section(result["browser_data"]["tool_visibility_timeline"])
        metrics_html = self._build_metrics_section(result["data"]["quality_metrics"])
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCPlaywright Test: {html.escape(result["test_name"])}</title>
    <style>
        {self._get_mcplaywright_css()}
    </style>
</head>
<body>
    <div class="container">
        <header class="report-header {status_class}">
            <div class="header-content">
                <h1>🎭 {html.escape(result["test_name"])}</h1>
                <div class="status-badge {status_class}">{status_text}</div>
            </div>
            <div class="report-meta">
                <span>Browser: {html.escape(result["browser_context"])}</span>
                <span>Duration: {result["duration"]:.3f}s</span>
                <span>Quality: {result["overall_quality_score"]:.1f}/10</span>
                <span>Timestamp: {result["timestamp"]}</span>
            </div>
        </header>
        
        {overview_html}
        {actions_html}
        {screenshots_html}
        {videos_html}
        {network_html}
        {tools_html}
        {metrics_html}
    </div>
    
    <script>
        {self._get_javascript_interactions()}
    </script>
</body>
</html>"""
    
    def _build_overview_section(self, result: Dict[str, Any]) -> str:
        """Build test overview section."""
        perf = result["performance_metrics"]
        
        return f"""
        <div class="overview-section">
            <h2>📊 Test Overview</h2>
            <div class="overview-grid">
                <div class="overview-item">
                    <span class="overview-number">{perf["action_count"]}</span>
                    <span class="overview-label">Browser Actions</span>
                </div>
                <div class="overview-item">
                    <span class="overview-number">{perf["successful_actions"]}</span>
                    <span class="overview-label">Successful</span>
                </div>
                <div class="overview-item">
                    <span class="overview-number">{perf["screenshot_count"]}</span>
                    <span class="overview-label">Screenshots</span>
                </div>
                <div class="overview-item">
                    <span class="overview-number">{perf["video_count"]}</span>
                    <span class="overview-label">Videos</span>
                </div>
                <div class="overview-item">
                    <span class="overview-number">{perf["network_request_count"]}</span>
                    <span class="overview-label">Network Requests</span>
                </div>
                <div class="overview-item">
                    <span class="overview-number">{perf["average_action_time"]:.0f}ms</span>
                    <span class="overview-label">Avg Action Time</span>
                </div>
            </div>
        </div>
        """
    
    def _build_inputs_section(self, inputs: Dict[str, Any]) -> str:
        """Build test inputs section with gruvbox terminal styling."""
        if not inputs:
            return """
            <div class="section">
                <h2>📥 Test Inputs</h2>
                <div class="empty-section">No test inputs recorded</div>
            </div>
            """
        
        inputs_html = []
        for name, input_data in inputs.items():
            value_preview = self._format_value_preview(input_data["value"])
            
            inputs_html.append(f"""
            <div class="input-item">
                <div class="input-header">
                    <span class="input-name">{html.escape(name)}</span>
                    <span class="input-type">{html.escape(input_data["type"])}</span>
                </div>
                {f'<div class="input-description">{html.escape(input_data["description"])}</div>' if input_data.get("description") else ''}
                <div class="input-value">
                    <pre>{self.syntax_highlighter.format_json_html(input_data["value"])}</pre>
                </div>
            </div>
            """)
        
        return f"""
        <div class="section">
            <h2>📥 Test Inputs</h2>
            <div class="inputs-container">
                {"".join(inputs_html)}
            </div>
        </div>
        """
    
    def _build_outputs_section(self, outputs: Dict[str, Any]) -> str:
        """Build test outputs section with gruvbox terminal styling."""
        if not outputs:
            return """
            <div class="section">
                <h2>📤 Test Outputs</h2>
                <div class="empty-section">No test outputs recorded</div>
            </div>
            """
        
        outputs_html = []
        for name, output_data in outputs.items():
            quality_indicator = ""
            if output_data.get("quality_score") is not None:
                quality_class = "high" if output_data["quality_score"] >= 8 else "medium" if output_data["quality_score"] >= 6 else "low"
                quality_indicator = f'<span class="quality-badge {quality_class}">{output_data["quality_score"]}/10</span>'
            
            outputs_html.append(f"""
            <div class="output-item">
                <div class="output-header">
                    <span class="output-name">{html.escape(name)}</span>
                    <div class="output-meta">
                        <span class="output-type">{html.escape(output_data["type"])}</span>
                        {quality_indicator}
                    </div>
                </div>
                {f'<div class="output-description">{html.escape(output_data["description"])}</div>' if output_data.get("description") else ''}
                <div class="output-value">
                    <pre>{self.syntax_highlighter.format_json_html(output_data["value"])}</pre>
                </div>
            </div>
            """)
        
        return f"""
        <div class="section">
            <h2>📤 Test Outputs</h2>
            <div class="outputs-container">
                {"".join(outputs_html)}
            </div>
        </div>
        """
    
    def _format_value_preview(self, value: Any) -> str:
        """Format a value for display preview."""
        if isinstance(value, str):
            return value[:100] + "..." if len(value) > 100 else value
        elif isinstance(value, (dict, list)):
            return str(type(value).__name__)
        else:
            return str(value)
    
    def _build_actions_section(self, actions: List[Dict[str, Any]]) -> str:
        """Build browser actions timeline section."""
        if not actions:
            return ""
        
        actions_html = []
        for i, action in enumerate(actions, 1):
            status_icon = "✅" if action["success"] else "❌"
            selector_text = f"<code>{html.escape(action['selector'])}</code>" if action["selector"] else ""
            
            action_html = f"""
            <div class="action-item {'action-success' if action['success'] else 'action-failure'}">
                <div class="action-header">
                    <span class="action-number">{i}</span>
                    <span class="action-name">{status_icon} {html.escape(action['action'])}</span>
                    <span class="action-timing">{action['duration_ms']:.0f}ms</span>
                </div>
                {f'<div class="action-selector">{selector_text}</div>' if selector_text else ''}
                <div class="action-result">
                    <pre>{self.syntax_highlighter.format_json_html(action['result'])}</pre>
                </div>
            </div>
            """
            actions_html.append(action_html)
        
        return f"""
        <div class="section">
            <h2>🎬 Browser Actions Timeline</h2>
            <div class="actions-timeline">
                {"".join(actions_html)}
            </div>
        </div>
        """
    
    def _build_screenshots_section(self, screenshots: List[Dict[str, Any]]) -> str:
        """Build screenshots gallery section."""
        if not screenshots:
            return ""
        
        gallery_html = []
        for screenshot in screenshots:
            quality_indicator = ""
            if screenshot["quality_score"]:
                quality_class = "high" if screenshot["quality_score"] >= 8 else "medium" if screenshot["quality_score"] >= 6 else "low"
                quality_indicator = f'<span class="quality-badge {quality_class}">{screenshot["quality_score"]}/10</span>'
            
            exists_indicator = "📸" if screenshot["exists"] else "❌"
            
            screenshot_html = f"""
            <div class="screenshot-item">
                <div class="screenshot-header">
                    <span class="screenshot-name">{exists_indicator} {html.escape(screenshot['name'])}</span>
                    {quality_indicator}
                </div>
                {f'<div class="screenshot-description">{html.escape(screenshot["description"])}</div>' if screenshot["description"] else ''}
                <div class="screenshot-container">
                    {f'<img src="{screenshot["path"]}" alt="{html.escape(screenshot["name"])}" class="screenshot-image">' if screenshot["exists"] else '<div class="screenshot-missing">Screenshot not found</div>'}
                </div>
            </div>
            """
            gallery_html.append(screenshot_html)
        
        return f"""
        <div class="section">
            <h2>📸 Screenshots Gallery</h2>
            <div class="screenshots-gallery">
                {"".join(gallery_html)}
            </div>
        </div>
        """
    
    def _build_videos_section(self, videos: List[Dict[str, Any]]) -> str:
        """Build video analysis section."""
        if not videos:
            return ""
        
        videos_html = []
        for video in videos:
            quality_indicator = ""
            if video["quality_score"]:
                quality_class = "high" if video["quality_score"] >= 8 else "medium" if video["quality_score"] >= 6 else "low"
                quality_indicator = f'<span class="quality-badge {quality_class}">{video["quality_score"]}/10</span>'
            
            exists_indicator = "🎥" if video["exists"] else "❌"
            
            video_html = f"""
            <div class="video-item">
                <div class="video-header">
                    <span class="video-name">{exists_indicator} {html.escape(video['name'])}</span>
                    {quality_indicator}
                </div>
                <div class="video-meta">
                    <span>Duration: {video['duration']:.1f}s</span>
                    <span>Size: {video['size_mb']:.1f} MB</span>
                </div>
                <div class="video-container">
                    {f'<video controls class="video-player"><source src="{video["path"]}" type="video/webm">Your browser does not support video playback.</video>' if video["exists"] else '<div class="video-missing">Video not found</div>'}
                </div>
            </div>
            """
            videos_html.append(video_html)
        
        return f"""
        <div class="section">
            <h2>🎥 Video Analysis</h2>
            <div class="videos-section">
                {"".join(videos_html)}
            </div>
        </div>
        """
    
    def _build_network_section(self, network_data: List[Dict[str, Any]]) -> str:
        """Build network requests analysis section."""
        if not network_data:
            return ""
        
        network_html = []
        for entry in network_data:
            requests_html = []
            for req in entry["requests"][:10]:  # Show first 10 requests
                status_class = "success" if 200 <= req.get("status", 0) < 400 else "error"
                
                request_html = f"""
                <div class="network-request {status_class}">
                    <div class="request-line">
                        <span class="method">{req.get('method', 'GET')}</span>
                        <span class="url">{html.escape(req.get('url', ''))}</span>
                        <span class="status">{req.get('status', 'N/A')}</span>
                    </div>
                </div>
                """
                requests_html.append(request_html)
            
            if len(entry["requests"]) > 10:
                requests_html.append(f'<div class="more-requests">... and {len(entry["requests"]) - 10} more requests</div>')
            
            network_html.append(f"""
            <div class="network-entry">
                <div class="network-header">
                    <h3>🌐 {html.escape(entry['description']) if entry['description'] else 'Network Requests'}</h3>
                    <div class="network-stats">
                        <span>Count: {entry['count']}</span>
                        <span>Success Rate: {entry['success_rate']:.1f}%</span>
                        <span>Avg Response: {entry['average_response_time']:.0f}ms</span>
                    </div>
                </div>
                <div class="network-requests">
                    {"".join(requests_html)}
                </div>
            </div>
            """)
        
        return f"""
        <div class="section">
            <h2>🌐 Network Analysis</h2>
            {"".join(network_html)}
        </div>
        """
    
    def _build_tools_timeline_section(self, timeline: List[Dict[str, Any]]) -> str:
        """Build dynamic tool visibility timeline."""
        if not timeline:
            return ""
        
        timeline_html = []
        for i, entry in enumerate(timeline, 1):
            timeline_html.append(f"""
            <div class="timeline-item">
                <div class="timeline-marker">{i}</div>
                <div class="timeline-content">
                    <div class="timeline-description">{html.escape(entry['description'])}</div>
                    <div class="timeline-details">
                        <div class="tools-visible">
                            <strong>Visible Tools ({entry['visible_count']}):</strong>
                            <div class="tool-tags">
                                {' '.join(f'<span class="tool-tag visible">{html.escape(tool)}</span>' for tool in entry['visible_tools'])}
                            </div>
                        </div>
                        <div class="tools-hidden">
                            <strong>Hidden Tools ({entry['hidden_count']}):</strong>
                            <div class="tool-tags">
                                {' '.join(f'<span class="tool-tag hidden">{html.escape(tool)}</span>' for tool in entry['hidden_tools'])}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            """)
        
        return f"""
        <div class="section">
            <h2>🛠️ Dynamic Tool Visibility Timeline</h2>
            <div class="tools-timeline">
                {"".join(timeline_html)}
            </div>
        </div>
        """
    
    def _build_metrics_section(self, metrics: Dict[str, Any]) -> str:
        """Build quality metrics section."""
        if not metrics:
            return ""
        
        metrics_html = []
        for name, data in metrics.items():
            status_class = "passed" if data["passed"] else "failed"
            status_text = "PASS" if data["passed"] else "FAIL"
            
            metrics_html.append(f"""
            <div class="quality-metric {status_class}">
                <div class="metric-info">
                    <div class="metric-name">{html.escape(name)}</div>
                    <div class="metric-values">
                        Value: {data['value']} | Threshold: {data['threshold']}
                    </div>
                </div>
                <span class="metric-status {status_class}">{status_text}</span>
            </div>
            """)
        
        return f"""
        <div class="section">
            <h2>📊 Quality Metrics</h2>
            {"".join(metrics_html)}
        </div>
        """
    
    def _get_mcplaywright_css(self) -> str:
        """Get MCPlaywright-themed CSS for browser test reports."""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            line-height: 1.6;
            color: #2d3748;
            background: #f8fafc;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        .report-header {
            background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            position: relative;
        }

        .report-header.failure {
            background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
        }

        .header-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }

        .header-content h1 {
            font-size: 2rem;
            margin: 0;
        }

        .status-badge {
            padding: 8px 20px;
            border-radius: 25px;
            font-weight: 600;
            font-size: 0.9rem;
        }

        .status-badge.success {
            background: rgba(34, 197, 94, 0.2);
            color: #16a34a;
            border: 2px solid #22c55e;
        }

        .status-badge.failure {
            background: rgba(239, 68, 68, 0.2);
            color: #dc2626;
            border: 2px solid #ef4444;
        }

        .report-meta {
            display: flex;
            gap: 25px;
            font-size: 0.9rem;
            opacity: 0.9;
            flex-wrap: wrap;
        }

        .section {
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        }

        .section h2 {
            color: #0ea5e9;
            font-size: 1.5rem;
            margin-bottom: 25px;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 10px;
        }

        .overview-section {
            background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
            color: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
        }

        .overview-section h2 {
            color: white;
            border-bottom-color: rgba(255, 255, 255, 0.3);
        }

        .overview-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
        }

        .overview-item {
            text-align: center;
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 8px;
        }

        .overview-number {
            display: block;
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 8px;
        }

        .overview-label {
            font-size: 0.9rem;
            opacity: 0.9;
        }

        .empty-section {
            text-align: center;
            padding: 40px;
            color: #64748b;
            font-style: italic;
            background: #f8fafc;
            border: 1px dashed #e2e8f0;
            border-radius: 8px;
        }

        .inputs-container, .outputs-container {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .input-item, .output-item {
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px;
            background: #f8fafc;
            border-left: 4px solid #0ea5e9;
        }

        .input-header, .output-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }

        .input-name, .output-name {
            font-weight: 600;
            color: #1e293b;
        }

        .input-type, .output-type {
            background: #e2e8f0;
            color: #64748b;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8rem;
            font-family: monospace;
        }

        .output-meta {
            display: flex;
            gap: 10px;
            align-items: center;
        }

        .input-description, .output-description {
            margin: 10px 0;
            color: #64748b;
            font-style: italic;
        }

        .input-value, .output-value {
            margin-top: 15px;
        }

        .input-value pre, .output-value pre {
            background: #1e293b;
            color: #e2e8f0;
            padding: 15px;
            border-radius: 6px;
            font-size: 0.8rem;
            overflow-x: auto;
            max-height: 300px;
            overflow-y: auto;
        }

        .actions-timeline {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }

        .action-item {
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px;
            background: #f8fafc;
        }

        .action-item.action-success {
            border-left: 4px solid #22c55e;
        }

        .action-item.action-failure {
            border-left: 4px solid #ef4444;
        }

        .action-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }

        .action-number {
            background: #0ea5e9;
            color: white;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8rem;
            font-weight: 600;
        }

        .action-name {
            font-weight: 600;
            flex: 1;
            margin-left: 15px;
        }

        .action-timing {
            background: #e2e8f0;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8rem;
            font-family: monospace;
        }

        .action-selector {
            margin: 10px 0;
            font-size: 0.9rem;
        }

        .action-selector code {
            background: #1e293b;
            color: #64748b;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.8rem;
        }

        .action-result {
            margin-top: 15px;
        }

        .action-result pre {
            background: #1e293b;
            color: #e2e8f0;
            padding: 15px;
            border-radius: 6px;
            font-size: 0.8rem;
            overflow-x: auto;
        }

        .screenshots-gallery {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }

        .screenshot-item {
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            overflow: hidden;
            background: white;
        }

        .screenshot-header {
            padding: 15px;
            background: #f8fafc;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .screenshot-name {
            font-weight: 600;
        }

        .quality-badge {
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
        }

        .quality-badge.high {
            background: #dcfce7;
            color: #166534;
        }

        .quality-badge.medium {
            background: #fef3c7;
            color: #92400e;
        }

        .quality-badge.low {
            background: #fee2e2;
            color: #991b1b;
        }

        .screenshot-description {
            padding: 0 15px 15px;
            font-style: italic;
            color: #64748b;
        }

        .screenshot-container {
            position: relative;
            overflow: hidden;
        }

        .screenshot-image {
            width: 100%;
            height: auto;
            display: block;
        }

        .screenshot-missing {
            padding: 40px;
            text-align: center;
            color: #64748b;
            background: #f1f5f9;
        }

        .videos-section {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .video-item {
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            overflow: hidden;
            background: white;
        }

        .video-header {
            padding: 15px;
            background: #f8fafc;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .video-name {
            font-weight: 600;
        }

        .video-meta {
            padding: 0 15px 15px;
            display: flex;
            gap: 20px;
            font-size: 0.9rem;
            color: #64748b;
        }

        .video-container {
            padding: 15px;
        }

        .video-player {
            width: 100%;
            height: auto;
            border-radius: 4px;
        }

        .video-missing {
            padding: 40px;
            text-align: center;
            color: #64748b;
            background: #f1f5f9;
        }

        .network-entry {
            margin-bottom: 30px;
        }

        .network-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }

        .network-header h3 {
            margin: 0;
            color: #0ea5e9;
        }

        .network-stats {
            display: flex;
            gap: 15px;
            font-size: 0.9rem;
            color: #64748b;
        }

        .network-requests {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .network-request {
            padding: 10px 15px;
            border-radius: 6px;
            border-left: 4px solid #e2e8f0;
        }

        .network-request.success {
            border-left-color: #22c55e;
            background: #f0fdf4;
        }

        .network-request.error {
            border-left-color: #ef4444;
            background: #fef2f2;
        }

        .request-line {
            display: flex;
            gap: 15px;
            align-items: center;
        }

        .method {
            background: #0ea5e9;
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: 600;
            min-width: 50px;
            text-align: center;
        }

        .url {
            flex: 1;
            font-family: monospace;
            font-size: 0.9rem;
        }

        .status {
            background: #e2e8f0;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.8rem;
            font-family: monospace;
        }

        .more-requests {
            text-align: center;
            padding: 10px;
            color: #64748b;
            font-style: italic;
        }

        .tools-timeline {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .timeline-item {
            display: flex;
            gap: 20px;
        }

        .timeline-marker {
            background: #0ea5e9;
            color: white;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            flex-shrink: 0;
        }

        .timeline-content {
            flex: 1;
            padding-bottom: 20px;
            border-bottom: 1px solid #e2e8f0;
        }

        .timeline-description {
            font-weight: 600;
            margin-bottom: 15px;
            color: #1e293b;
        }

        .timeline-details {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }

        .tools-visible, .tools-hidden {
            padding: 15px;
            border-radius: 8px;
        }

        .tools-visible {
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
        }

        .tools-hidden {
            background: #fef2f2;
            border: 1px solid #fecaca;
        }

        .tool-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 8px;
        }

        .tool-tag {
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 500;
        }

        .tool-tag.visible {
            background: #dcfce7;
            color: #166534;
        }

        .tool-tag.hidden {
            background: #fee2e2;
            color: #991b1b;
        }

        .quality-metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 6px;
            border-left: 4px solid #e2e8f0;
        }

        .quality-metric.passed {
            border-left-color: #22c55e;
            background: #f0fdf4;
        }

        .quality-metric.failed {
            border-left-color: #ef4444;
            background: #fef2f2;
        }

        .metric-name {
            font-weight: 600;
            margin-bottom: 5px;
        }

        .metric-values {
            font-family: monospace;
            font-size: 0.9rem;
            color: #64748b;
        }

        .metric-status {
            padding: 6px 12px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
        }

        .metric-status.passed {
            background: #dcfce7;
            color: #166534;
        }

        .metric-status.failed {
            background: #fee2e2;
            color: #991b1b;
        }

        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }
            
            .report-header {
                padding: 20px;
            }
            
            .header-content {
                flex-direction: column;
                align-items: flex-start;
                gap: 10px;
            }
            
            .report-meta {
                flex-direction: column;
                gap: 10px;
            }
            
            .overview-grid {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .screenshots-gallery {
                grid-template-columns: 1fr;
            }
            
            .network-header {
                flex-direction: column;
                align-items: flex-start;
                gap: 10px;
            }
            
            .timeline-item {
                flex-direction: column;
            }
            
            .timeline-details {
                margin-left: 0;
            }
        }
        """
    
    def _get_javascript_interactions(self) -> str:
        """Get JavaScript for interactive elements."""
        return """
        // Collapsible sections
        document.querySelectorAll('.section h2').forEach(header => {
            header.style.cursor = 'pointer';
            header.addEventListener('click', () => {
                const section = header.parentElement;
                const content = Array.from(section.children).filter(child => child !== header);
                const isCollapsed = section.classList.contains('collapsed');
                
                if (isCollapsed) {
                    section.classList.remove('collapsed');
                    content.forEach(el => el.style.display = '');
                } else {
                    section.classList.add('collapsed');
                    content.forEach(el => el.style.display = 'none');
                }
            });
        });
        
        // Screenshot zoom
        document.querySelectorAll('.screenshot-image').forEach(img => {
            img.style.cursor = 'zoom-in';
            img.addEventListener('click', () => {
                const modal = document.createElement('div');
                modal.style.cssText = `
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.8);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 1000;
                    cursor: zoom-out;
                `;
                
                const enlargedImg = img.cloneNode();
                enlargedImg.style.cssText = 'max-width: 90%; max-height: 90%; object-fit: contain;';
                modal.appendChild(enlargedImg);
                
                modal.addEventListener('click', () => {
                    document.body.removeChild(modal);
                });
                
                document.body.appendChild(modal);
            });
        });
        
        // Performance indicators
        console.log('MCPlaywright Test Report loaded successfully');
        """
    
    def generate_html_report(self) -> str:
        """Generate complete HTML report for the browser test."""
        # Calculate overall quality score
        overall_quality = self._calculate_overall_quality_score()
        
        # Performance metrics
        performance_metrics = {
            "action_count": len(self.browser_actions),
            "successful_actions": sum(1 for a in self.browser_actions if a.get("success", True)),
            "screenshot_count": len(self.screenshots),
            "video_count": len(self.video_segments),
            "network_request_count": sum(len(n.get("requests", [])) for n in self.network_requests),
            "average_action_time": sum(a.get("duration_ms", 0) for a in self.browser_actions) / max(len(self.browser_actions), 1)
        }
        
        # Build complete result object
        result = {
            "test_name": self.test_name,
            "browser_context": self.browser_context,
            "timestamp": datetime.now().isoformat(),
            "duration": time.time() - self.start_time,
            "passed": self.test_completed and self.data.get("test_info", {}).get("success", False),
            "overall_quality_score": overall_quality,
            "performance_metrics": performance_metrics,
            "data": self.data,
            "browser_data": {
                "actions": self.browser_actions,
                "screenshots": self.screenshots,
                "video_segments": self.video_segments,
                "network_requests": self.network_requests,
                "tool_visibility_timeline": self.tool_visibility_timeline
            }
        }
        
        return self._generate_browser_html_report(result)