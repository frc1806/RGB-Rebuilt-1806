"""
Notification Queue Module
Priority queue for managing robot status notifications
"""

import logging
import time
from typing import Dict, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass(order=True)
class Notification:
    """
    Represents a notification to be displayed.

    Notifications are ordered by priority (higher = more important).
    """

    priority: int
    notification_type: str = field(compare=False)
    duration: float = field(compare=False)
    start_time: float = field(default_factory=time.time, compare=False)
    metadata: Dict = field(default_factory=dict, compare=False)

    def is_expired(self) -> bool:
        """Check if notification has expired based on duration."""
        elapsed = time.time() - self.start_time
        return elapsed >= self.duration

    def time_remaining(self) -> float:
        """Get remaining time for this notification."""
        elapsed = time.time() - self.start_time
        return max(0.0, self.duration - elapsed)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"Notification(type='{self.notification_type}', "
            f"priority={self.priority}, "
            f"remaining={self.time_remaining():.1f}s)"
        )


class NotificationQueue:
    """
    Priority queue for managing notifications.

    Higher priority notifications are displayed first.
    Notifications expire after their duration.
    """

    def __init__(self, config):
        """
        Initialize notification queue.

        Args:
            config: Config object
        """
        self.config = config
        self.notifications: list[Notification] = []
        self.default_duration = config.notification_default_duration

        logger.info(f"Notification queue initialized (default duration={self.default_duration}s)")

    def add(
        self,
        notification_type: str,
        priority: Optional[int] = None,
        duration: Optional[float] = None,
        metadata: Optional[Dict] = None,
    ) -> None:
        """
        Add a notification to the queue.

        Args:
            notification_type: Type of notification
            priority: Priority level (higher = more important). If None, uses config default.
            duration: Duration in seconds. If None, uses default duration.
            metadata: Additional notification data
        """
        # Get priority from config if not specified
        if priority is None:
            priority = self.config.get_notification_priority(notification_type)

        # Use default duration if not specified
        if duration is None:
            duration = self.default_duration

        # Use empty dict if no metadata
        if metadata is None:
            metadata = {}

        # Check if this notification type already exists
        existing = self.find_by_type(notification_type)
        if existing:
            # Update existing notification (reset timer)
            existing.start_time = time.time()
            existing.duration = duration
            existing.priority = priority
            existing.metadata = metadata
            logger.debug(f"Updated notification: {existing}")
        else:
            # Add new notification
            notification = Notification(
                priority=priority,
                notification_type=notification_type,
                duration=duration,
                metadata=metadata,
            )
            self.notifications.append(notification)
            self._sort()
            logger.info(f"Added notification: {notification}")

    def find_by_type(self, notification_type: str) -> Optional[Notification]:
        """
        Find notification by type.

        Args:
            notification_type: Type of notification to find

        Returns:
            Notification object or None if not found
        """
        for notification in self.notifications:
            if notification.notification_type == notification_type:
                return notification
        return None

    def remove(self, notification_type: str) -> bool:
        """
        Remove a notification from the queue.

        Args:
            notification_type: Type of notification to remove

        Returns:
            True if removed, False if not found
        """
        for i, notification in enumerate(self.notifications):
            if notification.notification_type == notification_type:
                removed = self.notifications.pop(i)
                logger.info(f"Removed notification: {removed}")
                return True
        return False

    def peek(self) -> Optional[Notification]:
        """
        Get the highest priority notification without removing it.

        Returns:
            Highest priority notification or None if queue is empty
        """
        self._cleanup_expired()

        if self.notifications:
            return self.notifications[0]
        return None

    def is_empty(self) -> bool:
        """Check if queue is empty (after removing expired notifications)."""
        self._cleanup_expired()
        return len(self.notifications) == 0

    def clear(self) -> None:
        """Clear all notifications from queue."""
        count = len(self.notifications)
        self.notifications.clear()
        if count > 0:
            logger.info(f"Cleared {count} notifications from queue")

    def size(self) -> int:
        """Get number of active notifications in queue."""
        self._cleanup_expired()
        return len(self.notifications)

    def _cleanup_expired(self) -> None:
        """Remove expired notifications from queue."""
        original_count = len(self.notifications)
        self.notifications = [n for n in self.notifications if not n.is_expired()]

        removed_count = original_count - len(self.notifications)
        if removed_count > 0:
            logger.debug(f"Removed {removed_count} expired notifications")

    def _sort(self) -> None:
        """Sort notifications by priority (highest first)."""
        self.notifications.sort(reverse=True)

    def get_all(self) -> list[Notification]:
        """
        Get all active notifications sorted by priority.

        Returns:
            List of active notifications
        """
        self._cleanup_expired()
        return self.notifications.copy()

    def update_from_data(self, data: Dict) -> None:
        """
        Update queue based on robot data.

        Automatically adds/removes notifications based on robot state.

        Args:
            data: Current robot data from Network Tables
        """
        # Check flywheel status
        #if data.get("flywheel_at_speed", False):
        #    if not self.find_by_type("flywheel_ready"):
        #        self.add("flywheel_ready")
        #else:
        #    self.remove("flywheel_ready")

        # Check climb status
        if data.get("climb_complete", False):
            if not self.find_by_type("climb_complete"):
                self.add("climb_complete", duration=5.0)  # Longer duration for success

        # Check vision acquisition
        vision_connected = data.get("vision_connected", False)
        vision_has_targets = data.get("vision_has_targets", False)

        # Add vision acquired notification on transition
        if vision_connected and vision_has_targets:
            # This would need to track previous state to detect transition
            # For now, we'll skip this auto-detection
            pass

    def __repr__(self) -> str:
        """String representation."""
        self._cleanup_expired()
        return f"NotificationQueue(size={len(self.notifications)})"
