#!/usr/bin/env python3
"""
Report Registry for MCPlaywright Testing Framework.

Centralized registry system for managing test reports, tracking test runs,
and providing historical analysis of MCPlaywright browser automation testing.
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class TestReport:
    """Data class for test report metadata."""
    report_id: str
    test_name: str
    test_type: str
    timestamp: str
    duration: float
    success: bool
    quality_score: float
    file_path: str
    metadata: Dict[str, Any]


class ReportRegistry:
    """
    Centralized registry for MCPlaywright test reports.
    
    Provides functionality for:
    - Storing test report metadata and results
    - Tracking test history and trends
    - Searching and filtering test reports
    - Generating comparative analytics
    - Managing report lifecycle and cleanup
    """
    
    def __init__(self, registry_path: str = "mcplaywright_test_registry.db"):
        self.registry_path = Path(registry_path)
        self.connection = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize the SQLite database for report storage."""
        self.connection = sqlite3.connect(str(self.registry_path))
        self.connection.row_factory = sqlite3.Row  # Enable column access by name
        
        # Create tables
        self._create_tables()
    
    def _create_tables(self):
        """Create database tables for report storage."""
        cursor = self.connection.cursor()
        
        # Main reports table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_reports (
                report_id TEXT PRIMARY KEY,
                test_name TEXT NOT NULL,
                test_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                duration REAL NOT NULL,
                success BOOLEAN NOT NULL,
                quality_score REAL,
                file_path TEXT,
                metadata_json TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Quality metrics table for detailed analysis
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quality_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                threshold_value REAL,
                passed BOOLEAN NOT NULL,
                weight REAL,
                description TEXT,
                FOREIGN KEY (report_id) REFERENCES test_reports (report_id)
            )
        """)
        
        # Test steps table for detailed step tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id TEXT NOT NULL,
                step_name TEXT NOT NULL,
                step_description TEXT,
                step_order INTEGER NOT NULL,
                duration_ms REAL,
                success BOOLEAN NOT NULL,
                error_message TEXT,
                FOREIGN KEY (report_id) REFERENCES test_reports (report_id)
            )
        """)
        
        # Browser actions table for action-level tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS browser_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                selector TEXT,
                duration_ms REAL,
                success BOOLEAN NOT NULL,
                result_json TEXT,
                timestamp TEXT,
                FOREIGN KEY (report_id) REFERENCES test_reports (report_id)
            )
        """)
        
        # Create indexes for better query performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_timestamp ON test_reports (timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_test_type ON test_reports (test_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_success ON test_reports (success)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_quality_metrics_report ON quality_metrics (report_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_test_steps_report ON test_steps (report_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_browser_actions_report ON browser_actions (report_id)")
        
        self.connection.commit()
    
    def register_report(self, report_data: Dict[str, Any]) -> str:
        """Register a new test report in the registry."""
        report_id = report_data.get('test_id', f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        cursor = self.connection.cursor()
        
        # Handle both nested and flat data structures
        # The test runner adds metadata that creates flat structure
        test_name = report_data.get('test_name', 'Unknown Test')
        test_type = report_data.get('category', 'browser_test')
        quality_score = report_data.get('quality_score', 0.0)
        success = report_data.get('success', False)
        duration = report_data.get('duration', 0.0)
        timestamp = report_data.get('timestamp', datetime.now().isoformat())
        file_path = report_data.get('report_path')
        
        cursor.execute("""
            INSERT OR REPLACE INTO test_reports 
            (report_id, test_name, test_type, timestamp, duration, success, 
             quality_score, file_path, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            report_id,
            test_name,
            test_type,
            timestamp,
            duration,
            success,
            quality_score,
            file_path,
            json.dumps(report_data)  # Store all data as metadata
        ))
        
        # Store key quality metrics
        if quality_score > 0:
            cursor.execute("""
                INSERT INTO quality_metrics 
                (report_id, metric_name, metric_value, threshold_value, passed, weight, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                report_id,
                'overall_quality_score',
                quality_score,
                7.0,  # Threshold for good quality
                quality_score >= 7.0,
                1.0,
                'Overall test quality score'
            ))
        
        # Store success rate if available
        success_rate = report_data.get('success_rate')
        if success_rate is not None:
            cursor.execute("""
                INSERT INTO quality_metrics 
                (report_id, metric_name, metric_value, threshold_value, passed, weight, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                report_id,
                'success_rate',
                success_rate,
                80.0,  # 80% threshold for good success
                success_rate >= 80.0,
                1.0,
                'Test success rate percentage'
            ))
        
        # Store test steps
        test_steps = report_data.get('test_steps', [])
        for i, step in enumerate(test_steps):
            cursor.execute("""
                INSERT INTO test_steps 
                (report_id, step_name, step_description, step_order, duration_ms, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                report_id,
                step.get('name', f'Step {i+1}'),
                step.get('description', ''),
                i + 1,
                step.get('duration_ms', 0.0),
                step.get('success', True),
                step.get('error_message')
            ))
        
        # Store browser actions
        browser_actions = report_data.get('browser_data', {}).get('actions', [])
        for action in browser_actions:
            cursor.execute("""
                INSERT INTO browser_actions 
                (report_id, action_type, selector, duration_ms, success, result_json, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                report_id,
                action.get('action', 'unknown'),
                action.get('selector'),
                action.get('duration_ms', 0.0),
                action.get('success', True),
                json.dumps(action.get('result', {})),
                action.get('timestamp', datetime.now().isoformat())
            ))
        
        self.connection.commit()
        return report_id
    
    def get_report(self, report_id: str) -> Optional[TestReport]:
        """Retrieve a specific test report by ID."""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT * FROM test_reports WHERE report_id = ?
        """, (report_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return TestReport(
            report_id=row['report_id'],
            test_name=row['test_name'],
            test_type=row['test_type'],
            timestamp=row['timestamp'],
            duration=row['duration'],
            success=bool(row['success']),
            quality_score=row['quality_score'] or 0.0,
            file_path=row['file_path'] or '',
            metadata=json.loads(row['metadata_json'] or '{}')
        )
    
    def search_reports(self, 
                      test_type: Optional[str] = None,
                      success_only: Optional[bool] = None,
                      min_quality_score: Optional[float] = None,
                      days_back: Optional[int] = None,
                      limit: Optional[int] = 100) -> List[TestReport]:
        """Search for test reports with filtering options."""
        cursor = self.connection.cursor()
        
        # Build dynamic query
        where_clauses = []
        params = []
        
        if test_type:
            where_clauses.append("test_type = ?")
            params.append(test_type)
        
        if success_only is not None:
            where_clauses.append("success = ?")
            params.append(success_only)
        
        if min_quality_score is not None:
            where_clauses.append("quality_score >= ?")
            params.append(min_quality_score)
        
        if days_back is not None:
            cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
            where_clauses.append("timestamp >= ?")
            params.append(cutoff_date)
        
        where_clause = ""
        if where_clauses:
            where_clause = "WHERE " + " AND ".join(where_clauses)
        
        limit_clause = f"LIMIT {limit}" if limit else ""
        
        query = f"""
            SELECT * FROM test_reports 
            {where_clause}
            ORDER BY timestamp DESC
            {limit_clause}
        """
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [
            TestReport(
                report_id=row['report_id'],
                test_name=row['test_name'],
                test_type=row['test_type'],
                timestamp=row['timestamp'],
                duration=row['duration'],
                success=bool(row['success']),
                quality_score=row['quality_score'] or 0.0,
                file_path=row['file_path'] or '',
                metadata=json.loads(row['metadata_json'] or '{}')
            )
            for row in rows
        ]
    
    def get_test_analytics(self, days_back: int = 30) -> Dict[str, Any]:
        """Generate analytics for test reports over specified period."""
        cursor = self.connection.cursor()
        cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
        
        # Overall statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_tests,
                SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_tests,
                AVG(quality_score) as avg_quality_score,
                AVG(duration) as avg_duration,
                MIN(quality_score) as min_quality_score,
                MAX(quality_score) as max_quality_score
            FROM test_reports
            WHERE timestamp >= ?
        """, (cutoff_date,))
        
        stats = cursor.fetchone()
        
        # Test type breakdown
        cursor.execute("""
            SELECT 
                test_type,
                COUNT(*) as count,
                AVG(quality_score) as avg_quality,
                SUM(CASE WHEN success THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate
            FROM test_reports
            WHERE timestamp >= ?
            GROUP BY test_type
            ORDER BY count DESC
        """, (cutoff_date,))
        
        test_type_breakdown = [dict(row) for row in cursor.fetchall()]
        
        # Daily trend (last 7 days)
        cursor.execute("""
            SELECT 
                DATE(timestamp) as test_date,
                COUNT(*) as daily_count,
                AVG(quality_score) as daily_avg_quality,
                SUM(CASE WHEN success THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as daily_success_rate
            FROM test_reports
            WHERE timestamp >= ?
            GROUP BY DATE(timestamp)
            ORDER BY test_date DESC
            LIMIT 7
        """, ((datetime.now() - timedelta(days=7)).isoformat(),))
        
        daily_trend = [dict(row) for row in cursor.fetchall()]
        
        # Quality metrics analysis
        cursor.execute("""
            SELECT 
                metric_name,
                COUNT(*) as metric_count,
                AVG(metric_value) as avg_value,
                SUM(CASE WHEN passed THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as pass_rate
            FROM quality_metrics qm
            JOIN test_reports tr ON qm.report_id = tr.report_id
            WHERE tr.timestamp >= ?
            GROUP BY metric_name
            ORDER BY pass_rate ASC
        """, (cutoff_date,))
        
        quality_metrics_analysis = [dict(row) for row in cursor.fetchall()]
        
        return {
            "period_days": days_back,
            "overall_stats": {
                "total_tests": stats['total_tests'] or 0,
                "successful_tests": stats['successful_tests'] or 0,
                "success_rate": (stats['successful_tests'] / max(stats['total_tests'], 1)) * 100,
                "avg_quality_score": stats['avg_quality_score'] or 0.0,
                "avg_duration": stats['avg_duration'] or 0.0,
                "min_quality_score": stats['min_quality_score'] or 0.0,
                "max_quality_score": stats['max_quality_score'] or 0.0
            },
            "test_type_breakdown": test_type_breakdown,
            "daily_trend": daily_trend,
            "quality_metrics_analysis": quality_metrics_analysis,
            "generated_at": datetime.now().isoformat()
        }
    
    def get_failing_tests_analysis(self, days_back: int = 7) -> Dict[str, Any]:
        """Analyze failing tests to identify patterns and issues."""
        cursor = self.connection.cursor()
        cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
        
        # Recent failing tests
        cursor.execute("""
            SELECT report_id, test_name, test_type, timestamp, quality_score
            FROM test_reports
            WHERE success = 0 AND timestamp >= ?
            ORDER BY timestamp DESC
            LIMIT 20
        """, (cutoff_date,))
        
        failing_tests = [dict(row) for row in cursor.fetchall()]
        
        # Most common failing quality metrics
        cursor.execute("""
            SELECT 
                qm.metric_name,
                COUNT(*) as failure_count,
                AVG(qm.metric_value) as avg_failing_value,
                AVG(qm.threshold_value) as avg_threshold
            FROM quality_metrics qm
            JOIN test_reports tr ON qm.report_id = tr.report_id
            WHERE qm.passed = 0 AND tr.timestamp >= ?
            GROUP BY qm.metric_name
            ORDER BY failure_count DESC
            LIMIT 10
        """, (cutoff_date,))
        
        failing_metrics = [dict(row) for row in cursor.fetchall()]
        
        # Browser action failure patterns
        cursor.execute("""
            SELECT 
                ba.action_type,
                COUNT(*) as failure_count,
                AVG(ba.duration_ms) as avg_duration
            FROM browser_actions ba
            JOIN test_reports tr ON ba.report_id = tr.report_id
            WHERE ba.success = 0 AND tr.timestamp >= ?
            GROUP BY ba.action_type
            ORDER BY failure_count DESC
            LIMIT 10
        """, (cutoff_date,))
        
        failing_actions = [dict(row) for row in cursor.fetchall()]
        
        return {
            "analysis_period_days": days_back,
            "total_failing_tests": len(failing_tests),
            "recent_failing_tests": failing_tests,
            "most_common_failing_metrics": failing_metrics,
            "most_common_failing_actions": failing_actions,
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    def cleanup_old_reports(self, days_to_keep: int = 90) -> int:
        """Clean up old test reports beyond specified retention period."""
        cursor = self.connection.cursor()
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
        
        # Get count of reports to be deleted
        cursor.execute("""
            SELECT COUNT(*) FROM test_reports WHERE timestamp < ?
        """, (cutoff_date,))
        
        reports_to_delete = cursor.fetchone()[0]
        
        # Delete old reports (cascade deletes should handle related tables)
        cursor.execute("DELETE FROM browser_actions WHERE report_id IN (SELECT report_id FROM test_reports WHERE timestamp < ?)", (cutoff_date,))
        cursor.execute("DELETE FROM test_steps WHERE report_id IN (SELECT report_id FROM test_reports WHERE timestamp < ?)", (cutoff_date,))
        cursor.execute("DELETE FROM quality_metrics WHERE report_id IN (SELECT report_id FROM test_reports WHERE timestamp < ?)", (cutoff_date,))
        cursor.execute("DELETE FROM test_reports WHERE timestamp < ?", (cutoff_date,))
        
        self.connection.commit()
        
        return reports_to_delete
    
    def export_reports_csv(self, output_path: str, days_back: Optional[int] = None) -> bool:
        """Export test reports to CSV format."""
        try:
            import csv
            
            # Get reports to export
            reports = self.search_reports(days_back=days_back, limit=None)
            
            with open(output_path, 'w', newline='') as csvfile:
                fieldnames = ['report_id', 'test_name', 'test_type', 'timestamp', 
                             'duration', 'success', 'quality_score']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for report in reports:
                    writer.writerow({
                        'report_id': report.report_id,
                        'test_name': report.test_name,
                        'test_type': report.test_type,
                        'timestamp': report.timestamp,
                        'duration': report.duration,
                        'success': report.success,
                        'quality_score': report.quality_score
                    })
            
            return True
        except Exception:
            return False
    
    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()