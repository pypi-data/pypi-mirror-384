#!/usr/bin/env python3
"""
Base Reporter - Abstract interface for all test reporters.

Defines the core interface that all test reporters must implement.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
import time


class BaseReporter(ABC):
    """
    Abstract base class for test reporters.
    
    Provides common functionality and defines the interface
    that all concrete reporters must implement.
    """
    
    def __init__(self, test_name: str):
        """Initialize base reporter with test name."""
        self.test_name = test_name
        self.start_time = time.time()
        self.errors = []
        
        # Core data structure
        self.data = {
            "inputs": {},
            "processing_steps": [],
            "outputs": {},
            "quality_metrics": {},
            "assertions": [],
            "errors": []
        }
    
    def log_input(self, name: str, value: Any, description: Optional[str] = None) -> None:
        """Log test input with description."""
        self.data["inputs"][name] = {
            "value": value,
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "type": type(value).__name__
        }
    
    def log_output(self, name: str, value: Any, description: Optional[str] = None, 
                   quality_score: Optional[float] = None) -> None:
        """Log test output with optional quality assessment."""
        self.data["outputs"][name] = {
            "value": value,
            "description": description,
            "quality_score": quality_score,
            "timestamp": datetime.now().isoformat(),
            "type": type(value).__name__
        }
    
    def log_processing_step(self, step_name: str, details: Any, 
                          duration: Optional[float] = None) -> None:
        """Log a processing step with timing."""
        step = {
            "name": step_name,
            "details": details,
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        }
        self.data["processing_steps"].append(step)
    
    def log_quality_metric(self, name: str, value: float, threshold: float, 
                          passed: bool) -> None:
        """Track quality metrics with pass/fail status."""
        self.data["quality_metrics"][name] = {
            "value": value,
            "threshold": threshold,
            "passed": passed,
            "timestamp": datetime.now().isoformat()
        }
    
    def log_assertion(self, description: str, expected: Any, actual: Any, 
                     passed: bool) -> None:
        """Log test assertion with comparison."""
        assertion = {
            "description": description,
            "expected": expected,
            "actual": actual,
            "passed": passed,
            "timestamp": datetime.now().isoformat()
        }
        self.data["assertions"].append(assertion)
    
    def log_error(self, error: Exception, context: Optional[str] = None) -> None:
        """Log an error that occurred during testing."""
        error_entry = {
            "type": type(error).__name__,
            "message": str(error),
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        self.data["errors"].append(error_entry)
        self.errors.append(error)
    
    @abstractmethod
    async def finalize(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate final test report.
        
        Must be implemented by concrete reporter classes.
        """
        pass
    
    def _calculate_overall_status(self) -> bool:
        """Calculate overall test pass/fail status."""
        # Check quality metrics
        quality_passed = all(
            m["passed"] for m in self.data["quality_metrics"].values()
        )
        
        # Check assertions
        assertions_passed = all(
            a["passed"] for a in self.data["assertions"]
        )
        
        # Check for errors
        has_errors = len(self.errors) > 0
        
        return quality_passed and assertions_passed and not has_errors
    
    def _get_test_duration(self) -> float:
        """Calculate test execution duration."""
        return time.time() - self.start_time
    
    def _get_summary_stats(self) -> Dict[str, int]:
        """Get summary statistics for the test."""
        return {
            "inputs_count": len(self.data["inputs"]),
            "outputs_count": len(self.data["outputs"]),
            "processing_steps": len(self.data["processing_steps"]),
            "quality_metrics_count": len(self.data["quality_metrics"]),
            "quality_metrics_passed": sum(
                1 for m in self.data["quality_metrics"].values() if m["passed"]
            ),
            "assertions_count": len(self.data["assertions"]),
            "assertions_passed": sum(
                1 for a in self.data["assertions"] if a["passed"]
            ),
            "errors_count": len(self.data["errors"])
        }