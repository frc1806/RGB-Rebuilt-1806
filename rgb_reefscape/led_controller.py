"""
LED Controller Module
Manages WS2811/WS2812B LED strip using ws2812-spi library for Orange Pi 5
"""

import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class LEDController:
    """
    Controls WS2811/WS2812B LED strip with asyncio-compatible interface.
    Supports both real hardware and simulation mode for development.
    """

    def __init__(
        self,
        led_count: int,
        spi_dev: str = "/dev/spidev0.0",
        brightness: int = 128,
        simulate: bool = False,
        # Legacy parameters kept for compatibility (ignored)
        gpio_pin: int = None,
        led_freq_hz: int = None,
        dma: int = None,
        invert: bool = None,
        channel: int = None,
    ):
        """
        Initialize LED controller using SPI.

        Args:
            led_count: Number of LEDs in the strip
            spi_dev: SPI device path (e.g., "/dev/spidev0.0")
            brightness: Global brightness (0-255)
            simulate: Run in simulation mode (no hardware)
            gpio_pin: (Ignored, kept for compatibility)
            led_freq_hz: (Ignored, kept for compatibility)
            dma: (Ignored, kept for compatibility)
            invert: (Ignored, kept for compatibility)
            channel: (Ignored, kept for compatibility)
        """
        self.led_count = led_count
        self.spi_dev = spi_dev
        self.brightness = brightness
        self.simulate = simulate

        # LED buffer (in-memory representation)
        self._buffer = [(0, 0, 0)] * led_count

        if simulate:
            logger.info(
                f"LED Controller initialized in SIMULATION mode "
                f"({led_count} LEDs, SPI {spi_dev})"
            )
            self.strip = None
        else:
            try:
                from ws2812_spi import WS2812SPI

                self.strip = WS2812SPI(
                    num_leds=led_count,
                    spi_dev=spi_dev,
                )
                logger.info(
                    f"LED Controller initialized on {spi_dev} "
                    f"({led_count} LEDs, brightness {brightness})"
                )
            except ImportError:
                logger.warning(
                    "ws2812_spi library not available, falling back to simulation mode"
                )
                self.simulate = True
                self.strip = None
            except Exception as e:
                logger.error(f"Failed to initialize LED strip: {e}")
                logger.warning("Falling back to simulation mode")
                self.simulate = True
                self.strip = None

    def set_pixel(self, index: int, r: int, g: int, b: int) -> None:
        """
        Set a single pixel color.

        Args:
            index: LED index (0 to led_count-1)
            r: Red value (0-255)
            g: Green value (0-255)
            b: Blue value (0-255)
        """
        if not (0 <= index < self.led_count):
            logger.warning(f"LED index {index} out of range (0-{self.led_count-1})")
            return

        # Clamp values to 0-255
        r = max(0, min(255, int(r)))
        g = max(0, min(255, int(g)))
        b = max(0, min(255, int(b)))

        # Update buffer
        self._buffer[index] = (r, g, b)

        # Update hardware if not simulating
        if not self.simulate and self.strip:
            self.strip.set_pixel(index, r, g, b)

    def set_range(
        self,
        start: int,
        end: int,
        r: int,
        g: int,
        b: int,
    ) -> None:
        """
        Set a range of pixels to the same color.

        Args:
            start: Starting LED index (inclusive)
            end: Ending LED index (exclusive)
            r: Red value (0-255)
            g: Green value (0-255)
            b: Blue value (0-255)
        """
        for i in range(start, end):
            self.set_pixel(i, r, g, b)

    def get_pixel(self, index: int) -> Tuple[int, int, int]:
        """
        Get the color of a pixel from buffer.

        Args:
            index: LED index

        Returns:
            Tuple of (r, g, b) values
        """
        if 0 <= index < self.led_count:
            return self._buffer[index]
        return (0, 0, 0)

    def clear(self) -> None:
        """Clear all LEDs (set to black)."""
        self.set_range(0, self.led_count, 0, 0, 0)

    def fill(self, r: int, g: int, b: int) -> None:
        """
        Fill all LEDs with a single color.

        Args:
            r: Red value (0-255)
            g: Green value (0-255)
            b: Blue value (0-255)
        """
        self.set_range(0, self.led_count, r, g, b)

    def show(self) -> None:
        """
        Update the LED strip with current buffer.
        This is async-compatible and can be called from async context.
        """
        if not self.simulate and self.strip:
            try:
                self.strip.show()
            except Exception as e:
                logger.error(f"Failed to update LED strip: {e}")
        elif self.simulate:
            # In simulation mode, log a sample of the buffer for debugging
            logger.debug(f"LED Buffer (first 5): {self._buffer[:5]}")

    def set_brightness(self, brightness: int) -> None:
        """
        Set global brightness.

        Note: ws2812-spi doesn't have hardware brightness control.
        This stores the value but requires re-rendering pixels with
        adjusted colors to take effect.

        Args:
            brightness: Brightness value (0-255)
        """
        brightness = max(0, min(255, int(brightness)))
        old_brightness = self.brightness
        self.brightness = brightness

        if old_brightness != brightness:
            logger.info(f"Brightness set to {brightness} (requires re-render to apply)")

    def get_buffer(self) -> list:
        """
        Get a copy of the current LED buffer.

        Returns:
            List of (r, g, b) tuples
        """
        return self._buffer.copy()

    def cleanup(self) -> None:
        """Clean up resources and turn off LEDs."""
        logger.info("Cleaning up LED controller")
        self.clear()
        self.show()


# Utility functions for color manipulation


def dim_color(r: int, g: int, b: int, factor: float) -> Tuple[int, int, int]:
    """
    Dim a color by a factor.

    Args:
        r, g, b: RGB values
        factor: Dimming factor (0.0 = black, 1.0 = original)

    Returns:
        Dimmed (r, g, b) tuple
    """
    factor = max(0.0, min(1.0, factor))
    return (
        int(r * factor),
        int(g * factor),
        int(b * factor),
    )


def blend_colors(
    r1: int,
    g1: int,
    b1: int,
    r2: int,
    g2: int,
    b2: int,
    ratio: float,
) -> Tuple[int, int, int]:
    """
    Blend two colors.

    Args:
        r1, g1, b1: First color RGB
        r2, g2, b2: Second color RGB
        ratio: Blend ratio (0.0 = first color, 1.0 = second color)

    Returns:
        Blended (r, g, b) tuple
    """
    ratio = max(0.0, min(1.0, ratio))
    return (
        int(r1 * (1 - ratio) + r2 * ratio),
        int(g1 * (1 - ratio) + g2 * ratio),
        int(b1 * (1 - ratio) + b2 * ratio),
    )


def wheel_color(pos: int) -> Tuple[int, int, int]:
    """
    Generate rainbow colors across 0-255 positions.

    Args:
        pos: Position in color wheel (0-255)

    Returns:
        RGB tuple
    """
    pos = pos % 256

    if pos < 85:
        return (pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return (255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return (0, pos * 3, 255 - pos * 3)
