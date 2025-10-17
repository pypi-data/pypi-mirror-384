#!/usr/bin/env python3
"""
Test Dashboard for MCPlaywright Testing Framework.

Web dashboard for visualizing test results, trends, and analytics from
the MCPlaywright browser automation testing framework.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from utilities.syntax_highlighter import SyntaxHighlighter
from .report_registry import ReportRegistry


class TestDashboard:
    """
    Web dashboard for MCPlaywright test analytics and visualization.
    
    Provides:
    - Real-time test status overview
    - Historical trends and analytics
    - Quality metrics visualization
    - Failure analysis and insights
    - Interactive test report browsing
    """
    
    def __init__(self, registry: ReportRegistry):
        self.registry = registry
        self.highlighter = SyntaxHighlighter()
    
    def generate_dashboard_html(self, 
                              days_back: int = 7,
                              include_failure_analysis: bool = True) -> str:
        """Generate complete HTML dashboard for test analytics."""
        
        # Get analytics data
        analytics = self.registry.get_test_analytics(days_back)
        failure_analysis = None
        
        if include_failure_analysis:
            failure_analysis = self.registry.get_failing_tests_analysis(days_back)
        
        # Get recent test reports
        recent_reports = self.registry.search_reports(days_back=days_back, limit=10)
        
        # Generate timestamp for report links
        from datetime import datetime
        current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCPlaywright Test Dashboard</title>
    <style>
        {self._get_dashboard_css()}
        {self.highlighter.get_highlighting_css()}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="dashboard-container">
        <!-- Header -->
        <header class="dashboard-header">
            <div class="header-content">
                <h1>🎭 MCPlaywright Test Dashboard</h1>
                <div class="header-stats">
                    <span class="stat-badge">Last {days_back} days</span>
                    <span class="timestamp">Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
                </div>
            </div>
        </header>

        <!-- Main Content -->
        <main class="dashboard-main">
            <!-- Overview Cards -->
            <section class="overview-section">
                <h2>📊 Test Overview</h2>
                <div class="stats-grid">
                    {self._generate_overview_cards(analytics)}
                </div>
            </section>

            <!-- Charts Section -->
            <section class="charts-section">
                <div class="charts-grid">
                    <div class="chart-card">
                        <h3>📈 Daily Test Trend</h3>
                        <canvas id="dailyTrendChart" width="400" height="200"></canvas>
                    </div>
                    <div class="chart-card">
                        <h3>🎯 Quality Score Distribution</h3>
                        <canvas id="qualityScoreChart" width="400" height="200"></canvas>
                    </div>
                </div>
            </section>

            <!-- Test Types Breakdown -->
            <section class="test-types-section">
                <h2>🔧 Test Types Breakdown</h2>
                <div class="test-types-grid">
                    {self._generate_test_types_cards(analytics['test_type_breakdown'])}
                </div>
            </section>

            <!-- Quality Metrics Analysis -->
            <section class="quality-metrics-section">
                <h2>🎯 Quality Metrics Analysis</h2>
                <div class="metrics-table-container">
                    {self._generate_quality_metrics_table(analytics['quality_metrics_analysis'])}
                </div>
            </section>

            {self._generate_failure_analysis_section(failure_analysis) if failure_analysis else ''}

            <!-- Recent Test Reports -->
            <section class="recent-reports-section">
                <h2>📋 Recent Test Reports</h2>
                <div class="reports-table-container">
                    {self._generate_recent_reports_table(recent_reports)}
                </div>
            </section>
        </main>

        <!-- Footer -->
        <footer class="dashboard-footer">
            <p>MCPlaywright Testing Framework - Generated at {datetime.now().isoformat()}</p>
        </footer>
    </div>

    <script>
        {self._generate_dashboard_javascript(analytics, current_timestamp)}
    </script>
</body>
</html>
        """
    
    def _generate_overview_cards(self, analytics: Dict[str, Any]) -> str:
        """Generate overview statistics cards."""
        stats = analytics['overall_stats']
        
        success_rate = stats['success_rate']
        success_color = '#10b981' if success_rate >= 95 else '#f59e0b' if success_rate >= 80 else '#ef4444'
        
        quality_score = stats['avg_quality_score']
        quality_color = '#10b981' if quality_score >= 8 else '#f59e0b' if quality_score >= 6 else '#ef4444'
        
        return f"""
        <div class="stat-card">
            <div class="stat-icon">📊</div>
            <div class="stat-content">
                <h3>Total Tests</h3>
                <div class="stat-value">{stats['total_tests']}</div>
            </div>
        </div>
        
        <div class="stat-card">
            <div class="stat-icon">✅</div>
            <div class="stat-content">
                <h3>Success Rate</h3>
                <div class="stat-value" style="color: {success_color}">
                    {success_rate:.1f}%
                </div>
            </div>
        </div>
        
        <div class="stat-card">
            <div class="stat-icon">🎯</div>
            <div class="stat-content">
                <h3>Avg Quality Score</h3>
                <div class="stat-value" style="color: {quality_color}">
                    {quality_score:.1f}/10
                </div>
            </div>
        </div>
        
        <div class="stat-card">
            <div class="stat-icon">⏱️</div>
            <div class="stat-content">
                <h3>Avg Duration</h3>
                <div class="stat-value">{stats['avg_duration']:.1f}s</div>
            </div>
        </div>
        """
    
    def _generate_test_types_cards(self, test_types: List[Dict[str, Any]]) -> str:
        """Generate test type breakdown cards."""
        if not test_types:
            return '<div class="no-data">No test type data available</div>'
        
        cards = []
        for test_type in test_types:
            success_rate = test_type['success_rate'] or 0
            success_color = '#10b981' if success_rate >= 95 else '#f59e0b' if success_rate >= 80 else '#ef4444'
            
            cards.append(f"""
            <div class="test-type-card">
                <h4>{test_type['test_type'].replace('_', ' ').title()}</h4>
                <div class="test-type-stats">
                    <div class="test-type-stat">
                        <span class="label">Tests:</span>
                        <span class="value">{test_type['count']}</span>
                    </div>
                    <div class="test-type-stat">
                        <span class="label">Success Rate:</span>
                        <span class="value" style="color: {success_color}">
                            {success_rate:.1f}%
                        </span>
                    </div>
                    <div class="test-type-stat">
                        <span class="label">Avg Quality:</span>
                        <span class="value">{test_type['avg_quality'] or 0:.1f}/10</span>
                    </div>
                </div>
            </div>
            """)
        
        return ''.join(cards)
    
    def _generate_quality_metrics_table(self, metrics: List[Dict[str, Any]]) -> str:
        """Generate quality metrics analysis table."""
        if not metrics:
            return '<div class="no-data">No quality metrics data available</div>'
        
        rows = []
        for metric in metrics:
            pass_rate = metric['pass_rate'] or 0
            pass_color = '#10b981' if pass_rate >= 90 else '#f59e0b' if pass_rate >= 70 else '#ef4444'
            
            rows.append(f"""
            <tr>
                <td>{metric['metric_name'].replace('_', ' ').title()}</td>
                <td class="text-center">{metric['metric_count']}</td>
                <td class="text-center">{metric['avg_value']:.2f}</td>
                <td class="text-center" style="color: {pass_color}; font-weight: 600;">
                    {pass_rate:.1f}%
                </td>
            </tr>
            """)
        
        return f"""
        <table class="metrics-table">
            <thead>
                <tr>
                    <th>Metric</th>
                    <th>Tests</th>
                    <th>Avg Value</th>
                    <th>Pass Rate</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
        """
    
    def _generate_failure_analysis_section(self, failure_analysis: Dict[str, Any]) -> str:
        """Generate failure analysis section."""
        if not failure_analysis or failure_analysis['total_failing_tests'] == 0:
            return """
            <section class="failure-analysis-section">
                <h2>🎉 No Recent Failures</h2>
                <div class="success-message">
                    <p>Excellent! No test failures in the analyzed period.</p>
                </div>
            </section>
            """
        
        failing_tests = failure_analysis['recent_failing_tests'][:5]  # Show top 5
        failing_metrics = failure_analysis['most_common_failing_metrics'][:5]
        failing_actions = failure_analysis['most_common_failing_actions'][:5]
        
        return f"""
        <section class="failure-analysis-section">
            <h2>🔍 Failure Analysis</h2>
            <div class="failure-stats">
                <div class="failure-stat">
                    <strong>{failure_analysis['total_failing_tests']}</strong> failing tests found
                </div>
            </div>
            
            <div class="failure-grid">
                <div class="failure-card">
                    <h3>❌ Recent Failing Tests</h3>
                    <div class="failing-tests-list">
                        {self._format_failing_tests(failing_tests)}
                    </div>
                </div>
                
                <div class="failure-card">
                    <h3>📊 Most Common Failing Metrics</h3>
                    <div class="failing-metrics-list">
                        {self._format_failing_metrics(failing_metrics)}
                    </div>
                </div>
                
                {f'''
                <div class="failure-card">
                    <h3>🔧 Most Common Failing Actions</h3>
                    <div class="failing-actions-list">
                        {self._format_failing_actions(failing_actions)}
                    </div>
                </div>
                ''' if failing_actions else ''}
            </div>
        </section>
        """
    
    def _format_failing_tests(self, failing_tests: List[Dict[str, Any]]) -> str:
        """Format failing tests for display."""
        if not failing_tests:
            return '<p class="no-data">No recent failing tests</p>'
        
        items = []
        for test in failing_tests:
            timestamp = datetime.fromisoformat(test['timestamp']).strftime('%m/%d %H:%M')
            items.append(f"""
            <div class="failing-test-item">
                <span class="test-name">{test['test_name']}</span>
                <span class="test-type">{test['test_type']}</span>
                <span class="test-time">{timestamp}</span>
                <span class="quality-score">Q: {test['quality_score']:.1f}</span>
            </div>
            """)
        
        return ''.join(items)
    
    def _format_failing_metrics(self, failing_metrics: List[Dict[str, Any]]) -> str:
        """Format failing metrics for display."""
        if not failing_metrics:
            return '<p class="no-data">No failing metrics data</p>'
        
        items = []
        for metric in failing_metrics:
            items.append(f"""
            <div class="failing-metric-item">
                <span class="metric-name">{metric['metric_name'].replace('_', ' ').title()}</span>
                <span class="failure-count">{metric['failure_count']} failures</span>
                <span class="avg-value">Avg: {metric['avg_failing_value']:.2f}</span>
            </div>
            """)
        
        return ''.join(items)
    
    def _format_failing_actions(self, failing_actions: List[Dict[str, Any]]) -> str:
        """Format failing actions for display."""
        if not failing_actions:
            return '<p class="no-data">No failing actions data</p>'
        
        items = []
        for action in failing_actions:
            items.append(f"""
            <div class="failing-action-item">
                <span class="action-type">{action['action_type']}</span>
                <span class="failure-count">{action['failure_count']} failures</span>
                <span class="avg-duration">Avg: {action['avg_duration']:.0f}ms</span>
            </div>
            """)
        
        return ''.join(items)
    
    def _generate_recent_reports_table(self, reports: List) -> str:
        """Generate recent test reports table."""
        if not reports:
            return '<div class="no-data">No recent test reports available</div>'
        
        rows = []
        for report in reports:
            status_icon = '✅' if report.success else '❌'
            status_class = 'success' if report.success else 'failure'
            timestamp = datetime.fromisoformat(report.timestamp).strftime('%m/%d %H:%M')
            
            quality_color = '#10b981' if report.quality_score >= 8 else '#f59e0b' if report.quality_score >= 6 else '#ef4444'
            
            # Extract actual test name from report_id or file_path if test_name is generic
            display_name = report.test_name
            if report.test_name == "Unknown Test" or not report.test_name:
                # Try to extract name from report_id or file_path
                if hasattr(report, 'report_id') and report.report_id:
                    display_name = report.report_id.replace('_', ' ').title()
                elif hasattr(report, 'file_path') and report.file_path:
                    # Extract filename without extension
                    import os
                    filename = os.path.basename(report.file_path)
                    display_name = filename.replace('.html', '').replace('_', ' ').title()
                else:
                    display_name = f"Test Report {len(rows) + 1}"
            
            rows.append(f"""
            <tr class="report-row {status_class}">
                <td>
                    <span class="status-icon">{status_icon}</span>
                    <span class="test-name">{display_name}</span>
                </td>
                <td>{report.test_type.replace('_', ' ').title()}</td>
                <td>{timestamp}</td>
                <td>{report.duration:.1f}s</td>
                <td style="color: {quality_color}; font-weight: 600;">
                    {report.quality_score:.1f}/10
                </td>
                <td>
                    <button class="view-report-btn" onclick="viewReport('{report.report_id}')">
                        View Report
                    </button>
                </td>
            </tr>
            """)
        
        return f"""
        <table class="reports-table">
            <thead>
                <tr>
                    <th>Test Name</th>
                    <th>Type</th>
                    <th>Time</th>
                    <th>Duration</th>
                    <th>Quality</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
        """
    
    def _generate_dashboard_javascript(self, analytics: Dict[str, Any], timestamp: str) -> str:
        """Generate JavaScript for dashboard interactivity."""
        daily_trend = analytics.get('daily_trend', [])
        
        # Prepare chart data
        daily_dates = [item['test_date'] for item in daily_trend[-7:]]  # Last 7 days
        daily_counts = [item['daily_count'] for item in daily_trend[-7:]]
        daily_quality = [item['daily_avg_quality'] or 0 for item in daily_trend[-7:]]
        
        return f"""
        // Daily Trend Chart
        const dailyTrendCtx = document.getElementById('dailyTrendChart').getContext('2d');
        new Chart(dailyTrendCtx, {{
            type: 'line',
            data: {{
                labels: {json.dumps(daily_dates)},
                datasets: [{{
                    label: 'Test Count',
                    data: {json.dumps(daily_counts)},
                    borderColor: '#0ea5e9',
                    backgroundColor: 'rgba(14, 165, 233, 0.1)',
                    tension: 0.4
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true
                    }}
                }}
            }}
        }});

        // Quality Score Chart
        const qualityScoreCtx = document.getElementById('qualityScoreChart').getContext('2d');
        new Chart(qualityScoreCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(daily_dates)},
                datasets: [{{
                    label: 'Quality Score',
                    data: {json.dumps(daily_quality)},
                    backgroundColor: 'rgba(34, 197, 94, 0.8)',
                    borderColor: '#22c55e',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 10
                    }}
                }}
            }}
        }});

        // View report function - Fixed with actual file patterns
        function viewReport(reportId) {{
            console.log('Attempting to open report:', reportId);
            
            // Map report IDs to their actual long filename patterns
            const reportPatterns = {{
                'error_handling_recovery': 'error_handling_recovery_test_mcplaywright_error_handling_recovery_test_',
                'performance_benchmark': 'performance_benchmark_test_mcplaywright_performance_benchmark_test_',
                'multi_browser_compatibility': 'multi_browser_compatibility_test_mcplaywright_multi_browser_compatibility_test_',
                'session_lifecycle': 'session_lifecycle_test_mcplaywright_session_lifecycle_test_',
                'dynamic_tool_visibility': 'dynamic_tool_visibility_test_mcplaywright_dynamic_tool_visibility_test_'
            }};
            
            // Generate possible filenames with recent timestamps
            const timestamps = ['20250909_045540', '20250909_045139', '20250909_032302', '20250909_031929', '20250909_020147'];
            const possibleFilenames = [];
            
            // Try the exact pattern if we know it
            if (reportPatterns[reportId]) {{
                for (const timestamp of timestamps) {{
                    possibleFilenames.push(reportPatterns[reportId] + timestamp + '.html');
                }}
            }}
            
            // Also try simpler patterns
            possibleFilenames.push(
                reportId + '.html',
                reportId + '_test.html',
                reportId + '_20250909_045540.html'
            );
            
            console.log('Trying filenames:', possibleFilenames);
            
            // Try to open using full file:// URLs
            let success = false;
            const basePath = 'file:///home/rpm/claude/mcplaywright/testing_framework/reports/';
            
            for (const filename of possibleFilenames) {{
                try {{
                    const fullPath = basePath + filename;
                    console.log('Attempting to open:', fullPath);
                    window.open(fullPath, '_blank');
                    success = true;
                    break;
                }} catch (error) {{
                    console.log('Failed to open:', filename, error);
                }}
            }}
            
            if (!success) {{
                // Provide helpful information about available files
                const helpMessage = `Report file not found: ${{reportId}}

Available options:
1. Check for files matching these patterns in the reports directory:
   - ${{reportId}}_test_mcplaywright_${{reportId}}_test_YYYYMMDD_HHMMSS.html
   
2. Or manually browse to:
   file:///home/rpm/claude/mcplaywright/testing_framework/reports/
   
3. Look for files containing "${{reportId}}" in the filename`;
                
                alert(helpMessage);
                console.error('All attempts to open report failed:', reportId);
                console.error('Tried filenames:', possibleFilenames);
            }}
        }}
        
        // Auto-refresh dashboard every 5 minutes
        setTimeout(() => {{
            location.reload();
        }}, 300000);
        """
    
    def _get_dashboard_css(self) -> str:
        """Get CSS styles for the dashboard - Awesome Neovim Gruvbox Theme."""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', 'source-code-pro', monospace;
            background: #282828;
            color: #ebdbb2;
            line-height: 1.4;
            min-height: 100vh;
            margin: 0;
            padding: 0.5rem;
        }

        .dashboard-container {
            max-width: 1100px;
            margin: 0 auto;
            padding: 0;
        }

        /* Header - Neovim Style */
        .dashboard-header {
            background: #3c3836;
            border: 1px solid #504945;
            border-radius: 0;
            padding: 1.5rem;
            margin-bottom: 0.5rem;
            text-align: left;
            position: relative;
        }
        
        .dashboard-header::before {
            content: '# MCPlaywright Test Dashboard';
            position: absolute;
            top: 0.5rem;
            right: 1rem;
            font-size: 0.7rem;
            color: #928374;
            font-style: normal;
        }

        .header-content {
            max-width: none;
            margin: 0;
            padding: 0;
            display: block;
        }

        .dashboard-header h1 {
            color: #83a598;
            font-size: 2rem;
            font-weight: bold;
            margin: 0 0 0.25rem 0;
            font-family: inherit;
        }

        .header-stats {
            display: flex;
            gap: 15px;
            align-items: center;
        }

        .stat-badge {
            background: rgba(255, 255, 255, 0.2);
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.9rem;
        }

        .timestamp {
            font-size: 0.9rem;
            opacity: 0.9;
        }

        /* Main Content */
        .dashboard-main {
            flex: 1;
            max-width: 1200px;
            margin: 0 auto;
            padding: 30px 20px;
            width: 100%;
        }

        section {
            margin-bottom: 40px;
        }

        section h2 {
            font-size: 1.5rem;
            margin-bottom: 20px;
            color: #1e293b;
        }

        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            display: flex;
            align-items: center;
            gap: 15px;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .stat-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }

        .stat-icon {
            font-size: 2rem;
        }

        .stat-content h3 {
            color: #64748b;
            font-size: 0.9rem;
            font-weight: 500;
            margin-bottom: 5px;
        }

        .stat-value {
            font-size: 1.8rem;
            font-weight: 700;
            color: #1e293b;
        }

        /* Charts */
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .chart-card {
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .chart-card h3 {
            margin-bottom: 20px;
            color: #1e293b;
        }

        /* Test Types */
        .test-types-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
        }

        .test-type-card {
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .test-type-card h4 {
            color: #1e293b;
            margin-bottom: 15px;
            font-size: 1.1rem;
        }

        .test-type-stats {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .test-type-stat {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .test-type-stat .label {
            color: #64748b;
            font-size: 0.9rem;
        }

        .test-type-stat .value {
            font-weight: 600;
        }

        /* Tables */
        .metrics-table-container,
        .reports-table-container {
            background: white;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }

        .metrics-table,
        .reports-table {
            width: 100%;
            border-collapse: collapse;
        }

        .metrics-table th,
        .reports-table th {
            background: #f8fafc;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            color: #374151;
            border-bottom: 1px solid #e5e7eb;
        }

        .metrics-table td,
        .reports-table td {
            padding: 12px 15px;
            border-bottom: 1px solid #f3f4f6;
        }

        .metrics-table tr:hover,
        .reports-table tr:hover {
            background: #f8fafc;
        }

        .text-center {
            text-align: center;
        }

        /* Failure Analysis */
        .failure-analysis-section {
            background: #fef2f2;
            border: 1px solid #fecaca;
            border-radius: 12px;
            padding: 25px;
        }

        .success-message {
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            color: #166534;
        }

        .failure-stats {
            margin-bottom: 20px;
            padding: 15px;
            background: rgba(239, 68, 68, 0.1);
            border-radius: 8px;
        }

        .failure-stat {
            color: #dc2626;
            font-size: 1.1rem;
        }

        .failure-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }

        .failure-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #dc2626;
        }

        .failure-card h3 {
            color: #dc2626;
            margin-bottom: 15px;
            font-size: 1rem;
        }

        .failing-test-item,
        .failing-metric-item,
        .failing-action-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid #f3f4f6;
            font-size: 0.9rem;
        }

        /* Reports Table */
        .report-row.success {
            border-left: 4px solid #10b981;
        }

        .report-row.failure {
            border-left: 4px solid #ef4444;
        }

        .status-icon {
            margin-right: 8px;
        }

        .test-name {
            font-weight: 600;
        }

        .view-report-btn {
            background: #0ea5e9;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.8rem;
            transition: background 0.2s;
        }

        .view-report-btn:hover {
            background: #0284c7;
        }

        /* Footer */
        .dashboard-footer {
            background: #1e293b;
            color: #94a3b8;
            padding: 20px;
            text-align: center;
            margin-top: auto;
        }

        /* Utilities */
        .no-data {
            color: #64748b;
            font-style: italic;
            text-align: center;
            padding: 20px;
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .header-content {
                flex-direction: column;
                gap: 15px;
                text-align: center;
            }

            .dashboard-header h1 {
                font-size: 1.5rem;
            }

            .charts-grid {
                grid-template-columns: 1fr;
            }

            .chart-card {
                min-width: 0;
            }

            .dashboard-main {
                padding: 20px 15px;
            }
        }
        """
    
    def save_dashboard(self, output_path: str, days_back: int = 7) -> bool:
        """Save the dashboard HTML to a file."""
        try:
            html_content = self.generate_dashboard_html(days_back)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return True
        except Exception as e:
            print(f"Error saving dashboard: {e}")
            return False