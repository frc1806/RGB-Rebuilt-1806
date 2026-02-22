"""
Time Display Mode
Displays countdown for active/inactive game periods
"""

import logging
import time
from typing import Any, Dict, Tuple

from .base_mode import StaticMode

logger = logging.getLogger(__name__)


class TimeDisplayMode(StaticMode):
    """
    Displays time remaining in current period using LED countdown.

    - Inactive period: White LEDs counting down
    - Active period: Green LEDs counting down
    - Configurable direction: left, right, or center
    """

    def __init__(self, config, priority: int = 10):
        """
        Initialize time display mode.

        Args:
            config: Config object
            priority: Mode priority
        """
        super().__init__("TimeDisplay", priority)
        self.config = config

        # Get colors from config
        self.active_color = tuple(config.get_color("active_period"))
        self.inactive_color = tuple(config.get_color("inactive_period"))
        self.off_color = (0, 0, 0)

        # Periodic logging (tracked per section)
        self.last_log_times = {}  # Dict[section_name, last_log_time]
        self.log_interval = 2.0  # Log every 2 seconds

        logger.info(
            f"Time display initialized "
            f"(active={self.active_color}, "
            f"inactive={self.inactive_color})"
        )

    def render(self, section, led_controller, data: Dict[str, Any]) -> None:
        """
        Render time countdown to LED section.

        Args:
            section: Section object to render to
            led_controller: LEDController instance
            data: Current robot data from Network Tables
        """
        # Get direction from section properties (defaults to "right" if not specified)
        direction = section.properties.get("direction", "right")

        # Get time data
        goal_active = data.get("goal_active", False)
        time_remaining = data.get("time_remaining", 0.0)

        # Always use 15 seconds as max for better resolution
        # This gives drivers precise timing info in the critical last 15 seconds
        MAX_DISPLAY_TIME = 15.0

        # Determine color based on active/inactive
        color = self.active_color if goal_active else self.inactive_color

        # Calculate how many LEDs should be lit based on time remaining
        # Clip to 100% when more than 15 seconds remain (show all LEDs on)
        if time_remaining >= MAX_DISPLAY_TIME:
            ratio = 1.0  # 100% filled
        elif MAX_DISPLAY_TIME > 0:
            ratio = max(0.0, time_remaining / MAX_DISPLAY_TIME)
        else:
            ratio = 0.0

        leds_to_light = int(ratio * section.length)

        # Periodic logging (every 2 seconds, tracked per section)
        current_time = time.time()
        last_log_time = self.last_log_times.get(section.name, 0)
        if current_time - last_log_time >= self.log_interval:
            match_state = data.get("match_state", "unknown")
            logger.info(
                f"Time Display [{section.name}]: "
                f"direction={direction}, "
                f"state={match_state}, "
                f"goal_active={goal_active}, "
                f"time={time_remaining:.1f}/{MAX_DISPLAY_TIME:.1f}s, "
                f"ratio={ratio:.2%}, "
                f"LEDs={leds_to_light}/{section.length}, "
                f"color={'active' if goal_active else 'inactive'}"
            )
            self.last_log_times[section.name] = current_time

        # Render based on direction
        if direction == "left":
            self._render_left(section, led_controller, leds_to_light, color)
        elif direction == "right":
            self._render_right(section, led_controller, leds_to_light, color)
        elif direction == "center":
            self._render_center(section, led_controller, leds_to_light, color)
        else:
            logger.warning(f"Unknown direction: {direction}, using right")
            self._render_right(section, led_controller, leds_to_light, color)

    def _render_left(
        self,
        section,
        led_controller,
        leds_to_light: int,
        color: Tuple[int, int, int],
    ) -> None:
        """Render countdown from left (LEDs turn off from right to left)."""
        for i in range(section.length):
            abs_index = section.start + i
            if i < leds_to_light:
                led_controller.set_pixel(abs_index, *color)
            else:
                led_controller.set_pixel(abs_index, *self.off_color)

    def _render_right(
        self,
        section,
        led_controller,
        leds_to_light: int,
        color: Tuple[int, int, int],
    ) -> None:
        """Render countdown from right (LEDs turn off from left to right)."""
        for i in range(section.length):
            abs_index = section.start + i
            if i >= (section.length - leds_to_light):
                led_controller.set_pixel(abs_index, *color)
            else:
                led_controller.set_pixel(abs_index, *self.off_color)

    def _render_center(
        self,
        section,
        led_controller,
        leds_to_light: int,
        color: Tuple[int, int, int],
    ) -> None:
        """Render countdown from center (LEDs turn off from edges toward center)."""
        center = section.length // 2
        half_lit = leds_to_light // 2

        for i in range(section.length):
            abs_index = section.start + i
            distance_from_center = abs(i - center)

            if distance_from_center <= half_lit:
                led_controller.set_pixel(abs_index, *color)
            else:
                led_controller.set_pixel(abs_index, *self.off_color)

    def update(self, data: Dict[str, Any]) -> None:
        """
        Update time display state.

        Args:
            data: Current robot data from Network Tables
        """
        # Estimate max_time based on match state if not provided
        match_state = data.get("match_state", "pre-match")

        if match_state == "pre-match":
            data["max_time"] = 15.0  # Pre-match typically 15s
        elif match_state == "auto":
            data["max_time"] = 20.0  # Auto is 15s
        elif match_state == "teleop":
            data["max_time"] = 135.0  # Teleop is 2:15 = 135s
        elif match_state == "endgame":
            data["max_time"] = 30.0  # Endgame typically last 30s
        else:
            data["max_time"] = 30.0  # Default

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"TimeDisplayMode("
            f"active={self.active_color}, "
            f"inactive={self.inactive_color})"
        )
