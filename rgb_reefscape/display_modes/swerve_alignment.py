"""
Swerve Alignment Mode
Displays swerve module alignment status during pre-match
"""

import logging
from typing import Any, Dict, Tuple

from .base_mode import StaticMode

logger = logging.getLogger(__name__)


class SwerveAlignmentMode(StaticMode):
    """
    Displays swerve drive module alignment status.

    Shows 4 subsections (one per swerve module):
    - Green: Module aligned
    - Red: Module not aligned

    Modules are typically ordered: Front Left, Front Right, Back Left, Back Right
    """

    def __init__(self, config, priority: int = 5):
        """
        Initialize swerve alignment mode.

        Args:
            config: Config object
            priority: Mode priority
        """
        super().__init__("SwerveAlignment", priority)
        self.config = config

        # Get colors from config
        self.aligned_color = tuple(config.get_color("aligned"))
        self.not_aligned_color = tuple(config.get_color("not_aligned"))

        logger.info(
            f"Swerve alignment display initialized "
            f"(aligned={self.aligned_color}, "
            f"not_aligned={self.not_aligned_color})"
        )

    def render(self, section, led_controller, data: Dict[str, Any]) -> None:
        """
        Render swerve alignment status to LED section.

        Args:
            section: Section object to render to
            led_controller: LEDController instance
            data: Current robot data from Network Tables
        """
        # Get swerve module alignment data
        modules_aligned = data.get("swerve_modules_aligned", [False, False, False, False])

        # Ensure we have 4 module states
        if len(modules_aligned) < 4:
            modules_aligned = list(modules_aligned) + [False] * (4 - len(modules_aligned))

        # Divide section into 4 equal parts
        leds_per_module = section.length // 4
        remainder = section.length % 4

        # Render each module subsection
        for module_idx in range(4):
            is_aligned = modules_aligned[module_idx]
            color = self.aligned_color if is_aligned else self.not_aligned_color

            # Calculate subsection bounds
            start_offset = module_idx * leds_per_module
            # Distribute remainder LEDs to first modules
            if module_idx < remainder:
                start_offset += module_idx
                length = leds_per_module + 1
            else:
                start_offset += remainder
                length = leds_per_module

            # Render subsection
            for i in range(length):
                abs_index = section.start + start_offset + i
                led_controller.set_pixel(abs_index, *color)

    def update(self, data: Dict[str, Any]) -> None:
        """
        Update swerve alignment state.

        Args:
            data: Current robot data from Network Tables
        """
        # Only active during pre-match
        match_state = data.get("match_state", "pre-match")
        self.set_active(match_state == "pre-match")

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"SwerveAlignmentMode("
            f"aligned={self.aligned_color}, "
            f"not_aligned={self.not_aligned_color})"
        )
