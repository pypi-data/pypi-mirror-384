# Debug Toolbar Usage Examples 🎭

## Overview

This document provides practical examples of using MCPlaywright's debug toolbar system for various development and testing scenarios. The debug toolbar system provides Django-style visual debugging capabilities that are particularly valuable for multi-developer environments.

## 🎯 **Quick Start Examples**

### Basic Debug Toolbar Setup

```python
# Enable basic debug toolbar
await browser_enable_debug_toolbar({
    "project_name": "My Project",
    "theme": "dark",
    "position": "bottom-right"
})

# Navigate to a page and the toolbar will appear
await browser_navigate({"url": "https://example.com"})

# The toolbar shows:
# 🟢 My Project                    ▼
# ─────────────────────────────────
# Session: mcp_20250117_143027
# Client: Python MCPlaywright
# Time: 14:30:27
# Injections: 1
```

### Multi-Developer Team Setup

```python
# Developer Alice working on authentication features
await browser_enable_debug_toolbar({
    "project_name": "Alice-Auth-Testing",
    "theme": "dark",
    "position": "bottom-left",
    "opacity": 0.8
})

# Developer Bob working on payment processing
await browser_enable_debug_toolbar({
    "project_name": "Bob-Payment-Testing", 
    "theme": "light",
    "position": "bottom-right",
    "opacity": 0.9
})

# QA Team automated testing
await browser_enable_debug_toolbar({
    "project_name": "QA-Automated-Tests",
    "theme": "dark",
    "position": "top-right",
    "minimized": True  # Start minimized for clean screenshots
})
```

## 🧪 **Testing Environment Examples**

### Test Environment Visual Indicators

```python
# Add prominent test environment indicator
await browser_inject_custom_code({
    "name": "test_environment_banner",
    "code": """
        body::before { 
            content: '⚠️ TEST ENVIRONMENT - NOT PRODUCTION ⚠️'; 
            position: fixed; 
            top: 0; 
            left: 0; 
            right: 0;
            background: linear-gradient(45deg, #ff6b35, #f7931e); 
            color: white; 
            text-align: center;
            padding: 10px; 
            font-size: 16px;
            font-weight: bold;
            z-index: 999998;
            font-family: 'Arial', sans-serif;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }
        
        body { margin-top: 50px !important; }
    """,
    "type": "css",
    "auto_inject": True
})

# Add debug toolbar for the testing team
await browser_enable_debug_toolbar({
    "project_name": "E2E-Testing-Suite",
    "position": "bottom-right",
    "theme": "dark"
})
```

### Staging vs Production Identification

```python
# Staging environment setup
await browser_inject_custom_code({
    "name": "staging_indicator", 
    "code": """
        const indicator = document.createElement('div');
        indicator.innerHTML = '🚧 STAGING';
        indicator.style.cssText = `
            position: fixed;
            top: 10px;
            right: 10px;
            background: #ffa500;
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            font-family: monospace;
            font-weight: bold;
            z-index: 999999;
            font-size: 12px;
        `;
        document.body.appendChild(indicator);
    """,
    "type": "javascript",
    "auto_inject": True
})

await browser_enable_debug_toolbar({
    "project_name": "Staging-Validation",
    "theme": "light",
    "position": "bottom-left"
})
```

## 🔧 **Development & Debugging Examples**

### Performance Monitoring Injection

```python
# Add comprehensive performance monitoring
await browser_inject_custom_code({
    "name": "performance_suite",
    "code": """
        // Global performance monitoring suite
        window.PERF = {
            startTime: performance.now(),
            marks: {},
            
            // Mark a performance point
            mark: (name) => {
                const time = performance.now();
                window.PERF.marks[name] = {
                    time: time,
                    elapsed: time - window.PERF.startTime
                };
                console.log(`⏱️ PERF MARK [${name}]: ${time.toFixed(2)}ms (${(time - window.PERF.startTime).toFixed(2)}ms elapsed)`);
                return time;
            },
            
            // Get elapsed time
            elapsed: () => performance.now() - window.PERF.startTime,
            
            // Log all marks
            report: () => {
                console.table(window.PERF.marks);
                return window.PERF.marks;
            },
            
            // Memory usage (if available)
            memory: () => {
                if (performance.memory) {
                    return {
                        used: (performance.memory.usedJSHeapSize / 1048576).toFixed(2) + ' MB',
                        total: (performance.memory.totalJSHeapSize / 1048576).toFixed(2) + ' MB',
                        limit: (performance.memory.jsHeapSizeLimit / 1048576).toFixed(2) + ' MB'
                    };
                }
                return 'Memory API not available';
            }
        };
        
        // Auto-mark key events
        document.addEventListener('DOMContentLoaded', () => window.PERF.mark('DOMContentLoaded'));
        window.addEventListener('load', () => window.PERF.mark('WindowLoad'));
        
        console.log('🚀 Performance suite loaded. Use window.PERF for monitoring.');
    """,
    "type": "javascript", 
    "auto_inject": True
})

# Enable debug toolbar for performance testing
await browser_enable_debug_toolbar({
    "project_name": "Performance-Testing",
    "theme": "dark",
    "position": "top-left"
})
```

### Form Debugging Utilities

```python
# Add form debugging and validation utilities
await browser_inject_custom_code({
    "name": "form_debugger",
    "code": """
        window.FORMS = {
            // Highlight all form fields
            highlight: () => {
                const fields = document.querySelectorAll('input, textarea, select');
                fields.forEach(field => {
                    field.style.outline = '2px solid #00ff00';
                    field.addEventListener('focus', () => {
                        console.log('Field focused:', field.name || field.id, field);
                    });
                });
                return fields.length;
            },
            
            // Get all form data
            getData: () => {
                const forms = document.querySelectorAll('form');
                return Array.from(forms).map(form => ({
                    action: form.action,
                    method: form.method,
                    data: new FormData(form),
                    fields: Array.from(form.elements).map(el => ({
                        name: el.name,
                        type: el.type,
                        value: el.value,
                        required: el.required,
                        valid: el.checkValidity()
                    }))
                }));
            },
            
            // Validate all forms
            validate: () => {
                const forms = document.querySelectorAll('form');
                const results = [];
                forms.forEach(form => {
                    const isValid = form.checkValidity();
                    results.push({
                        form: form,
                        valid: isValid,
                        invalidFields: Array.from(form.elements).filter(el => !el.checkValidity())
                    });
                    
                    if (!isValid) {
                        console.warn('Invalid form detected:', form);
                    }
                });
                return results;
            }
        };
        
        console.log('📝 Form debugger loaded. Use window.FORMS for form utilities.');
    """,
    "type": "javascript",
    "auto_inject": True
})
```

### API Request Monitoring

```python
# Inject API request monitoring (works alongside MCPlaywright's request monitoring)
await browser_inject_custom_code({
    "name": "api_monitor",
    "code": """
        // Override fetch to monitor API calls
        const originalFetch = window.fetch;
        window.API_CALLS = [];
        
        window.fetch = function(...args) {
            const startTime = performance.now();
            const url = args[0];
            const options = args[1] || {};
            
            console.log(`🌐 API CALL: ${options.method || 'GET'} ${url}`);
            
            return originalFetch.apply(this, args)
                .then(response => {
                    const endTime = performance.now();
                    const duration = endTime - startTime;
                    
                    const callInfo = {
                        url: url,
                        method: options.method || 'GET',
                        status: response.status,
                        duration: duration.toFixed(2) + 'ms',
                        timestamp: new Date().toISOString()
                    };
                    
                    window.API_CALLS.push(callInfo);
                    
                    console.log(`✅ API RESPONSE: ${response.status} ${url} (${duration.toFixed(2)}ms)`);
                    
                    return response;
                })
                .catch(error => {
                    const endTime = performance.now();
                    const duration = endTime - startTime;
                    
                    console.error(`❌ API ERROR: ${url} (${duration.toFixed(2)}ms)`, error);
                    
                    throw error;
                });
        };
        
        // Utility to view API calls
        window.getAPICalls = () => {
            console.table(window.API_CALLS);
            return window.API_CALLS;
        };
        
        console.log('🔍 API monitor loaded. Use window.getAPICalls() to view calls.');
    """,
    "type": "javascript",
    "auto_inject": True
})
```

## 🎥 **Recording & Demo Examples**

### Demo Recording Setup

```python
# Setup for clean demo recording
await browser_enable_debug_toolbar({
    "project_name": "Product-Demo",
    "theme": "light",
    "position": "top-right",
    "opacity": 0.7,
    "minimized": True  # Start minimized for clean recording
})

# Add subtle branding for demo
await browser_inject_custom_code({
    "name": "demo_branding",
    "code": """
        body::after { 
            content: 'Demo Environment'; 
            position: fixed; 
            bottom: 10px; 
            left: 10px; 
            background: rgba(0,0,0,0.7); 
            color: white; 
            padding: 4px 8px; 
            border-radius: 3px;
            font-size: 11px;
            font-family: sans-serif;
            z-index: 999999; 
            opacity: 0.6;
        }
    """,
    "type": "css",
    "auto_inject": True
})
```

### Training Video Setup

```python
# Setup for training video with helpful indicators
await browser_enable_debug_toolbar({
    "project_name": "Training-Video",
    "theme": "dark",
    "position": "bottom-right",
    "show_details": True
})

# Add step indicators for training
await browser_inject_custom_code({
    "name": "training_steps",
    "code": """
        window.TRAINING = {
            currentStep: 0,
            steps: [],
            
            addStep: (description) => {
                window.TRAINING.steps.push(description);
                return window.TRAINING.steps.length;
            },
            
            showStep: (stepNumber, description) => {
                // Remove existing step indicator
                const existing = document.getElementById('training-step');
                if (existing) existing.remove();
                
                // Create new step indicator
                const indicator = document.createElement('div');
                indicator.id = 'training-step';
                indicator.innerHTML = `Step ${stepNumber}: ${description}`;
                indicator.style.cssText = `
                    position: fixed;
                    top: 60px;
                    left: 50%;
                    transform: translateX(-50%);
                    background: rgba(76, 175, 80, 0.9);
                    color: white;
                    padding: 12px 20px;
                    border-radius: 6px;
                    font-family: Arial, sans-serif;
                    font-size: 14px;
                    font-weight: bold;
                    z-index: 999999;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.3);
                    animation: slideIn 0.3s ease-out;
                `;
                
                // Add CSS animation
                if (!document.getElementById('training-styles')) {
                    const styles = document.createElement('style');
                    styles.id = 'training-styles';
                    styles.textContent = `
                        @keyframes slideIn {
                            from { opacity: 0; transform: translateX(-50%) translateY(-20px); }
                            to { opacity: 1; transform: translateX(-50%) translateY(0); }
                        }
                    `;
                    document.head.appendChild(styles);
                }
                
                document.body.appendChild(indicator);
                window.TRAINING.currentStep = stepNumber;
                
                console.log(`📚 Training Step ${stepNumber}: ${description}`);
            },
            
            hideStep: () => {
                const existing = document.getElementById('training-step');
                if (existing) existing.remove();
            }
        };
        
        console.log('📚 Training utilities loaded. Use window.TRAINING for step management.');
    """,
    "type": "javascript",
    "auto_inject": True
})
```

## 🔧 **Advanced Usage Examples**

### CI/CD Integration

```python
# CI/CD pipeline setup with automated reporting
await browser_enable_debug_toolbar({
    "project_name": f"CI-Build-{os.getenv('BUILD_NUMBER', 'local')}",
    "theme": "dark",
    "position": "top-left",
    "minimized": True
})

# Add CI-specific monitoring
await browser_inject_custom_code({
    "name": "ci_monitoring",
    "code": f"""
        window.CI_MONITOR = {{
            buildNumber: '{os.getenv("BUILD_NUMBER", "local")}',
            branch: '{os.getenv("GIT_BRANCH", "unknown")}',
            errors: [],
            warnings: [],
            
            logError: (message, details = {{}}) => {{
                const error = {{
                    message,
                    details,
                    timestamp: new Date().toISOString(),
                    url: window.location.href
                }};
                window.CI_MONITOR.errors.push(error);
                console.error('CI ERROR:', error);
            }},
            
            logWarning: (message, details = {{}}) => {{
                const warning = {{
                    message,
                    details,
                    timestamp: new Date().toISOString(),
                    url: window.location.href
                }};
                window.CI_MONITOR.warnings.push(warning);
                console.warn('CI WARNING:', warning);
            }},
            
            getReport: () => {{
                return {{
                    buildNumber: window.CI_MONITOR.buildNumber,
                    branch: window.CI_MONITOR.branch,
                    errors: window.CI_MONITOR.errors,
                    warnings: window.CI_MONITOR.warnings,
                    errorCount: window.CI_MONITOR.errors.length,
                    warningCount: window.CI_MONITOR.warnings.length
                }};
            }}
        }};
        
        // Auto-capture console errors
        window.addEventListener('error', (event) => {{
            window.CI_MONITOR.logError('JavaScript Error', {{
                message: event.message,
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno
            }});
        }});
        
        console.log('🤖 CI monitoring loaded for build {os.getenv("BUILD_NUMBER", "local")}');
    """,
    "type": "javascript",
    "auto_inject": True
})
```

### Custom Theme Example

```python
# Custom corporate theme
await browser_inject_custom_code({
    "name": "corporate_theme",
    "code": """
        /* Custom debug toolbar styling */
        #mcp-debug-toolbar {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            border: 2px solid #4a5568 !important;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
        }
        
        #mcp-debug-toolbar strong {
            color: #ffffff !important;
        }
        
        /* Add company logo */
        #mcp-debug-toolbar::before {
            content: '🏢';
            margin-right: 8px;
        }
    """,
    "type": "css",
    "auto_inject": True
})

await browser_enable_debug_toolbar({
    "project_name": "Corporate-Testing",
    "theme": "dark", 
    "position": "bottom-right"
})
```

## 🧹 **Cleanup Examples**

### Session Cleanup

```python
# List all active injections
injections = await browser_list_injections()
print(f"Active injections: {injections['injection_count']}")

# Clear specific injections but keep toolbar
await browser_clear_injections({"include_toolbar": False})

# Or disable everything including toolbar
await browser_disable_debug_toolbar()
await browser_clear_injections({"include_toolbar": True})
```

### Conditional Cleanup

```python
# Clean up based on environment
if os.getenv("ENVIRONMENT") == "production":
    # Never leave debug code in production
    await browser_disable_debug_toolbar()
    await browser_clear_injections({"include_toolbar": True})
else:
    # Keep debug features in development/staging
    print("Debug toolbar remains active in non-production environment")
```

## 🎯 **Best Practices**

### 1. Environment-Specific Configuration

```python
def get_debug_config():
    env = os.getenv("ENVIRONMENT", "development")
    
    if env == "production":
        return None  # No debug toolbar in production
    elif env == "staging":
        return {
            "project_name": f"Staging-{os.getenv('USER', 'unknown')}",
            "theme": "light",
            "position": "top-right",
            "opacity": 0.7
        }
    else:  # development
        return {
            "project_name": f"Dev-{os.getenv('USER', 'developer')}",
            "theme": "dark", 
            "position": "bottom-right",
            "opacity": 0.9
        }

# Apply environment-specific configuration
debug_config = get_debug_config()
if debug_config:
    await browser_enable_debug_toolbar(debug_config)
```

### 2. Team Coordination

```python
# Use consistent naming conventions for team identification
team_configs = {
    "frontend": {
        "project_name": "Frontend-Team",
        "theme": "light",
        "position": "bottom-left"
    },
    "backend": {
        "project_name": "Backend-Team", 
        "theme": "dark",
        "position": "bottom-right"
    },
    "qa": {
        "project_name": "QA-Testing",
        "theme": "dark",
        "position": "top-right",
        "minimized": True
    }
}

# Team member uses their team configuration
team = os.getenv("TEAM", "frontend")
await browser_enable_debug_toolbar(team_configs.get(team, team_configs["frontend"]))
```

### 3. Performance Considerations

```python
# Lightweight debug setup for performance testing
await browser_enable_debug_toolbar({
    "project_name": "Perf-Test",
    "theme": "dark",
    "position": "top-left",
    "minimized": True,  # Minimized to reduce visual impact
    "opacity": 0.5      # Low opacity
})

# Only inject essential monitoring code
await browser_inject_custom_code({
    "name": "minimal_perf_monitor",
    "code": "window.perfStart = performance.now();",
    "type": "javascript",
    "auto_inject": True
})
```

The debug toolbar system provides a powerful foundation for team coordination, debugging, and testing workflows. These examples demonstrate how to leverage its capabilities for various development scenarios while maintaining clean, professional automation practices.