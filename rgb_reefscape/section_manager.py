"""
Section Manager Module
Manages LED strip partitioning into sections
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class Section:
    """Represents a section of the LED strip."""

    def __init__(self, name: str, start: int, length: int, section_type: str = None, **kwargs):
        """
        Initialize a section.

        Args:
            name: Section name (unique identifier)
            start: Starting LED index
            length: Number of LEDs in section
            section_type: Section type (e.g., "time_display", "notifications").
                         If None, uses name as type.
            **kwargs: Additional section properties (e.g., direction)
        """
        self.name = name
        self.start = start
        self.length = length
        self.end = start + length
        self.type = section_type if section_type else name
        self.properties = kwargs

    def contains(self, index: int) -> bool:
        """Check if an LED index is within this section."""
        return self.start <= index < self.end

    def get_relative_index(self, index: int) -> int:
        """
        Convert absolute LED index to section-relative index.

        Args:
            index: Absolute LED index

        Returns:
            Section-relative index (0 to length-1), or -1 if out of range
        """
        if self.contains(index):
            return index - self.start
        return -1

    def get_absolute_index(self, relative_index: int) -> int:
        """
        Convert section-relative index to absolute LED index.

        Args:
            relative_index: Index within section (0 to length-1)

        Returns:
            Absolute LED index, or -1 if out of range
        """
        if 0 <= relative_index < self.length:
            return self.start + relative_index
        return -1

    def get_indices(self) -> List[int]:
        """Get list of all LED indices in this section."""
        return list(range(self.start, self.end))

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"Section(name='{self.name}', start={self.start}, "
            f"length={self.length}, end={self.end})"
        )


class SectionManager:
    """Manages LED strip sections based on configuration."""

    def __init__(self, config):
        """
        Initialize section manager.

        Args:
            config: Config object
        """
        self.config = config
        self.sections: Dict[str, Section] = {}
        self._load_sections()
        self._validate_sections()
        logger.info(f"Loaded {len(self.sections)} sections: {list(self.sections.keys())}")

    def _load_sections(self) -> None:
        """Load sections from configuration."""
        sections_config = self.config.sections

        for name, section_data in sections_config.items():
            start = section_data.get("start", 0)
            length = section_data.get("length", 0)
            section_type = section_data.get("type", None)

            # Extract additional properties
            kwargs = {
                k: v
                for k, v in section_data.items()
                if k not in ("start", "length", "type")
            }

            section = Section(name, start, length, section_type=section_type, **kwargs)
            self.sections[name] = section
            logger.debug(f"Loaded section: {section} (type={section.type})")

    def _validate_sections(self) -> None:
        """Validate that sections don't overlap and fit within LED count."""
        led_count = self.config.led_count

        # Check each section is within bounds
        for name, section in self.sections.items():
            if section.start < 0:
                raise ValueError(f"Section '{name}' has negative start index")
            if section.end > led_count:
                raise ValueError(
                    f"Section '{name}' extends beyond LED count "
                    f"({section.end} > {led_count})"
                )

        # Check for overlaps
        sections_list = list(self.sections.values())
        for i, section1 in enumerate(sections_list):
            for section2 in sections_list[i + 1 :]:
                if self._sections_overlap(section1, section2):
                    raise ValueError(
                        f"Sections '{section1.name}' and '{section2.name}' overlap"
                    )

        logger.debug("Section validation passed")

    @staticmethod
    def _sections_overlap(section1: Section, section2: Section) -> bool:
        """Check if two sections overlap."""
        return not (section1.end <= section2.start or section2.end <= section1.start)

    def get_section(self, name: str) -> Optional[Section]:
        """
        Get section by name.

        Args:
            name: Section name

        Returns:
            Section object or None if not found
        """
        return self.sections.get(name)

    def get_sections_by_type(self, section_type: str) -> List[Section]:
        """
        Get all sections of a specific type.

        Args:
            section_type: Type of sections to retrieve (e.g., "time_display")

        Returns:
            List of Section objects matching the type (may be empty)
        """
        return [
            section
            for section in self.sections.values()
            if section.type == section_type
        ]

    def get_section_at_index(self, index: int) -> Optional[Section]:
        """
        Find which section contains a given LED index.

        Args:
            index: LED index

        Returns:
            Section object or None if index not in any section
        """
        for section in self.sections.values():
            if section.contains(index):
                return section
        return None

    def list_sections(self) -> List[str]:
        """Get list of all section names."""
        return list(self.sections.keys())

    def get_coverage(self) -> float:
        """
        Calculate what percentage of LEDs are covered by sections.

        Returns:
            Coverage percentage (0.0 to 1.0)
        """
        covered = set()
        for section in self.sections.values():
            covered.update(section.get_indices())

        return len(covered) / self.config.led_count if self.config.led_count > 0 else 0.0

    def get_uncovered_indices(self) -> List[int]:
        """
        Get list of LED indices not covered by any section.

        Returns:
            List of uncovered LED indices
        """
        all_indices = set(range(self.config.led_count))
        covered = set()

        for section in self.sections.values():
            covered.update(section.get_indices())

        return sorted(list(all_indices - covered))

    def __repr__(self) -> str:
        """String representation."""
        coverage = self.get_coverage() * 100
        return (
            f"SectionManager({len(self.sections)} sections, "
            f"{coverage:.1f}% coverage)"
        )
