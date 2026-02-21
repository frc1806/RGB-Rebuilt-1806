"""
Vision Status Mode
Displays PhotonVision connection and target acquisition status
"""

import logging
import math
from typing import Any, Dict, Tuple

from .base_mode import AnimatedMode
from ..led_controller import dim_color

logger = logging.getLogger(__name__)


class VisionStatusMode(AnimatedMode):
    """
    Displays vision system status with animated effects.

    - Green pulse: Connected with targets detected
    - Yellow pulse: Connected, no targets
    - Red flash: Disconnected or error
    """

    def __init__(self, config, priority: int = 5):
        """
        Initialize vision status mode.

        Args:
            config: Config object
            priority: Mode priority
        """
        super().__init__("VisionStatus", priority, animation_speed=2.0)
        self.config = config

        # Get colors from config
        self.vision_ok_color = tuple(config.get_color("vision_ok"))
        self.vision_no_targets_color = tuple(config.get_color("vision_no_targets"))
        self.vision_error_color = tuple(config.get_color("vision_error"))
        self.off_color = (0, 0, 0)

        logger.info(
            f"Vision status display initialized "
            f"(ok={self.vision_ok_color}, "
            f"no_targets={self.vision_no_targets_color}, "
            f"error={self.vision_error_color})"
        )

    def render(self, section, led_controller, data: Dict[str, Any]) -> None:
        """
        Render vision status to LED section.

        Args:
            section: Section object to render to
            led_controller: LEDController instance
            data: Current robot data from Network Tables
        """
        # Get vision data
        vision_connected = data.get("vision_connected", False)
        vision_has_targets = data.get("vision_has_targets", False)

        # Determine status and color
        if not vision_connected:
            # Red flash for disconnected
            color = self.vision_error_color
            effect = "flash"
        elif vision_has_targets:
            # Green pulse for connected with targets
            color = self.vision_ok_color
            effect = "pulse"
        else:
            # Yellow pulse for connected without targets
            color = self.vision_no_targets_color
            effect = "pulse"

        # Apply effect
        if effect == "pulse":
            self._render_pulse(section, led_controller, color)
        elif effect == "flash":
            self._render_flash(section, led_controller, color)

        self.increment_frame()

    def _render_pulse(
        self,
        section,
        led_controller,
        color: Tuple[int, int, int],
    ) -> None:
        """Render smooth pulsing effect."""
        # Sine wave for smooth pulsing (0.3 to 1.0 brightness)
        brightness = 0.3 + 0.7 * (0.5 + 0.5 * math.sin(self.frame_count * 0.1))
        dimmed_color = dim_color(*color, brightness)

        # Fill entire section with pulsing color
        for i in range(section.length):
            abs_index = section.start + i
            led_controller.set_pixel(abs_index, *dimmed_color)

    def _render_flash(
        self,
        section,
        led_controller,
        color: Tuple[int, int, int],
    ) -> None:
        """Render flashing effect (on/off)."""
        # Flash every 15 frames (0.5s at 30fps)
        is_on = (self.frame_count // 15) % 2 == 0

        if is_on:
            flash_color = color
        else:
            flash_color = self.off_color

        # Fill entire section
        for i in range(section.length):
            abs_index = section.start + i
            led_controller.set_pixel(abs_index, *flash_color)

    def __repr__(self) -> str:
        """String representation."""
        return f"VisionStatusMode(priority={self.priority})"
