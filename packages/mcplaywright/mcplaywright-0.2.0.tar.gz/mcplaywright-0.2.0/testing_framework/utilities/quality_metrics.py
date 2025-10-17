#!/usr/bin/env python3
"""
Quality Metrics System for MCPlaywright Testing Framework.

Provides comprehensive quality assessment and scoring for browser automation
testing including action success rates, screenshot quality, video analysis,
network monitoring completeness, and tool visibility accuracy.
"""

from typing import Dict, List, Any, Optional, Tuple
import statistics
from datetime import datetime


class QualityMetrics:
    """
    Quality metrics calculator for MCPlaywright browser automation testing.
    
    Provides specialized metrics for:
    - Browser action success rates and timing
    - Screenshot and video quality assessment
    - Network monitoring completeness
    - Dynamic tool visibility accuracy
    - Overall test reliability scoring
    """
    
    # MCPlaywright-specific quality thresholds
    MCPLAYWRIGHT_THRESHOLDS = {
        'action_success_rate': 95.0,      # 95% minimum success rate
        'screenshot_quality': 8.0,        # 8/10 minimum screenshot quality
        'video_quality': 7.5,             # 7.5/10 minimum video quality
        'network_completeness': 90.0,     # 90% request capture rate
        'response_time': 3000,            # 3 seconds max browser response
        'tool_visibility_accuracy': True, # Must pass tool filtering tests
        'session_stability': 8.0,         # 8/10 minimum session reliability
        'error_rate': 5.0,                # Maximum 5% error rate
    }
    
    def __init__(self):
        self.metrics_history = []
        self.quality_cache = {}
    
    def calculate_action_success_rate(self, browser_actions: List[Dict[str, Any]]) -> Tuple[float, bool]:
        """Calculate browser action success rate."""
        if not browser_actions:
            return 0.0, False
        
        successful_actions = sum(1 for action in browser_actions if action.get('success', True))
        success_rate = (successful_actions / len(browser_actions)) * 100
        
        threshold = self.MCPLAYWRIGHT_THRESHOLDS['action_success_rate']
        passed = success_rate >= threshold
        
        return success_rate, passed
    
    def calculate_screenshot_quality_score(self, screenshots: List[Dict[str, Any]]) -> Tuple[float, bool]:
        """Calculate average screenshot quality score."""
        if not screenshots:
            return 0.0, False
        
        quality_scores = [
            s.get('quality_score', 7.0) for s in screenshots 
            if s.get('quality_score') is not None
        ]
        
        if not quality_scores:
            # Default quality assessment based on availability
            available_screenshots = sum(1 for s in screenshots if s.get('exists', False))
            quality_score = (available_screenshots / len(screenshots)) * 10
        else:
            quality_score = statistics.mean(quality_scores)
        
        threshold = self.MCPLAYWRIGHT_THRESHOLDS['screenshot_quality']
        passed = quality_score >= threshold
        
        return quality_score, passed
    
    def calculate_video_quality_score(self, videos: List[Dict[str, Any]]) -> Tuple[float, bool]:
        """Calculate video recording quality score."""
        if not videos:
            return 0.0, False
        
        quality_scores = []
        for video in videos:
            if video.get('quality_score') is not None:
                quality_scores.append(video['quality_score'])
            else:
                # Assess quality based on duration and file size
                duration = video.get('duration', 0)
                size_mb = video.get('size_mb', 0)
                
                if duration > 0 and size_mb > 0:
                    # Simple quality heuristic: reasonable file size for duration
                    expected_size = duration * 0.5  # Expect ~0.5MB per second
                    size_ratio = min(size_mb / expected_size, 2.0)  # Cap at 2x expected
                    quality_score = min(size_ratio * 5, 10.0)  # Scale to 0-10
                    quality_scores.append(quality_score)
                else:
                    quality_scores.append(5.0)  # Default middle score
        
        if not quality_scores:
            return 0.0, False
        
        avg_quality = statistics.mean(quality_scores)
        threshold = self.MCPLAYWRIGHT_THRESHOLDS['video_quality']
        passed = avg_quality >= threshold
        
        return avg_quality, passed
    
    def calculate_network_completeness(self, network_requests: List[Dict[str, Any]], 
                                     expected_requests: Optional[int] = None) -> Tuple[float, bool]:
        """Calculate network monitoring completeness score."""
        if not network_requests:
            return 0.0, False
        
        total_captured = sum(entry.get('count', 0) for entry in network_requests)
        
        if expected_requests is not None:
            completeness = min((total_captured / expected_requests) * 100, 100.0)
        else:
            # Assess completeness based on success rates
            success_rates = [entry.get('success_rate', 0) for entry in network_requests]
            if success_rates:
                completeness = statistics.mean(success_rates)
            else:
                completeness = 0.0
        
        threshold = self.MCPLAYWRIGHT_THRESHOLDS['network_completeness']
        passed = completeness >= threshold
        
        return completeness, passed
    
    def calculate_response_time_score(self, browser_actions: List[Dict[str, Any]]) -> Tuple[float, bool]:
        """Calculate browser response time performance."""
        if not browser_actions:
            return 0.0, False
        
        response_times = [
            action.get('duration_ms', 0) for action in browser_actions 
            if action.get('duration_ms', 0) > 0
        ]
        
        if not response_times:
            return 0.0, False
        
        avg_response_time = statistics.mean(response_times)
        threshold = self.MCPLAYWRIGHT_THRESHOLDS['response_time']
        passed = avg_response_time <= threshold
        
        return avg_response_time, passed
    
    def calculate_tool_visibility_accuracy(self, tool_timeline: List[Dict[str, Any]], 
                                         expected_states: Optional[List[Dict]] = None) -> Tuple[bool, bool]:
        """Calculate dynamic tool visibility accuracy."""
        if not tool_timeline:
            return False, False
        
        if expected_states is None:
            # Basic validation: ensure tool counts are reasonable
            for entry in tool_timeline:
                visible_count = entry.get('visible_count', 0)
                hidden_count = entry.get('hidden_count', 0)
                
                # Basic sanity checks
                if visible_count < 1:  # At least one tool should always be visible
                    return False, False
                if visible_count + hidden_count > 50:  # Reasonable upper limit
                    return False, False
            
            return True, True
        else:
            # Detailed validation against expected states
            accuracy = True
            for i, expected in enumerate(expected_states):
                if i >= len(tool_timeline):
                    accuracy = False
                    break
                
                actual = tool_timeline[i]
                expected_visible = set(expected.get('visible_tools', []))
                actual_visible = set(actual.get('visible_tools', []))
                
                if expected_visible != actual_visible:
                    accuracy = False
                    break
            
            return accuracy, accuracy
    
    def calculate_session_stability(self, browser_actions: List[Dict[str, Any]], 
                                  errors: List[Dict[str, Any]]) -> Tuple[float, bool]:
        """Calculate browser session stability score."""
        if not browser_actions:
            return 0.0, False
        
        # Factors affecting stability
        factors = []
        
        # Error rate factor
        error_count = len(errors)
        total_operations = len(browser_actions)
        error_rate = (error_count / total_operations) * 100 if total_operations > 0 else 0
        error_factor = max(0, 10 - (error_rate * 2))  # Scale inversely with error rate
        factors.append(error_factor)
        
        # Action success consistency
        success_rates = []
        chunk_size = max(1, len(browser_actions) // 5)  # Analyze in chunks
        for i in range(0, len(browser_actions), chunk_size):
            chunk = browser_actions[i:i + chunk_size]
            chunk_success = sum(1 for a in chunk if a.get('success', True)) / len(chunk)
            success_rates.append(chunk_success)
        
        if success_rates:
            consistency = 1 - statistics.stdev(success_rates) if len(success_rates) > 1 else 1
            consistency_factor = consistency * 10
            factors.append(consistency_factor)
        
        # Response time stability
        response_times = [a.get('duration_ms', 0) for a in browser_actions if a.get('duration_ms', 0) > 0]
        if len(response_times) > 1:
            time_consistency = 1 - (statistics.stdev(response_times) / statistics.mean(response_times))
            time_factor = max(0, min(10, time_consistency * 10))
            factors.append(time_factor)
        
        stability_score = statistics.mean(factors) if factors else 0.0
        threshold = self.MCPLAYWRIGHT_THRESHOLDS['session_stability']
        passed = stability_score >= threshold
        
        return stability_score, passed
    
    def calculate_overall_quality_score(self, test_data: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """Calculate comprehensive overall quality score for a test."""
        browser_data = test_data.get('browser_data', {})
        base_data = test_data.get('data', {})
        
        metrics = {}
        scores = []
        
        # Browser action success rate
        actions = browser_data.get('actions', [])
        if actions:
            success_rate, passed = self.calculate_action_success_rate(actions)
            metrics['action_success_rate'] = {
                'value': success_rate,
                'passed': passed,
                'weight': 0.25,
                'description': f'{success_rate:.1f}% of browser actions succeeded'
            }
            scores.append(success_rate / 10)  # Normalize to 0-10 scale
        
        # Screenshot quality
        screenshots = browser_data.get('screenshots', [])
        if screenshots:
            screenshot_quality, passed = self.calculate_screenshot_quality_score(screenshots)
            metrics['screenshot_quality'] = {
                'value': screenshot_quality,
                'passed': passed,
                'weight': 0.15,
                'description': f'Average screenshot quality: {screenshot_quality:.1f}/10'
            }
            scores.append(screenshot_quality)
        
        # Video quality
        videos = browser_data.get('video_segments', [])
        if videos:
            video_quality, passed = self.calculate_video_quality_score(videos)
            metrics['video_quality'] = {
                'value': video_quality,
                'passed': passed,
                'weight': 0.15,
                'description': f'Average video quality: {video_quality:.1f}/10'
            }
            scores.append(video_quality)
        
        # Network monitoring
        network_data = browser_data.get('network_requests', [])
        if network_data:
            network_completeness, passed = self.calculate_network_completeness(network_data)
            metrics['network_completeness'] = {
                'value': network_completeness,
                'passed': passed,
                'weight': 0.15,
                'description': f'Network capture completeness: {network_completeness:.1f}%'
            }
            scores.append(network_completeness / 10)  # Normalize to 0-10 scale
        
        # Response time performance
        if actions:
            response_time, passed = self.calculate_response_time_score(actions)
            response_score = max(0, 10 - (response_time / 300))  # Scale response time to 0-10
            metrics['response_time'] = {
                'value': response_time,
                'passed': passed,
                'weight': 0.10,
                'description': f'Average response time: {response_time:.0f}ms'
            }
            scores.append(response_score)
        
        # Tool visibility accuracy
        tool_timeline = browser_data.get('tool_visibility_timeline', [])
        if tool_timeline:
            tool_accuracy, passed = self.calculate_tool_visibility_accuracy(tool_timeline)
            accuracy_score = 10.0 if tool_accuracy else 0.0
            metrics['tool_visibility_accuracy'] = {
                'value': tool_accuracy,
                'passed': passed,
                'weight': 0.10,
                'description': f'Tool visibility accuracy: {"PASS" if tool_accuracy else "FAIL"}'
            }
            scores.append(accuracy_score)
        
        # Session stability
        errors = base_data.get('errors', [])
        if actions:
            stability_score, passed = self.calculate_session_stability(actions, errors)
            metrics['session_stability'] = {
                'value': stability_score,
                'passed': passed,
                'weight': 0.10,
                'description': f'Session stability: {stability_score:.1f}/10'
            }
            scores.append(stability_score)
        
        # Calculate weighted overall score
        if scores:
            overall_score = statistics.mean(scores)
        else:
            overall_score = 0.0
        
        return overall_score, metrics
    
    def get_quality_assessment(self, score: float) -> Dict[str, Any]:
        """Get quality assessment based on score."""
        if score >= 9.0:
            return {
                'grade': 'A+',
                'description': 'Excellent',
                'color': '#059669',
                'recommendation': 'Test performance is outstanding. Ready for production.'
            }
        elif score >= 8.0:
            return {
                'grade': 'A',
                'description': 'Very Good',
                'color': '#0ea5e9',
                'recommendation': 'Test performance is very good with minor improvements possible.'
            }
        elif score >= 7.0:
            return {
                'grade': 'B',
                'description': 'Good',
                'color': '#f59e0b',
                'recommendation': 'Test performance is acceptable but could be improved.'
            }
        elif score >= 6.0:
            return {
                'grade': 'C',
                'description': 'Fair',
                'color': '#f97316',
                'recommendation': 'Test performance needs improvement before production.'
            }
        elif score >= 5.0:
            return {
                'grade': 'D',
                'description': 'Poor',
                'color': '#ef4444',
                'recommendation': 'Test performance is poor and requires significant improvement.'
            }
        else:
            return {
                'grade': 'F',
                'description': 'Failed',
                'color': '#dc2626',
                'recommendation': 'Test failed quality standards and needs major fixes.'
            }
    
    def generate_quality_report(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive quality report for a test."""
        overall_score, metrics = self.calculate_overall_quality_score(test_data)
        assessment = self.get_quality_assessment(overall_score)
        
        # Calculate pass/fail counts
        total_metrics = len(metrics)
        passed_metrics = sum(1 for m in metrics.values() if m['passed'])
        
        return {
            'overall_score': overall_score,
            'assessment': assessment,
            'metrics': metrics,
            'summary': {
                'total_metrics': total_metrics,
                'passed_metrics': passed_metrics,
                'failed_metrics': total_metrics - passed_metrics,
                'pass_rate': (passed_metrics / total_metrics * 100) if total_metrics > 0 else 0
            },
            'timestamp': datetime.now().isoformat(),
            'thresholds': self.MCPLAYWRIGHT_THRESHOLDS
        }
    
    def compare_quality_scores(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare quality scores across multiple test runs."""
        if not test_results:
            return {}
        
        scores = [r.get('overall_quality_score', 0) for r in test_results]
        
        return {
            'count': len(scores),
            'average': statistics.mean(scores),
            'median': statistics.median(scores),
            'min': min(scores),
            'max': max(scores),
            'std_dev': statistics.stdev(scores) if len(scores) > 1 else 0,
            'trend': self._calculate_trend(scores),
            'consistency': 'High' if (statistics.stdev(scores) if len(scores) > 1 else 0) < 1.0 else 'Low'
        }
    
    def _calculate_trend(self, scores: List[float]) -> str:
        """Calculate trend direction in quality scores."""
        if len(scores) < 2:
            return 'N/A'
        
        # Simple linear trend calculation
        n = len(scores)
        x_sum = sum(range(n))
        y_sum = sum(scores)
        xy_sum = sum(i * score for i, score in enumerate(scores))
        x2_sum = sum(i * i for i in range(n))
        
        slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
        
        if slope > 0.1:
            return 'Improving'
        elif slope < -0.1:
            return 'Declining'
        else:
            return 'Stable'