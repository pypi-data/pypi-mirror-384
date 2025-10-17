#!/usr/bin/env python3
"""
Network Monitoring Test Fixtures for MCPlaywright Testing Framework.

Provides test scenarios and mock data for HTTP request monitoring features
including request capture, network analysis, and performance assessment.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta


class NetworkFixtures:
    """
    Test fixtures for network monitoring scenarios.
    
    Provides realistic test data for:
    - HTTP request monitoring and capture
    - Network performance analysis  
    - Request/response filtering and analysis
    - API testing and validation
    """
    
    @staticmethod
    def http_monitoring_config() -> Dict[str, Any]:
        """Configuration for HTTP request monitoring test."""
        return {
            "name": "HTTP Request Monitoring Test Configuration",
            "description": "Test comprehensive HTTP request capture and analysis",
            "monitoring_settings": {
                "capture_body": True,
                "max_body_size": 10485760,  # 10MB
                "auto_save": False,
                "url_filter": ".*",  # Capture all requests
                "capture_headers": True,
                "capture_timing": True
            },
            "expected_features": [
                "request_capture",
                "response_analysis", 
                "timing_metrics",
                "header_inspection",
                "body_content_capture"
            ],
            "test_scenarios": [
                {
                    "scenario": "api_interaction_monitoring",
                    "url": "https://jsonplaceholder.typicode.com",
                    "actions": [
                        {"action": "navigate", "path": "/posts", "expected_requests": 1},
                        {"action": "fetch_data", "endpoint": "/posts/1", "expected_requests": 1},
                        {"action": "post_data", "endpoint": "/posts", "data": {"title": "test"}, "expected_requests": 1}
                    ],
                    "expected_total_requests": 3,
                    "expected_success_rate": 100.0
                }
            ]
        }
    
    @staticmethod
    def network_performance_config() -> Dict[str, Any]:
        """Configuration for network performance monitoring test."""
        return {
            "name": "Network Performance Monitoring Test",
            "description": "Test network timing and performance analysis",
            "performance_thresholds": {
                "dns_lookup": 100,      # 100ms max DNS lookup
                "tcp_connect": 200,     # 200ms max TCP connection
                "ssl_handshake": 300,   # 300ms max SSL handshake
                "request_send": 50,     # 50ms max request send
                "response_receive": 500, # 500ms max response receive
                "total_time": 1000      # 1 second max total time
            },
            "test_scenarios": [
                {
                    "scenario": "fast_api_response",
                    "url": "https://httpbin.org/json",
                    "expected_performance": {
                        "total_time": 800,
                        "response_size": 429,  # bytes
                        "status_code": 200
                    }
                },
                {
                    "scenario": "large_response_handling",
                    "url": "https://httpbin.org/stream/100",
                    "expected_performance": {
                        "total_time": 2000,
                        "response_size": 10000,  # approximate
                        "status_code": 200
                    }
                }
            ]
        }
    
    @staticmethod
    def request_filtering_config() -> Dict[str, Any]:
        """Configuration for request filtering and analysis test."""
        return {
            "name": "Request Filtering and Analysis Test",
            "description": "Test advanced request filtering and categorization",
            "filter_configurations": [
                {
                    "name": "api_only_filter",
                    "url_pattern": ".*/api/.*",
                    "description": "Capture only API requests"
                },
                {
                    "name": "images_filter",
                    "url_pattern": ".*\\.(jpg|jpeg|png|gif|webp)$",
                    "description": "Capture only image requests"
                },
                {
                    "name": "slow_requests_filter",
                    "timing_threshold": 1000,  # > 1 second
                    "description": "Capture only slow requests"
                }
            ],
            "analysis_criteria": {
                "request_categorization": True,
                "performance_analysis": True,
                "error_detection": True,
                "duplicate_request_detection": True
            },
            "test_scenarios": [
                {
                    "scenario": "mixed_content_page",
                    "url": "https://playwright.dev",
                    "expected_categories": [
                        {"category": "document", "min_count": 1},
                        {"category": "script", "min_count": 5},
                        {"category": "stylesheet", "min_count": 2},
                        {"category": "image", "min_count": 3}
                    ],
                    "expected_total_requests": 15
                }
            ]
        }
    
    @staticmethod
    def api_testing_scenario() -> Dict[str, Any]:
        """Test scenario for API endpoint testing and validation."""
        return {
            "name": "API Testing and Validation",
            "description": "Test API endpoints with request/response validation",
            "api_endpoints": [
                {
                    "name": "get_posts",
                    "method": "GET",
                    "url": "https://jsonplaceholder.typicode.com/posts",
                    "expected_response": {
                        "status_code": 200,
                        "content_type": "application/json",
                        "response_time": 1000,  # max 1 second
                        "body_schema": "array_of_objects"
                    },
                    "validation_rules": [
                        {"field": "length", "operator": "gt", "value": 0},
                        {"field": "[0].title", "operator": "exists", "value": True}
                    ]
                },
                {
                    "name": "create_post",
                    "method": "POST", 
                    "url": "https://jsonplaceholder.typicode.com/posts",
                    "request_body": {
                        "title": "MCPlaywright Test Post",
                        "body": "Testing API with MCPlaywright",
                        "userId": 1
                    },
                    "expected_response": {
                        "status_code": 201,
                        "content_type": "application/json",
                        "response_time": 1500,
                        "body_schema": "object"
                    },
                    "validation_rules": [
                        {"field": "id", "operator": "exists", "value": True},
                        {"field": "title", "operator": "equals", "value": "MCPlaywright Test Post"}
                    ]
                }
            ],
            "test_workflow": [
                "start_monitoring",
                "execute_api_calls",
                "validate_responses", 
                "analyze_performance",
                "generate_report"
            ]
        }
    
    @staticmethod
    def error_handling_scenario() -> Dict[str, Any]:
        """Test scenario for network error handling and recovery."""
        return {
            "name": "Network Error Handling Test",
            "description": "Test error scenarios and network failure handling",
            "error_scenarios": [
                {
                    "scenario": "404_not_found",
                    "url": "https://httpbin.org/status/404",
                    "expected_status": 404,
                    "expected_handling": "log_error_continue",
                    "recovery_action": None
                },
                {
                    "scenario": "500_server_error",
                    "url": "https://httpbin.org/status/500", 
                    "expected_status": 500,
                    "expected_handling": "log_error_retry",
                    "recovery_action": "retry_request"
                },
                {
                    "scenario": "timeout_error",
                    "url": "https://httpbin.org/delay/10",
                    "timeout": 5000,  # 5 second timeout
                    "expected_error": "TimeoutError",
                    "expected_handling": "log_timeout_continue",
                    "recovery_action": "use_fallback"
                },
                {
                    "scenario": "connection_refused",
                    "url": "http://localhost:99999/nonexistent",
                    "expected_error": "ConnectionError",
                    "expected_handling": "log_connection_error",
                    "recovery_action": "skip_request"
                }
            ],
            "error_handling_strategy": {
                "max_retries": 3,
                "retry_delay": 1000,  # 1 second
                "exponential_backoff": True,
                "fallback_urls": ["https://httpbin.org/json"],
                "continue_on_error": True
            }
        }
    
    @staticmethod
    def security_monitoring_scenario() -> Dict[str, Any]:
        """Test scenario for security-focused network monitoring."""
        return {
            "name": "Security Network Monitoring",
            "description": "Monitor and analyze network security aspects",
            "security_checks": [
                {
                    "check": "https_enforcement",
                    "description": "Ensure all requests use HTTPS",
                    "validation": "protocol_https_only"
                },
                {
                    "check": "header_security",
                    "description": "Validate security headers presence",
                    "required_headers": [
                        "Strict-Transport-Security",
                        "X-Content-Type-Options",
                        "X-Frame-Options"
                    ]
                },
                {
                    "check": "sensitive_data_leakage",
                    "description": "Check for sensitive data in requests/responses",
                    "sensitive_patterns": [
                        "password",
                        "api_key", 
                        "secret",
                        "token",
                        "credit_card"
                    ]
                }
            ],
            "test_urls": [
                "https://github.com",
                "https://api.github.com",
                "https://stackoverflow.com"
            ],
            "security_thresholds": {
                "https_compliance": 100.0,  # 100% HTTPS
                "security_header_coverage": 80.0,  # 80% coverage
                "sensitive_data_leaks": 0  # Zero tolerance
            }
        }
    
    @staticmethod
    def get_mock_http_requests() -> List[Dict[str, Any]]:
        """Get mock HTTP request data for testing."""
        base_time = datetime.now()
        return [
            {
                "id": "req_001",
                "method": "GET",
                "url": "https://jsonplaceholder.typicode.com/posts",
                "status_code": 200,
                "request_headers": {
                    "User-Agent": "MCPlaywright/1.0",
                    "Accept": "application/json",
                    "Accept-Encoding": "gzip, deflate"
                },
                "response_headers": {
                    "Content-Type": "application/json; charset=utf-8",
                    "Content-Length": "6395",
                    "Cache-Control": "max-age=43200"
                },
                "request_body": None,
                "response_body": '[{"userId": 1, "id": 1, "title": "sunt aut facere..."}]',
                "timing": {
                    "dns_lookup": 45.2,
                    "tcp_connect": 123.8,
                    "ssl_handshake": 234.1,
                    "request_send": 12.3,
                    "response_receive": 456.7,
                    "total_time": 872.1
                },
                "timestamp": base_time.isoformat(),
                "success": True,
                "error": None
            },
            {
                "id": "req_002", 
                "method": "POST",
                "url": "https://jsonplaceholder.typicode.com/posts",
                "status_code": 201,
                "request_headers": {
                    "User-Agent": "MCPlaywright/1.0",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Content-Length": "78"
                },
                "response_headers": {
                    "Content-Type": "application/json; charset=utf-8",
                    "Content-Length": "87",
                    "Location": "https://jsonplaceholder.typicode.com/posts/101"
                },
                "request_body": '{"title": "Test Post", "body": "Test content", "userId": 1}',
                "response_body": '{"id": 101, "title": "Test Post", "body": "Test content", "userId": 1}',
                "timing": {
                    "dns_lookup": 2.1,  # Cached
                    "tcp_connect": 0.0,  # Keep-alive
                    "ssl_handshake": 0.0,  # Reused
                    "request_send": 23.4,
                    "response_receive": 234.5,
                    "total_time": 260.0
                },
                "timestamp": (base_time + timedelta(seconds=2)).isoformat(),
                "success": True,
                "error": None
            },
            {
                "id": "req_003",
                "method": "GET", 
                "url": "https://httpbin.org/status/404",
                "status_code": 404,
                "request_headers": {
                    "User-Agent": "MCPlaywright/1.0",
                    "Accept": "*/*"
                },
                "response_headers": {
                    "Content-Type": "text/html",
                    "Content-Length": "233"
                },
                "request_body": None,
                "response_body": "<html><body><h1>404 Not Found</h1></body></html>",
                "timing": {
                    "dns_lookup": 67.8,
                    "tcp_connect": 145.6,
                    "ssl_handshake": 289.3,
                    "request_send": 8.9,
                    "response_receive": 123.4,
                    "total_time": 635.0
                },
                "timestamp": (base_time + timedelta(seconds=4)).isoformat(),
                "success": False,
                "error": "HTTP 404: Not Found"
            }
        ]
    
    @staticmethod
    def get_mock_performance_metrics() -> Dict[str, Any]:
        """Get mock network performance metrics for testing."""
        return {
            "total_requests": 25,
            "successful_requests": 22,
            "failed_requests": 3,
            "success_rate": 88.0,
            "average_response_time": 645.3,
            "median_response_time": 512.1,
            "min_response_time": 123.4,
            "max_response_time": 1234.5,
            "total_bytes_sent": 2048,
            "total_bytes_received": 45678,
            "requests_by_method": {
                "GET": 18,
                "POST": 5,
                "PUT": 1,
                "DELETE": 1
            },
            "requests_by_status": {
                "200": 15,
                "201": 5,
                "404": 2,
                "500": 1,
                "304": 2
            },
            "top_slow_requests": [
                {"url": "https://example.com/slow-api", "time": 1234.5},
                {"url": "https://api.example.com/data", "time": 987.6},
                {"url": "https://cdn.example.com/large-file", "time": 876.5}
            ],
            "bandwidth_usage": {
                "peak_downstream": "2.3 MB/s",
                "peak_upstream": "456 KB/s", 
                "average_downstream": "890 KB/s",
                "average_upstream": "123 KB/s"
            }
        }
    
    @staticmethod
    def get_mock_network_analysis() -> Dict[str, Any]:
        """Get mock network analysis results for testing."""
        return {
            "analysis_summary": {
                "total_requests_analyzed": 47,
                "unique_domains": 8,
                "unique_endpoints": 23,
                "cache_hit_rate": 34.2,
                "compression_savings": 67.8
            },
            "domain_breakdown": [
                {"domain": "api.github.com", "requests": 12, "success_rate": 100.0, "avg_time": 456.7},
                {"domain": "cdn.jsdelivr.net", "requests": 8, "success_rate": 98.5, "avg_time": 234.1},
                {"domain": "fonts.googleapis.com", "requests": 6, "success_rate": 100.0, "avg_time": 123.8},
                {"domain": "www.google-analytics.com", "requests": 15, "success_rate": 93.3, "avg_time": 567.2}
            ],
            "content_type_analysis": {
                "application/json": {"count": 12, "total_size": 34567, "avg_size": 2880},
                "text/html": {"count": 8, "total_size": 123456, "avg_size": 15432},
                "text/css": {"count": 6, "total_size": 45678, "avg_size": 7613},
                "application/javascript": {"count": 9, "total_size": 98765, "avg_size": 10974},
                "image/png": {"count": 4, "total_size": 234567, "avg_size": 58642}
            },
            "performance_insights": [
                {
                    "category": "optimization",
                    "insight": "Enable compression for text resources",
                    "potential_savings": "45% reduction in transfer size",
                    "affected_requests": 15
                },
                {
                    "category": "caching",
                    "insight": "Implement proper cache headers",
                    "potential_savings": "67% reduction in repeat requests",
                    "affected_requests": 23
                },
                {
                    "category": "performance",
                    "insight": "Reduce API response times",
                    "potential_savings": "23% improvement in page load",
                    "affected_requests": 8
                }
            ]
        }
    
    @staticmethod
    def get_network_quality_thresholds() -> Dict[str, float]:
        """Get network monitoring quality thresholds."""
        return {
            "request_success_rate": 95.0,      # 95% minimum success rate
            "average_response_time": 1000.0,   # 1 second average response
            "max_response_time": 5000.0,       # 5 seconds maximum response
            "dns_lookup_time": 200.0,          # 200ms maximum DNS lookup
            "ssl_handshake_time": 500.0,       # 500ms maximum SSL handshake
            "monitoring_completeness": 90.0,   # 90% request capture rate
            "error_rate": 5.0,                 # Maximum 5% error rate
            "timeout_rate": 2.0,               # Maximum 2% timeout rate
            "network_efficiency": 75.0         # 75% minimum efficiency score
        }