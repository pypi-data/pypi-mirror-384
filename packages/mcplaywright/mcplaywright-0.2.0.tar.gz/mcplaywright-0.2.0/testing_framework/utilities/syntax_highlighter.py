#!/usr/bin/env python3
"""
Syntax highlighting utilities for MCPlaywright test reports.

Provides automatic detection and HTML formatting for JSON, Python, JavaScript,
and other code types with beautiful color-coded syntax elements optimized
for browser automation testing.
"""

import html
import json
import re
from typing import Any, Union


class SyntaxHighlighter:
    """
    Automatic syntax highlighting for various data types and languages.
    
    Optimized for MCPlaywright browser automation testing with support for:
    - JSON data structures (API responses, test data)
    - Python code (test scripts, browser automation)
    - JavaScript code (browser evaluation, frontend code)
    - Browser action logs and results
    - Network request/response data
    """
    
    def __init__(self):
        self.python_keywords = r'\b(def|class|import|from|if|else|elif|for|while|try|except|finally|with|as|return|yield|lambda|and|or|not|in|is|True|False|None|async|await)\b'
        self.javascript_keywords = r'\b(function|const|let|var|if|else|for|while|return|async|await|try|catch|finally|class|extends|import|export|default)\b'
        self.code_indicators = [
            'def ', 'class ', 'import ', 'from ', '#!/usr/bin',  # Python
            'function ', 'const ', 'let ', 'var ', '=>',         # JavaScript
            'browser.', 'page.', 'await ', 'async ',             # Browser automation
            'click(', 'navigate(', 'screenshot(', 'evaluate('    # MCPlaywright methods
        ]
    
    def auto_format_value(self, value: Any) -> str:
        """Automatically detect type and format with appropriate highlighting."""
        if isinstance(value, dict) or isinstance(value, list):
            return self.format_json_html(value)
        elif isinstance(value, str):
            if self._looks_like_json(value):
                try:
                    parsed = json.loads(value)
                    return self.format_json_html(parsed)
                except json.JSONDecodeError:
                    pass
            elif self._looks_like_browser_code(value):
                return self.format_browser_code_html(value)
            elif self._looks_like_code(value):
                return self.format_code_html(value)
            else:
                return self.format_text_html(value)
        elif isinstance(value, (int, float, bool)):
            return self.format_simple_value_html(value)
        else:
            return self.format_json_html(value)
    
    def format_json_html(self, data: Any, max_depth: int = 5) -> str:
        """Format JSON data with HTML syntax highlighting optimized for test reports."""
        try:
            if isinstance(data, str):
                try:
                    parsed = json.loads(data)
                    formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
                except:
                    return self.format_text_html(data)
            else:
                formatted = json.dumps(data, indent=2, ensure_ascii=False, default=str)
            
            # Escape HTML first
            formatted = html.escape(formatted)
            
            # Apply JSON syntax highlighting with MCPlaywright color scheme
            formatted = re.sub(r'"([^"]*)"(?=\s*:)', r'<span class="json-key">"\1"</span>', formatted)
            formatted = re.sub(r'"([^"]*)"(?!\s*:)', r'<span class="json-string">"\1"</span>', formatted)
            formatted = formatted.replace('{', '<span class="json-brace">{</span>')
            formatted = formatted.replace('}', '<span class="json-brace">}</span>')
            formatted = formatted.replace('[', '<span class="json-bracket">[</span>')
            formatted = formatted.replace(']', '<span class="json-bracket">]</span>')
            formatted = formatted.replace(':', '<span class="json-colon">:</span>')
            formatted = formatted.replace(',', '<span class="json-comma">,</span>')
            
            # Highlight values with context-aware colors
            formatted = re.sub(r'\b(\d+\.?\d*)\b', r'<span class="json-number">\1</span>', formatted)
            formatted = re.sub(r'\b(true|false|null)\b', r'<span class="json-boolean">\1</span>', formatted)
            
            # Special highlighting for common browser automation fields
            formatted = re.sub(r'(<span class="json-key">"(url|selector|action|status|method|response)"</span>)', 
                             r'<span class="browser-field">\1</span>', formatted)
            
            return f'<pre class="json-block">{formatted}</pre>'
            
        except Exception as e:
            return f'<pre class="error-block">Error formatting JSON: {html.escape(str(e))}</pre>'
    
    def format_browser_code_html(self, code: str) -> str:
        """Format browser automation code with specialized highlighting."""
        escaped = html.escape(code)
        
        # Browser automation method highlighting
        browser_methods = r'\b(navigate|click|type|screenshot|evaluate|waitFor|select|hover|drag|scroll|reload|goBack|goForward)\b'
        escaped = re.sub(browser_methods, r'<span class="browser-method">\1</span>', escaped)
        
        # Selector highlighting
        escaped = re.sub(r'["\']([^"\']*(?:#|\.|\[)[^"\']*)["\']', r'<span class="css-selector">"\1"</span>', escaped)
        
        # Async/await highlighting for browser code
        escaped = re.sub(r'\b(async|await)\b', r'<span class="async-keyword">\1</span>', escaped)
        
        # JavaScript keywords
        escaped = re.sub(self.javascript_keywords, r'<span class="js-keyword">\1</span>', escaped)
        
        # Python keywords
        escaped = re.sub(self.python_keywords, r'<span class="python-keyword">\1</span>', escaped)
        
        # Comments
        escaped = re.sub(r'#.*$', r'<span class="code-comment">\g<0></span>', escaped, flags=re.MULTILINE)
        escaped = re.sub(r'//.*$', r'<span class="code-comment">\g<0></span>', escaped, flags=re.MULTILINE)
        
        # Strings (not already highlighted as selectors)
        escaped = re.sub(r'(?<!<span class="css-selector">)["\']([^"\']*)["\'](?!</span>)', 
                        r'<span class="code-string">"\1"</span>', escaped)
        
        # Numbers
        escaped = re.sub(r'\b(\d+\.?\d*)\b', r'<span class="code-number">\1</span>', escaped)
        
        return f'<pre class="browser-code-block">{escaped}</pre>'
    
    def format_code_html(self, code: str) -> str:
        """Format general code with syntax highlighting."""
        escaped = html.escape(code)
        
        # Detect language and apply appropriate highlighting
        if any(indicator in code for indicator in ['def ', 'import ', 'from ']):
            # Python code
            escaped = re.sub(self.python_keywords, r'<span class="python-keyword">\1</span>', escaped)
            escaped = re.sub(r'#.*$', r'<span class="python-comment">\g<0></span>', escaped, flags=re.MULTILINE)
        elif any(indicator in code for indicator in ['function', 'const ', 'let ', '=>']):
            # JavaScript code
            escaped = re.sub(self.javascript_keywords, r'<span class="js-keyword">\1</span>', escaped)
            escaped = re.sub(r'//.*$', r'<span class="js-comment">\g<0></span>', escaped, flags=re.MULTILINE)
        
        # Generic highlighting
        escaped = re.sub(r'["\']([^"\']*)["\']', r'<span class="code-string">"\1"</span>', escaped)
        escaped = re.sub(r'\b(\d+\.?\d*)\b', r'<span class="code-number">\1</span>', escaped)
        
        return f'<pre class="code-block">{escaped}</pre>'
    
    def format_text_html(self, text: str) -> str:
        """Format plain text with basic styling and URL detection."""
        escaped = html.escape(str(text))
        
        # Highlight URLs
        url_pattern = r'(https?://[^\s<>"]+)'
        escaped = re.sub(url_pattern, r'<a href="\1" target="_blank" class="text-url">\1</a>', escaped)
        
        # Highlight file paths
        path_pattern = r'(/[^\s<>"]+\.[a-zA-Z0-9]+)'
        escaped = re.sub(path_pattern, r'<span class="file-path">\1</span>', escaped)
        
        # Highlight error messages
        if 'error' in text.lower() or 'exception' in text.lower():
            return f'<div class="error-text">{escaped}</div>'
        
        # Highlight success messages
        if 'success' in text.lower() or 'passed' in text.lower():
            return f'<div class="success-text">{escaped}</div>'
        
        return f'<div class="text-block">{escaped}</div>'
    
    def format_simple_value_html(self, value: Union[int, float, bool]) -> str:
        """Format simple values with appropriate styling."""
        if isinstance(value, bool):
            css_class = "boolean-true" if value else "boolean-false"
            return f'<span class="{css_class}">{str(value).lower()}</span>'
        elif isinstance(value, (int, float)):
            return f'<span class="number-value">{value}</span>'
        else:
            return f'<span class="simple-value">{html.escape(str(value))}</span>'
    
    def format_browser_result_html(self, result: dict) -> str:
        """Specialized formatting for browser action results."""
        if not isinstance(result, dict):
            return self.auto_format_value(result)
        
        # Extract common browser result fields
        formatted_parts = []
        
        if 'success' in result:
            status_class = "result-success" if result['success'] else "result-failure"
            status_text = "SUCCESS" if result['success'] else "FAILURE"
            formatted_parts.append(f'<span class="{status_class}">Status: {status_text}</span>')
        
        if 'error' in result and result['error']:
            formatted_parts.append(f'<span class="result-error">Error: {html.escape(str(result["error"]))}</span>')
        
        if 'duration' in result:
            formatted_parts.append(f'<span class="result-duration">Duration: {result["duration"]}ms</span>')
        
        if 'url' in result:
            formatted_parts.append(f'<span class="result-url">URL: <a href="{result["url"]}" target="_blank">{result["url"]}</a></span>')
        
        # Format remaining fields as JSON
        remaining_fields = {k: v for k, v in result.items() 
                           if k not in ['success', 'error', 'duration', 'url']}
        
        if remaining_fields:
            json_part = self.format_json_html(remaining_fields)
            formatted_parts.append(json_part)
        
        if formatted_parts:
            parts_html = '<br>'.join(formatted_parts)
            return f'<div class="browser-result">{parts_html}</div>'
        else:
            return self.format_json_html(result)
    
    def _looks_like_json(self, text: str) -> bool:
        """Heuristic to detect JSON strings."""
        text = text.strip()
        return (text.startswith('{') and text.endswith('}')) or \
               (text.startswith('[') and text.endswith(']'))
    
    def _looks_like_browser_code(self, text: str) -> bool:
        """Heuristic to detect browser automation code."""
        browser_indicators = [
            'browser.', 'page.', 'await page.', 'await browser.',
            'click(', 'navigate(', 'screenshot(', 'evaluate(',
            'waitFor(', 'select(', 'type(', 'fill(',
            'selector:', 'element:', '.locator('
        ]
        return any(indicator in text for indicator in browser_indicators)
    
    def _looks_like_code(self, text: str) -> bool:
        """Heuristic to detect general code strings."""
        return any(indicator in text for indicator in self.code_indicators)
    
    def get_highlighting_css(self) -> str:
        """Get CSS for syntax highlighting with MCPlaywright theme."""
        return """
        /* JSON Highlighting */
        .json-block {
            background: #1e293b;
            color: #e2e8f0;
            padding: 15px;
            border-radius: 6px;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', monospace;
            font-size: 0.9rem;
            line-height: 1.4;
            overflow-x: auto;
        }
        
        .json-key { color: #0ea5e9; font-weight: 600; }
        .json-string { color: #22c55e; }
        .json-number { color: #f59e0b; }
        .json-boolean { color: #ec4899; }
        .json-brace, .json-bracket { color: #8b5cf6; font-weight: bold; }
        .json-colon { color: #64748b; }
        .json-comma { color: #64748b; }
        
        /* Browser Code Highlighting */
        .browser-code-block {
            background: #0f172a;
            color: #cbd5e1;
            padding: 15px;
            border-radius: 6px;
            font-family: 'SF Mono', Monaco, monospace;
            font-size: 0.9rem;
            line-height: 1.4;
            overflow-x: auto;
            border-left: 4px solid #0ea5e9;
        }
        
        .browser-method { color: #0ea5e9; font-weight: 600; }
        .browser-field { font-weight: bold; }
        .css-selector { color: #22c55e; font-weight: 500; }
        .async-keyword { color: #ec4899; font-weight: 600; }
        
        /* General Code Highlighting */
        .code-block {
            background: #1e293b;
            color: #e2e8f0;
            padding: 15px;
            border-radius: 6px;
            font-family: 'SF Mono', Monaco, monospace;
            font-size: 0.9rem;
            line-height: 1.4;
            overflow-x: auto;
        }
        
        .python-keyword { color: #8b5cf6; font-weight: 600; }
        .js-keyword { color: #06b6d4; font-weight: 600; }
        .code-string { color: #22c55e; }
        .code-number { color: #f59e0b; }
        .code-comment { color: #64748b; font-style: italic; }
        .python-comment { color: #64748b; font-style: italic; }
        .js-comment { color: #64748b; font-style: italic; }
        
        /* Text Highlighting */
        .text-block {
            padding: 10px;
            border-radius: 4px;
            background: #f8fafc;
            color: #374151;
            white-space: pre-wrap;
            word-break: break-word;
        }
        
        .text-url {
            color: #0ea5e9;
            text-decoration: none;
            font-weight: 500;
        }
        
        .text-url:hover {
            text-decoration: underline;
        }
        
        .file-path {
            color: #059669;
            font-family: monospace;
            background: rgba(5, 150, 105, 0.1);
            padding: 1px 4px;
            border-radius: 3px;
        }
        
        .error-text {
            color: #dc2626;
            background: #fef2f2;
            padding: 10px;
            border-radius: 4px;
            border-left: 4px solid #dc2626;
        }
        
        .success-text {
            color: #059669;
            background: #f0fdf4;
            padding: 10px;
            border-radius: 4px;
            border-left: 4px solid #059669;
        }
        
        /* Simple Values */
        .boolean-true { color: #22c55e; font-weight: 600; }
        .boolean-false { color: #ef4444; font-weight: 600; }
        .number-value { color: #f59e0b; font-weight: 500; font-family: monospace; }
        .simple-value { color: #374151; }
        
        /* Browser Results */
        .browser-result {
            padding: 15px;
            background: #f8fafc;
            border-radius: 6px;
            border: 1px solid #e2e8f0;
        }
        
        .result-success { color: #059669; font-weight: 600; }
        .result-failure { color: #dc2626; font-weight: 600; }
        .result-error { color: #dc2626; }
        .result-duration { color: #6b7280; font-family: monospace; }
        .result-url { color: #0ea5e9; }
        
        /* Error Blocks */
        .error-block {
            background: #fef2f2;
            color: #dc2626;
            padding: 15px;
            border-radius: 6px;
            border: 1px solid #fecaca;
            font-family: monospace;
        }
        """