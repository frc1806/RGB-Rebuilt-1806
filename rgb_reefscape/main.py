"""
RGB-Rebuilt-1806 Main Application
FRC Robot LED Controller
"""

import argparse
import asyncio
import logging
import signal
import sys
from pathlib import Path

# Import our modules
from .config import Config
from .led_controller import LEDController
from .nt_client import NetworkTablesClient
from .section_manager import SectionManager
from .notification_queue import NotificationQueue
from .display_modes.time_display import TimeDisplayMode
from .display_modes.vision_status import VisionStatusMode
from .display_modes.swerve_alignment import SwerveAlignmentMode
from .display_modes.notifications import NotificationMode

logger = logging.getLogger(__name__)


class RGBReefscape:
    """Main application controller."""

    def __init__(self, config_path: str = None, simulate: bool = False):
        """
        Initialize RGB-Rebuilt application.

        Args:
            config_path: Path to configuration file
            simulate: Run in simulation mode
        """
        # Load configuration
        self.config = Config(config_path)

        # Override simulation mode if specified
        if simulate:
            logger.info("Simulation mode enabled via command line")

        self.simulate = simulate or self.config.simulation_enabled

        # Initialize components
        self.led_controller = LEDController(
            led_count=self.config.led_count,
            spi_dev=self.config.spi_dev,
            brightness=self.config.brightness,
            simulate=self.simulate,
        )

        self.section_manager = SectionManager(self.config)

        self.nt_client = NetworkTablesClient(
            self.config,
            simulate=self.simulate or self.config.mock_network_tables,
        )

        self.notification_queue = NotificationQueue(self.config)

        # Initialize display modes
        self.time_display = TimeDisplayMode(self.config, priority=10)
        self.vision_status = VisionStatusMode(self.config, priority=5)
        self.swerve_alignment = SwerveAlignmentMode(self.config, priority=8)
        self.notification_mode = NotificationMode(self.config, priority=7)

        # Runtime state
        self.running = False
        self.frame_count = 0
        self.fps = self.config.fps

        logger.info("RGB-Rebuilt initialized")

    async def connect_network_tables(self) -> None:
        """Connect to Network Tables server."""
        logger.info("Connecting to Network Tables...")
        connected = await self.nt_client.connect()

        if connected:
            logger.info("Network Tables connected successfully")
        else:
            logger.warning("Failed to connect to Network Tables, will retry")

    async def main_loop(self) -> None:
        """Main render loop using asyncio."""
        logger.info(f"Starting main loop at {self.fps} FPS")
        frame_delay = 1.0 / self.fps

        while self.running:
            frame_start = asyncio.get_event_loop().time()

            try:
                # Update Network Tables data
                await self.nt_client.update()

                # Get current robot data
                data = self.nt_client.data

                # Update notification queue based on robot state (if enabled)
                if self.config.notification_auto_update:
                    self.notification_queue.update_from_data(data)

                # Update display modes
                self.time_display.update(data)
                self.vision_status.update(data)
                self.swerve_alignment.update(data)

                # Render displays
                await self.render_frame(data)

                # Update LED strip
                self.led_controller.show()

                self.frame_count += 1

                # Log status periodically
                if self.frame_count % (self.fps * 10) == 0:  # Every 10 seconds
                    logger.debug(
                        f"Frame {self.frame_count}, "
                        f"NT connected: {self.nt_client.is_connected()}, "
                        f"Notifications: {self.notification_queue.size()}"
                    )

            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)

            # Frame timing
            frame_time = asyncio.get_event_loop().time() - frame_start
            sleep_time = max(0, frame_delay - frame_time)
            await asyncio.sleep(sleep_time)

    async def render_frame(self, data: dict) -> None:
        """
        Render one frame to the LED strip.

        Args:
            data: Current robot data
        """
        # Get sections by type (supports multiple sections of same type)
        time_sections = self.section_manager.get_sections_by_type("time_display")
        notification_sections = self.section_manager.get_sections_by_type("notifications")

        # Render time display to all time display sections
        for time_section in time_sections:
            self.time_display.render(time_section, self.led_controller, data)

        # Render notifications sections
        for notification_section in notification_sections:
            # Check if we have active notifications
            current_notification = self.notification_queue.peek()

            if current_notification:
                # Render highest priority notification
                self.notification_mode.set_notification(
                    current_notification.notification_type
                )
                self.notification_mode.render(
                    notification_section, self.led_controller, data
                )
            else:
                # No notifications, render default modes
                match_state = data.get("match_state", "pre-match")

                if match_state == "pre-match":
                    # Show swerve alignment during pre-match
                    self.swerve_alignment.render(
                        notification_section, self.led_controller, data
                    )
                else:
                    # Show vision status during match
                    self.vision_status.render(
                        notification_section, self.led_controller, data
                    )

    async def run(self) -> None:
        """Run the application."""
        self.running = True

        # Connect to Network Tables
        await self.connect_network_tables()

        # Start main loop
        try:
            await self.main_loop()
        except asyncio.CancelledError:
            logger.info("Main loop cancelled")
        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        """Clean shutdown."""
        logger.info("Shutting down RGB-Rebuilt...")
        self.running = False

        # Clean up components
        self.led_controller.cleanup()
        self.nt_client.cleanup()

        logger.info("Shutdown complete")


def setup_logging(verbose: bool = False) -> None:
    """
    Set up logging configuration.

    Args:
        verbose: Enable verbose (DEBUG) logging
    """
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Reduce noise from some libraries
    logging.getLogger("ntcore").setLevel(logging.WARNING)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="RGB-Rebuilt-1806: FRC Robot LED Controller"
    )

    parser.add_argument(
        "-c",
        "--config",
        type=str,
        help="Path to configuration file",
    )

    parser.add_argument(
        "-s",
        "--simulate",
        action="store_true",
        help="Run in simulation mode (no hardware required)",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    return parser.parse_args()


async def async_main() -> None:
    """Async main entry point."""
    # Parse arguments
    args = parse_args()

    # Set up logging
    setup_logging(args.verbose)

    logger.info("=" * 60)
    logger.info("RGB-Rebuilt-1806 Starting")
    logger.info("FRC Robot LED Controller for Orange Pi 5")
    logger.info("=" * 60)

    # Create application
    app = RGBReefscape(config_path=args.config, simulate=args.simulate)

    # Set up signal handlers for graceful shutdown
    loop = asyncio.get_event_loop()

    def signal_handler(sig):
        logger.info(f"Received signal {sig}, initiating shutdown...")
        app.running = False

    # Register signal handlers
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: signal_handler(s))

    # Run application
    try:
        await app.run()
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        return 1

    return 0


def main() -> int:
    """Main entry point."""
    try:
        if sys.platform == "win32":
            # Windows doesn't support signal handlers in asyncio
            # Use ProactorEventLoop
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

        return asyncio.run(async_main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
