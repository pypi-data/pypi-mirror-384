"""
MCPlaywright Theme System

Professional theme management system for MCPlaywright UI customization.
Provides dynamic theme switching, professional theme registry, and accessibility-compliant designs.

Features:
- 5 built-in professional themes
- Dynamic CSS custom property generation
- Accessibility compliance (WCAG 2.1 AA/AAA)
- Custom theme creation and management
- Theme export/import functionality
- Professional design patterns
"""

import json
import logging
from typing import Dict, Any, List, Optional, Literal, Union
from pydantic import BaseModel, Field
from enum import Enum

from ..context import Context

logger = logging.getLogger(__name__)

class ThemeCategory(str, Enum):
    """Theme category enumeration"""
    MINIMAL = "minimal"
    CORPORATE = "corporate"
    CREATIVE = "creative"
    ACCESSIBILITY = "accessibility"
    CUSTOM = "custom"

class ThemeColors(BaseModel):
    """Theme color configuration"""
    # Core semantic colors
    primary: str = Field(description="Primary brand color")
    primary_hover: str = Field(description="Primary color hover state")
    success: str = Field(description="Success state color")
    warning: str = Field(description="Warning state color")
    error: str = Field(description="Error state color")
    
    # Surface colors (backgrounds)
    surface: str = Field(description="Main surface background")
    surface_elevated: str = Field(description="Elevated surface background")
    surface_transparent: Optional[str] = Field(default=None, description="Transparent surface overlay")
    
    # Text colors
    text_primary: str = Field(description="Primary text color")
    text_secondary: str = Field(description="Secondary text color")
    text_inverse: str = Field(description="Inverse text color")
    
    # Border colors
    border: str = Field(description="Standard border color")
    border_subtle: str = Field(description="Subtle border color")
    border_focus: str = Field(description="Focus state border color")
    
    # Interactive states
    background_hover: str = Field(description="Hover state background")
    background_active: str = Field(description="Active state background")
    background_selected: str = Field(description="Selected state background")

class ThemeTypography(BaseModel):
    """Theme typography configuration"""
    font_family: str = Field(description="Primary font family")
    font_family_mono: str = Field(description="Monospace font family")
    font_size_xs: str = Field(default="0.75rem", description="Extra small font size")
    font_size_sm: str = Field(default="0.875rem", description="Small font size")
    font_size_base: str = Field(default="1rem", description="Base font size")
    font_size_lg: str = Field(default="1.125rem", description="Large font size")

class ThemeSpacing(BaseModel):
    """Theme spacing configuration"""
    xs: str = Field(default="0.25rem", description="Extra small spacing")
    sm: str = Field(default="0.5rem", description="Small spacing")
    md: str = Field(default="0.75rem", description="Medium spacing")
    lg: str = Field(default="1rem", description="Large spacing")
    xl: str = Field(default="1.5rem", description="Extra large spacing")
    xxl: str = Field(default="2rem", description="Double extra large spacing")

class ThemeEffects(BaseModel):
    """Theme visual effects configuration"""
    border_radius_sm: str = Field(default="0.375rem", description="Small border radius")
    border_radius_md: str = Field(default="0.5rem", description="Medium border radius")
    border_radius_lg: str = Field(default="0.75rem", description="Large border radius")
    border_radius_pill: str = Field(default="9999px", description="Pill border radius")
    border_radius_full: str = Field(default="50%", description="Full circle border radius")
    
    shadow_sm: str = Field(description="Small shadow")
    shadow_md: str = Field(description="Medium shadow")
    shadow_lg: str = Field(description="Large shadow")
    shadow_xl: str = Field(description="Extra large shadow")
    
    backdrop_blur: str = Field(default="4px", description="Backdrop blur amount")
    backdrop_opacity: str = Field(default="0.9", description="Backdrop opacity")
    
    transition_fast: str = Field(default="150ms cubic-bezier(0.4, 0, 0.2, 1)", description="Fast transition")
    transition_normal: str = Field(default="250ms cubic-bezier(0.4, 0, 0.2, 1)", description="Normal transition")
    transition_slow: str = Field(default="350ms cubic-bezier(0.4, 0, 0.2, 1)", description="Slow transition")

class ThemeToolbar(BaseModel):
    """Theme-specific toolbar configuration"""
    min_width: str = Field(default="280px", description="Minimum toolbar width")
    max_width: str = Field(default="360px", description="Maximum toolbar width")
    default_opacity: float = Field(default=0.95, description="Default toolbar opacity")
    animation_duration: str = Field(default="250ms", description="Animation duration")

class ThemeAccessibility(BaseModel):
    """Theme accessibility features"""
    contrast_ratio: float = Field(description="WCAG contrast ratio")
    supports_high_contrast: bool = Field(description="High contrast mode support")
    supports_reduced_motion: bool = Field(description="Reduced motion support")
    supports_dark_mode: bool = Field(description="Dark mode support")

class ThemePreview(BaseModel):
    """Theme preview colors for UI display"""
    background_color: str = Field(description="Preview background color")
    foreground_color: str = Field(description="Preview foreground color")
    accent_color: str = Field(description="Preview accent color")

class ThemeDefinition(BaseModel):
    """Complete theme definition"""
    id: str = Field(description="Unique theme identifier")
    name: str = Field(description="Human-readable theme name")
    description: str = Field(description="Theme description")
    version: str = Field(default="1.0.0", description="Theme version")
    author: Optional[str] = Field(default=None, description="Theme author")
    category: ThemeCategory = Field(description="Theme category")
    
    # Theme configuration
    colors: ThemeColors = Field(description="Color configuration")
    typography: ThemeTypography = Field(description="Typography configuration")
    spacing: ThemeSpacing = Field(description="Spacing configuration")
    effects: ThemeEffects = Field(description="Visual effects configuration")
    toolbar: ThemeToolbar = Field(default_factory=ThemeToolbar, description="Toolbar configuration")
    accessibility: ThemeAccessibility = Field(description="Accessibility features")
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Theme tags")
    preview: ThemePreview = Field(description="Preview colors")

# Built-in theme definitions
BUILTIN_THEMES: Dict[str, ThemeDefinition] = {
    "minimal": ThemeDefinition(
        id="minimal",
        name="Minimal",
        description="Clean, minimal design inspired by GitHub's subtle indicators",
        category=ThemeCategory.MINIMAL,
        colors=ThemeColors(
            primary="#0969da",
            primary_hover="#0550ae",
            success="#1a7f37",
            warning="#9a6700",
            error="#cf222e",
            surface="#ffffff",
            surface_elevated="#f6f8fa",
            surface_transparent="rgba(255, 255, 255, 0.9)",
            text_primary="#1f2328",
            text_secondary="#656d76",
            text_inverse="#ffffff",
            border="#d1d9e0",
            border_subtle="#f6f8fa",
            border_focus="#0969da",
            background_hover="#f3f4f6",
            background_active="#e5e7eb",
            background_selected="#dbeafe"
        ),
        typography=ThemeTypography(
            font_family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
            font_family_mono="'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Liberation Mono', 'Menlo', monospace"
        ),
        spacing=ThemeSpacing(),
        effects=ThemeEffects(
            shadow_sm="0 1px 2px 0 rgba(0, 0, 0, 0.05)",
            shadow_md="0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
            shadow_lg="0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
            shadow_xl="0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)"
        ),
        accessibility=ThemeAccessibility(
            contrast_ratio=7.1,
            supports_high_contrast=True,
            supports_reduced_motion=True,
            supports_dark_mode=False
        ),
        tags=["minimal", "github", "clean", "subtle"],
        preview=ThemePreview(
            background_color="#ffffff",
            foreground_color="#1f2328",
            accent_color="#0969da"
        )
    ),
    
    "corporate": ThemeDefinition(
        id="corporate",
        name="Corporate",
        description="Professional, enterprise-friendly design with excellent accessibility",
        category=ThemeCategory.CORPORATE,
        colors=ThemeColors(
            primary="#2563eb",
            primary_hover="#1d4ed8",
            success="#059669",
            warning="#d97706",
            error="#dc2626",
            surface="#ffffff",
            surface_elevated="#f8fafc",
            surface_transparent="rgba(248, 250, 252, 0.95)",
            text_primary="#0f172a",
            text_secondary="#64748b",
            text_inverse="#ffffff",
            border="#e2e8f0",
            border_subtle="#f1f5f9",
            border_focus="#2563eb",
            background_hover="#f1f5f9",
            background_active="#e2e8f0",
            background_selected="#dbeafe"
        ),
        typography=ThemeTypography(
            font_family="'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
            font_family_mono="'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Liberation Mono', 'Menlo', monospace"
        ),
        spacing=ThemeSpacing(),
        effects=ThemeEffects(
            border_radius_sm="0.25rem",
            border_radius_md="0.375rem",
            border_radius_lg="0.5rem",
            shadow_sm="0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)",
            shadow_md="0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
            shadow_lg="0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
            shadow_xl="0 25px 50px -12px rgba(0, 0, 0, 0.25)",
            backdrop_blur="8px",
            backdrop_opacity="0.95",
            transition_fast="150ms ease-out",
            transition_normal="250ms ease-out",
            transition_slow="350ms ease-out"
        ),
        toolbar=ThemeToolbar(
            min_width="280px",
            max_width="360px",
            default_opacity=0.98,
            animation_duration="200ms"
        ),
        accessibility=ThemeAccessibility(
            contrast_ratio=8.2,
            supports_high_contrast=True,
            supports_reduced_motion=True,
            supports_dark_mode=False
        ),
        tags=["corporate", "professional", "enterprise", "accessible"],
        preview=ThemePreview(
            background_color="#ffffff",
            foreground_color="#0f172a",
            accent_color="#2563eb"
        )
    ),
    
    "hacker": ThemeDefinition(
        id="hacker",
        name="Hacker Matrix",
        description="Matrix-style neon green terminal aesthetic for developers",
        category=ThemeCategory.CREATIVE,
        colors=ThemeColors(
            primary="#00ff41",
            primary_hover="#00cc33",
            success="#00ff41",
            warning="#ffff00",
            error="#ff4444",
            surface="#0d1117",
            surface_elevated="#161b22",
            surface_transparent="rgba(13, 17, 23, 0.9)",
            text_primary="#00ff41",
            text_secondary="#7dd3fc",
            text_inverse="#000000",
            border="#30363d",
            border_subtle="#21262d",
            border_focus="#00ff41",
            background_hover="rgba(0, 255, 65, 0.1)",
            background_active="rgba(0, 255, 65, 0.2)",
            background_selected="rgba(0, 255, 65, 0.15)"
        ),
        typography=ThemeTypography(
            font_family="'Fira Code', 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, monospace",
            font_family_mono="'Fira Code', 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, monospace"
        ),
        spacing=ThemeSpacing(),
        effects=ThemeEffects(
            border_radius_sm="0.125rem",
            border_radius_md="0.25rem",
            border_radius_lg="0.375rem",
            shadow_sm="0 0 5px rgba(0, 255, 65, 0.3)",
            shadow_md="0 0 10px rgba(0, 255, 65, 0.4), 0 0 20px rgba(0, 255, 65, 0.1)",
            shadow_lg="0 0 15px rgba(0, 255, 65, 0.5), 0 0 30px rgba(0, 255, 65, 0.2)",
            shadow_xl="0 0 25px rgba(0, 255, 65, 0.6), 0 0 50px rgba(0, 255, 65, 0.3)",
            backdrop_blur="6px",
            backdrop_opacity="0.9",
            transition_fast="100ms linear",
            transition_normal="200ms linear",
            transition_slow="300ms linear"
        ),
        toolbar=ThemeToolbar(
            min_width="250px",
            max_width="400px",
            default_opacity=0.92,
            animation_duration="150ms"
        ),
        accessibility=ThemeAccessibility(
            contrast_ratio=6.8,
            supports_high_contrast=True,
            supports_reduced_motion=True,
            supports_dark_mode=True
        ),
        tags=["hacker", "matrix", "terminal", "developer", "neon"],
        preview=ThemePreview(
            background_color="#0d1117",
            foreground_color="#00ff41",
            accent_color="#7dd3fc"
        )
    ),
    
    "glassmorphism": ThemeDefinition(
        id="glassmorphism",
        name="Glass Morphism",
        description="Modern glass/blur effects with beautiful transparency",
        category=ThemeCategory.CREATIVE,
        colors=ThemeColors(
            primary="#8b5cf6",
            primary_hover="#7c3aed",
            success="#10b981",
            warning="#f59e0b",
            error="#ef4444",
            surface="rgba(255, 255, 255, 0.1)",
            surface_elevated="rgba(255, 255, 255, 0.15)",
            surface_transparent="rgba(255, 255, 255, 0.05)",
            text_primary="#ffffff",
            text_secondary="rgba(255, 255, 255, 0.8)",
            text_inverse="#000000",
            border="rgba(255, 255, 255, 0.2)",
            border_subtle="rgba(255, 255, 255, 0.1)",
            border_focus="#8b5cf6",
            background_hover="rgba(255, 255, 255, 0.15)",
            background_active="rgba(255, 255, 255, 0.2)",
            background_selected="rgba(139, 92, 246, 0.2)"
        ),
        typography=ThemeTypography(
            font_family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
            font_family_mono="'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Liberation Mono', 'Menlo', monospace"
        ),
        spacing=ThemeSpacing(),
        effects=ThemeEffects(
            border_radius_sm="0.5rem",
            border_radius_md="0.75rem",
            border_radius_lg="1rem",
            shadow_sm="0 4px 6px -1px rgba(0, 0, 0, 0.1)",
            shadow_md="0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
            shadow_lg="0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
            shadow_xl="0 25px 50px -12px rgba(0, 0, 0, 0.25), 0 0 0 1px rgba(255, 255, 255, 0.1)",
            backdrop_blur="16px",
            backdrop_opacity="0.85",
            transition_fast="200ms cubic-bezier(0.4, 0, 0.2, 1)",
            transition_normal="300ms cubic-bezier(0.4, 0, 0.2, 1)",
            transition_slow="400ms cubic-bezier(0.4, 0, 0.2, 1)"
        ),
        toolbar=ThemeToolbar(
            min_width="260px",
            max_width="350px",
            default_opacity=0.9,
            animation_duration="300ms"
        ),
        accessibility=ThemeAccessibility(
            contrast_ratio=5.2,
            supports_high_contrast=False,
            supports_reduced_motion=True,
            supports_dark_mode=True
        ),
        tags=["glassmorphism", "modern", "blur", "transparency", "glass"],
        preview=ThemePreview(
            background_color="rgba(255, 255, 255, 0.1)",
            foreground_color="#ffffff",
            accent_color="#8b5cf6"
        )
    ),
    
    "high_contrast": ThemeDefinition(
        id="high_contrast",
        name="High Contrast",
        description="Maximum accessibility with WCAG AAA contrast standards",
        category=ThemeCategory.ACCESSIBILITY,
        colors=ThemeColors(
            primary="#0066cc",
            primary_hover="#004499",
            success="#006600",
            warning="#cc6600",
            error="#cc0000",
            surface="#ffffff",
            surface_elevated="#ffffff",
            surface_transparent="rgba(255, 255, 255, 1)",
            text_primary="#000000",
            text_secondary="#333333",
            text_inverse="#ffffff",
            border="#000000",
            border_subtle="#666666",
            border_focus="#0066cc",
            background_hover="#f0f0f0",
            background_active="#e0e0e0",
            background_selected="#cce6ff"
        ),
        typography=ThemeTypography(
            font_family="Arial, sans-serif",
            font_family_mono="'Courier New', Courier, monospace"
        ),
        spacing=ThemeSpacing(
            xs="0.25rem",
            sm="0.75rem",  # Larger touch targets
            md="1rem",
            lg="1.25rem",
            xl="1.5rem",
            xxl="2rem"
        ),
        effects=ThemeEffects(
            border_radius_sm="0.25rem",
            border_radius_md="0.375rem",
            border_radius_lg="0.5rem",
            shadow_sm="0 2px 4px 0 rgba(0, 0, 0, 0.5)",
            shadow_md="0 4px 8px 0 rgba(0, 0, 0, 0.5)",
            shadow_lg="0 8px 16px 0 rgba(0, 0, 0, 0.5)",
            shadow_xl="0 16px 32px 0 rgba(0, 0, 0, 0.5)",
            backdrop_blur="0px",  # No blur for clarity
            backdrop_opacity="1",
            transition_fast="0ms",  # Respects reduced motion
            transition_normal="0ms",
            transition_slow="0ms"
        ),
        toolbar=ThemeToolbar(
            min_width="300px",
            max_width="400px",
            default_opacity=1.0,
            animation_duration="0ms"
        ),
        accessibility=ThemeAccessibility(
            contrast_ratio=21.0,  # WCAG AAA
            supports_high_contrast=True,
            supports_reduced_motion=True,
            supports_dark_mode=False
        ),
        tags=["accessibility", "high-contrast", "wcag-aaa", "screen-reader"],
        preview=ThemePreview(
            background_color="#ffffff",
            foreground_color="#000000",
            accent_color="#0066cc"
        )
    )
}

class ThemeRegistry:
    """Theme registry for managing and switching themes"""
    
    def __init__(self):
        self.themes = BUILTIN_THEMES.copy()
        self.custom_themes: Dict[str, ThemeDefinition] = {}
        self.current_theme_id = "corporate"
    
    def list_themes(self, filter_type: Literal["all", "builtin", "custom"] = "all") -> List[ThemeDefinition]:
        """List available themes with optional filtering"""
        if filter_type == "builtin":
            return list(BUILTIN_THEMES.values())
        elif filter_type == "custom":
            return list(self.custom_themes.values())
        else:
            return list(self.themes.values())
    
    def get_theme(self, theme_id: str) -> Optional[ThemeDefinition]:
        """Get theme by ID"""
        return self.themes.get(theme_id)
    
    def get_current_theme(self) -> ThemeDefinition:
        """Get currently active theme"""
        return self.themes.get(self.current_theme_id, BUILTIN_THEMES["corporate"])
    
    def set_current_theme(self, theme_id: str) -> bool:
        """Set current theme"""
        if theme_id in self.themes:
            self.current_theme_id = theme_id
            return True
        return False
    
    def register_custom_theme(self, theme: ThemeDefinition) -> str:
        """Register a custom theme and return the ID"""
        custom_id = f"custom_{theme.id}"
        custom_theme = theme.model_copy()
        custom_theme.id = custom_id
        custom_theme.category = ThemeCategory.CUSTOM
        
        self.themes[custom_id] = custom_theme
        self.custom_themes[custom_id] = custom_theme
        
        return custom_id
    
    def remove_custom_theme(self, theme_id: str) -> bool:
        """Remove a custom theme"""
        if theme_id.startswith("custom_") and theme_id in self.custom_themes:
            del self.themes[theme_id]
            del self.custom_themes[theme_id]
            
            if self.current_theme_id == theme_id:
                self.current_theme_id = "corporate"
            
            return True
        return False
    
    def generate_css_variables(self, theme_id: Optional[str] = None) -> str:
        """Generate CSS custom properties for a theme"""
        theme = self.get_theme(theme_id) if theme_id else self.get_current_theme()
        if not theme:
            return ""
        
        css_vars = [
            # Colors
            f"--mcp-primary: {theme.colors.primary};",
            f"--mcp-primary-hover: {theme.colors.primary_hover};",
            f"--mcp-success: {theme.colors.success};",
            f"--mcp-warning: {theme.colors.warning};",
            f"--mcp-error: {theme.colors.error};",
            f"--mcp-surface: {theme.colors.surface};",
            f"--mcp-surface-elevated: {theme.colors.surface_elevated};",
            f"--mcp-surface-transparent: {theme.colors.surface_transparent or theme.colors.surface};",
            f"--mcp-text-primary: {theme.colors.text_primary};",
            f"--mcp-text-secondary: {theme.colors.text_secondary};",
            f"--mcp-text-inverse: {theme.colors.text_inverse};",
            f"--mcp-border: {theme.colors.border};",
            f"--mcp-border-subtle: {theme.colors.border_subtle};",
            f"--mcp-border-focus: {theme.colors.border_focus};",
            f"--mcp-bg-hover: {theme.colors.background_hover};",
            f"--mcp-bg-active: {theme.colors.background_active};",
            f"--mcp-bg-selected: {theme.colors.background_selected};",
            
            # Typography
            f"--mcp-font-family: {theme.typography.font_family};",
            f"--mcp-font-family-mono: {theme.typography.font_family_mono};",
            f"--mcp-font-size-xs: {theme.typography.font_size_xs};",
            f"--mcp-font-size-sm: {theme.typography.font_size_sm};",
            f"--mcp-font-size-base: {theme.typography.font_size_base};",
            f"--mcp-font-size-lg: {theme.typography.font_size_lg};",
            
            # Spacing
            f"--mcp-spacing-xs: {theme.spacing.xs};",
            f"--mcp-spacing-sm: {theme.spacing.sm};",
            f"--mcp-spacing-md: {theme.spacing.md};",
            f"--mcp-spacing-lg: {theme.spacing.lg};",
            f"--mcp-spacing-xl: {theme.spacing.xl};",
            f"--mcp-spacing-xxl: {theme.spacing.xxl};",
            
            # Effects
            f"--mcp-border-radius-sm: {theme.effects.border_radius_sm};",
            f"--mcp-border-radius-md: {theme.effects.border_radius_md};",
            f"--mcp-border-radius-lg: {theme.effects.border_radius_lg};",
            f"--mcp-border-radius-pill: {theme.effects.border_radius_pill};",
            f"--mcp-border-radius-full: {theme.effects.border_radius_full};",
            f"--mcp-shadow-sm: {theme.effects.shadow_sm};",
            f"--mcp-shadow-md: {theme.effects.shadow_md};",
            f"--mcp-shadow-lg: {theme.effects.shadow_lg};",
            f"--mcp-shadow-xl: {theme.effects.shadow_xl};",
            f"--mcp-backdrop-blur: {theme.effects.backdrop_blur};",
            f"--mcp-backdrop-opacity: {theme.effects.backdrop_opacity};",
            f"--mcp-transition-fast: {theme.effects.transition_fast};",
            f"--mcp-transition-normal: {theme.effects.transition_normal};",
            f"--mcp-transition-slow: {theme.effects.transition_slow};",
            
            # Toolbar
            f"--mcp-toolbar-min-width: {theme.toolbar.min_width};",
            f"--mcp-toolbar-max-width: {theme.toolbar.max_width};",
            f"--mcp-toolbar-opacity: {theme.toolbar.default_opacity};",
            f"--mcp-toolbar-animation-duration: {theme.toolbar.animation_duration};"
        ]
        
        return f":root {{\n  {chr(10).join(css_vars)}\n}}"
    
    def export_theme(self, theme_id: str) -> Optional[str]:
        """Export theme configuration as JSON"""
        theme = self.get_theme(theme_id)
        if not theme:
            return None
        
        return theme.model_dump_json(indent=2)
    
    def import_theme(self, json_data: str) -> Optional[str]:
        """Import theme from JSON and return the custom ID"""
        try:
            theme_data = json.loads(json_data)
            theme = ThemeDefinition(**theme_data)
            return self.register_custom_theme(theme)
        except Exception as e:
            logger.error(f"Failed to import theme: {e}")
            return None
    
    def reset_to_default(self) -> None:
        """Reset to default corporate theme"""
        self.current_theme_id = "corporate"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get theme registry statistics"""
        categories = {}
        for theme in self.themes.values():
            categories[theme.category.value] = categories.get(theme.category.value, 0) + 1
        
        return {
            "total": len(self.themes),
            "builtin": len(BUILTIN_THEMES),
            "custom": len(self.custom_themes),
            "categories": categories,
            "current_theme": self.current_theme_id
        }

# Global theme registry
theme_registry = ThemeRegistry()

# Parameter models for tools
class ListThemesParams(BaseModel):
    """Parameters for listing themes"""
    filter_type: Literal["all", "builtin", "custom"] = Field(default="all", description="Filter themes by type")

class SetThemeParams(BaseModel):
    """Parameters for setting active theme"""
    theme_id: str = Field(description="Theme identifier to apply")
    persist: bool = Field(default=True, description="Whether to persist theme preference")

class GetThemeParams(BaseModel):
    """Parameters for getting theme details"""
    theme_id: Optional[str] = Field(default=None, description="Theme ID (current theme if not specified)")
    include_variables: bool = Field(default=False, description="Include CSS variables in response")

class CreateThemeParams(BaseModel):
    """Parameters for creating custom theme"""
    id: str = Field(description="Unique theme identifier")
    name: str = Field(description="Human-readable theme name")
    description: str = Field(description="Theme description")
    base_theme: Optional[str] = Field(default=None, description="Base theme to extend")
    colors: Optional[Dict[str, str]] = Field(default=None, description="Color overrides")
    effects: Optional[Dict[str, str]] = Field(default=None, description="Effect overrides")

class ResetThemeParams(BaseModel):
    """Parameters for resetting theme"""
    clear_storage: bool = Field(default=True, description="Clear stored theme preferences")

# Theme tool implementations
async def browser_theme_list(context: Context, params: ListThemesParams) -> Dict[str, Any]:
    """List all available themes"""
    themes = theme_registry.list_themes(params.filter_type)
    
    theme_list = [
        {
            "id": theme.id,
            "name": theme.name,
            "description": theme.description,
            "category": theme.category.value,
            "tags": theme.tags,
            "accessibility": {
                "contrast_ratio": theme.accessibility.contrast_ratio,
                "supports_high_contrast": theme.accessibility.supports_high_contrast,
                "supports_reduced_motion": theme.accessibility.supports_reduced_motion,
                "supports_dark_mode": theme.accessibility.supports_dark_mode
            },
            "preview": theme.preview.model_dump()
        }
        for theme in themes
    ]
    
    return {
        "status": "themes_listed",
        "filter": params.filter_type,
        "count": len(theme_list),
        "themes": theme_list,
        "current_theme": theme_registry.current_theme_id,
        "description": f"Found {len(theme_list)} available themes"
    }

async def browser_theme_set(context: Context, params: SetThemeParams) -> Dict[str, Any]:
    """Set active theme"""
    theme = theme_registry.get_theme(params.theme_id)
    if not theme:
        available_themes = list(theme_registry.themes.keys())
        return {
            "status": "error",
            "error": f"Theme '{params.theme_id}' not found",
            "available_themes": available_themes
        }
    
    # Set the theme
    theme_registry.set_current_theme(params.theme_id)
    
    # Generate CSS for theme application
    css_variables = theme_registry.generate_css_variables(params.theme_id)
    
    # Apply theme via JavaScript injection
    page = await context.get_current_page()
    
    theme_script = f"""
    // Apply MCPlaywright theme: {theme.name}
    (function() {{
        try {{
            // Remove existing theme styles
            const existingStyle = document.getElementById('mcp-theme-styles');
            if (existingStyle) {{
                existingStyle.remove();
            }}
            
            // Create new theme styles
            const style = document.createElement('style');
            style.id = 'mcp-theme-styles';
            style.textContent = `{css_variables}`;
            document.head.appendChild(style);
            
            // Store theme preference
            {'localStorage.setItem("mcp-theme", "' + params.theme_id + '");' if params.persist else ''}
            
            console.log('MCPlaywright theme applied: {theme.name}');
        }} catch (error) {{
            console.error('Failed to apply MCPlaywright theme:', error);
        }}
    }})();
    """
    
    await page.add_init_script(theme_script)
    
    return {
        "status": "theme_applied",
        "theme_id": params.theme_id,
        "theme_name": theme.name,
        "description": theme.description,
        "category": theme.category.value,
        "persisted": params.persist,
        "css_variables_count": len(css_variables.split('\n')) - 2  # Exclude :root and closing brace
    }

async def browser_theme_get(context: Context, params: GetThemeParams) -> Dict[str, Any]:
    """Get current or specified theme details"""
    theme = theme_registry.get_theme(params.theme_id) if params.theme_id else theme_registry.get_current_theme()
    
    if not theme:
        return {
            "status": "error",
            "error": f"Theme '{params.theme_id}' not found"
        }
    
    result = {
        "status": "theme_details",
        "theme": {
            "id": theme.id,
            "name": theme.name,
            "description": theme.description,
            "category": theme.category.value,
            "version": theme.version,
            "author": theme.author,
            "tags": theme.tags,
            "accessibility": theme.accessibility.model_dump(),
            "preview": theme.preview.model_dump()
        },
        "is_current": theme.id == theme_registry.current_theme_id
    }
    
    if params.include_variables:
        result["css_variables"] = theme_registry.generate_css_variables(theme.id)
    
    return result

async def browser_theme_create(context: Context, params: CreateThemeParams) -> Dict[str, Any]:
    """Create a custom theme"""
    # Get base theme
    base_theme = theme_registry.get_theme(params.base_theme) if params.base_theme else BUILTIN_THEMES["corporate"]
    if not base_theme:
        return {
            "status": "error",
            "error": f"Base theme '{params.base_theme}' not found"
        }
    
    # Create custom theme by extending base theme
    custom_colors = base_theme.colors.model_copy()
    if params.colors:
        for key, value in params.colors.items():
            if hasattr(custom_colors, key):
                setattr(custom_colors, key, value)
    
    custom_effects = base_theme.effects.model_copy()
    if params.effects:
        for key, value in params.effects.items():
            if hasattr(custom_effects, key):
                setattr(custom_effects, key, value)
    
    custom_theme = ThemeDefinition(
        id=params.id,
        name=params.name,
        description=params.description,
        category=ThemeCategory.CUSTOM,
        colors=custom_colors,
        typography=base_theme.typography.model_copy(),
        spacing=base_theme.spacing.model_copy(),
        effects=custom_effects,
        toolbar=base_theme.toolbar.model_copy(),
        accessibility=base_theme.accessibility.model_copy(),
        tags=["custom"],
        preview=ThemePreview(
            background_color=custom_colors.surface,
            foreground_color=custom_colors.text_primary,
            accent_color=custom_colors.primary
        )
    )
    
    # Register the custom theme
    custom_id = theme_registry.register_custom_theme(custom_theme)
    
    return {
        "status": "theme_created",
        "theme_id": custom_id,
        "theme_name": params.name,
        "description": params.description,
        "base_theme": params.base_theme,
        "custom_properties": {
            "colors": len(params.colors or {}),
            "effects": len(params.effects or {})
        }
    }

async def browser_theme_reset(context: Context, params: ResetThemeParams) -> Dict[str, Any]:
    """Reset to default theme"""
    theme_registry.reset_to_default()
    default_theme = theme_registry.get_current_theme()
    
    # Apply default theme
    page = await context.get_current_page()
    
    reset_script = f"""
    // Reset MCPlaywright theme to default
    (function() {{
        try {{
            // Remove existing theme styles
            const existingStyle = document.getElementById('mcp-theme-styles');
            if (existingStyle) {{
                existingStyle.remove();
            }}
            
            // Apply default theme
            const style = document.createElement('style');
            style.id = 'mcp-theme-styles';
            style.textContent = `{theme_registry.generate_css_variables()}`;
            document.head.appendChild(style);
            
            // Clear storage if requested
            {'localStorage.removeItem("mcp-theme");' if params.clear_storage else ''}
            
            console.log('MCPlaywright theme reset to default: {default_theme.name}');
        }} catch (error) {{
            console.error('Failed to reset MCPlaywright theme:', error);
        }}
    }})();
    """
    
    await page.add_init_script(reset_script)
    
    return {
        "status": "theme_reset",
        "theme_id": default_theme.id,
        "theme_name": default_theme.name,
        "description": default_theme.description,
        "storage_cleared": params.clear_storage
    }