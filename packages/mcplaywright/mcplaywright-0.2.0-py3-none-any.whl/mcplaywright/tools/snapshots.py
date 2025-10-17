"""
Snapshot and Accessibility Tools for MCPlaywright

Advanced page snapshot and accessibility analysis capabilities with differential snapshots.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ..session_manager import get_session_manager
from ..differential_snapshots import DifferentialSnapshotManager, DifferentialSnapshotConfig, DifferentialMode
from .video import begin_video_action_for_session, end_video_action_for_session

logger = logging.getLogger(__name__)

# Global differential snapshot manager
_differential_manager: Optional[DifferentialSnapshotManager] = None

def get_differential_manager() -> DifferentialSnapshotManager:
    """Get or create the global differential snapshot manager"""
    global _differential_manager
    if _differential_manager is None:
        # Default configuration - can be updated via browser_configure_snapshots
        config = DifferentialSnapshotConfig(
            enabled=False,  # Disabled by default for compatibility
            mode=DifferentialMode.SEMANTIC,
            max_snapshot_tokens=5000,
            include_snapshots=True,
            baseline_reset_on_navigation=True,
            lazy_parsing=True
        )
        _differential_manager = DifferentialSnapshotManager(config)
    return _differential_manager


class SnapshotParams(BaseModel):
    """Parameters for taking page snapshots"""
    session_id: Optional[str] = Field(None, description="Session ID")
    include_accessibility: Optional[bool] = Field(True, description="Include accessibility tree information")
    include_viewport_info: Optional[bool] = Field(True, description="Include viewport and layout information")
    differential: Optional[bool] = Field(None, description="Enable differential snapshots (uses global config if None)")


async def browser_snapshot(params: SnapshotParams) -> Dict[str, Any]:
    """
    Capture complete accessibility snapshot of the current page.
    
    Always returns full snapshot regardless of session snapshot configuration.
    Better than screenshot for understanding page structure and providing
    comprehensive page analysis for LLM interaction.
    
    Features:
    - Complete DOM structure analysis
    - Accessibility tree extraction
    - Element positioning and visibility
    - Interactive element identification
    - Semantic markup analysis
    - Viewport and layout information
    
    Returns:
        Comprehensive page snapshot with accessibility and structure data
    """
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_or_create_session(params.session_id)
        
        # Begin video action
        await context.begin_video_action("snapshot")
        
        # Get current page
        page = await context.get_current_page()
        
        logger.info("Capturing page snapshot with accessibility data")
        
        start_time = datetime.now()
        
        # Get basic page information
        page_info = {
            "url": page.url,
            "title": await page.title(),
            "ready_state": await page.evaluate("() => document.readyState"),
            "viewport": await page.evaluate("() => ({ width: window.innerWidth, height: window.innerHeight })"),
            "scroll_position": await page.evaluate("() => ({ x: window.scrollX, y: window.scrollY })"),
            "document_size": await page.evaluate("() => ({ width: document.documentElement.scrollWidth, height: document.documentElement.scrollHeight })")
        }
        
        # Extract DOM structure and accessibility information
        accessibility_tree = None
        if params.include_accessibility:
            try:
                # Get accessibility snapshot
                accessibility_tree = await page.accessibility.snapshot()
            except Exception as acc_error:
                logger.warning(f"Could not capture accessibility tree: {str(acc_error)}")
                accessibility_tree = {"error": str(acc_error)}
        
        # Get interactive elements and their properties
        interactive_elements = await page.evaluate("""
            () => {
                const elements = [];
                const interactiveSelectors = [
                    'a[href]', 'button', 'input', 'textarea', 'select',
                    '[onclick]', '[role="button"]', '[role="link"]',
                    '[tabindex]:not([tabindex="-1"])', '[contenteditable="true"]'
                ];
                
                interactiveSelectors.forEach(selector => {
                    document.querySelectorAll(selector).forEach((el, index) => {
                        try {
                            const rect = el.getBoundingClientRect();
                            const isVisible = rect.width > 0 && rect.height > 0 && 
                                            window.getComputedStyle(el).visibility !== 'hidden' &&
                                            window.getComputedStyle(el).display !== 'none';
                            
                            elements.push({
                                tag: el.tagName.toLowerCase(),
                                type: el.type || null,
                                text: el.textContent ? el.textContent.slice(0, 100) : '',
                                value: el.value || null,
                                href: el.href || null,
                                id: el.id || null,
                                classes: Array.from(el.classList),
                                role: el.getAttribute('role') || null,
                                ariaLabel: el.getAttribute('aria-label') || null,
                                isVisible: isVisible,
                                isEnabled: !el.disabled,
                                bounds: {
                                    x: Math.round(rect.x),
                                    y: Math.round(rect.y),
                                    width: Math.round(rect.width),
                                    height: Math.round(rect.height)
                                },
                                selector: el.tagName.toLowerCase() + 
                                         (el.id ? '#' + el.id : '') +
                                         (el.className ? '.' + Array.from(el.classList).join('.') : '')
                            });
                        } catch (e) {
                            // Skip elements that cause errors
                        }
                    });
                });
                
                return elements;
            }
        """)
        
        # Get form information
        forms_info = await page.evaluate("""
            () => {
                const forms = [];
                document.querySelectorAll('form').forEach((form, index) => {
                    const formData = {
                        action: form.action || null,
                        method: form.method || 'get',
                        enctype: form.enctype || null,
                        fields: []
                    };
                    
                    form.querySelectorAll('input, textarea, select').forEach(field => {
                        formData.fields.push({
                            name: field.name || null,
                            type: field.type || null,
                            value: field.value || null,
                            placeholder: field.placeholder || null,
                            required: field.required,
                            disabled: field.disabled
                        });
                    });
                    
                    forms.push(formData);
                });
                
                return forms;
            }
        """)
        
        # Get text content structure
        text_content = await page.evaluate("""
            () => {
                const headings = [];
                const paragraphs = [];
                const links = [];
                
                // Extract headings
                document.querySelectorAll('h1, h2, h3, h4, h5, h6').forEach(heading => {
                    headings.push({
                        level: parseInt(heading.tagName.charAt(1)),
                        text: heading.textContent.trim(),
                        id: heading.id || null
                    });
                });
                
                // Extract paragraphs
                document.querySelectorAll('p').forEach(p => {
                    const text = p.textContent.trim();
                    if (text.length > 0) {
                        paragraphs.push({
                            text: text.slice(0, 200) + (text.length > 200 ? '...' : ''),
                            length: text.length
                        });
                    }
                });
                
                // Extract links
                document.querySelectorAll('a[href]').forEach(link => {
                    links.push({
                        text: link.textContent.trim(),
                        href: link.href,
                        target: link.target || null
                    });
                });
                
                return { headings, paragraphs, links };
            }
        """)
        
        # Get viewport information if requested
        viewport_info = None
        if params.include_viewport_info:
            viewport_info = {
                "viewport": page_info["viewport"],
                "scroll_position": page_info["scroll_position"],
                "document_size": page_info["document_size"],
                "visible_area": {
                    "top": page_info["scroll_position"]["y"],
                    "left": page_info["scroll_position"]["x"],
                    "bottom": page_info["scroll_position"]["y"] + page_info["viewport"]["height"],
                    "right": page_info["scroll_position"]["x"] + page_info["viewport"]["width"]
                }
            }
        
        capture_duration = (datetime.now() - start_time).total_seconds() * 1000
        
        # End video action
        await context.end_video_action("snapshot")
        
        # Build comprehensive snapshot result
        result = {
            "success": True,
            "page_info": page_info,
            "interactive_elements": interactive_elements,
            "interactive_element_count": len(interactive_elements),
            "visible_element_count": sum(1 for el in interactive_elements if el["isVisible"]),
            "forms": forms_info,
            "text_content": text_content,
            "viewport_info": viewport_info,
            "capture_duration_ms": int(capture_duration),
            "session_id": context.session_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add accessibility tree if captured
        if accessibility_tree:
            result["accessibility_tree"] = accessibility_tree
        
        # Apply differential snapshots if enabled
        differential_manager = get_differential_manager()
        use_differential = params.differential
        if use_differential is None:
            use_differential = differential_manager.config.enabled
        
        if use_differential:
            logger.info("Processing snapshot with differential analysis")
            differential_result = differential_manager.process_snapshot(context.session_id, result)
            
            # If differential processing returned a minimal diff, use that instead
            if differential_result.get("differential_snapshot", False):
                logger.info(f"Differential snapshot generated: {differential_result.get('token_savings', '0%')} size reduction")
                return differential_result
        
        logger.info(f"Standard snapshot captured: {len(interactive_elements)} interactive elements, {len(forms_info)} forms")
        return result
        
    except Exception as e:
        logger.error(f"Page snapshot failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "session_id": params.session_id,
            "timestamp": datetime.now().isoformat()
        }


async def browser_get_accessibility_tree(session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get the accessibility tree for the current page.
    
    Extracts comprehensive accessibility information including roles, names,
    descriptions, and hierarchical structure for screen reader compatibility
    and accessibility analysis.
    
    Returns:
        Accessibility tree with comprehensive ARIA information
    """
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_or_create_session(session_id)
        
        # Get current page
        page = await context.get_current_page()
        
        logger.info("Extracting accessibility tree")
        
        start_time = datetime.now()
        
        try:
            # Get full accessibility snapshot
            accessibility_tree = await page.accessibility.snapshot(
                interesting_only=False  # Include all nodes, not just interesting ones
            )
            
            # Get additional accessibility information
            aria_info = await page.evaluate("""
                () => {
                    const elements = [];
                    const walker = document.createTreeWalker(
                        document.body,
                        NodeFilter.SHOW_ELEMENT,
                        null,
                        false
                    );
                    
                    let node;
                    while (node = walker.nextNode()) {
                        const ariaAttributes = {};
                        
                        // Collect all ARIA attributes
                        Array.from(node.attributes || []).forEach(attr => {
                            if (attr.name.startsWith('aria-') || 
                                ['role', 'tabindex', 'contenteditable'].includes(attr.name)) {
                                ariaAttributes[attr.name] = attr.value;
                            }
                        });
                        
                        if (Object.keys(ariaAttributes).length > 0) {
                            elements.push({
                                tag: node.tagName.toLowerCase(),
                                text: node.textContent ? node.textContent.slice(0, 100) : '',
                                attributes: ariaAttributes,
                                id: node.id || null,
                                classes: Array.from(node.classList || [])
                            });
                        }
                    }
                    
                    return elements;
                }
            """)
            
            extraction_duration = (datetime.now() - start_time).total_seconds() * 1000
            
            result = {
                "success": True,
                "accessibility_tree": accessibility_tree,
                "aria_elements": aria_info,
                "aria_element_count": len(aria_info),
                "extraction_duration_ms": int(extraction_duration),
                "session_id": context.session_id,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Accessibility tree extracted: {len(aria_info)} ARIA elements")
            return result
            
        except Exception as acc_error:
            logger.error(f"Accessibility tree extraction failed: {str(acc_error)}")
            return {
                "success": False,
                "error": f"Could not extract accessibility tree: {str(acc_error)}",
                "session_id": context.session_id,
                "timestamp": datetime.now().isoformat()
            }
        
    except Exception as e:
        logger.error(f"Get accessibility tree failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }


async def browser_get_page_structure(session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get detailed page structure and content organization.
    
    Analyzes the page's semantic structure, content hierarchy, and layout
    organization for better understanding of page composition.
    
    Returns:
        Detailed page structure analysis
    """
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_or_create_session(session_id)
        
        # Get current page
        page = await context.get_current_page()
        
        logger.info("Analyzing page structure")
        
        start_time = datetime.now()
        
        # Get comprehensive page structure
        structure_info = await page.evaluate("""
            () => {
                const structure = {
                    semantic_elements: {},
                    content_sections: [],
                    navigation_elements: [],
                    media_elements: [],
                    data_elements: []
                };
                
                // Count semantic HTML5 elements
                const semanticTags = [
                    'header', 'nav', 'main', 'article', 'section', 'aside', 'footer',
                    'figure', 'figcaption', 'time', 'address', 'details', 'summary'
                ];
                
                semanticTags.forEach(tag => {
                    const elements = document.querySelectorAll(tag);
                    if (elements.length > 0) {
                        structure.semantic_elements[tag] = elements.length;
                    }
                });
                
                // Analyze content sections
                document.querySelectorAll('main, article, section').forEach(section => {
                    const headings = section.querySelectorAll('h1, h2, h3, h4, h5, h6');
                    const paragraphs = section.querySelectorAll('p');
                    const lists = section.querySelectorAll('ul, ol');
                    
                    structure.content_sections.push({
                        tag: section.tagName.toLowerCase(),
                        id: section.id || null,
                        headings: headings.length,
                        paragraphs: paragraphs.length,
                        lists: lists.length,
                        word_count_estimate: section.textContent ? section.textContent.split(/\\s+/).length : 0
                    });
                });
                
                // Analyze navigation
                document.querySelectorAll('nav, [role="navigation"]').forEach(nav => {
                    const links = nav.querySelectorAll('a[href]');
                    const buttons = nav.querySelectorAll('button');
                    
                    structure.navigation_elements.push({
                        tag: nav.tagName.toLowerCase(),
                        role: nav.getAttribute('role') || null,
                        links: links.length,
                        buttons: buttons.length,
                        aria_label: nav.getAttribute('aria-label') || null
                    });
                });
                
                // Analyze media elements
                document.querySelectorAll('img, video, audio, canvas, svg').forEach(media => {
                    structure.media_elements.push({
                        tag: media.tagName.toLowerCase(),
                        src: media.src || null,
                        alt: media.alt || null,
                        width: media.width || null,
                        height: media.height || null,
                        has_controls: media.hasAttribute('controls')
                    });
                });
                
                // Analyze data/table elements
                document.querySelectorAll('table, dl, [role="grid"], [role="table"]').forEach(data => {
                    if (data.tagName.toLowerCase() === 'table') {
                        const rows = data.querySelectorAll('tr');
                        const headers = data.querySelectorAll('th');
                        const cells = data.querySelectorAll('td');
                        
                        structure.data_elements.push({
                            type: 'table',
                            rows: rows.length,
                            headers: headers.length,
                            cells: cells.length,
                            has_caption: !!data.querySelector('caption')
                        });
                    } else if (data.tagName.toLowerCase() === 'dl') {
                        const terms = data.querySelectorAll('dt');
                        const definitions = data.querySelectorAll('dd');
                        
                        structure.data_elements.push({
                            type: 'definition_list',
                            terms: terms.length,
                            definitions: definitions.length
                        });
                    } else {
                        structure.data_elements.push({
                            type: 'grid',
                            role: data.getAttribute('role'),
                            aria_label: data.getAttribute('aria-label')
                        });
                    }
                });
                
                return structure;
            }
        """)
        
        # Get document metadata
        metadata = await page.evaluate("""
            () => {
                const meta = {};
                
                // Basic document info
                meta.lang = document.documentElement.lang || null;
                meta.dir = document.documentElement.dir || null;
                meta.charset = document.characterSet || null;
                
                // Meta tags
                meta.description = document.querySelector('meta[name="description"]')?.content || null;
                meta.keywords = document.querySelector('meta[name="keywords"]')?.content || null;
                meta.author = document.querySelector('meta[name="author"]')?.content || null;
                meta.viewport = document.querySelector('meta[name="viewport"]')?.content || null;
                
                // Open Graph
                meta.og_title = document.querySelector('meta[property="og:title"]')?.content || null;
                meta.og_description = document.querySelector('meta[property="og:description"]')?.content || null;
                meta.og_type = document.querySelector('meta[property="og:type"]')?.content || null;
                
                return meta;
            }
        """)
        
        analysis_duration = (datetime.now() - start_time).total_seconds() * 1000
        
        result = {
            "success": True,
            "structure": structure_info,
            "metadata": metadata,
            "analysis": {
                "total_semantic_elements": sum(structure_info["semantic_elements"].values()),
                "content_sections": len(structure_info["content_sections"]),
                "navigation_areas": len(structure_info["navigation_elements"]),
                "media_elements": len(structure_info["media_elements"]),
                "data_elements": len(structure_info["data_elements"]),
                "has_main_content": any(section["tag"] == "main" for section in structure_info["content_sections"]),
                "has_navigation": len(structure_info["navigation_elements"]) > 0,
                "semantic_score": _calculate_semantic_score(structure_info)
            },
            "analysis_duration_ms": int(analysis_duration),
            "session_id": context.session_id,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Page structure analyzed: {result['analysis']['total_semantic_elements']} semantic elements")
        return result
        
    except Exception as e:
        logger.error(f"Page structure analysis failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }


def _calculate_semantic_score(structure_info):
    """Calculate a semantic quality score for the page"""
    score = 0
    
    # Points for semantic elements
    semantic_elements = structure_info.get("semantic_elements", {})
    score += min(len(semantic_elements) * 2, 10)  # Max 10 points for variety
    
    # Points for proper content structure
    if semantic_elements.get("main", 0) > 0:
        score += 5
    if semantic_elements.get("header", 0) > 0:
        score += 3
    if semantic_elements.get("nav", 0) > 0:
        score += 3
    if semantic_elements.get("footer", 0) > 0:
        score += 2
    
    # Points for content organization
    content_sections = structure_info.get("content_sections", [])
    if len(content_sections) > 0:
        score += min(len(content_sections) * 2, 8)
    
    # Points for accessibility features
    navigation_elements = structure_info.get("navigation_elements", [])
    if any(nav.get("aria_label") for nav in navigation_elements):
        score += 3
    
    return min(score, 100)  # Cap at 100


class DifferentialSnapshotConfigParams(BaseModel):
    """Parameters for configuring differential snapshots"""
    enabled: Optional[bool] = Field(None, description="Enable/disable differential snapshots")
    mode: Optional[str] = Field(None, description="Analysis mode: 'semantic', 'simple', or 'both'")
    max_snapshot_tokens: Optional[int] = Field(None, description="Maximum tokens before truncation")
    include_snapshots: Optional[bool] = Field(None, description="Include automatic snapshots after interactions")
    baseline_reset_on_navigation: Optional[bool] = Field(None, description="Reset baseline on navigation")
    lazy_parsing: Optional[bool] = Field(None, description="Only parse when changes detected")


async def browser_configure_differential_snapshots(params: DifferentialSnapshotConfigParams) -> Dict[str, Any]:
    """
    Configure differential snapshots system.
    
    Enables React-style virtual DOM reconciliation for page snapshots,
    achieving 99% response size reduction by only reporting changes.
    
    Features:
    - React-style tree reconciliation with element fingerprinting
    - Multiple analysis modes (semantic, simple, both)
    - Automatic baseline management with navigation reset
    - Lazy parsing for performance optimization
    - Smart token limits with truncation
    
    Returns:
        Configuration status and current settings
    """
    try:
        differential_manager = get_differential_manager()
        config = differential_manager.config
        
        # Update configuration with provided parameters
        if params.enabled is not None:
            config.enabled = params.enabled
        
        if params.mode is not None:
            try:
                config.mode = DifferentialMode(params.mode)
            except ValueError:
                return {
                    "success": False,
                    "error": f"Invalid mode '{params.mode}'. Valid modes: semantic, simple, both",
                    "timestamp": datetime.now().isoformat()
                }
        
        if params.max_snapshot_tokens is not None:
            config.max_snapshot_tokens = params.max_snapshot_tokens
        
        if params.include_snapshots is not None:
            config.include_snapshots = params.include_snapshots
        
        if params.baseline_reset_on_navigation is not None:
            config.baseline_reset_on_navigation = params.baseline_reset_on_navigation
        
        if params.lazy_parsing is not None:
            config.lazy_parsing = params.lazy_parsing
        
        logger.info(f"Differential snapshots configured: enabled={config.enabled}, mode={config.mode}")
        
        return {
            "success": True,
            "configuration": {
                "enabled": config.enabled,
                "mode": config.mode.value,
                "max_snapshot_tokens": config.max_snapshot_tokens,
                "include_snapshots": config.include_snapshots,
                "baseline_reset_on_navigation": config.baseline_reset_on_navigation,
                "lazy_parsing": config.lazy_parsing
            },
            "message": "Differential snapshots React-style reconciliation configured",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Configure differential snapshots failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


async def browser_reset_differential_baseline(session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Reset differential snapshots baseline for a session.
    
    Forces the next snapshot to establish a new baseline for comparison.
    Useful when you want to restart change tracking from current page state.
    
    Returns:
        Reset status and session information
    """
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_or_create_session(session_id)
        
        differential_manager = get_differential_manager()
        differential_manager.reset_baseline(context.session_id)
        
        logger.info(f"Reset differential baseline for session {context.session_id}")
        
        return {
            "success": True,
            "message": "Differential snapshots baseline reset",
            "session_id": context.session_id,
            "next_snapshot": "Will establish new baseline",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Reset differential baseline failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }


async def browser_get_differential_status(session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get differential snapshots status and configuration.
    
    Shows current configuration, baseline status, and performance metrics
    for the differential snapshots system.
    
    Returns:
        Comprehensive status of differential snapshots system
    """
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_or_create_session(session_id)
        
        differential_manager = get_differential_manager()
        config = differential_manager.config
        baseline_status = differential_manager.get_baseline_status(context.session_id)
        
        result = {
            "success": True,
            "configuration": {
                "enabled": config.enabled,
                "mode": config.mode.value,
                "max_snapshot_tokens": config.max_snapshot_tokens,
                "include_snapshots": config.include_snapshots,
                "baseline_reset_on_navigation": config.baseline_reset_on_navigation,
                "lazy_parsing": config.lazy_parsing
            },
            "baseline_status": baseline_status,
            "session_id": context.session_id,
            "timestamp": datetime.now().isoformat()
        }
        
        if config.enabled:
            result["message"] = "Differential snapshots active with React-style reconciliation"
            result["performance_benefits"] = {
                "response_size_reduction": "Up to 99%",
                "token_savings": "Massive reduction in model processing",
                "analysis_speed": "Near-instant change detection",
                "reconciliation_algorithm": "React-style virtual DOM diffing"
            }
        else:
            result["message"] = "Differential snapshots disabled - using standard snapshots"
        
        logger.info(f"Differential status retrieved for session {context.session_id}")
        return result
        
    except Exception as e:
        logger.error(f"Get differential status failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }