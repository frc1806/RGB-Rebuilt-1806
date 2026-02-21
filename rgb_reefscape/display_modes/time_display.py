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

        # Get direction from section config
        section_config = config.get_section("time_display")
        self.direction = section_config.get("direction", "right") if section_config else "right"

        # Periodic logging
        self.last_log_time = 0
        self.log_interval = 2.0  # Log every 2 seconds

        logger.info(
            f"Time display initialized "
            f"(direction={self.direction}, "
            f"active={self.active_color}, "
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
        # Get time data
        goal_active = data.get("goal_active", False)
        time_remaining = data.get("time_remaining", 0.0)
        max_time = data.get("max_time", 10.0)  # Default max time

        # Determine color based on active/inactive
        color = self.active_color if goal_active else self.inactive_color

        # Calculate how many LEDs should be lit based on time remaining
        if max_time > 0:
            ratio = max(0.0, min(1.0, time_remaining / max_time))
        else:
            ratio = 0.0

        leds_to_light = int(ratio * section.length)

        # Periodic logging (every 2 seconds)
        current_time = time.time()
        if current_time - self.last_log_time >= self.log_interval:
            match_state = data.get("match_state", "unknown")
            logger.info(
                f"Time Display [{section.name}]: "
                f"state={match_state}, "
                f"goal_active={goal_active}, "
                f"time={time_remaining:.1f}/{max_time:.1f}s, "
                f"ratio={ratio:.2%}, "
                f"LEDs={leds_to_light}/{section.length}, "
                f"color={'active' if goal_active else 'inactive'}"
            )
            self.last_log_time = current_time

        # Render based on direction
        if self.direction == "left":
            self._render_left(section, led_controller, leds_to_light, color)
        elif self.direction == "right":
            self._render_right(section, led_controller, leds_to_light, color)
        elif self.direction == "center":
            self._render_center(section, led_controller, leds_to_light, color)
        else:
            logger.warning(f"Unknown direction: {self.direction}, using right")
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
            f"TimeDisplayMode(direction={self.direction}, "
            f"active={self.active_color}, "
            f"inactive={self.inactive_color})"
        )
