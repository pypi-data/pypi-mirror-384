"""
MCPlaywright Professional Test Reporting Framework

A comprehensive testing framework specifically designed for browser automation
testing with beautiful HTML reports, video analysis, and network monitoring.
"""

from .reporters.test_reporter import TestReporter
from .reporters.browser_reporter import BrowserTestReporter
from .utilities.syntax_highlighter import SyntaxHighlighter
from .utilities.quality_metrics import QualityMetrics
from .fixtures.browser_fixtures import BrowserFixtures
from .fixtures.video_fixtures import VideoFixtures
from .fixtures.network_fixtures import NetworkFixtures

__version__ = "1.0.0"
__author__ = "MCPlaywright Team"

__all__ = [
    "TestReporter",
    "BrowserTestReporter", 
    "SyntaxHighlighter",
    "QualityMetrics",
    "BrowserFixtures",
    "VideoFixtures",
    "NetworkFixtures"
]