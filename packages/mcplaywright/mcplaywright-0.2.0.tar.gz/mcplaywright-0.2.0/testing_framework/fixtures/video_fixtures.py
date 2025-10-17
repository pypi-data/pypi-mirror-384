#!/usr/bin/env python3
"""
Video Recording Test Fixtures for MCPlaywright Testing Framework.

Provides test scenarios and mock data for smart video recording features
including viewport matching, recording modes, and quality assessment.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta


class VideoFixtures:
    """
    Test fixtures for video recording scenarios.
    
    Provides realistic test data for:
    - Smart video recording with auto pause/resume
    - Viewport matching and recording optimization
    - Multiple recording modes (smart, continuous, action-only, segment)
    - Video quality assessment and validation
    """
    
    @staticmethod
    def smart_recording_config() -> Dict[str, Any]:
        """Configuration for smart video recording test."""
        return {
            "name": "Smart Recording Test Configuration",
            "mode": "smart",
            "auto_set_viewport": True,
            "size": {
                "width": 1280,
                "height": 720
            },
            "filename": "smart_recording_demo.webm",
            "expected_features": [
                "auto_pause_on_wait",
                "auto_resume_on_action", 
                "viewport_matching",
                "intelligent_segmentation"
            ],
            "quality_settings": {
                "fps": 30,
                "bitrate": "2M",
                "codec": "vp9"
            },
            "test_scenarios": [
                {
                    "scenario": "navigation_with_wait",
                    "actions": [
                        {"action": "navigate", "url": "https://playwright.dev", "expected_recording": True},
                        {"action": "wait_for_element", "selector": ".hero", "timeout": 5000, "expected_recording": False},
                        {"action": "click", "selector": "text=Get started", "expected_recording": True}
                    ],
                    "expected_segments": 2,  # Navigate + click (wait should be paused)
                    "expected_duration_reduction": 30  # 30% reduction due to pausing
                }
            ]
        }
    
    @staticmethod
    def continuous_recording_config() -> Dict[str, Any]:
        """Configuration for continuous video recording test."""
        return {
            "name": "Continuous Recording Test Configuration", 
            "mode": "continuous",
            "auto_set_viewport": False,
            "size": {
                "width": 1920,
                "height": 1080
            },
            "filename": "continuous_recording_test.webm",
            "expected_features": [
                "uninterrupted_recording",
                "fixed_viewport_size",
                "complete_session_capture"
            ],
            "test_scenarios": [
                {
                    "scenario": "complete_workflow",
                    "actions": [
                        {"action": "navigate", "url": "https://example.com"},
                        {"action": "wait_for_element", "selector": "h1", "timeout": 3000},
                        {"action": "click", "selector": "a[href='/about']"},
                        {"action": "wait_for_load_state", "state": "networkidle"}
                    ],
                    "expected_segments": 1,  # Single continuous recording
                    "expected_duration": "full"  # Records entire duration including waits
                }
            ]
        }
    
    @staticmethod
    def action_only_recording_config() -> Dict[str, Any]:
        """Configuration for action-only video recording test."""
        return {
            "name": "Action-Only Recording Test Configuration",
            "mode": "action-only", 
            "auto_set_viewport": True,
            "size": {
                "width": 1280,
                "height": 720
            },
            "filename": "actions_only_recording.webm",
            "expected_features": [
                "minimal_recording_time",
                "action_focused_segments",
                "automatic_start_stop"
            ],
            "test_scenarios": [
                {
                    "scenario": "isolated_actions",
                    "actions": [
                        {"action": "click", "selector": "button#submit", "record_duration": 2.0},
                        {"action": "type", "selector": "input", "text": "test", "record_duration": 1.5},
                        {"action": "screenshot", "name": "final_state", "record_duration": 0.5}
                    ],
                    "expected_segments": 3,  # One per action
                    "expected_total_duration": 4.0  # Sum of action durations
                }
            ]
        }
    
    @staticmethod
    def segment_recording_config() -> Dict[str, Any]:
        """Configuration for segmented video recording test."""
        return {
            "name": "Segmented Recording Test Configuration",
            "mode": "segment",
            "auto_set_viewport": True,
            "size": {
                "width": 1440,
                "height": 900
            },
            "filename_pattern": "segment_{index}_{timestamp}.webm",
            "expected_features": [
                "multiple_video_files",
                "logical_segmentation",
                "easy_editing_workflow"
            ],
            "segmentation_triggers": [
                "page_navigation",
                "significant_wait",
                "user_interaction_pause",
                "error_occurrence"
            ],
            "test_scenarios": [
                {
                    "scenario": "multi_page_workflow",
                    "actions": [
                        {"action": "navigate", "url": "https://playwright.dev", "segment": "intro"},
                        {"action": "click", "selector": "text=Docs", "segment": "docs_nav"},
                        {"action": "navigate", "url": "https://playwright.dev/docs/intro", "segment": "docs_page"},
                        {"action": "scroll", "position": "bottom", "segment": "docs_page"}
                    ],
                    "expected_segments": 3,  # intro, docs_nav, docs_page
                    "expected_files": 3
                }
            ]
        }
    
    @staticmethod
    def viewport_matching_scenario() -> Dict[str, Any]:
        """Test scenario for viewport matching functionality."""
        return {
            "name": "Viewport Matching Test",
            "description": "Test automatic viewport matching for video recording",
            "test_cases": [
                {
                    "case": "desktop_recording",
                    "initial_viewport": {"width": 1024, "height": 768},
                    "recording_size": {"width": 1280, "height": 720},
                    "auto_set_viewport": True,
                    "expected_final_viewport": {"width": 1280, "height": 720},
                    "expected_video_quality": 9.0  # Perfect match
                },
                {
                    "case": "mobile_recording",
                    "initial_viewport": {"width": 375, "height": 667},  # iPhone SE
                    "recording_size": {"width": 375, "height": 667},
                    "auto_set_viewport": True,
                    "expected_final_viewport": {"width": 375, "height": 667},
                    "expected_video_quality": 9.5  # Perfect mobile match
                },
                {
                    "case": "mismatched_recording",
                    "initial_viewport": {"width": 1920, "height": 1080},
                    "recording_size": {"width": 1280, "height": 720},
                    "auto_set_viewport": False,
                    "expected_final_viewport": {"width": 1920, "height": 1080},
                    "expected_video_quality": 6.5,  # Gray bars expected
                    "expected_issues": ["viewport_mismatch", "gray_borders"]
                }
            ],
            "validation_criteria": {
                "viewport_updated": "auto_set_viewport == True",
                "video_dimensions_correct": True,
                "no_gray_borders": "viewport_match == True", 
                "optimal_quality": "quality_score >= 8.0"
            }
        }
    
    @staticmethod
    def recording_quality_assessment() -> Dict[str, Any]:
        """Test scenario for video recording quality assessment."""
        return {
            "name": "Video Recording Quality Assessment",
            "description": "Assess video recording quality across different scenarios",
            "quality_factors": [
                {
                    "factor": "resolution_clarity",
                    "weight": 0.25,
                    "assessment_method": "pixel_density_analysis",
                    "thresholds": {
                        "excellent": 9.0,
                        "good": 7.0,
                        "acceptable": 5.0,
                        "poor": 3.0
                    }
                },
                {
                    "factor": "frame_consistency", 
                    "weight": 0.20,
                    "assessment_method": "frame_rate_stability",
                    "thresholds": {
                        "excellent": 9.0,  # <2% frame rate variation
                        "good": 7.0,       # <5% frame rate variation
                        "acceptable": 5.0, # <10% frame rate variation
                        "poor": 3.0        # >10% frame rate variation
                    }
                },
                {
                    "factor": "content_capture",
                    "weight": 0.20,
                    "assessment_method": "viewport_coverage",
                    "thresholds": {
                        "excellent": 9.0,  # 100% viewport captured
                        "good": 7.0,       # 95% viewport captured
                        "acceptable": 5.0, # 90% viewport captured  
                        "poor": 3.0        # <90% viewport captured
                    }
                },
                {
                    "factor": "timing_accuracy",
                    "weight": 0.15,
                    "assessment_method": "action_sync_analysis",
                    "thresholds": {
                        "excellent": 9.0,  # <100ms timing drift
                        "good": 7.0,       # <250ms timing drift
                        "acceptable": 5.0, # <500ms timing drift
                        "poor": 3.0        # >500ms timing drift
                    }
                },
                {
                    "factor": "file_efficiency",
                    "weight": 0.20,
                    "assessment_method": "size_per_duration",
                    "thresholds": {
                        "excellent": 9.0,  # <0.5MB per second
                        "good": 7.0,       # <1MB per second
                        "acceptable": 5.0, # <2MB per second
                        "poor": 3.0        # >2MB per second
                    }
                }
            ],
            "test_videos": [
                {
                    "scenario": "simple_navigation",
                    "duration": 10.0,
                    "expected_quality": 8.5,
                    "quality_factors": {
                        "resolution_clarity": 9.0,
                        "frame_consistency": 8.5,
                        "content_capture": 9.0,
                        "timing_accuracy": 8.0,
                        "file_efficiency": 8.0
                    }
                },
                {
                    "scenario": "complex_interaction",
                    "duration": 30.0,
                    "expected_quality": 7.8,
                    "quality_factors": {
                        "resolution_clarity": 8.5,
                        "frame_consistency": 7.5,
                        "content_capture": 8.0,
                        "timing_accuracy": 7.5,
                        "file_efficiency": 7.5
                    }
                }
            ]
        }
    
    @staticmethod
    def recording_performance_benchmarks() -> Dict[str, Any]:
        """Performance benchmarks for video recording."""
        return {
            "name": "Video Recording Performance Benchmarks",
            "description": "Performance benchmarks for different recording configurations",
            "benchmarks": [
                {
                    "configuration": "smart_720p",
                    "resolution": {"width": 1280, "height": 720},
                    "mode": "smart", 
                    "fps": 30,
                    "expected_metrics": {
                        "cpu_usage": 15.0,     # 15% max CPU usage
                        "memory_usage": 150.0, # 150MB max memory
                        "disk_write": 1.0,     # 1MB/s disk write
                        "startup_time": 2.0,   # 2 seconds to start recording
                        "stop_time": 1.0       # 1 second to stop and save
                    }
                },
                {
                    "configuration": "continuous_1080p",
                    "resolution": {"width": 1920, "height": 1080},
                    "mode": "continuous",
                    "fps": 60,
                    "expected_metrics": {
                        "cpu_usage": 25.0,     # 25% max CPU usage
                        "memory_usage": 300.0, # 300MB max memory
                        "disk_write": 4.0,     # 4MB/s disk write
                        "startup_time": 3.0,   # 3 seconds to start recording
                        "stop_time": 2.0       # 2 seconds to stop and save
                    }
                }
            ],
            "performance_thresholds": {
                "cpu_usage_max": 30.0,      # 30% CPU usage limit
                "memory_usage_max": 400.0,  # 400MB memory limit
                "disk_write_max": 5.0,      # 5MB/s write limit
                "startup_time_max": 5.0,    # 5 second startup limit
                "stop_time_max": 3.0        # 3 second stop limit
            }
        }
    
    @staticmethod
    def get_mock_video_recording() -> Dict[str, Any]:
        """Get mock video recording data for testing."""
        return {
            "name": "test_recording",
            "path": "videos/test_recording.webm",
            "duration": 15.5,
            "quality_score": 8.2,
            "timestamp": datetime.now().isoformat(),
            "exists": True,
            "size_mb": 7.8,
            "metadata": {
                "resolution": {"width": 1280, "height": 720},
                "fps": 30,
                "codec": "vp9",
                "bitrate": "2M"
            },
            "analysis": {
                "frame_count": 465,
                "avg_frame_rate": 30.0,
                "quality_factors": {
                    "resolution_clarity": 8.5,
                    "frame_consistency": 8.0,
                    "content_capture": 8.8,
                    "timing_accuracy": 7.8,
                    "file_efficiency": 8.1
                }
            }
        }
    
    @staticmethod
    def get_mock_video_segments() -> List[Dict[str, Any]]:
        """Get mock video segment data for testing."""
        base_time = datetime.now()
        return [
            {
                "name": "intro_navigation",
                "path": "videos/segment_1_intro.webm", 
                "duration": 5.2,
                "quality_score": 8.5,
                "timestamp": base_time.isoformat(),
                "exists": True,
                "size_mb": 2.1,
                "segment_type": "navigation"
            },
            {
                "name": "user_interaction",
                "path": "videos/segment_2_interaction.webm",
                "duration": 8.7,
                "quality_score": 8.0,
                "timestamp": (base_time + timedelta(seconds=6)).isoformat(),
                "exists": True,
                "size_mb": 3.8,
                "segment_type": "interaction"
            },
            {
                "name": "final_state",
                "path": "videos/segment_3_final.webm",
                "duration": 3.3,
                "quality_score": 8.8,
                "timestamp": (base_time + timedelta(seconds=15)).isoformat(),
                "exists": True,
                "size_mb": 1.4,
                "segment_type": "validation"
            }
        ]
    
    @staticmethod
    def get_video_quality_thresholds() -> Dict[str, float]:
        """Get video quality assessment thresholds."""
        return {
            "excellent_quality": 9.0,
            "good_quality": 7.5,
            "acceptable_quality": 6.0,
            "poor_quality": 4.0,
            "min_duration": 1.0,      # 1 second minimum
            "max_file_size_mb": 50.0, # 50MB maximum  
            "min_fps": 15.0,          # 15 FPS minimum
            "max_cpu_usage": 30.0,    # 30% CPU maximum
            "max_memory_mb": 400.0    # 400MB memory maximum
        }