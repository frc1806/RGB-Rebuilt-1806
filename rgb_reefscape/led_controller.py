"""
LED Controller Module
Manages WS2811/WS2812B LED strip using SPI interface
Compatible with Orange Pi 5 and Raspberry Pi 5
"""

import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class LEDController:
    """
    Controls WS2811/WS2812B LED strip via SPI interface.

    Uses SPI to encode WS2812 protocol:
    - Each bit encoded as 4 SPI bits at 3.2MHz
    - '1' bit = 0b1110 (0.9375us high, 0.3125us low) ≈ target 0.8us/0.45us
    - '0' bit = 0b1000 (0.3125us high, 0.9375us low) ≈ target 0.4us/0.85us
    - Color order: GRB (not RGB!)

    Supports both real hardware and simulation mode for development.
    """

    # WS2812 timing encoded as SPI bits (4 bits per WS2812 bit)
    # At 3.2MHz SPI, each SPI bit is ~312.5ns
    # WS2812 spec: '1'=0.8us high/0.45us low, '0'=0.4us high/0.85us low
    # Using 4 SPI bits per WS2812 bit for better timing accuracy
    BIT_1 = 0b1110  # High bit: 3 high, 1 low (0.9375us / 0.3125us)
    BIT_0 = 0b1000  # Low bit: 1 high, 3 low (0.3125us / 0.9375us)

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

        # LED buffer (in-memory representation - RGB format)
        self._buffer = [(0, 0, 0)] * led_count

        # SPI device
        self.spi = None

        if simulate:
            logger.info(
                f"LED Controller initialized in SIMULATION mode "
                f"({led_count} LEDs, SPI {spi_dev})"
            )
        else:
            try:
                import spidev

                # Parse SPI device path (e.g., "/dev/spidev0.0" -> bus 0, device 0)
                parts = spi_dev.replace("/dev/spidev", "").split(".")
                bus = int(parts[0])
                device = int(parts[1])

                self.spi = spidev.SpiDev()
                self.spi.open(bus, device)

                # SPI settings for WS2812:
                # - Speed: 3.2 MHz (optimal for 4-bit encoding at 800kHz WS2812 rate)
                # - Mode: 0 (CPOL=0, CPHA=0)
                # - Bits per word: 8
                self.spi.max_speed_hz = 3200000  # 3.2 MHz
                self.spi.mode = 0
                self.spi.bits_per_word = 8

                logger.info(
                    f"LED Controller initialized on {spi_dev} "
                    f"({led_count} LEDs, brightness {brightness}, 3.2MHz SPI)"
                )
            except ImportError:
                logger.warning(
                    "spidev library not available, falling back to simulation mode"
                )
                self.simulate = True
                self.spi = None
            except Exception as e:
                logger.error(f"Failed to initialize SPI device: {e}")
                logger.warning("Falling back to simulation mode")
                self.simulate = True
                self.spi = None

    def _encode_byte(self, byte_val: int) -> bytes:
        """
        Encode a single byte into SPI data for WS2812.

        Each bit becomes 4 SPI bits: 1110 for '1', 1000 for '0'
        One byte (8 bits) becomes 4 bytes (32 SPI bits)

        Args:
            byte_val: Value to encode (0-255)

        Returns:
            4 bytes of SPI data
        """
        # Build bit array for all 8 bits
        bits = []
        for bit_index in range(7, -1, -1):  # MSB first
            bit = (byte_val >> bit_index) & 1
            if bit:
                bits.extend([1, 1, 1, 0])  # HIGH: 1110
            else:
                bits.extend([1, 0, 0, 0])  # LOW: 1000

        # Convert 32 bits into 4 bytes
        result = bytearray(4)
        for i in range(4):
            byte_val = 0
            for j in range(8):
                byte_val = (byte_val << 1) | bits[i * 8 + j]
            result[i] = byte_val

        return bytes(result)

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
        if self.simulate:
            # In simulation mode, log a sample of the buffer for debugging
            logger.debug(f"LED Buffer (first 5): {self._buffer[:5]}")
            return

        if not self.spi:
            return

        try:
            # Build SPI data
            spi_data = bytearray()

            # Reset signal: at least 50us of low (zeros)
            # At 3.2MHz, 50us = 160 bits = 20 bytes
            # Add extra for safety
            spi_data.extend(b'\x00' * 30)

            # Encode each LED (GRB order for WS2812B)
            for r, g, b in self._buffer:
                # Apply brightness scaling
                if self.brightness < 255:
                    scale = self.brightness / 255.0
                    r = int(r * scale)
                    g = int(g * scale)
                    b = int(b * scale)

                # WS2812B uses GRB order
                # Each color byte becomes 4 SPI bytes
                spi_data.extend(self._encode_byte(g))
                spi_data.extend(self._encode_byte(r))
                spi_data.extend(self._encode_byte(b))

            # Add trailing reset for latch
            spi_data.extend(b'\x00' * 30)

            # Send to SPI
            self.spi.writebytes(list(spi_data))

        except Exception as e:
            logger.error(f"Failed to update LED strip: {e}")

    def set_brightness(self, brightness: int) -> None:
        """
        Set global brightness.

        Args:
            brightness: Brightness value (0-255)
        """
        brightness = max(0, min(255, int(brightness)))
        old_brightness = self.brightness
        self.brightness = brightness

        if old_brightness != brightness:
            logger.info(f"Brightness set to {brightness}")

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

        if self.spi:
            try:
                self.spi.close()
            except Exception as e:
                logger.error(f"Error closing SPI device: {e}")


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
