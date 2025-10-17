#!/usr/bin/env python3
"""
MCPlaywright Test Index Generator

Creates a comprehensive index page showing test history, available reports,
and dashboard analytics for the MCPlaywright testing framework.
"""

import os
import re
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import json


class TestIndexGenerator:
    """Generate comprehensive test index and dashboard."""
    
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.reports_dir = self.base_path / "reports"
        self.registry_db = self.base_path / "mcplaywright_test_registry.db"
        
    def scan_report_files(self) -> List[Dict[str, Any]]:
        """Scan reports directory for HTML files."""
        reports = []
        
        if not self.reports_dir.exists():
            return reports
            
        for file_path in self.reports_dir.glob("*.html"):
            # Skip index.html - it shouldn't appear in the test results list
            filename = file_path.name
            if filename == "index.html":
                continue
                
            # Extract metadata from filename
            file_stats = file_path.stat()
            
            # Try to extract timestamp from filename
            timestamp_match = re.search(r'(\d{8}_\d{6})', filename)
            if timestamp_match:
                timestamp_str = timestamp_match.group(1)
                try:
                    timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                except ValueError:
                    timestamp = datetime.fromtimestamp(file_stats.st_mtime)
            else:
                timestamp = datetime.fromtimestamp(file_stats.st_mtime)
            
            # Determine test type from filename
            test_type = "unknown"
            if "dynamic_tool_visibility" in filename:
                test_type = "dynamic_tool_visibility"
            elif "session_lifecycle" in filename:
                test_type = "session_lifecycle"
            elif "multi_browser" in filename:
                test_type = "multi_browser_compatibility"
            elif "performance" in filename:
                test_type = "performance_benchmarks"
            elif "error_handling" in filename:
                test_type = "error_handling_recovery"
            elif "mcplaywright_test_report" in filename:
                test_type = "comprehensive_suite"
            
            reports.append({
                "file_path": str(file_path),
                "filename": filename,
                "test_type": test_type,
                "timestamp": timestamp.isoformat(),
                "file_size": file_stats.st_size,
                "last_modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                "source": "file_scan"
            })
        
        return sorted(reports, key=lambda x: x["timestamp"], reverse=True)
    
    def get_database_reports(self) -> List[Dict[str, Any]]:
        """Get reports from SQLite database."""
        reports = []
        
        if not self.registry_db.exists():
            return reports
        
        try:
            conn = sqlite3.connect(str(self.registry_db))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT report_id, test_name, test_type, timestamp, duration, 
                       success, quality_score, file_path, metadata_json
                FROM test_reports 
                ORDER BY timestamp DESC
            """)
            
            for row in cursor.fetchall():
                metadata = json.loads(row['metadata_json'] or '{}')
                reports.append({
                    "report_id": row['report_id'],
                    "test_name": row['test_name'],
                    "test_type": row['test_type'],
                    "timestamp": row['timestamp'],
                    "duration": row['duration'],
                    "success": bool(row['success']),
                    "quality_score": row['quality_score'] or 0.0,
                    "file_path": row['file_path'],
                    "metadata": metadata,
                    "source": "database"
                })
            
            conn.close()
        except Exception as e:
            print(f"Database error: {e}")
        
        return reports
    
    def get_test_analytics(self) -> Dict[str, Any]:
        """Generate analytics from available data."""
        file_reports = self.scan_report_files()
        db_reports = self.get_database_reports()
        
        # Combine reports
        all_reports = file_reports + db_reports
        total_reports = len(all_reports)
        
        if total_reports == 0:
            return {
                "total_reports": 0,
                "test_types": {},
                "recent_activity": [],
                "success_rate": 0,
                "avg_quality_score": 0
            }
        
        # Analyze test types
        test_types = {}
        successful_tests = 0
        total_quality_score = 0
        quality_count = 0
        
        for report in all_reports:
            test_type = report.get("test_type", "unknown")
            test_types[test_type] = test_types.get(test_type, 0) + 1
            
            if report.get("success", True):  # Default to True for file scans
                successful_tests += 1
            
            quality_score = report.get("quality_score", 0)
            if quality_score > 0:
                total_quality_score += quality_score
                quality_count += 1
        
        # Recent activity (last 7 days)
        recent_cutoff = datetime.now() - timedelta(days=7)
        recent_activity = []
        
        for report in all_reports:
            report_time = datetime.fromisoformat(report["timestamp"].replace('Z', '+00:00').replace('+00:00', ''))
            if report_time >= recent_cutoff:
                recent_activity.append({
                    "timestamp": report["timestamp"],
                    "test_type": report.get("test_type", "unknown"),
                    "success": report.get("success", True),
                    "filename": report.get("filename", report.get("test_name", "Unknown"))
                })
        
        return {
            "total_reports": total_reports,
            "test_types": test_types,
            "recent_activity": sorted(recent_activity, key=lambda x: x["timestamp"], reverse=True),
            "success_rate": (successful_tests / total_reports) * 100 if total_reports > 0 else 0,
            "avg_quality_score": total_quality_score / quality_count if quality_count > 0 else 0,
            "file_reports_count": len(file_reports),
            "database_reports_count": len(db_reports)
        }
    
    def generate_index_html(self) -> str:
        """Generate the main index HTML page."""
        file_reports = self.scan_report_files()
        db_reports = self.get_database_reports()
        analytics = self.get_test_analytics()
        
        # Generate report cards
        report_cards_html = ""
        
        # Database reports first (more detailed)
        if db_reports:
            report_cards_html += "<h3>📊 Database Reports (Detailed)</h3>\\n"
            for report in db_reports:
                success_icon = "✅" if report["success"] else "❌"
                success_class = "success" if report["success"] else "failure"
                
                report_cards_html += f"""
                <div class="report-card {success_class}">
                    <div class="report-header">
                        <h4>{success_icon} {report['test_name']}</h4>
                        <span class="test-type">{report['test_type']}</span>
                    </div>
                    <div class="report-meta">
                        <span class="timestamp">🕒 {report['timestamp'][:19].replace('T', ' ')}</span>
                        <span class="duration">⏱️ {report['duration']:.1f}s</span>
                        <span class="quality">⭐ {report['quality_score']:.1f}/10</span>
                    </div>
                    <div class="report-actions">
                        <a href="{report['file_path']}" class="btn btn-primary" target="_blank">View Report</a>
                        <span class="report-id">ID: {report['report_id']}</span>
                    </div>
                </div>
                """
        
        # File-based reports as datatable
        if file_reports:
            report_cards_html += "<h3>📁 File Reports</h3>\\n"
            report_cards_html += """
            <div class="datatable-container">
                <table class="file-reports-table">
                    <thead>
                        <tr>
                            <th>📄 File Name</th>
                            <th>🧪 Test Type</th>
                            <th>🕒 Created</th>
                            <th>📝 Modified</th>
                            <th>💾 Size</th>
                            <th>🔗 Actions</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            for report in file_reports:
                file_size_mb = report['file_size'] / (1024 * 1024)
                test_type_display = report['test_type'].replace('_', ' ').title()
                created_time = report['timestamp'][:19].replace('T', ' ')
                modified_time = report['last_modified'][:19].replace('T', ' ')
                
                report_cards_html += f"""
                        <tr>
                            <td>
                                <div class="file-name-cell">
                                    <span class="file-icon">📄</span>
                                    <span class="file-text">{report['filename']}</span>
                                </div>
                            </td>
                            <td>
                                <span class="test-type-badge">{test_type_display}</span>
                            </td>
                            <td class="timestamp-cell">{created_time}</td>
                            <td class="timestamp-cell">{modified_time}</td>
                            <td class="file-size-cell">{file_size_mb:.1f} MB</td>
                            <td>
                                <a href="{report['filename']}" class="btn btn-small btn-primary" target="_blank">
                                    👁️ View
                                </a>
                            </td>
                        </tr>
                """
            
            report_cards_html += """
                    </tbody>
                </table>
            </div>
            """
        
        # No reports message
        if not report_cards_html:
            report_cards_html = """
            <div class="no-reports">
                <h3>📭 No Reports Found</h3>
                <p>No test reports have been generated yet. Run some tests to see them here!</p>
                <div class="getting-started">
                    <h4>🚀 Get Started:</h4>
                    <ul>
                        <li>Run <code>python3 examples/test_dynamic_tool_visibility.py</code></li>
                        <li>Run <code>python3 run_all_tests.py</code></li>
                        <li>Check the <code>reports/</code> directory for generated HTML files</li>
                    </ul>
                </div>
            </div>
            """
        
        # Test type breakdown
        test_types_html = ""
        for test_type, count in analytics["test_types"].items():
            test_types_html += f"""
            <div class="test-type-item">
                <span class="test-type-name">{test_type.replace('_', ' ').title()}</span>
                <span class="test-type-count">{count}</span>
            </div>
            """
        
        # Recent activity
        recent_activity_html = ""
        for activity in analytics["recent_activity"][:10]:  # Show last 10
            activity_icon = "✅" if activity["success"] else "❌"
            activity_time = activity["timestamp"][:19].replace('T', ' ')
            
            recent_activity_html += f"""
            <div class="activity-item">
                <span class="activity-icon">{activity_icon}</span>
                <span class="activity-test">{activity['test_type'].replace('_', ' ')}</span>
                <span class="activity-time">{activity_time}</span>
            </div>
            """
        
        if not recent_activity_html:
            recent_activity_html = "<div class='no-activity'>No recent test activity</div>"
        
        # Generate HTML with terminal modal
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCPlaywright Test Dashboard</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', 'source-code-pro', monospace;
            background: #282828;
            color: #ebdbb2;
            line-height: 1.4;
            min-height: 100vh;
            margin: 0;
            padding: 0.5rem;
        }}
        
        .container {{
            max-width: 1100px;
            margin: 0 auto;
            padding: 0;
        }}
        
        .header {{
            background: #3c3836;
            border: 1px solid #504945;
            border-radius: 0;
            padding: 1.5rem;
            margin-bottom: 0.5rem;
            text-align: left;
            position: relative;
        }}
        
        .header::before {{
            content: '# MCPlaywright Test Dashboard';
            position: absolute;
            top: 0.5rem;
            right: 1rem;
            font-size: 0.7rem;
            color: #928374;
            font-style: normal;
        }}
        
        .header h1 {{
            color: #83a598;
            font-size: 2rem;
            font-weight: bold;
            margin: 0 0 0.25rem 0;
            font-family: inherit;
        }}
        
        .header .subtitle {{
            color: #d3869b;
            font-size: 0.9rem;
            margin-bottom: 0.25rem;
            font-weight: normal;
        }}
        
        .header .tagline {{
            color: #b8bb26;
            font-size: 0.8rem;
            font-weight: normal;
            margin-bottom: 0.75rem;
            font-style: normal;
        }}
        
        .header .info {{
            color: #928374;
            font-size: 0.7rem;
            font-family: inherit;
        }}
        
        .status-line {{
            background: #458588;
            color: #ebdbb2;
            padding: 0.25rem 1rem;
            font-size: 0.75rem;
            margin-bottom: 0.5rem;
            font-weight: normal;
            border-left: 2px solid #83a598;
        }}
        
        .command-line {{
            background: #1d2021;
            color: #ebdbb2;
            padding: 0.5rem 1rem;
            font-size: 0.8rem;
            margin-bottom: 0.5rem;
            border: 1px solid #504945;
        }}
        
        .command-line::before {{
            content: '❯ ';
            color: #fe8019;
            font-weight: bold;
        }}
        
        .dashboard-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 0.5rem;
            margin-bottom: 0.5rem;
        }}
        
        .dashboard-card {{
            background: #3c3836;
            border: 1px solid #504945;
            border-radius: 0;
            padding: 1rem;
            transition: border-color 0.2s;
        }}
        
        .dashboard-card:hover {{
            border-color: #83a598;
        }}
        
        .dashboard-card h3 {{
            color: #ebdbb2;
            margin-bottom: 0.5rem;
            font-size: 0.8rem;
            font-weight: normal;
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }}
        
        .stat-number {{
            font-size: 1.8rem;
            font-weight: bold;
            color: #fabd2f;
            display: block;
            line-height: 1;
        }}
        
        .stat-label {{
            color: #928374;
            font-size: 0.7rem;
            margin-top: 0.25rem;
        }}
        
        .reports-section {{
            background: #3c3836;
            border: 1px solid #504945;
            border-radius: 0;
            padding: 1rem;
        }}
        
        .reports-section h2 {{
            color: #ebdbb2;
            margin-bottom: 1rem;
            font-size: 1rem;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            border-bottom: 1px solid #504945;
            padding-bottom: 0.5rem;
        }}
        
        .report-card {{
            background: #f7fafc;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            border-left: 4px solid #667eea;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .report-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }}
        
        .report-card.success {{
            border-left-color: #48bb78;
        }}
        
        .report-card.failure {{
            border-left-color: #f56565;
        }}
        
        .report-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }}
        
        .report-header h4 {{
            color: #2d3748;
            font-size: 1.1rem;
        }}
        
        .test-type {{
            background: #e2e8f0;
            color: #4a5568;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
        }}
        
        .report-meta {{
            display: flex;
            gap: 1rem;
            margin-bottom: 1rem;
            font-size: 0.9rem;
            color: #718096;
        }}
        
        .report-actions {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .btn {{
            padding: 0.5rem 1rem;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 500;
            transition: background-color 0.2s;
            border: none;
            cursor: pointer;
            font-family: inherit;
            font-size: 0.9rem;
        }}
        
        .btn-primary {{
            background: #667eea;
            color: white;
        }}
        
        .btn-primary:hover {{
            background: #5a67d8;
        }}
        
        .btn-small {{
            padding: 0.25rem 0.5rem;
            font-size: 0.8rem;
        }}
        
        .report-id {{
            font-size: 0.8rem;
            color: #a0aec0;
            font-family: monospace;
        }}
        
        /* Datatable Styles */
        .datatable-container {{
            background: #f7fafc;
            border-radius: 12px;
            padding: 1rem;
            margin: 1rem 0;
            overflow-x: auto;
        }}
        
        .file-reports-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }}
        
        .file-reports-table th {{
            background: #e2e8f0;
            color: #2d3748;
            padding: 0.75rem;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #cbd5e0;
        }}
        
        .file-reports-table td {{
            padding: 0.75rem;
            border-bottom: 1px solid #e2e8f0;
            color: #2d3748;
        }}
        
        .file-reports-table tr:hover {{
            background: #f1f5f9;
        }}
        
        .file-name-cell {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .file-icon {{
            font-size: 1.2rem;
        }}
        
        .file-text {{
            font-family: monospace;
            font-size: 0.8rem;
            word-break: break-all;
        }}
        
        .test-type-badge {{
            background: #667eea;
            color: white;
            padding: 0.25rem 0.5rem;
            border-radius: 12px;
            font-size: 0.7rem;
            font-weight: 500;
            text-transform: uppercase;
        }}
        
        .timestamp-cell {{
            font-family: monospace;
            font-size: 0.8rem;
            color: #718096;
        }}
        
        .file-size-cell {{
            font-family: monospace;
            font-size: 0.8rem;
            color: #718096;
        }}
        
        /* Terminal Modal Styles */
        .modal-overlay {{
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
            visibility: hidden;
            opacity: 0;
            transition: all 0.3s ease;
        }}
        
        .modal-overlay.show {{
            visibility: visible;
            opacity: 1;
        }}
        
        .terminal-modal {{
            background: #1d2021;
            border: 2px solid #504945;
            border-radius: 8px;
            width: 90%;
            max-width: 700px;
            max-height: 80vh;
            overflow: hidden;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        }}
        
        .terminal-header {{
            background: #3c3836;
            padding: 0.75rem 1rem;
            border-bottom: 1px solid #504945;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .terminal-title {{
            color: #ebdbb2;
            font-size: 0.9rem;
            font-weight: bold;
        }}
        
        .terminal-close {{
            background: #cc241d;
            color: white;
            border: none;
            border-radius: 50%;
            width: 24px;
            height: 24px;
            cursor: pointer;
            font-size: 0.8rem;
        }}
        
        .terminal-body {{
            padding: 1rem;
            background: #1d2021;
            color: #ebdbb2;
            max-height: 60vh;
            overflow-y: auto;
        }}
        
        .command-block {{
            margin-bottom: 1rem;
            padding: 0.75rem;
            background: #282828;
            border: 1px solid #504945;
            border-radius: 4px;
        }}
        
        .command-description {{
            color: #928374;
            font-size: 0.8rem;
            margin-bottom: 0.5rem;
        }}
        
        .command-line-modal {{
            font-family: monospace;
            background: #1d2021;
            color: #ebdbb2;
            padding: 0.5rem;
            border-radius: 4px;
            border: 1px solid #504945;
            position: relative;
            user-select: all;
        }}
        
        .command-line-modal::before {{
            content: '❯ ';
            color: #fe8019;
            user-select: none;
        }}
        
        .copy-btn {{
            background: #458588;
            color: white;
            border: none;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.7rem;
            cursor: pointer;
            margin-top: 0.5rem;
        }}
        
        .copy-btn:hover {{
            background: #83a598;
        }}
        
        .copy-btn.copied {{
            background: #98971a;
        }}
        
        .test-type-item {{
            display: flex;
            justify-content: space-between;
            padding: 0.5rem 0;
            border-bottom: 1px solid #e2e8f0;
        }}
        
        .test-type-name {{
            font-weight: 500;
        }}
        
        .test-type-count {{
            background: #667eea;
            color: white;
            padding: 0.25rem 0.5rem;
            border-radius: 12px;
            font-size: 0.8rem;
        }}
        
        .activity-item {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.5rem 0;
            border-bottom: 1px solid #e2e8f0;
        }}
        
        .activity-icon {{
            font-size: 1.2rem;
        }}
        
        .activity-test {{
            flex: 1;
            font-weight: 500;
        }}
        
        .activity-time {{
            font-size: 0.8rem;
            color: #a0aec0;
        }}
        
        .no-reports {{
            text-align: center;
            padding: 3rem;
            color: #718096;
        }}
        
        .getting-started {{
            background: #f7fafc;
            border-radius: 12px;
            padding: 1.5rem;
            margin-top: 1.5rem;
            text-align: left;
        }}
        
        .getting-started h4 {{
            color: #4a5568;
            margin-bottom: 0.5rem;
        }}
        
        .getting-started ul {{
            list-style: none;
            padding-left: 0;
        }}
        
        .getting-started li {{
            padding: 0.5rem 0;
            color: #718096;
        }}
        
        .getting-started code {{
            background: #e2e8f0;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-family: monospace;
            color: #2d3748;
        }}
        
        .no-activity {{
            text-align: center;
            color: #a0aec0;
            font-style: italic;
            padding: 1rem;
        }}
        
        @media (max-width: 768px) {{
            .dashboard-grid {{
                grid-template-columns: 1fr;
            }}
            
            .report-header {{
                flex-direction: column;
                align-items: flex-start;
                gap: 0.5rem;
            }}
            
            .report-meta {{
                flex-direction: column;
                gap: 0.5rem;
            }}
            
            .report-actions {{
                flex-direction: column;
                align-items: flex-start;
                gap: 0.5rem;
            }}
            
            .terminal-modal {{
                width: 95%;
                margin: 1rem;
            }}
            
            .file-reports-table {{
                font-size: 0.8rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="status-line">
            NORMAL | MCPlaywright v1.0 | reports/{analytics['total_reports']} | {analytics['success_rate']:.0f}% pass rate
        </div>
        
        <div class="header">
            <h1>MCPlaywright</h1>
            <div class="subtitle">Browser Automation Testing Framework</div>
            <div class="tagline">Intelligent tool visibility • Comprehensive reporting • Production-ready</div>
            <div class="info">Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Last update: {datetime.now().strftime('%H:%M')}</div>
        </div>
        
        <div class="command-line">python3 run_all_tests.py --output=reports/ --format=html</div>
        
        <div class="dashboard-grid">
            <div class="dashboard-card">
                <h3>📊 Total Reports</h3>
                <span class="stat-number">{analytics['total_reports']}</span>
                <span class="stat-label">DB: {analytics['database_reports_count']} | Files: {analytics['file_reports_count']}</span>
            </div>
            
            <div class="dashboard-card">
                <h3>✅ Success Rate</h3>
                <span class="stat-number">{analytics['success_rate']:.1f}%</span>
                <span class="stat-label">Tests passing</span>
            </div>
            
            <div class="dashboard-card">
                <h3>⭐ Avg Quality</h3>
                <span class="stat-number">{analytics['avg_quality_score']:.1f}</span>
                <span class="stat-label">Out of 10.0</span>
            </div>
        </div>
        
        <div class="dashboard-grid">
            <div class="dashboard-card">
                <h3>🧪 Test Types</h3>
                {test_types_html or "<div class='no-activity'>No test types yet</div>"}
            </div>
            
            <div class="dashboard-card">
                <h3>📈 Recent Activity</h3>
                <div style="max-height: 300px; overflow-y: auto;">
                    {recent_activity_html}
                </div>
            </div>
            
            <div class="dashboard-card">
                <h3>🔗 Quick Actions</h3>
                <div style="display: flex; flex-direction: column; gap: 0.5rem;">
                    <button class="btn btn-primary" onclick="showTerminalModal('run_all')">🏃 Run All Tests</button>
                    <button class="btn btn-primary" onclick="showTerminalModal('single_test')">🧪 Run Single Test</button>
                    <button class="btn btn-primary" onclick="showTerminalModal('view_examples')">📂 View Examples</button>
                    <a href="." class="btn btn-primary" onclick="window.location.reload()">🔄 Refresh Dashboard</a>
                </div>
            </div>
        </div>
        
        <div class="reports-section">
            <h2>📋 Available Test Reports</h2>
            {report_cards_html}
        </div>
    </div>
    
    <!-- Terminal Modal -->
    <div id="terminalModal" class="modal-overlay">
        <div class="terminal-modal">
            <div class="terminal-header">
                <span class="terminal-title">🖥️ Terminal Commands</span>
                <button class="terminal-close" onclick="hideTerminalModal()">×</button>
            </div>
            <div class="terminal-body" id="terminalBody">
                <!-- Content will be populated by JavaScript -->
            </div>
        </div>
    </div>
    
    <script>
        // Terminal command definitions
        const terminalCommands = {{
            'run_all': {{
                title: 'Run All MCPlaywright Tests',
                commands: [
                    {{
                        description: 'Navigate to testing framework directory and run all tests',
                        command: 'cd /home/rpm/claude/mcplaywright/testing_framework && python3 run_all_tests.py'
                    }},
                    {{
                        description: 'Run tests with custom output directory',
                        command: 'cd /home/rpm/claude/mcplaywright/testing_framework && python3 run_all_tests.py --output=custom_reports/'
                    }},
                    {{
                        description: 'Run tests with verbose output',
                        command: 'cd /home/rpm/claude/mcplaywright/testing_framework && python3 run_all_tests.py --verbose'
                    }}
                ]
            }},
            'single_test': {{
                title: 'Run Individual Test Examples',
                commands: [
                    {{
                        description: 'Run Dynamic Tool Visibility Test',
                        command: 'cd /home/rpm/claude/mcplaywright/testing_framework && python3 examples/test_dynamic_tool_visibility.py'
                    }},
                    {{
                        description: 'Run Session Lifecycle Test',
                        command: 'cd /home/rpm/claude/mcplaywright/testing_framework && python3 examples/test_session_lifecycle.py'
                    }},
                    {{
                        description: 'Run Multi-Browser Compatibility Test',
                        command: 'cd /home/rpm/claude/mcplaywright/testing_framework && python3 examples/test_multi_browser_compatibility.py'
                    }},
                    {{
                        description: 'Run Performance Benchmarks',
                        command: 'cd /home/rpm/claude/mcplaywright/testing_framework && python3 examples/test_performance_benchmarks.py'
                    }}
                ]
            }},
            'view_examples': {{
                title: 'Browse Test Examples and Framework',
                commands: [
                    {{
                        description: 'List all test examples',
                        command: 'cd /home/rpm/claude/mcplaywright/testing_framework && ls -la examples/'
                    }},
                    {{
                        description: 'View testing framework structure',
                        command: 'cd /home/rpm/claude/mcplaywright/testing_framework && tree . || find . -type f -name "*.py" | head -20'
                    }},
                    {{
                        description: 'View generated reports',
                        command: 'cd /home/rpm/claude/mcplaywright/testing_framework && ls -la reports/'
                    }},
                    {{
                        description: 'Generate fresh dashboard',
                        command: 'cd /home/rpm/claude/mcplaywright/testing_framework && python3 generate_index.py'
                    }}
                ]
            }}
        }};
        
        function showTerminalModal(commandType) {{
            const modal = document.getElementById('terminalModal');
            const body = document.getElementById('terminalBody');
            const commands = terminalCommands[commandType];
            
            if (!commands) return;
            
            // Build terminal content
            let content = `<h3 style="color: #83a598; margin-bottom: 1rem;">${{commands.title}}</h3>`;
            
            commands.commands.forEach((cmd, index) => {{
                content += `
                    <div class="command-block">
                        <div class="command-description">${{cmd.description}}</div>
                        <div class="command-line-modal" id="cmd-${{index}}">${{cmd.command}}</div>
                        <button class="copy-btn" onclick="copyCommand('cmd-${{index}}', this)">📋 Copy Command</button>
                    </div>
                `;
            }});
            
            body.innerHTML = content;
            modal.classList.add('show');
        }}
        
        function hideTerminalModal() {{
            const modal = document.getElementById('terminalModal');
            modal.classList.remove('show');
        }}
        
        function copyCommand(elementId, button) {{
            const element = document.getElementById(elementId);
            const command = element.textContent.trim();
            
            navigator.clipboard.writeText(command).then(() => {{
                button.textContent = '✅ Copied!';
                button.classList.add('copied');
                
                setTimeout(() => {{
                    button.textContent = '📋 Copy Command';
                    button.classList.remove('copied');
                }}, 2000);
            }}).catch(err => {{
                console.error('Failed to copy command:', err);
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = command;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                
                button.textContent = '✅ Copied!';
                button.classList.add('copied');
                
                setTimeout(() => {{
                    button.textContent = '📋 Copy Command';
                    button.classList.remove('copied');
                }}, 2000);
            }});
        }}
        
        // Close modal when clicking outside
        document.getElementById('terminalModal').addEventListener('click', function(e) {{
            if (e.target === this) {{
                hideTerminalModal();
            }}
        }});
        
        // Close modal with Escape key
        document.addEventListener('keydown', function(e) {{
            if (e.key === 'Escape') {{
                hideTerminalModal();
            }}
        }});
        
        // Auto-refresh every 5 minutes
        setTimeout(function() {{
            window.location.reload();
        }}, 300000);
        
        console.log('MCPlaywright Test Dashboard loaded successfully');
    </script>
</body>
</html>"""
        
        return html_content
    
    def generate_and_save_index(self, output_path: str = "reports/index.html") -> str:
        """Generate index HTML and save to file."""
        html_content = self.generate_index_html()
        
        # Ensure reports directory exists
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write HTML file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(output_file.absolute())


def main():
    """Generate the test index page."""
    print("🎭 Generating MCPlaywright Test Dashboard...")
    
    generator = TestIndexGenerator()
    index_path = generator.generate_and_save_index()
    
    print(f"✅ Dashboard generated: {index_path}")
    print(f"🌐 Open in browser: file://{index_path}")
    
    return index_path


if __name__ == "__main__":
    main()