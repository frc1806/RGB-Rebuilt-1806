"""
Base Display Mode Module
Abstract base class for all display modes
"""

from abc import ABC, abstractmethod
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class DisplayMode(ABC):
    """
    Abstract base class for LED display modes.

    Each display mode knows how to render LEDs for a specific purpose
    (time display, vision status, notifications, etc.).
    """

    def __init__(self, name: str, priority: int = 0):
        """
        Initialize display mode.

        Args:
            name: Mode name
            priority: Mode priority (higher = more important)
        """
        self.name = name
        self.priority = priority
        self.active = True
        self.frame_count = 0

    @abstractmethod
    def render(self, section, led_controller, data: Dict[str, Any]) -> None:
        """
        Render this display mode to a section of LEDs.

        Args:
            section: Section object to render to
            led_controller: LEDController instance
            data: Current robot data from Network Tables
        """
        pass

    def update(self, data: Dict[str, Any]) -> None:
        """
        Update internal state based on new data.
        Called before render(). Override if needed.

        Args:
            data: Current robot data from Network Tables
        """
        pass

    def reset(self) -> None:
        """
        Reset mode state. Override if needed.
        Called when mode becomes active again.
        """
        self.frame_count = 0

    def set_active(self, active: bool) -> None:
        """
        Set active state.

        Args:
            active: Whether mode should be active
        """
        was_active = self.active
        self.active = active

        if active and not was_active:
            self.reset()
            logger.debug(f"Display mode '{self.name}' activated")
        elif not active and was_active:
            logger.debug(f"Display mode '{self.name}' deactivated")

    def is_active(self) -> bool:
        """Check if mode is currently active."""
        return self.active

    def increment_frame(self) -> None:
        """Increment frame counter. Useful for animations."""
        self.frame_count += 1

    def __repr__(self) -> str:
        """String representation."""
        status = "active" if self.active else "inactive"
        return f"{self.__class__.__name__}(name='{self.name}', priority={self.priority}, {status})"


class AnimatedMode(DisplayMode):
    """
    Base class for animated display modes.
    Provides common animation utilities.
    """

    def __init__(self, name: str, priority: int = 0, animation_speed: float = 1.0):
        """
        Initialize animated mode.

        Args:
            name: Mode name
            priority: Mode priority
            animation_speed: Animation speed multiplier
        """
        super().__init__(name, priority)
        self.animation_speed = animation_speed
        self.animation_phase = 0.0

    def update_animation(self, delta_time: float) -> None:
        """
        Update animation phase.

        Args:
            delta_time: Time since last frame in seconds
        """
        self.animation_phase += delta_time * self.animation_speed
        # Wrap phase to 0-1 range
        self.animation_phase = self.animation_phase % 1.0

    def reset(self) -> None:
        """Reset animation state."""
        super().reset()
        self.animation_phase = 0.0


class StaticMode(DisplayMode):
    """
    Base class for static (non-animated) display modes.
    """

    def __init__(self, name: str, priority: int = 0):
        """
        Initialize static mode.

        Args:
            name: Mode name
            priority: Mode priority
        """
        super().__init__(name, priority)
