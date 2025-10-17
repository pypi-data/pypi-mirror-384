# Mathematical Mouse Precision Tools

⚠️ **IN HEAVY DEVELOPMENT - FEATURES MAY CHANGE** ⚠️

**Subpixel precision mouse control with mathematical interpolation and complex gesture patterns**

## Overview

MCPlaywright's advanced mathematical mouse tools provide unprecedented precision in browser automation. Using mathematical functions like bezier curves, smooth interpolation, and complex gesture patterns, these tools enable natural, human-like mouse movements with subpixel accuracy.

## Core Mathematical Functions

### Hermite Interpolation
**Smooth easing function for natural acceleration and deceleration**

```python
def smooth_step(t: float) -> float:
    """Hermite interpolation for smooth easing"""
    return t * t * (3.0 - 2.0 * t)
```

**Applications**: Natural mouse acceleration, organic movement patterns, human-like timing

### Quadratic Bezier Curves
**Curved mouse paths with control points for sophisticated movement**

```python
def quadratic_bezier(t: float, p0: float, p1: float, p2: float) -> float:
    """Quadratic bezier curve interpolation"""
    u = 1 - t
    return u**2 * p0 + 2 * u * t * p1 + t**2 * p2
```

**Applications**: Curved mouse paths, artistic gestures, natural cursor flow

### Cubic Bezier Curves
**Advanced curves with multiple control points for complex paths**

```python
def cubic_bezier(t: float, p0: float, p1: float, p2: float, p3: float) -> float:
    """Cubic bezier curve interpolation"""
    u = 1 - t
    return u**3 * p0 + 3 * u**2 * t * p1 + 3 * u * t**2 * p2 + t**3 * p3
```

**Applications**: Complex gesture patterns, signature simulation, artistic drawing

### Arc-Based Movement
**Circular and elliptical mouse paths for sophisticated interactions**

```python
def calculate_arc_point(
    center_x: float, center_y: float, 
    radius_x: float, radius_y: float, 
    angle: float
) -> Tuple[float, float]:
    """Calculate point on elliptical arc"""
    x = center_x + radius_x * math.cos(angle)
    y = center_y + radius_y * math.sin(angle)
    return x, y
```

**Applications**: Circular gestures, spiral movements, orbital interactions

## API Reference

### Smooth Mouse Movement

#### Basic Smooth Movement
```python
await browser_mouse_move_smooth({
    "target_x": 500,
    "target_y": 300,
    "duration": 1000,
    "easing": "smooth_step",  # smooth_step, bezier, linear
    "precision": "subpixel"   # pixel, subpixel
})
```

#### Bezier Curve Movement
```python
await browser_mouse_move_smooth({
    "target_x": 800,
    "target_y": 600,
    "duration": 1500,
    "easing": "bezier",
    "control_points": [
        {"x": 200, "y": 100},  # First control point
        {"x": 600, "y": 200}   # Second control point
    ],
    "precision": "subpixel"
})
```

### Arc-Based Movement

#### Circular Arc Movement
```python
await browser_mouse_move_arc({
    "center_x": 400,
    "center_y": 300,
    "radius": 150,
    "start_angle": 0,      # Radians
    "end_angle": 1.57,     # π/2 radians (90 degrees)
    "duration": 2000,
    "clockwise": True
})
```

#### Elliptical Arc Movement
```python
await browser_mouse_move_arc({
    "center_x": 500,
    "center_y": 400,
    "radius_x": 200,       # Horizontal radius
    "radius_y": 100,       # Vertical radius
    "start_angle": 0,
    "end_angle": 6.28,     # 2π radians (full ellipse)
    "duration": 3000,
    "precision": "subpixel"
})
```

### Complex Gesture Patterns

#### Multi-Waypoint Gesture
```python
await browser_mouse_draw_gesture({
    "waypoints": [
        {"x": 100, "y": 100, "timing": 0.0},
        {"x": 200, "y": 150, "timing": 0.25},
        {"x": 300, "y": 100, "timing": 0.5},
        {"x": 400, "y": 200, "timing": 0.75},
        {"x": 500, "y": 100, "timing": 1.0}
    ],
    "interpolation": "bezier",
    "total_duration": 2500,
    "smooth_acceleration": True
})
```

#### Signature Simulation
```python
await browser_mouse_draw_gesture({
    "waypoints": [
        # Complex signature pattern with timing
        {"x": 50, "y": 200, "timing": 0.0},
        {"x": 150, "y": 180, "timing": 0.15},
        {"x": 250, "y": 220, "timing": 0.35},
        {"x": 300, "y": 180, "timing": 0.55},
        {"x": 380, "y": 200, "timing": 0.75},
        {"x": 450, "y": 190, "timing": 1.0}
    ],
    "interpolation": "cubic_bezier",
    "pressure_simulation": True,
    "natural_variations": True,
    "total_duration": 3000
})
```

### Element Boundary Tracing

#### Trace Element Outline
```python
await browser_mouse_trace_element({
    "selector": "button.primary",
    "trace_type": "outline",   # outline, border, padding
    "speed": "medium",         # slow, medium, fast
    "precision": "subpixel",
    "smooth_corners": True
})
```

#### Custom Path Tracing
```python
await browser_mouse_trace_element({
    "selector": ".complex-shape",
    "trace_type": "custom",
    "path_algorithm": "bezier_approximation",
    "sample_points": 50,
    "smooth_interpolation": True,
    "duration": 4000
})
```

## Advanced Mathematical Concepts

### Easing Functions

#### Built-in Easing Types
```python
# Available easing functions
easing_functions = {
    "linear": lambda t: t,
    "smooth_step": lambda t: t * t * (3.0 - 2.0 * t),
    "ease_in": lambda t: t * t,
    "ease_out": lambda t: 1 - (1 - t) * (1 - t),
    "ease_in_out": lambda t: 2 * t * t if t < 0.5 else 1 - 2 * (1 - t) * (1 - t),
    "bounce": lambda t: bounce_function(t),
    "elastic": lambda t: elastic_function(t)
}
```

#### Custom Easing Function
```python
await browser_mouse_move_smooth({
    "target_x": 600,
    "target_y": 400,
    "duration": 1200,
    "easing": "custom",
    "easing_function": {
        "type": "polynomial",
        "coefficients": [0, 0, 3, -2]  # 3t² - 2t³
    }
})
```

### Subpixel Precision

#### High-Resolution Coordinates
```python
await browser_mouse_move_smooth({
    "target_x": 123.75,    # Subpixel X coordinate
    "target_y": 456.25,    # Subpixel Y coordinate
    "precision": "subpixel",
    "anti_aliasing": True,
    "duration": 800
})
```

#### Precision Validation
```python
# Verify subpixel positioning accuracy
position_data = await browser_get_mouse_position({
    "precision": "subpixel",
    "include_velocity": True,
    "include_acceleration": True
})

# Response:
{
    "x": 123.75,
    "y": 456.25,
    "velocity_x": 0.5,      # pixels/ms
    "velocity_y": -0.3,
    "acceleration_x": 0.1,   # pixels/ms²
    "acceleration_y": 0.05,
    "timestamp": "2024-01-15T10:30:45.123Z"
}
```

### Natural Movement Simulation

#### Human-Like Variations
```python
await browser_mouse_move_smooth({
    "target_x": 400,
    "target_y": 300,
    "duration": 1000,
    "natural_variations": {
        "enabled": True,
        "tremor_amplitude": 0.5,     # Slight hand tremor
        "path_deviation": 2.0,       # Natural path variation
        "speed_variation": 0.1,      # Timing inconsistency
        "micro_corrections": True    # Small adjustments
    }
})
```

#### Fatigue Simulation
```python
await browser_mouse_move_smooth({
    "target_x": 700,
    "target_y": 500,
    "duration": 1500,
    "fatigue_simulation": {
        "enabled": True,
        "tremor_increase": 0.02,     # Increasing tremor
        "speed_reduction": 0.95,     # Slightly slower
        "accuracy_decrease": 0.98    # Less precise
    }
})
```

## Performance Optimization

### Efficient Path Calculation
```python
# Pre-calculate complex paths for performance
path_data = await browser_calculate_mouse_path({
    "start": {"x": 100, "y": 100},
    "end": {"x": 500, "y": 400},
    "path_type": "bezier",
    "control_points": [{"x": 200, "y": 50}, {"x": 400, "y": 300}],
    "sample_rate": 60,  # 60 FPS
    "duration": 2000
})

# Execute pre-calculated path
await browser_execute_mouse_path({
    "path_data": path_data,
    "execution_mode": "optimized"
})
```

### Adaptive Sampling
```python
# Automatically adjust sampling based on curve complexity
await browser_mouse_move_smooth({
    "target_x": 600,
    "target_y": 350,
    "duration": 1200,
    "adaptive_sampling": {
        "enabled": True,
        "min_samples": 30,
        "max_samples": 120,
        "complexity_threshold": 0.1
    }
})
```

## Practical Applications

### UI Testing with Natural Movements

#### Form Interaction Testing
```python
# Natural form filling with human-like mouse movements
form_fields = [
    {"selector": "#first-name", "x": 150, "y": 100},
    {"selector": "#last-name", "x": 150, "y": 150},
    {"selector": "#email", "x": 150, "y": 200},
    {"selector": "#phone", "x": 150, "y": 250}
]

for i, field in enumerate(form_fields):
    if i == 0:
        # First field - direct movement
        await browser_mouse_move_smooth({
            "target_x": field["x"],
            "target_y": field["y"],
            "duration": 800,
            "easing": "ease_out"
        })
    else:
        # Subsequent fields - natural curved movement
        await browser_mouse_move_smooth({
            "target_x": field["x"],
            "target_y": field["y"],
            "duration": 600,
            "easing": "bezier",
            "control_points": [
                {"x": field["x"] - 50, "y": field["y"] - 30}
            ],
            "natural_variations": {"enabled": True}
        })
    
    await browser_click({"selector": field["selector"]})
```

### Creative Gesture Testing

#### Drawing Application Testing
```python
# Test drawing application with artistic gestures
await browser_mouse_draw_gesture({
    "waypoints": [
        # Draw a flower pattern
        {"x": 300, "y": 300, "timing": 0.0},   # Center
        {"x": 350, "y": 250, "timing": 0.125}, # Petal 1
        {"x": 300, "y": 300, "timing": 0.25},  # Back to center
        {"x": 250, "y": 250, "timing": 0.375}, # Petal 2
        {"x": 300, "y": 300, "timing": 0.5},   # Back to center
        {"x": 250, "y": 350, "timing": 0.625}, # Petal 3
        {"x": 300, "y": 300, "timing": 0.75},  # Back to center
        {"x": 350, "y": 350, "timing": 0.875}, # Petal 4
        {"x": 300, "y": 300, "timing": 1.0}    # Back to center
    ],
    "interpolation": "bezier",
    "smooth_acceleration": True,
    "pressure_simulation": True,
    "total_duration": 3000
})
```

### Game Testing Automation

#### Complex Game Interactions
```python
# RPG game character movement testing
await browser_mouse_move_arc({
    "center_x": 400,
    "center_y": 300,
    "radius": 100,
    "start_angle": 0,
    "end_angle": 6.28,  # Full circle
    "duration": 5000,
    "natural_variations": {"enabled": True},
    "game_mode": True  # Optimized for game interaction
})

# Simulate complex spell casting gesture
await browser_mouse_draw_gesture({
    "waypoints": [
        # Mystical symbol pattern
        {"x": 200, "y": 200, "timing": 0.0},
        {"x": 300, "y": 150, "timing": 0.2},
        {"x": 400, "y": 200, "timing": 0.4},
        {"x": 350, "y": 300, "timing": 0.6},
        {"x": 250, "y": 300, "timing": 0.8},
        {"x": 200, "y": 200, "timing": 1.0}
    ],
    "interpolation": "cubic_bezier",
    "mystical_effects": True,  # Special game testing mode
    "total_duration": 2500
})
```

## Error Handling and Edge Cases

### Boundary Validation
```python
# Automatic boundary checking
await browser_mouse_move_smooth({
    "target_x": 2000,  # May exceed viewport
    "target_y": 1500,
    "duration": 1000,
    "boundary_handling": {
        "mode": "clamp",  # clamp, wrap, reject
        "viewport_aware": True,
        "safe_margins": 10
    }
})
```

### Path Collision Detection
```python
# Avoid obstacles during movement
await browser_mouse_move_smooth({
    "target_x": 600,
    "target_y": 400,
    "duration": 1200,
    "obstacle_avoidance": {
        "enabled": True,
        "exclusion_zones": [
            {"x": 300, "y": 200, "width": 100, "height": 50},
            {"x": 450, "y": 300, "width": 80, "height": 80}
        ],
        "avoidance_strategy": "bezier_curve"
    }
})
```

## Browser Compatibility

### Feature Support Matrix
- **Chromium/Chrome**: Full support including subpixel precision
- **Firefox**: Full support with hardware acceleration
- **WebKit/Safari**: Basic support, limited subpixel precision
- **Edge**: Full support with enhanced performance

### Performance Optimization by Browser
```python
# Browser-specific optimizations
browser_configs = {
    "chromium": {
        "hardware_acceleration": True,
        "subpixel_precision": True,
        "high_refresh_rate": True
    },
    "firefox": {
        "smooth_scrolling": True,
        "precision_timing": True
    },
    "webkit": {
        "touch_simulation": True,
        "gesture_recognition": True
    }
}
```

The Mathematical Mouse Precision Tools provide unparalleled control over cursor movement, enabling natural, human-like interactions and sophisticated gesture patterns for comprehensive browser automation testing.