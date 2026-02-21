"""
Notifications Mode
Displays robot status notifications with animations
"""

import logging
import math
from typing import Any, Dict, Optional, Tuple

from .base_mode import AnimatedMode
from ..led_controller import wheel_color, dim_color

logger = logging.getLogger(__name__)


class NotificationMode(AnimatedMode):
    """
    Displays robot status notifications with various animations.

    Supported notifications:
    - Flywheel at speed: Spinning rainbow animation
    - Climb complete: Success animation (green pulse)
    - Custom notifications: Configurable colors and effects
    """

    def __init__(self, config, priority: int = 7):
        """
        Initialize notification mode.

        Args:
            config: Config object
            priority: Mode priority
        """
        super().__init__("Notifications", priority, animation_speed=3.0)
        self.config = config

        # Current notification being displayed
        self.current_notification: Optional[str] = None

        logger.info("Notification display initialized")

    def set_notification(self, notification_type: str) -> None:
        """
        Set the current notification to display.

        Args:
            notification_type: Type of notification to display
        """
        if notification_type != self.current_notification:
            self.current_notification = notification_type
            self.reset()
            logger.info(f"Displaying notification: {notification_type}")

    def render(self, section, led_controller, data: Dict[str, Any]) -> None:
        """
        Render notification to LED section.

        Args:
            section: Section object to render to
            led_controller: LEDController instance
            data: Current robot data from Network Tables
        """
        if not self.current_notification:
            # No notification, clear section
            for i in range(section.length):
                abs_index = section.start + i
                led_controller.set_pixel(abs_index, 0, 0, 0)
            return

        # Route to appropriate renderer based on notification type
        if self.current_notification == "flywheel_ready":
            self._render_flywheel(section, led_controller)
        elif self.current_notification == "climb_complete":
            self._render_climb_complete(section, led_controller)
        elif self.current_notification == "vision_acquired":
            self._render_vision_acquired(section, led_controller)
        else:
            # Default notification rendering
            self._render_default(section, led_controller)

        self.increment_frame()

    def _render_flywheel(self, section, led_controller) -> None:
        """Render spinning rainbow animation for flywheel ready."""
        for i in range(section.length):
            abs_index = section.start + i

            # Rainbow wheel effect that spins
            wheel_pos = int((i / section.length * 255 + self.frame_count * 3) % 256)
            color = wheel_color(wheel_pos)

            led_controller.set_pixel(abs_index, *color)

    def _render_climb_complete(self, section, led_controller) -> None:
        """Render success animation for climb complete."""
        # Green pulse with sparkle effect
        base_color = (0, 255, 0)

        # Pulse brightness
        brightness = 0.5 + 0.5 * math.sin(self.frame_count * 0.2)

        # Sparkle: make some LEDs brighter
        for i in range(section.length):
            abs_index = section.start + i

            # Create sparkle effect by varying brightness
            sparkle = (math.sin(self.frame_count * 0.1 + i * 0.5) + 1) * 0.5
            led_brightness = brightness * (0.5 + 0.5 * sparkle)

            color = dim_color(*base_color, led_brightness)
            led_controller.set_pixel(abs_index, *color)

    def _render_vision_acquired(self, section, led_controller) -> None:
        """Render animation for vision target acquired."""
        # Quick green flash, then fade
        if self.frame_count < 10:
            # Bright flash
            color = (0, 255, 0)
        else:
            # Fade out
            fade_frames = 20
            progress = min((self.frame_count - 10) / fade_frames, 1.0)
            brightness = 1.0 - progress
            color = dim_color(0, 255, 0, brightness)

        for i in range(section.length):
            abs_index = section.start + i
            led_controller.set_pixel(abs_index, *color)

    def _render_default(self, section, led_controller) -> None:
        """Render default notification animation."""
        # Simple blue pulse for unknown notifications
        brightness = 0.3 + 0.7 * (0.5 + 0.5 * math.sin(self.frame_count * 0.15))
        color = dim_color(0, 0, 255, brightness)

        for i in range(section.length):
            abs_index = section.start + i
            led_controller.set_pixel(abs_index, *color)

    def clear_notification(self) -> None:
        """Clear the current notification."""
        self.current_notification = None
        self.reset()

    def __repr__(self) -> str:
        """String representation."""
        return f"NotificationMode(current={self.current_notification})"


class NotificationRenderer:
    """
    Helper class to manage notification rendering.
    Maps notification types to colors and effects.
    """

    def __init__(self, config):
        """
        Initialize notification renderer.

        Args:
            config: Config object
        """
        self.config = config

        # Define notification types and their defaults
        self.notification_types = {
            "flywheel_ready": {
                "effect": "spin",
                "color": (255, 100, 0),  # Orange
            },
            "climb_complete": {
                "effect": "pulse",
                "color": (0, 255, 0),  # Green
            },
            "vision_acquired": {
                "effect": "flash",
                "color": (0, 255, 0),  # Green
            },
        }

    def get_effect(self, notification_type: str) -> str:
        """Get effect type for notification."""
        return self.notification_types.get(notification_type, {}).get(
            "effect", "pulse"
        )

    def get_color(self, notification_type: str) -> Tuple[int, int, int]:
        """Get color for notification."""
        return self.notification_types.get(notification_type, {}).get(
            "color", (0, 0, 255)
        )
