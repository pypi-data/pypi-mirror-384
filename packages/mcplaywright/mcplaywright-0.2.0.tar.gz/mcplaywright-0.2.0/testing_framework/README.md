# MCPlaywright Testing Framework 🎭

A comprehensive testing framework designed specifically for **MCPlaywright**'s revolutionary Dynamic Tool Visibility System and browser automation features.

## 🌟 Framework Overview

This testing framework provides specialized tools for validating MCPlaywright's core innovations:
- **Dynamic Tool Visibility System** - Tests the intelligent filtering of 40+ browser tools
- **Smart Video Recording** - Validates viewport matching and intelligent recording modes  
- **HTTP Request Monitoring** - Tests comprehensive network analysis capabilities
- **Quality Metrics & Reporting** - Provides detailed HTML reports with MCPlaywright theming

## 🚀 Key Features

### ✨ Dynamic Tool Visibility Testing
- Validates the middleware system that shows only 5 tools initially, expanding to 31 with sessions, and all 40 with recording
- Tests state transitions: Initial → Session → Recording → Monitoring
- Ensures proper tool filtering based on browser automation context

### 📊 Comprehensive Reporting
- **HTML Reports** with MCPlaywright's signature blue/teal color scheme
- **Syntax Highlighting** for JSON, Python, JavaScript, and browser code
- **Quality Metrics** with MCPlaywright-specific thresholds (95% action success, 8.0 screenshot quality)
- **Interactive Dashboard** with charts, trends, and failure analysis

### 🎯 Quality Assessment
- MCPlaywright-specific quality thresholds and scoring
- Browser action success rate analysis
- Screenshot and video quality assessment
- Network monitoring completeness validation
- Session stability scoring

## 📂 Framework Structure

```
testing_framework/
├── reporters/              # Test reporting system
│   ├── base_reporter.py   # Abstract base reporter
│   └── browser_reporter.py # MCPlaywright browser-specific reporter
├── utilities/              # Core utilities
│   ├── quality_metrics.py # MCPlaywright quality assessment
│   └── syntax_highlighter.py # Code highlighting for reports
├── fixtures/               # Test data and scenarios
│   ├── browser_fixtures.py   # Dynamic Tool Visibility scenarios
│   ├── video_fixtures.py    # Smart video recording scenarios
│   └── network_fixtures.py  # HTTP monitoring scenarios
├── registry/               # Test management system
│   ├── report_registry.py  # SQLite-based report storage
│   └── dashboard.py        # Web dashboard for analytics
└── examples/               # Example test implementations
    └── test_dynamic_tool_visibility.py # Core feature test
```

## 🎭 MCPlaywright-Specific Features

### Dynamic Tool Visibility System
The framework's flagship test validates MCPlaywright's revolutionary middleware:

```python
# Expected tool visibility transitions:
# Initial state: 5 tools visible (configure, list_sessions, start_recording, etc.)
# Session active: 31 tools visible (all browser interaction tools enabled)
# Recording active: 40 tools visible (recording controls enabled)
# Monitoring active: 40 tools remain visible (monitoring tools active)
```

### Quality Thresholds
Tailored specifically for MCPlaywright browser automation:

```python
MCPLAYWRIGHT_THRESHOLDS = {
    'action_success_rate': 95.0,      # 95% minimum browser action success
    'screenshot_quality': 8.0,        # 8/10 minimum screenshot quality
    'video_quality': 7.5,             # 7.5/10 minimum video quality
    'network_completeness': 90.0,     # 90% HTTP request capture rate
    'response_time': 3000,            # 3 seconds max browser response
    'session_stability': 8.0,         # 8/10 minimum session reliability
}
```

### Smart Video Recording Validation
Tests MCPlaywright's intelligent video recording features:
- **Viewport Matching** - Ensures browser viewport matches recording dimensions
- **Smart Mode** - Validates auto-pause on waits, auto-resume on actions
- **Quality Assessment** - Analyzes recording quality and efficiency

## 🔧 Usage Examples

### Basic Test Execution
```python
from examples.test_dynamic_tool_visibility import TestDynamicToolVisibility

# Run the flagship Dynamic Tool Visibility test
test = TestDynamicToolVisibility()
result = test.run_complete_test()

if result["success"]:
    print(f"✅ Test Passed - Quality Score: {result['quality_score']:.1f}/10")
```

### Reporting and Analytics
```python
from reporters.browser_reporter import BrowserTestReporter
from registry.report_registry import ReportRegistry
from registry.dashboard import TestDashboard

# Create comprehensive test report
reporter = BrowserTestReporter("my_mcplaywright_test")
reporter.log_browser_action("navigate", None, {"success": True, "url": "https://playwright.dev"})
reporter.log_screenshot("homepage", "/path/to/screenshot.png", quality_score=8.5)

# Generate HTML report with MCPlaywright styling
html_report = reporter.generate_html_report()

# Store in registry and generate dashboard
registry = ReportRegistry("mcplaywright_tests.db")
report_id = registry.register_report(reporter.get_test_data())

dashboard = TestDashboard(registry)
dashboard.save_dashboard("mcplaywright_dashboard.html", days_back=7)
```

### Quality Metrics Analysis
```python
from utilities.quality_metrics import QualityMetrics

metrics = QualityMetrics()
quality_report = metrics.generate_quality_report(test_data)

print(f"Overall Quality: {quality_report['overall_score']:.1f}/10")
print(f"Assessment: {quality_report['assessment']['description']}")
```

## 📊 Dashboard Features

The interactive web dashboard provides:
- **Real-time Test Overview** with success rates and quality scores
- **Daily Trend Charts** showing test execution patterns
- **Test Type Breakdown** with MCPlaywright-specific categories
- **Quality Metrics Analysis** with pass/fail rates by metric
- **Failure Analysis** identifying common issues and patterns
- **Recent Test Reports** with drill-down capabilities

## 🎯 Specialized Test Scenarios

### Dynamic Tool Visibility Test
Validates the core innovation of MCPlaywright - intelligent tool filtering:
- ✅ Initial state shows only 5 essential tools
- ✅ Session creation enables 31 browser interaction tools
- ✅ Recording activation shows all 40 tools
- ✅ State transitions work correctly without tool count regression

### Smart Video Recording Test  
Tests MCPlaywright's advanced video capabilities:
- ✅ Viewport matching prevents gray borders
- ✅ Smart mode auto-pauses during waits
- ✅ Quality assessment meets MCPlaywright standards
- ✅ Multiple recording modes work correctly

### HTTP Monitoring Test
Validates comprehensive network analysis:
- ✅ Request capture completeness above 90%
- ✅ Performance metrics within thresholds
- ✅ Security analysis for HTTPS compliance
- ✅ API testing and validation capabilities

## 🏆 Quality Standards

This framework maintains MCPlaywright's high quality standards:
- **A+ Grade (9.0+)**: Excellent - Ready for production
- **A Grade (8.0+)**: Very Good - Minor improvements possible
- **B Grade (7.0+)**: Good - Acceptable with room for improvement
- **C Grade (6.0+)**: Fair - Needs improvement before production

## 🚀 Getting Started

1. **Run the Dynamic Tool Visibility test** to validate core MCPlaywright functionality
2. **Generate HTML reports** to see detailed test results with MCPlaywright styling
3. **Use the dashboard** to track test trends and identify issues
4. **Customize fixtures** for your specific MCPlaywright testing needs

## 🎭 About MCPlaywright

MCPlaywright revolutionizes browser automation testing through its **Dynamic Tool Visibility System**, transforming the overwhelming experience of 40+ tools into an intelligent, context-aware interface that shows exactly what you need, when you need it.

This testing framework ensures that revolutionary feature works flawlessly across all browser automation scenarios.