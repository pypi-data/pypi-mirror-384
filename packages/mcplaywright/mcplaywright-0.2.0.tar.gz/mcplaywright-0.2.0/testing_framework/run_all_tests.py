#!/usr/bin/env python3
"""
MCPlaywright Testing Framework - Test Runner

Comprehensive test runner for all MCPlaywright test examples including:
- Dynamic Tool Visibility Test
- Session Lifecycle Test  
- Multi-Browser Compatibility Test
- Performance Benchmark Test
- Error Handling and Recovery Test

Provides unified execution, reporting, and dashboard generation.
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime
import importlib.util

# Add the testing framework to path
testing_framework_path = Path(__file__).parent
sys.path.append(str(testing_framework_path))

from registry.report_registry import ReportRegistry
from registry.dashboard import TestDashboard


class MCPlaywrightTestRunner:
    """
    Main test runner for MCPlaywright Testing Framework.
    
    Orchestrates execution of all test examples and generates unified reporting
    with comprehensive analytics, trend analysis, and quality metrics.
    """
    
    def __init__(self):
        self.registry = ReportRegistry()
        self.dashboard = TestDashboard(self.registry)
        self.test_results = {}
        self.overall_start_time = time.time()
        
        # Test configurations
        self.test_suite = {
            "dynamic_tool_visibility": {
                "name": "Dynamic Tool Visibility Test",
                "description": "Test MCPlaywright's intelligent tool filtering system",
                "module": "examples.test_dynamic_tool_visibility",
                "class": "TestDynamicToolVisibility",
                "priority": "high",
                "category": "core_functionality"
            },
            "session_lifecycle": {
                "name": "Session Lifecycle Test", 
                "description": "Test complete browser session management lifecycle",
                "module": "examples.test_session_lifecycle",
                "class": "TestSessionLifecycle",
                "priority": "high",
                "category": "session_management"
            },
            "multi_browser_compatibility": {
                "name": "Multi-Browser Compatibility Test",
                "description": "Test compatibility across different browser engines",
                "module": "examples.test_multi_browser_compatibility", 
                "class": "TestMultiBrowserCompatibility",
                "priority": "medium",
                "category": "compatibility"
            },
            "performance_benchmarks": {
                "name": "Performance Benchmark Test",
                "description": "Benchmark performance across different scenarios",
                "module": "examples.test_performance_benchmarks",
                "class": "TestPerformanceBenchmarks", 
                "priority": "medium",
                "category": "performance"
            },
            "error_handling_recovery": {
                "name": "Error Handling and Recovery Test",
                "description": "Test error handling and recovery mechanisms",
                "module": "examples.test_error_handling_recovery",
                "class": "TestErrorHandlingRecovery",
                "priority": "high", 
                "category": "reliability"
            },
            "claude_mcp_integration": {
                "name": "Claude MCP Integration Test",
                "description": "Test Claude Code MCP installation and connection validation",
                "module": "examples.test_claude_mcp_integration", 
                "class": "ClaudeMCPIntegrationTest",
                "priority": "critical",
                "category": "integration"
            }
        }
        
    def print_banner(self):
        """Print test runner banner."""
        print("🎭 MCPlaywright Testing Framework - Complete Test Suite")
        print("=" * 60)
        print(f"📅 Test Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🧪 Tests: {len(self.test_suite)} test suites")
        print(f"📊 Reporting: Unified dashboard and analytics")
        print("=" * 60)
        print()
    
    def load_test_module(self, test_config):
        """Dynamically load a test module and class."""
        try:
            module_path = testing_framework_path / f"{test_config['module'].replace('.', '/')}.py"
            
            spec = importlib.util.spec_from_file_location(
                test_config['module'], 
                module_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            test_class = getattr(module, test_config['class'])
            return test_class()
            
        except Exception as e:
            print(f"❌ Failed to load test {test_config['name']}: {str(e)}")
            return None
    
    def run_single_test(self, test_id, test_config):
        """Run a single test and capture results."""
        print(f"🧪 Running {test_config['name']}...")
        print(f"   📝 {test_config['description']}")
        print(f"   🎯 Priority: {test_config['priority'].upper()}")
        print(f"   📂 Category: {test_config['category']}")
        
        start_time = time.time()
        
        try:
            # Load test class
            test_instance = self.load_test_module(test_config)
            if not test_instance:
                return {
                    "success": False,
                    "error": "Failed to load test module",
                    "duration": 0
                }
            
            # Execute test (handle both sync and async tests)
            if hasattr(test_instance, 'run_test'):
                # Async test (like our integration test)
                import asyncio
                result = asyncio.run(test_instance.run_test())
                # Convert success_rate to success boolean for compatibility
                if 'success_rate' in result and 'success' not in result:
                    result['success'] = result['success_rate'] >= 0.8  # 80% threshold
            else:
                # Sync test (like our existing tests)
                result = test_instance.run_complete_test()
            duration = time.time() - start_time
            
            # Add metadata to result
            result.update({
                "test_id": test_id,
                "test_name": test_config['name'],
                "category": test_config['category'],
                "priority": test_config['priority'],
                "duration": duration,
                "timestamp": datetime.now().isoformat()
            })
            
            # Register result in registry
            report_id = self.registry.register_report(result)
            result["registry_id"] = report_id
            
            # Print result summary
            status = "✅ PASSED" if result.get("success", False) else "❌ FAILED"
            print(f"   {status} - {duration:.1f}s")
            
            if result.get("success", False):
                quality_score = result.get("quality_score", 0)
                success_rate = result.get("success_rate", 0)
                print(f"   🎯 Quality: {quality_score:.1f}/10, Success: {success_rate:.1f}%")
            else:
                error_msg = result.get("error", "Unknown error")
                print(f"   ❌ Error: {error_msg}")
            
            print()
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            error_result = {
                "test_id": test_id,
                "test_name": test_config['name'],
                "success": False,
                "error": str(e),
                "duration": duration,
                "timestamp": datetime.now().isoformat(),
                "category": test_config['category'],
                "priority": test_config['priority']
            }
            
            print(f"   ❌ FAILED - {duration:.1f}s")
            print(f"   ❌ Error: {str(e)}")
            print()
            
            return error_result
    
    def run_all_tests(self, test_filter=None):
        """Run all tests in the suite."""
        self.print_banner()
        
        # Filter tests if specified
        tests_to_run = self.test_suite
        if test_filter:
            if isinstance(test_filter, str):
                # Single test
                if test_filter in self.test_suite:
                    tests_to_run = {test_filter: self.test_suite[test_filter]}
                else:
                    print(f"❌ Test '{test_filter}' not found")
                    return False
            elif isinstance(test_filter, list):
                # List of tests
                tests_to_run = {k: v for k, v in self.test_suite.items() if k in test_filter}
            elif isinstance(test_filter, dict):
                # Filter by criteria (e.g., priority, category)
                tests_to_run = {}
                for test_id, test_config in self.test_suite.items():
                    match = True
                    for key, value in test_filter.items():
                        if test_config.get(key) != value:
                            match = False
                            break
                    if match:
                        tests_to_run[test_id] = test_config
        
        if not tests_to_run:
            print("❌ No tests match the specified filter")
            return False
        
        print(f"🏃 Executing {len(tests_to_run)} tests...")
        print()
        
        # Run tests
        for test_id, test_config in tests_to_run.items():
            result = self.run_single_test(test_id, test_config)
            self.test_results[test_id] = result
        
        # Generate summary and dashboard
        self.generate_summary()
        self.generate_dashboard()
        
        return True
    
    def generate_summary(self):
        """Generate comprehensive test run summary."""
        total_duration = time.time() - self.overall_start_time
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results.values() if r.get("success", False))
        failed_tests = total_tests - passed_tests
        
        overall_success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Calculate quality metrics
        quality_scores = [r.get("quality_score", 0) for r in self.test_results.values() 
                         if r.get("quality_score") is not None]
        avg_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # Category breakdown
        category_stats = {}
        for result in self.test_results.values():
            category = result.get("category", "unknown")
            if category not in category_stats:
                category_stats[category] = {"total": 0, "passed": 0}
            category_stats[category]["total"] += 1
            if result.get("success", False):
                category_stats[category]["passed"] += 1
        
        # Priority breakdown
        priority_stats = {}
        for result in self.test_results.values():
            priority = result.get("priority", "unknown")
            if priority not in priority_stats:
                priority_stats[priority] = {"total": 0, "passed": 0}
            priority_stats[priority]["total"] += 1
            if result.get("success", False):
                priority_stats[priority]["passed"] += 1
        
        print("📊 TEST RUN SUMMARY")
        print("=" * 40)
        print(f"⏱️  Total Duration: {total_duration:.1f}s")
        print(f"🧪 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {overall_success_rate:.1f}%")
        print(f"🎯 Avg Quality Score: {avg_quality_score:.1f}/10")
        print()
        
        print("📂 BY CATEGORY:")
        for category, stats in category_stats.items():
            success_rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            print(f"   {category}: {stats['passed']}/{stats['total']} ({success_rate:.1f}%)")
        print()
        
        print("🎯 BY PRIORITY:")
        for priority, stats in priority_stats.items():
            success_rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            print(f"   {priority}: {stats['passed']}/{stats['total']} ({success_rate:.1f}%)")
        print()
        
        # Individual test results
        print("🧪 INDIVIDUAL RESULTS:")
        for test_id, result in self.test_results.items():
            status = "✅ PASS" if result.get("success", False) else "❌ FAIL"
            duration = result.get("duration", 0)
            quality = result.get("quality_score", 0)
            success_rate = result.get("success_rate", 0)
            
            print(f"   {status} {result.get('test_name', test_id):<35} "
                  f"({duration:.1f}s, Q:{quality:.1f}, SR:{success_rate:.1f}%)")
        
        print()
        
        # Save summary to file
        summary_data = {
            "timestamp": datetime.now().isoformat(),
            "total_duration": total_duration,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "overall_success_rate": overall_success_rate,
            "avg_quality_score": avg_quality_score,
            "category_stats": category_stats,
            "priority_stats": priority_stats,
            "test_results": self.test_results
        }
        
        summary_path = testing_framework_path / "reports" / f"test_run_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        summary_path.parent.mkdir(exist_ok=True)
        
        with open(summary_path, 'w') as f:
            json.dump(summary_data, f, indent=2, default=str)
        
        print(f"💾 Summary saved to: {summary_path}")
        
        return summary_data
    
    def generate_dashboard(self):
        """Generate interactive test dashboard."""
        print("🎨 Generating interactive dashboard...")
        
        try:
            dashboard_html = self.dashboard.generate_dashboard_html(days_back=7)
            dashboard_path = testing_framework_path / "reports" / f"dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            dashboard_path.parent.mkdir(exist_ok=True)
            
            with open(dashboard_path, 'w') as f:
                f.write(dashboard_html)
            
            print(f"📊 Dashboard generated: {dashboard_path}")
            print(f"🌐 Open in browser: file://{dashboard_path.absolute()}")
            
        except Exception as e:
            print(f"⚠️  Dashboard generation failed: {str(e)}")
    
    def list_available_tests(self):
        """List all available tests."""
        print("🧪 Available Tests:")
        print("=" * 30)
        
        for test_id, config in self.test_suite.items():
            print(f"📋 {test_id}")
            print(f"   Name: {config['name']}")
            print(f"   Description: {config['description']}")
            print(f"   Priority: {config['priority']}")
            print(f"   Category: {config['category']}")
            print()
    
    def get_registry_analytics(self):
        """Display registry analytics."""
        print("📈 Test History Analytics:")
        print("=" * 30)
        
        try:
            analytics = self.registry.get_test_analytics(days_back=30)
            
            print(f"📊 Total test runs (30 days): {analytics.get('total_runs', 0)}")
            print(f"✅ Successful runs: {analytics.get('successful_runs', 0)}")
            print(f"❌ Failed runs: {analytics.get('failed_runs', 0)}")
            print(f"📈 Success rate: {analytics.get('success_rate', 0):.1f}%")
            print(f"🎯 Average quality: {analytics.get('avg_quality_score', 0):.1f}/10")
            print()
            
            # Recent failing tests
            failing_tests = self.registry.get_failing_tests_analysis(days_back=7)
            if failing_tests.get('failing_tests'):
                print("⚠️  Recent failing tests:")
                for test in failing_tests['failing_tests']:
                    print(f"   • {test['test_name']} - {test['failure_rate']:.1f}% failure rate")
                print()
                
        except Exception as e:
            print(f"⚠️  Analytics unavailable: {str(e)}")


def main():
    """Main entry point for test runner."""
    runner = MCPlaywrightTestRunner()
    
    if len(sys.argv) == 1:
        # Run all tests
        success = runner.run_all_tests()
        sys.exit(0 if success else 1)
    
    command = sys.argv[1]
    
    if command == "list":
        runner.list_available_tests()
        
    elif command == "analytics":
        runner.get_registry_analytics()
        
    elif command == "dashboard":
        runner.generate_dashboard()
        
    elif command == "run":
        if len(sys.argv) < 3:
            print("Usage: python run_all_tests.py run <test_name|all>")
            sys.exit(1)
        
        test_arg = sys.argv[2]
        if test_arg == "all":
            success = runner.run_all_tests()
        elif test_arg in runner.test_suite:
            success = runner.run_all_tests(test_filter=test_arg)
        else:
            print(f"❌ Unknown test: {test_arg}")
            runner.list_available_tests()
            sys.exit(1)
        
        sys.exit(0 if success else 1)
        
    elif command == "priority":
        if len(sys.argv) < 3:
            print("Usage: python run_all_tests.py priority <high|medium|low>")
            sys.exit(1)
        
        priority = sys.argv[2]
        success = runner.run_all_tests(test_filter={"priority": priority})
        sys.exit(0 if success else 1)
        
    elif command == "category":
        if len(sys.argv) < 3:
            print("Usage: python run_all_tests.py category <category_name>")
            sys.exit(1)
        
        category = sys.argv[2]
        success = runner.run_all_tests(test_filter={"category": category})
        sys.exit(0 if success else 1)
        
    else:
        print("🎭 MCPlaywright Testing Framework - Test Runner")
        print()
        print("Usage:")
        print("  python run_all_tests.py                    # Run all tests")
        print("  python run_all_tests.py list               # List available tests")
        print("  python run_all_tests.py run <test_name>    # Run specific test")
        print("  python run_all_tests.py run all            # Run all tests")
        print("  python run_all_tests.py priority <level>   # Run tests by priority")
        print("  python run_all_tests.py category <cat>     # Run tests by category")
        print("  python run_all_tests.py analytics          # Show test analytics")
        print("  python run_all_tests.py dashboard          # Generate dashboard")
        print()
        print("Examples:")
        print("  python run_all_tests.py run dynamic_tool_visibility")
        print("  python run_all_tests.py priority high")
        print("  python run_all_tests.py category performance")


if __name__ == "__main__":
    main()