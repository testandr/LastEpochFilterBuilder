"""Profile selection utilities for Maxroll Planner data.

Provides strategies for selecting which profile(s) to parse from planner data.
"""
from typing import Any, Dict, List, Literal
import logging

ProfileSelectionStrategy = Literal["active", "all"]

logger = logging.getLogger(__name__)


class ProfileSelector:
    """Handles profile selection from Maxroll planner build data."""

    def select(
        self,
        build_data: Dict[str, Any],
        strategy: ProfileSelectionStrategy = "active"
    ) -> List[Dict[str, Any]]:
        """Select profiles according to the specified strategy.

        Args:
            build_data: Planner build_data dict containing 'profiles' and 'activeProfile'
            strategy: Selection strategy ("active" or "all")

        Returns:
            List of selected profile dicts

        Raises:
            ValueError: If profiles array is empty or build_data is malformed
        """
        profiles = build_data.get("profiles")
        if profiles is None:
            raise ValueError("build_data contains no profiles array")

        if not isinstance(profiles, list):
            raise ValueError(f"profiles must be a list, got {type(profiles)}")

        if len(profiles) == 0:
            raise ValueError("profiles array is empty")

        if strategy == "active":
            return [self._select_active(build_data)]
        elif strategy == "all":
            return profiles
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    def _select_active(self, build_data: Dict[str, Any]) -> Dict[str, Any]:
        """Select the active profile.

        Args:
            build_data: Planner build_data dict

        Returns:
            The active profile dict

        Raises:
            ValueError: If activeProfile index is invalid
        """
        profiles = build_data["profiles"]
        active_index = build_data.get("activeProfile")

        if active_index is None:
            logger.warning("activeProfile not found, defaulting to first profile")
            return profiles[0]

        if not isinstance(active_index, int):
            logger.warning(
                f"activeProfile is not an int ({type(active_index)}), "
                "defaulting to first profile"
            )
            return profiles[0]

        if active_index < 0 or active_index >= len(profiles):
            logger.warning(
                f"activeProfile index {active_index} out of range "
                f"(0-{len(profiles)-1}), defaulting to first profile"
            )
            return profiles[0]

        return profiles[active_index]
