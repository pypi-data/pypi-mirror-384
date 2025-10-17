# Professional Theme System

⚠️ **IN HEAVY DEVELOPMENT - FEATURES MAY CHANGE** ⚠️

**5 Built-in Professional Themes with WCAG Accessibility Compliance**

## Overview

MCPlaywright features a comprehensive professional theme system that provides visual consistency, accessibility compliance, and brand customization capabilities. The system includes 5 carefully designed built-in themes and supports custom theme creation with 47 CSS custom properties.

## Built-in Themes

### 1. Minimal Theme (Default)
**Clean, distraction-free design with maximum readability**

- **Primary Color**: `#3b82f6` (Blue 500)
- **Background**: `#ffffff` (Pure White)
- **Text Color**: `#1f2937` (Gray 800)
- **Contrast Ratio**: 12.6:1 (AAA compliant)
- **Use Case**: Professional documentation, technical interfaces

```python
await browser_mcp_theme_set({"theme_id": "minimal"})
```

### 2. Corporate Theme
**Professional business environment styling**

- **Primary Color**: `#1e40af` (Blue 800)
- **Secondary Color**: `#64748b` (Slate 500)
- **Background**: `#f8fafc` (Slate 50)
- **Text Color**: `#0f172a` (Slate 900)
- **Contrast Ratio**: 18.7:1 (AAA compliant)
- **Use Case**: Enterprise applications, business dashboards

```python
await browser_mcp_theme_set({"theme_id": "corporate"})
```

### 3. Hacker Theme
**Dark cyberpunk aesthetic for technical professionals**

- **Primary Color**: `#00ff88` (Neon Green)
- **Secondary Color**: `#ff0088` (Neon Pink)
- **Background**: `#0a0a0a` (Near Black)
- **Text Color**: `#00ff88` (Matrix Green)
- **Contrast Ratio**: 12.1:1 (AAA compliant)
- **Use Case**: Security testing, penetration testing, developer tools

```python
await browser_mcp_theme_set({"theme_id": "hacker"})
```

### 4. Glassmorphism Theme
**Modern translucent design with depth and sophistication**

- **Primary Color**: `#6366f1` (Indigo 500)
- **Background**: `rgba(255, 255, 255, 0.1)` (Translucent)
- **Backdrop Filter**: `blur(10px)` (Glass effect)
- **Border**: `1px solid rgba(255, 255, 255, 0.2)`
- **Contrast Ratio**: 8.2:1 (AA compliant)
- **Use Case**: Modern web applications, creative tools

```python
await browser_mcp_theme_set({"theme_id": "glassmorphism"})
```

### 5. High Contrast Theme
**Maximum accessibility for users with visual impairments**

- **Primary Color**: `#000000` (Pure Black)
- **Background**: `#ffffff` (Pure White)
- **Text Color**: `#000000` (Pure Black)
- **Contrast Ratio**: 21:1 (AAA+ maximum)
- **Use Case**: Accessibility compliance, visual impairments

```python
await browser_mcp_theme_set({"theme_id": "high-contrast"})
```

## CSS Custom Properties

### Complete Variable System (47 Properties)

#### Color System
```css
--mcp-primary-color: #3b82f6;
--mcp-primary-hover: #2563eb;
--mcp-primary-active: #1d4ed8;
--mcp-secondary-color: #64748b;
--mcp-secondary-hover: #475569;
--mcp-accent-color: #f59e0b;
--mcp-accent-hover: #d97706;
```

#### Background & Surface Colors
```css
--mcp-background-color: #ffffff;
--mcp-surface-color: #f8fafc;
--mcp-surface-hover: #f1f5f9;
--mcp-overlay-color: rgba(15, 23, 42, 0.8);
--mcp-modal-background: #ffffff;
```

#### Text & Content Colors
```css
--mcp-text-color: #1f2937;
--mcp-text-secondary: #6b7280;
--mcp-text-muted: #9ca3af;
--mcp-text-inverse: #ffffff;
--mcp-link-color: #3b82f6;
--mcp-link-hover: #2563eb;
```

#### Status & Semantic Colors
```css
--mcp-success-color: #10b981;
--mcp-warning-color: #f59e0b;
--mcp-error-color: #ef4444;
--mcp-info-color: #3b82f6;
```

#### Border & Structural Elements
```css
--mcp-border-color: #e5e7eb;
--mcp-border-hover: #d1d5db;
--mcp-border-focus: #3b82f6;
--mcp-divider-color: #f3f4f6;
```

#### Spacing & Layout
```css
--mcp-spacing-xs: 0.25rem;
--mcp-spacing-sm: 0.5rem;
--mcp-spacing-md: 1rem;
--mcp-spacing-lg: 1.5rem;
--mcp-spacing-xl: 2rem;
```

#### Typography
```css
--mcp-font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
--mcp-font-mono: 'SF Mono', Monaco, 'Cascadia Code', monospace;
--mcp-font-size-xs: 0.75rem;
--mcp-font-size-sm: 0.875rem;
--mcp-font-size-base: 1rem;
--mcp-font-size-lg: 1.125rem;
--mcp-font-size-xl: 1.25rem;
--mcp-line-height-tight: 1.25;
--mcp-line-height-normal: 1.5;
--mcp-line-height-relaxed: 1.75;
```

#### Visual Effects
```css
--mcp-border-radius: 0.375rem;
--mcp-border-radius-sm: 0.25rem;
--mcp-border-radius-lg: 0.5rem;
--mcp-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
--mcp-shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
--mcp-shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
--mcp-transition: all 0.15s ease-in-out;
--mcp-animation-duration: 0.3s;
```

## API Reference

### Theme Management

#### List Available Themes
```python
themes = await browser_mcp_theme_list({
    "filter": "all",  # all, builtin, custom
    "include_details": True
})

# Response:
{
    "themes": [
        {
            "id": "minimal",
            "name": "Minimal Theme",
            "category": "builtin",
            "description": "Clean, distraction-free design",
            "accessibility": {"contrast_ratio": 12.6, "wcag_level": "AAA"},
            "variables": {...}
        }
    ]
}
```

#### Apply Theme
```python
await browser_mcp_theme_set({
    "theme_id": "corporate",
    "persist": True  # Save preference for future sessions
})
```

#### Get Current Theme
```python
current_theme = await browser_mcp_theme_get({
    "include_variables": True
})

# Response:
{
    "active_theme": "corporate",
    "variables": {...},
    "accessibility": {"contrast_ratio": 18.7, "wcag_level": "AAA"}
}
```

#### Reset to Default
```python
await browser_mcp_theme_reset({
    "clear_storage": True  # Clear stored preferences
})
```

### Custom Theme Creation

#### Create Custom Theme
```python
await browser_mcp_theme_create({
    "id": "company-brand",
    "name": "Company Brand Theme",
    "description": "Corporate brand colors with high accessibility",
    "base_theme": "corporate",  # Extend existing theme
    "variables": {
        "--mcp-primary-color": "#2563eb",
        "--mcp-secondary-color": "#64748b",
        "--mcp-accent-color": "#f59e0b",
        "--mcp-background-color": "#ffffff",
        "--mcp-text-color": "#1e293b",
        "--mcp-border-radius": "8px",
        "--mcp-shadow": "0 4px 6px -1px rgba(0, 0, 0, 0.1)"
    }
})
```

## Accessibility Compliance

### WCAG Standards

#### Contrast Ratio Compliance
- **Minimal**: 12.6:1 (AAA)
- **Corporate**: 18.7:1 (AAA)
- **Hacker**: 12.1:1 (AAA)
- **Glassmorphism**: 8.2:1 (AA)
- **High Contrast**: 21:1 (AAA+)

#### Accessibility Features
- **Screen Reader Support**: Semantic HTML and ARIA attributes
- **Keyboard Navigation**: Full keyboard accessibility
- **Focus Indicators**: Clear focus outlines and states
- **Color Independence**: Information not conveyed by color alone
- **Scalable Text**: Responsive typography that scales properly

### Testing Tools Integration
```python
# Automatic accessibility testing
accessibility_report = await browser_analyze_accessibility({
    "theme_id": "current",
    "include_contrast": True,
    "wcag_level": "AAA"
})

# Response:
{
    "theme": "corporate",
    "wcag_compliance": "AAA",
    "contrast_ratios": {
        "primary_text": 18.7,
        "secondary_text": 12.3,
        "link_text": 15.2
    },
    "issues": [],
    "recommendations": []
}
```

## Advanced Customization

### Dynamic Theme Variables
```python
# Runtime theme modification
await browser_modify_theme_variables({
    "variables": {
        "--mcp-primary-color": "#8b5cf6",  # Purple
        "--mcp-border-radius": "12px"      # Rounded
    },
    "temporary": True  # Don't persist changes
})
```

### Theme Inheritance
```python
# Create theme based on existing theme
await browser_mcp_theme_create({
    "id": "dark-corporate",
    "name": "Dark Corporate Theme",
    "base_theme": "corporate",
    "variables": {
        "--mcp-background-color": "#1f2937",
        "--mcp-text-color": "#f9fafb",
        "--mcp-surface-color": "#374151"
    }
})
```

### Conditional Theme Application
```python
# Apply theme based on conditions
await browser_apply_conditional_theme({
    "conditions": {
        "time_of_day": "night",
        "user_preference": "dark_mode"
    },
    "theme_mapping": {
        "day": "minimal",
        "night": "hacker"
    }
})
```

## Integration Examples

### E-commerce Branding
```python
# Apply brand theme for e-commerce testing
await browser_mcp_theme_create({
    "id": "ecommerce-brand",
    "name": "E-commerce Brand Theme",
    "base_theme": "minimal",
    "variables": {
        "--mcp-primary-color": "#059669",    # Brand green
        "--mcp-accent-color": "#dc2626",     # Sale red
        "--mcp-secondary-color": "#6b7280",  # Neutral gray
        "--mcp-success-color": "#10b981",    # Purchase success
        "--mcp-warning-color": "#f59e0b"     # Stock warning
    }
})

await browser_mcp_theme_set({"theme_id": "ecommerce-brand"})
```

### Accessibility Testing
```python
# High contrast theme for accessibility testing
await browser_mcp_theme_set({"theme_id": "high-contrast"})

# Test form visibility with high contrast
await browser_navigate({"url": "https://example.com/form"})
await browser_take_screenshot({"filename": "high-contrast-form.png"})

# Generate accessibility report
report = await browser_analyze_accessibility({
    "include_contrast": True,
    "wcag_level": "AAA"
})
```

### Security Testing UI
```python
# Apply hacker theme for penetration testing
await browser_mcp_theme_set({"theme_id": "hacker"})

# Create custom security testing theme
await browser_mcp_theme_create({
    "id": "security-testing",
    "name": "Security Testing Theme",
    "base_theme": "hacker",
    "variables": {
        "--mcp-warning-color": "#ff0000",    # Critical vulnerabilities
        "--mcp-info-color": "#ffff00",       # Information disclosure
        "--mcp-success-color": "#00ff00"     # Secure endpoints
    }
})
```

## Performance Considerations

### Optimized CSS Generation
- **Minimal Output**: Only necessary CSS variables included
- **Caching**: Theme definitions cached for performance
- **Lazy Loading**: Themes loaded only when applied
- **Tree Shaking**: Unused theme variables excluded

### Memory Management
- **Cleanup**: Automatic cleanup of unused theme data
- **Storage**: Efficient storage of theme preferences
- **Synchronization**: Real-time theme updates across components

## Browser Compatibility

### Supported Features
- **CSS Custom Properties**: Full support in modern browsers
- **Graceful Degradation**: Fallback values for older browsers
- **Feature Detection**: Automatic detection of CSS capabilities

### Cross-Browser Testing
```python
# Test theme across multiple browsers
browsers = ["chromium", "firefox", "webkit"]

for browser in browsers:
    await browser_configure({"browser_type": browser})
    await browser_mcp_theme_set({"theme_id": "corporate"})
    await browser_take_screenshot({
        "filename": f"theme-{browser}.png"
    })
```

The Professional Theme System provides a comprehensive foundation for visual consistency, accessibility compliance, and brand customization in browser automation workflows.