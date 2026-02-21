# LED Section Configuration Guide

## Overview

RGB-Rebuilt-1806 supports flexible LED section configuration, allowing you to partition your LED strip into multiple sections with different purposes. This is especially useful for wrapping LEDs around the robot perimeter.

## Section Types

Sections are defined by their **type**, which determines what display mode will be rendered to them:

- **`time_display`** - Shows countdown timer for active/inactive periods
- **`notifications`** - Shows robot status and notifications
- **`custom`** - Can be extended for custom display modes

## Multiple Sections of Same Type

You can have **multiple sections of the same type**. For example, if your LED strip wraps around the robot, you can have time displays on multiple sides:

```yaml
sections:
  time_display_left:
    type: time_display
    start: 0
    length: 50
    direction: "right"

  notifications:
    type: notifications
    start: 50
    length: 50

  time_display_right:
    type: time_display
    start: 100
    length: 50
    direction: "left"
```

In this configuration:
- **LEDs 0-49**: Time display (left side, counting right)
- **LEDs 50-99**: Notifications/status
- **LEDs 100-149**: Time display (right side, counting left)

Both time display sections will show the same time information but can have different directions for visual effect.

## Configuration Format

### Basic Section Definition

```yaml
section_name:
  type: section_type       # Required: time_display, notifications, custom
  start: 0                 # Required: Starting LED index
  length: 50               # Required: Number of LEDs
  direction: "right"       # Optional: Display-specific properties
```

### Fields

| Field | Required | Description |
|-------|----------|-------------|
| `type` | Yes | Section type: `time_display`, `notifications`, etc. |
| `start` | Yes | Starting LED index (0-based) |
| `length` | Yes | Number of LEDs in this section |
| Additional fields | No | Display-specific properties (e.g., `direction` for time_display) |

### Section Names

- Must be **unique** within the configuration
- Can be any valid YAML key (use descriptive names)
- Recommend naming convention: `{type}_{location}` (e.g., `time_display_front`)

## Common Layouts

### Single Strip - Simple Layout

```yaml
sections:
  time:
    type: time_display
    start: 0
    length: 50

  status:
    type: notifications
    start: 50
    length: 100
```

### Perimeter Wrap - Multiple Sides

```yaml
sections:
  time_front:
    type: time_display
    start: 0
    length: 40
    direction: "right"

  time_back:
    type: time_display
    start: 40
    length: 40
    direction: "left"

  status_left:
    type: notifications
    start: 80
    length: 35

  status_right:
    type: notifications
    start: 115
    length: 35
```

### Three-Sided Display

```yaml
sections:
  # Front bumper - time display
  front:
    type: time_display
    start: 0
    length: 50
    direction: "center"

  # Left side - notifications
  left:
    type: notifications
    start: 50
    length: 50

  # Right side - notifications
  right:
    type: notifications
    start: 100
    length: 50
```

## Time Display Direction

Time display sections support a `direction` property:

- **`"left"`** - Countdown shrinks from right to left
- **`"right"`** - Countdown shrinks from left to right
- **`"center"`** - Countdown shrinks from both edges toward center

```yaml
time_display_left:
  type: time_display
  start: 0
  length: 50
  direction: "right"    # Counts down toward the right

time_display_right:
  type: time_display
  start: 100
  length: 50
  direction: "left"     # Counts down toward the left (opposite side)
```

This creates a **mirror effect** where both sides count down in opposite directions.

## Validation Rules

The system validates your section configuration:

1. **No Overlaps**: Sections cannot overlap in LED index ranges
2. **Within Bounds**: All sections must fit within `hardware.led_count`
3. **Valid Indices**: `start >= 0` and `start + length <= led_count`

Invalid configurations will cause an error on startup.

## Examples by Robot Type

### Swerve Drive Robot (Perimeter LEDs)

```yaml
# 150 LEDs wrapping around robot perimeter
sections:
  front_time:
    type: time_display
    start: 0
    length: 50
    direction: "center"

  left_status:
    type: notifications
    start: 50
    length: 25

  back_time:
    type: time_display
    start: 75
    length: 50
    direction: "center"

  right_status:
    type: notifications
    start: 125
    length: 25
```

### Tank Drive Robot (Front/Back)

```yaml
# 150 LEDs: front and back bumpers
sections:
  front_time:
    type: time_display
    start: 0
    length: 75
    direction: "center"

  back_status:
    type: notifications
    start: 75
    length: 75
```

### Shooter Robot (Single Strip)

```yaml
# 150 LEDs: single strip with time and status
sections:
  shooter_time:
    type: time_display
    start: 0
    length: 50
    direction: "right"

  shooter_status:
    type: notifications
    start: 50
    length: 100
```

## Advanced: Custom Section Types

You can extend the system with custom section types:

1. Create a new display mode class in `display_modes/`
2. Inherit from `DisplayMode` or `AnimatedMode`
3. Implement the `render()` method
4. Update `main.py` to instantiate and render your custom mode
5. Use your custom type in `config.yaml`

Example:
```yaml
sections:
  custom_intake:
    type: intake_status    # Custom type
    start: 0
    length: 30
    # Custom properties
    intake_state_colors:
      empty: [255, 0, 0]
      full: [0, 255, 0]
```

## Troubleshooting

### "Section validation failed: sections overlap"

Two sections have overlapping LED indices. Check your `start` and `length` values:

```yaml
# BAD - overlaps!
section1:
  start: 0
  length: 60

section2:
  start: 50    # Overlaps with section1 (ends at 60)
  length: 30

# GOOD - no overlap
section1:
  start: 0
  length: 50

section2:
  start: 50    # Starts where section1 ends
  length: 30
```

### "Section extends beyond LED count"

Section goes past the total LED count. Reduce length or adjust start:

```yaml
hardware:
  led_count: 150

sections:
  too_long:
    start: 100
    length: 60    # 100 + 60 = 160 > 150 (ERROR!)

# Fix: reduce length
  fixed:
    start: 100
    length: 50    # 100 + 50 = 150 (OK!)
```

### Sections not rendering

- Check section `type` matches expected types
- Verify sections are defined in `config.yaml`
- Check logs: `sudo journalctl -u rgb-reefscape -f`

## See Also

- [config.yaml](../config.yaml) - Main configuration file
- [README.md](../README.md) - General documentation
- [display_modes/](../rgb_reefscape/display_modes/) - Display mode implementations
