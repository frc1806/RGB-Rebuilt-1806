"""
Network Tables Client Module
Handles communication with RoboRio via Network Tables
"""

import asyncio
import logging
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class NetworkTablesClient:
    """
    Network Tables client for communicating with RoboRio.
    Uses asyncio for non-blocking updates.
    """

    def __init__(self, config, simulate: bool = False):
        """
        Initialize Network Tables client.

        Args:
            config: Config object
            simulate: Run in simulation mode with mock data
        """
        self.config = config
        self.simulate = simulate
        self.connected = False
        self.last_connection_attempt = 0

        # Debug logging
        self.last_debug_log = 0
        self.debug_log_interval = 5.0  # Log NT data every 5 seconds

        # Data storage - simple dict (no locks needed with asyncio)
        self.data: Dict[str, Any] = {
            # FMS Info
            "match_number": 0,
            "event_name": "Unknown",
            # Robot State
            "match_state": "pre-match",  # pre-match, auto, teleop, endgame
            "goal_active": False,
            "time_remaining": 0.0,
            # Vision
            "vision_connected": False,
            "vision_has_targets": False,
            # Swerve
            "swerve_modules_aligned": [False, False, False, False],
            # Mechanisms
            "flywheel_at_speed": False,
            "climb_complete": False,
            # Notifications
            "notifications": {},
        }

        if simulate or config.mock_network_tables:
            logger.info("Network Tables client initialized in SIMULATION mode")
            self.inst = None
            self.topics = {}
        else:
            try:
                import ntcore

                self.ntcore = ntcore
                self.inst = ntcore.NetworkTableInstance.getDefault()
                self.topics = {}
                self._setup_connection()
                logger.info(
                    f"Network Tables client initialized "
                    f"(server: {config.server_address})"
                )
            except ImportError as e:
                import sys
                logger.error(
                    f"ntcore library not available: {e}\n"
                    f"Python executable: {sys.executable}\n"
                    f"Python path: {sys.path[:3]}...\n"
                    f"Install with: pip install pyntcore\n"
                    f"Falling back to simulation mode"
                )
                self.simulate = True
                self.inst = None
                self.topics = {}

    def _setup_connection(self) -> None:
        """Set up Network Tables connection."""
        if self.inst is None:
            return

        # Set client mode
        self.inst.startClient4("rgb-rebuilt")

        # Set server
        server_address = self.config.server_address
        if server_address:
            self.inst.setServer(server_address)
            logger.info(f"Network Tables server set to {server_address}")

        # Subscribe to topics
        self._subscribe_topics()

    def _subscribe_topics(self) -> None:
        """Subscribe to all required Network Tables topics."""
        if self.inst is None:
            return

        table = self.inst.getTable("Robot")
        fms_table = self.inst.getTable("FMSInfo")
        led_table = self.inst.getTable("LED")

        # FMS Info
        self.topics["match_number"] = fms_table.getIntegerTopic("MatchNumber").subscribe(0)
        self.topics["event_name"] = fms_table.getStringTopic("EventName").subscribe("Unknown")

        # Robot State
        self.topics["match_state"] = table.getStringTopic("MatchState").subscribe("pre-match")
        self.topics["goal_active"] = table.getBooleanTopic("Timer/GoalActive").subscribe(False)
        self.topics["time_remaining"] = table.getDoubleTopic("Timer/TimeRemaining").subscribe(0.0)

        # Vision
        self.topics["vision_connected"] = table.getBooleanTopic("Vision/Connected").subscribe(False)
        self.topics["vision_has_targets"] = table.getBooleanTopic("Vision/HasTargets").subscribe(False)

        # Swerve
        self.topics["swerve_modules_aligned"] = table.getBooleanArrayTopic("Swerve/ModuleAligned").subscribe([False, False, False, False])

        # Mechanisms
        self.topics["flywheel_at_speed"] = table.getBooleanTopic("Flywheel/AtSpeed").subscribe(False)
        self.topics["climb_complete"] = table.getBooleanTopic("Climb/Complete").subscribe(False)

        # LED Status publishing
        self.topics["led_connected"] = led_table.getBooleanTopic("Status/Connected").publish()
        self.topics["led_error"] = led_table.getStringTopic("Status/Error").publish()

        logger.info(f"Subscribed to {len(self.topics)} Network Tables topics")

    async def connect(self) -> bool:
        """
        Attempt to connect to Network Tables server.

        Returns:
            True if connected, False otherwise
        """
        if self.simulate:
            self.connected = True
            self._generate_mock_data()
            return True

        if self.inst is None:
            return False

        self.last_connection_attempt = time.time()

        # Wait for connection with timeout
        timeout = self.config.connection_timeout
        start_time = time.time()

        while time.time() - start_time < timeout:
            if self.inst.isConnected():
                self.connected = True
                self._publish_status(True, "")
                logger.info("Connected to Network Tables server")
                return True
            await asyncio.sleep(0.1)

        logger.warning(f"Failed to connect to Network Tables server within {timeout}s")
        return False

    async def update(self) -> None:
        """Update local data from Network Tables. Called periodically from main loop."""
        if self.simulate:
            logger.debug("Using simulated/mock data (simulation mode active)")
            self._generate_mock_data()
            return

        if self.inst is None:
            logger.debug("NetworkTables instance is None, cannot update")
            return

        # Check connection status
        if not self.inst.isConnected():
            if self.connected:
                logger.warning("Lost connection to Network Tables server")
                self.connected = False
                self._publish_status(False, "Connection lost")

            # Attempt reconnect if interval elapsed
            if time.time() - self.last_connection_attempt > self.config.reconnect_interval:
                logger.info("Attempting to reconnect to Network Tables...")
                await self.connect()
            return

        # Connection is good, update data
        # Only update values if they are not None (published by robot)
        try:
            # FMS Info
            val = self.topics["match_number"].get()
            if val is not None:
                self.data["match_number"] = val
            val = self.topics["event_name"].get()
            if val is not None:
                self.data["event_name"] = val

            # Robot State
            val = self.topics["match_state"].get()
            if val is not None:
                self.data["match_state"] = val
            val = self.topics["goal_active"].get()
            if val is not None:
                self.data["goal_active"] = val
            val = self.topics["time_remaining"].get()
            if val is not None:
                self.data["time_remaining"] = val

            # Vision
            val = self.topics["vision_connected"].get()
            if val is not None:
                self.data["vision_connected"] = val
            val = self.topics["vision_has_targets"].get()
            if val is not None:
                self.data["vision_has_targets"] = val

            # Swerve
            modules = self.topics["swerve_modules_aligned"].get()
            if modules is not None and len(modules) >= 4:
                self.data["swerve_modules_aligned"] = list(modules[:4])

            # Mechanisms
            val = self.topics["flywheel_at_speed"].get()
            if val is not None:
                self.data["flywheel_at_speed"] = val
            val = self.topics["climb_complete"].get()
            if val is not None:
                self.data["climb_complete"] = val

            # Periodic debug logging
            current_time = time.time()
            if current_time - self.last_debug_log >= self.debug_log_interval:
                logger.info(
                    f"Network Tables Data: "
                    f"match_state={self.data.get('match_state')}, "
                    f"goal_active={self.data.get('goal_active')}, "
                    f"time={self.data.get('time_remaining'):.1f}s, "
                    f"flywheel={self.data.get('flywheel_at_speed')}, "
                    f"vision_connected={self.data.get('vision_connected')}, "
                    f"simulate={self.simulate}, "
                    f"connected={self.connected}"
                )
                self.last_debug_log = current_time

        except Exception as e:
            logger.error(f"Error updating Network Tables data: {e}")

    def _publish_status(self, connected: bool, error: str = "") -> None:
        """Publish LED controller status to Network Tables."""
        if self.inst is None or "led_connected" not in self.topics:
            return

        try:
            self.topics["led_connected"].set(connected)
            if error:
                self.topics["led_error"].set(error)
        except Exception as e:
            logger.error(f"Error publishing status: {e}")

    def _generate_mock_data(self) -> None:
        """Generate mock data for simulation/testing."""
        # Simulate a match in progress
        current_time = time.time()

        # Cycle through match states
        cycle_time = current_time % 60
        if cycle_time < 15:
            self.data["match_state"] = "pre-match"
            self.data["goal_active"] = False
            self.data["time_remaining"] = 15 - cycle_time
        elif cycle_time < 30:
            self.data["match_state"] = "auto"
            self.data["goal_active"] = (cycle_time % 10) < 5  # Toggle every 5s
            self.data["time_remaining"] = 30 - cycle_time
        elif cycle_time < 50:
            self.data["match_state"] = "teleop"
            self.data["goal_active"] = (cycle_time % 8) < 4  # Toggle
            self.data["time_remaining"] = 50 - cycle_time
        else:
            self.data["match_state"] = "endgame"
            self.data["goal_active"] = False
            self.data["time_remaining"] = 60 - cycle_time

        # Mock vision data
        self.data["vision_connected"] = True
        self.data["vision_has_targets"] = (current_time % 5) < 3

        # Mock swerve alignment (all aligned in simulation)
        self.data["swerve_modules_aligned"] = [True, True, True, True]

        # Mock mechanisms
        self.data["flywheel_at_speed"] = (current_time % 10) < 7
        self.data["climb_complete"] = self.data["match_state"] == "endgame"

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get data value by key.

        Args:
            key: Data key
            default: Default value if key not found

        Returns:
            Data value or default
        """
        return self.data.get(key, default)

    def is_connected(self) -> bool:
        """Check if connected to Network Tables server."""
        return self.connected

    def cleanup(self) -> None:
        """Clean up Network Tables connection."""
        logger.info("Cleaning up Network Tables client")

        if not self.simulate and self.inst:
            self._publish_status(False, "Shutting down")
            # Unsubscribe from topics
            for topic in self.topics.values():
                if hasattr(topic, "close"):
                    topic.close()

        self.connected = False

    def __repr__(self) -> str:
        """String representation."""
        status = "connected" if self.connected else "disconnected"
        mode = "simulation" if self.simulate else "real"
        return f"NetworkTablesClient({status}, {mode})"
