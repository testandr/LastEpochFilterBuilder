"""Maxroll Planner Profile Parser.

Converts Maxroll planner JSON + game data into normalized DTOs.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.dto.models import AffixDTO, BuildDetails, IdolDTO, ItemDTO
from app.parsers.profile_selector import ProfileSelector, ProfileSelectionStrategy

logger = logging.getLogger(__name__)


class PlannerProfileParser:
    """Parses Maxroll planner profile data into DTOs."""

    # Slot mapping from planner keys to display names
    SLOT_MAPPING = {
        "altar": "Altar",
        "weapon": "Weapon",
        "offhand": "Off-hand",
        "neck": "Amulet",
        "hands": "Gloves",
        "body": "Body Armor",
        "waist": "Belt",
        "feet": "Boots",
        "finger1": "Ring 1",
        "finger2": "Ring 2",
        "relic": "Relic",
        "head": "Helmet"
    }

    # Idol size mapping
    IDOL_SIZES = {
        26: "Minor Idol (1x1)",
        27: "Humble Idol (1x2)",
        29: "Grand Idol (1x3)",
        33: "Adorned Idol (1x4)"
    }

    def __init__(self, game_data: Dict[str, Any]):
        """Initialize parser with game data.

        Args:
            game_data: The game_data dict from Maxroll
        """
        self.game_data = game_data
        self.profile_selector = ProfileSelector()

        # Validate critical game data sections
        if "affixes" not in game_data:
            raise ValueError("game_data missing 'affixes' section")
        if "uniques" not in game_data:
            raise ValueError("game_data missing 'uniques' section")
        if "itemTypes" not in game_data:
            raise ValueError("game_data missing 'itemTypes' section")

    def parse(
        self,
        planner_profile: Dict[str, Any],
        strategy: ProfileSelectionStrategy = "active"
    ) -> List[BuildDetails]:
        """Parse planner profile data into BuildDetails DTOs.

        Args:
            planner_profile: Full planner profile response dict
            strategy: Profile selection strategy

        Returns:
            List of BuildDetails (one per selected profile)
        """
        build_data = planner_profile.get("build_data")
        if not build_data:
            raise ValueError("planner_profile missing 'build_data'")

        selected_profiles = self.profile_selector.select(build_data, strategy)

        results = []
        for profile in selected_profiles:
            try:
                build_details = self._parse_profile(profile, build_data)
                results.append(build_details)
            except Exception as e:
                logger.error(
                    f"Failed to parse profile '{profile.get('name', 'unknown')}': {e}"
                )
                # Continue with other profiles

        return results

    def _parse_profile(
        self,
        profile: Dict[str, Any],
        build_data: Dict[str, Any]
    ) -> BuildDetails:
        """Parse a single profile into BuildDetails.

        Args:
            profile: Profile dict
            build_data: Parent build_data dict (for item lookups)

        Returns:
            BuildDetails DTO
        """
        name = profile.get("name", "Unknown Build")
        class_name = self._get_class_name(profile.get("class"))
        mastery = self._get_mastery_name(profile.get("class"), profile.get("mastery"))

        # Parse equipment
        items = self._parse_equipment(profile, build_data)

        # Parse idols
        idols = self._parse_idols(profile, build_data)

        return BuildDetails(
            name=name,
            class_name=class_name,
            mastery=mastery,
            items=items,
            idols=idols
        )

    def _parse_equipment(
        self,
        profile: Dict[str, Any],
        build_data: Dict[str, Any]
    ) -> List[ItemDTO]:
        """Parse equipment items from profile.

        Args:
            profile: Profile dict
            build_data: Parent build_data dict

        Returns:
            List of ItemDTO
        """
        items = []
        equipment = profile.get("items", {})

        for slot_key, slot_value in equipment.items():
            try:
                item_dto = self._parse_equipment_slot(
                    slot_key, slot_value, build_data
                )
                if item_dto:
                    items.append(item_dto)
            except Exception as e:
                logger.warning(
                    f"Failed to parse equipment slot '{slot_key}': {e}"
                )

        return items

    def _parse_equipment_slot(
        self,
        slot_key: str,
        slot_value: Any,
        build_data: Dict[str, Any]
    ) -> Optional[ItemDTO]:
        """Parse a single equipment slot.

        Args:
            slot_key: Slot name (e.g., "weapon", "body")
            slot_value: int reference, inline object, or null
            build_data: Parent build_data dict

        Returns:
            ItemDTO or None if slot is empty
        """
        if slot_value is None:
            return None

        # Resolve item data
        if isinstance(slot_value, int):
            # Reference to build_data.items
            item_data = build_data.get("items", {}).get(str(slot_value))
            if not item_data:
                logger.warning(
                    f"Item reference {slot_value} not found in build_data.items"
                )
                return None
        elif isinstance(slot_value, dict):
            # Inline item definition
            item_data = slot_value
        else:
            logger.warning(
                f"Unexpected slot value type: {type(slot_value)} for slot {slot_key}"
            )
            return None

        return self._parse_item(item_data, slot_key)

    def _parse_item(
        self,
        item_data: Dict[str, Any],
        slot_key: str
    ) -> ItemDTO:
        """Parse item data into ItemDTO.

        Args:
            item_data: Item dict from planner
            slot_key: Equipment slot key

        Returns:
            ItemDTO
        """
        # Check if unique
        unique_id = item_data.get("uniqueID")
        is_unique = unique_id is not None

        if is_unique:
            name = self._get_unique_name(unique_id)
            rarity = "Unique"
        else:
            # For normal/exalted items, use generic name based on slot
            name = self.SLOT_MAPPING.get(slot_key, slot_key.title())
            rarity = None

        # Parse affixes
        affixes = self._parse_affixes(item_data.get("affixes", []))

        # Check if exalted (has T6+ affixes) - only for non-unique items
        is_exalted = self._is_exalted(item_data) if not is_unique else False
        if is_exalted:
            rarity = "Exalted"
        elif not is_unique and affixes:
            rarity = "Rare"

        # Store raw data for reference
        additional = {
            "itemType": item_data.get("itemType"),
            "subType": item_data.get("subType"),
            "corrupted": item_data.get("corrupted", False)
        }
        if unique_id is not None:
            additional["uniqueID"] = unique_id

        return ItemDTO(
            name=name,
            slot=self.SLOT_MAPPING.get(slot_key, slot_key.title()),
            rarity=rarity,
            is_unique=is_unique,
            is_exalted=is_exalted,
            affixes=affixes,
            additional=additional
        )

    def _parse_affixes(self, affixes_data: List[Dict[str, Any]]) -> List[AffixDTO]:
        """Parse affixes into AffixDTO list.

        Args:
            affixes_data: List of affix dicts from planner

        Returns:
            List of AffixDTO
        """
        result = []

        for affix_entry in affixes_data:
            try:
                affix_dto = self._parse_affix(affix_entry)
                if affix_dto:
                    result.append(affix_dto)
            except Exception as e:
                logger.warning(f"Failed to parse affix {affix_entry}: {e}")

        return result

    def _parse_affix(self, affix_entry: Dict[str, Any]) -> Optional[AffixDTO]:
        """Parse a single affix.

        Args:
            affix_entry: Affix dict with 'id', 'tier', 'roll'

        Returns:
            AffixDTO or None if affix data not found
        """
        affix_id = affix_entry.get("id")
        if affix_id is None:
            logger.warning("Affix entry missing 'id'")
            return None

        planner_tier = affix_entry.get("tier")
        if planner_tier is None:
            logger.warning(f"Affix {affix_id} missing 'tier'")
            return None

        # Lookup in game data
        affixes_list = self.game_data.get("affixes", [])
        if affix_id >= len(affixes_list):
            logger.warning(
                f"Affix ID {affix_id} out of range (max: {len(affixes_list)-1})"
            )
            return None

        affix_data = affixes_list[affix_id]
        affix_name = affix_data.get("affixName", f"Unknown Affix {affix_id}")

        # Convert planner tier (0-based) to displayed tier (1-based)
        displayed_tier = planner_tier + 1

        return AffixDTO(
            name=affix_name,
            affix_id=affix_id,
            tier=displayed_tier
        )

    def _is_exalted(self, item_data: Dict[str, Any]) -> bool:
        """Check if item is exalted (has T6+ affixes).

        Args:
            item_data: Item dict

        Returns:
            True if item has any affix with planner tier >= 5 (displayed T6+)
        """
        affixes = item_data.get("affixes", [])
        if not affixes:
            return False

        return any(a.get("tier", -1) >= 5 for a in affixes)

    def _get_unique_name(self, unique_id: int) -> str:
        """Get unique item name from game data.

        Args:
            unique_id: Unique ID (array index)

        Returns:
            Unique item name
        """
        uniques = self.game_data.get("uniques", [])
        if unique_id >= len(uniques):
            logger.warning(
                f"Unique ID {unique_id} out of range (max: {len(uniques)-1})"
            )
            return f"Unknown Unique {unique_id}"

        unique_data = uniques[unique_id]
        return unique_data.get("name", f"Unknown Unique {unique_id}")

    def _parse_idols(
        self,
        profile: Dict[str, Any],
        build_data: Dict[str, Any]
    ) -> List[IdolDTO]:
        """Parse idols from profile.

        Args:
            profile: Profile dict
            build_data: Parent build_data dict

        Returns:
            List of IdolDTO
        """
        idols = []
        idols_data = profile.get("idols", [])

        for idx, idol_value in enumerate(idols_data):
            try:
                idol_dto = self._parse_idol_slot(idol_value, build_data, idx)
                if idol_dto:
                    idols.append(idol_dto)
            except Exception as e:
                logger.warning(f"Failed to parse idol slot {idx}: {e}")

        return idols

    def _parse_idol_slot(
        self,
        idol_value: Any,
        build_data: Dict[str, Any],
        slot_index: int
    ) -> Optional[IdolDTO]:
        """Parse a single idol slot.

        Args:
            idol_value: int reference, inline object, or null
            build_data: Parent build_data dict
            slot_index: Idol slot index (for logging)

        Returns:
            IdolDTO or None if slot is empty
        """
        if idol_value is None:
            return None

        # Resolve idol data
        if isinstance(idol_value, int):
            idol_data = build_data.get("items", {}).get(str(idol_value))
            if not idol_data:
                logger.warning(
                    f"Idol reference {idol_value} not found in build_data.items"
                )
                return None
        elif isinstance(idol_value, dict):
            idol_data = idol_value
        else:
            logger.warning(
                f"Unexpected idol value type: {type(idol_value)} at slot {slot_index}"
            )
            return None

        return self._parse_idol(idol_data)

    def _parse_idol(self, idol_data: Dict[str, Any]) -> IdolDTO:
        """Parse idol data into IdolDTO.

        Args:
            idol_data: Idol dict from planner

        Returns:
            IdolDTO
        """
        item_type = idol_data.get("itemType")

        # Get idol size/name
        size = self.IDOL_SIZES.get(item_type)
        if size is None:
            # Try to lookup in itemTypes
            item_types = self.game_data.get("itemTypes", [])
            if item_type is not None and item_type < len(item_types):
                display_name = item_types[item_type].get("displayName")
                if display_name:
                    size = display_name
                else:
                    size = f"Unknown Idol Type {item_type}"
            else:
                size = None

        name = size or "Unknown Idol"

        # Parse affixes into modifier strings
        affixes = self._parse_affixes(idol_data.get("affixes", []))
        modifiers = [f"{a.name} T{a.tier}" for a in affixes if a.tier is not None]

        # Determine rarity
        is_exalted = self._is_exalted(idol_data)
        rarity = "Exalted" if is_exalted else "Rare" if affixes else None

        return IdolDTO(
            name=name,
            size=size,
            modifiers=modifiers,
            modifier_affixes=affixes,
            rarity=rarity
        )

    def _get_class_name(self, class_id: Optional[int]) -> Optional[str]:
        """Get class name from game data.

        Args:
            class_id: Class ID

        Returns:
            Class name or None
        """
        if class_id is None:
            return None

        classes = self.game_data.get("classes", [])
        if class_id >= len(classes):
            return None

        class_data = classes[class_id]
        return class_data.get("name")

    def _get_mastery_name(
        self,
        class_id: Optional[int],
        mastery_id: Optional[int]
    ) -> Optional[str]:
        """Get mastery name from game data.

        Args:
            class_id: Class ID
            mastery_id: Mastery ID

        Returns:
            Mastery name or None
        """
        if class_id is None or mastery_id is None:
            return None

        classes = self.game_data.get("classes", [])
        if class_id >= len(classes):
            return None

        class_data = classes[class_id]
        masteries = class_data.get("masteries", [])

        if mastery_id >= len(masteries):
            return None

        mastery_data = masteries[mastery_id]
        return mastery_data.get("name")
