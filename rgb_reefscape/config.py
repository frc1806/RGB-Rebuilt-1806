"""
Configuration Management Module
Loads and validates YAML configuration
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

logger = logging.getLogger(__name__)


class Config:
    """Configuration manager for RGB-Reefscape-1806."""

    DEFAULT_CONFIG_PATHS = [
        "config.yaml",
        "/etc/rgb-reefscape/config.yaml",
        str(Path.home() / ".config" / "rgb-reefscape" / "config.yaml"),
    ]

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration.

        Args:
            config_path: Path to config file. If None, searches default locations.
        """
        self.config_path = self._find_config(config_path)
        self._data = self._load_config()
        self._validate_config()
        logger.info(f"Configuration loaded from {self.config_path}")

    def _find_config(self, config_path: Optional[str]) -> str:
        """Find configuration file."""
        if config_path:
            if os.path.exists(config_path):
                return config_path
            raise FileNotFoundError(f"Config file not found: {config_path}")

        # Search default locations
        for path in self.DEFAULT_CONFIG_PATHS:
            if os.path.exists(path):
                return path

        raise FileNotFoundError(
            f"No config file found. Searched: {', '.join(self.DEFAULT_CONFIG_PATHS)}"
        )

    def _load_config(self) -> Dict[str, Any]:
        """Load YAML configuration file."""
        try:
            with open(self.config_path, "r") as f:
                data = yaml.safe_load(f)
                if data is None:
                    raise ValueError("Config file is empty")
                return data
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file: {e}")
        except Exception as e:
            raise ValueError(f"Failed to load config: {e}")

    def _validate_config(self) -> None:
        """Validate configuration structure and values."""
        # Validate hardware section
        if "hardware" not in self._data:
            raise ValueError("Missing 'hardware' section in config")

        hw = self._data["hardware"]
        if not isinstance(hw.get("led_count"), int) or hw["led_count"] <= 0:
            raise ValueError("Invalid hardware.led_count")

        if not isinstance(hw.get("gpio_pin"), int):
            raise ValueError("Invalid hardware.gpio_pin")

        # Validate network_tables section
        if "network_tables" not in self._data:
            raise ValueError("Missing 'network_tables' section in config")

        nt = self._data["network_tables"]
        has_team = "team_number" in nt
        has_server = "server_address" in nt
        if not (has_team or has_server):
            raise ValueError(
                "Must specify either team_number or server_address in network_tables"
            )

        # Validate sections
        if "sections" not in self._data:
            raise ValueError("Missing 'sections' section in config")

        sections = self._data["sections"]
        if "time_display" not in sections:
            raise ValueError("Missing sections.time_display")
        if "notifications" not in sections:
            raise ValueError("Missing sections.notifications")

        # Validate section bounds
        led_count = hw["led_count"]
        for name, section in sections.items():
            start = section.get("start", 0)
            length = section.get("length", 0)
            if start < 0 or start >= led_count:
                raise ValueError(f"Invalid start index for section '{name}'")
            if length <= 0 or (start + length) > led_count:
                raise ValueError(f"Invalid length for section '{name}'")

        logger.debug("Configuration validation passed")

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.

        Args:
            key_path: Dot-separated path (e.g., "hardware.led_count")
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key_path.split(".")
        value = self._data

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    # Hardware properties

    @property
    def led_count(self) -> int:
        """Number of LEDs in strip."""
        return self.get("hardware.led_count", 150)

    @property
    def spi_dev(self) -> str:
        """SPI device path for LED control."""
        return self.get("hardware.spi_dev", "/dev/spidev0.0")

    @property
    def brightness(self) -> int:
        """Global brightness (0-255)."""
        return self.get("hardware.brightness", 128)

    # Legacy properties for backward compatibility (kept but deprecated)
    @property
    def gpio_pin(self) -> int:
        """GPIO pin number (deprecated, use spi_dev)."""
        return self.get("hardware.gpio_pin", 18)

    @property
    def led_freq_hz(self) -> int:
        """LED signal frequency (deprecated for SPI)."""
        return self.get("hardware.led_freq_hz", 800000)

    @property
    def dma(self) -> int:
        """DMA channel (deprecated for SPI)."""
        return self.get("hardware.dma", 10)

    @property
    def invert(self) -> bool:
        """Signal inversion (deprecated for SPI)."""
        return self.get("hardware.invert", False)

    @property
    def channel(self) -> int:
        """PWM channel (deprecated for SPI)."""
        return self.get("hardware.channel", 0)

    # Network Tables properties

    @property
    def team_number(self) -> Optional[int]:
        """FRC team number."""
        return self.get("network_tables.team_number")

    @property
    def server_address(self) -> Optional[str]:
        """Network Tables server address."""
        # Calculate from team number if not explicitly set
        if self.get("network_tables.server_address"):
            return self.get("network_tables.server_address")
        elif self.team_number:
            # FRC standard: 10.TE.AM.2
            team = self.team_number
            return f"10.{team // 100}.{team % 100}.2"
        return None

    @property
    def connection_timeout(self) -> float:
        """Network Tables connection timeout in seconds."""
        return self.get("network_tables.connection_timeout", 5.0)

    @property
    def reconnect_interval(self) -> float:
        """Network Tables reconnect interval in seconds."""
        return self.get("network_tables.reconnect_interval", 2.0)

    # Section properties

    def get_section(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get section configuration.

        Args:
            name: Section name

        Returns:
            Section dict or None
        """
        return self.get(f"sections.{name}")

    @property
    def sections(self) -> Dict[str, Dict[str, Any]]:
        """All sections configuration."""
        return self.get("sections", {})

    # Color properties

    def get_color(self, name: str) -> Tuple[int, int, int]:
        """
        Get color by name.

        Args:
            name: Color name

        Returns:
            RGB tuple (r, g, b)
        """
        color = self.get(f"colors.{name}", [0, 0, 0])
        if isinstance(color, list) and len(color) == 3:
            return tuple(color)
        return (0, 0, 0)

    @property
    def colors(self) -> Dict[str, List[int]]:
        """All color definitions."""
        return self.get("colors", {})

    # Display properties

    @property
    def fps(self) -> int:
        """Target frames per second."""
        return self.get("display.fps", 30)

    @property
    def animation_speed(self) -> float:
        """Animation speed multiplier."""
        return self.get("display.animation_speed", 1.0)

    # Notification properties

    def get_notification_priority(self, notification_type: str) -> int:
        """
        Get priority for notification type.

        Args:
            notification_type: Type of notification

        Returns:
            Priority value (higher = more important)
        """
        return self.get(f"notifications.priorities.{notification_type}", 1)

    @property
    def notification_default_duration(self) -> float:
        """Default notification duration in seconds."""
        return self.get("notifications.default_duration", 3.0)

    # Simulation properties

    @property
    def simulation_enabled(self) -> bool:
        """Whether simulation mode is enabled."""
        return self.get("simulation.enabled", False)

    @property
    def mock_network_tables(self) -> bool:
        """Whether to use mock Network Tables data."""
        return self.get("simulation.mock_network_tables", False)

    def __repr__(self) -> str:
        """String representation."""
        return f"Config(path='{self.config_path}')"
