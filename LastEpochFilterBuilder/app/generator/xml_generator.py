"""XML Generator for Last Epoch Loot Filter.

Serializes OptimizedRule objects into valid Last Epoch ItemFilter XML.

This module is responsible for:
- Converting OptimizationResult into Last Epoch XML format
- Mapping categories to XML condition structures
- Assigning sequential Order values
- Applying style defaults
- Validating rule structure before generation
- Failing explicitly when rules cannot be represented correctly

Does NOT perform:
- Rule optimization or pruning (handled by RuleOptimizer)
- Priority sorting (handled by RuleOptimizer)
- Semantic analysis (handled by Analyzer)
"""

import xml.etree.ElementTree as ET
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path

from .rule_models import OptimizationResult, OptimizedRule
from .equipment_type_mapper import map_equipment_type, EquipmentTypeMappingError
from .idol_size_mapper import map_idol_size, IdolSizeMappingError


class XMLGenerationError(Exception):
    """Base exception for XML generation errors."""
    pass


class UnsupportedMixedAffixTierError(XMLGenerationError):
    """Raised when a rule has mixed affix tier requirements that cannot be represented in XML."""
    pass


class MissingIDError(XMLGenerationError):
    """Raised when a required numeric ID is missing."""
    pass


class UnsupportedCategoryError(XMLGenerationError):
    """Raised when a rule category is not supported."""
    pass


class ValidationError(XMLGenerationError):
    """Raised when validation fails before XML generation."""
    pass


# Default metadata values
DEFAULT_FILTER_NAME = "Last Epoch Smart Loot Filter"
DEFAULT_GAME_VERSION = "1.4.7"
DEFAULT_FILTER_VERSION = 0
DEFAULT_FILTER_ICON = 0
DEFAULT_FILTER_ICON_COLOR = 0

# Maximum rules budget
MAX_RULES = 140

# Style defaults by category
STYLE_EXALTED = {
    "recolor": True,
    "color": 2,
    "emphasized": False,
    "SoundId": 0,
    "MapIconId": 0,
    "BeamOverride": False,
    "BeamSizeOverride": "NONE",
    "BeamColorOverride": 0,
}

STYLE_IDOL = {
    "recolor": True,
    "color": 4,
    "emphasized": False,
    "SoundId": 0,
    "MapIconId": 0,
    "BeamOverride": False,
    "BeamSizeOverride": "NONE",
    "BeamColorOverride": 0,
}

STYLE_UNIQUE = {
    "recolor": False,
    "color": 0,
    "emphasized": False,
    "SoundId": 0,
    "MapIconId": 0,
    "BeamOverride": False,
    "BeamSizeOverride": "NONE",
    "BeamColorOverride": 0,
}


def _get_style_for_category(category: str) -> Dict[str, Any]:
    """Get style defaults for a given category."""
    if category == "exalted":
        return STYLE_EXALTED.copy()
    elif category == "idol":
        return STYLE_IDOL.copy()
    elif category == "unique":
        return STYLE_UNIQUE.copy()
    else:
        raise UnsupportedCategoryError(f"Unknown category: {category}")


def _validate_optimization_result(result: OptimizationResult) -> None:
    """Validate OptimizationResult before generation.

    Args:
        result: OptimizationResult to validate

    Raises:
        ValidationError: If validation fails
    """
    if not result.success:
        raise ValidationError(
            f"OptimizationResult success is False: {result.message}"
        )

    if result.final_count > MAX_RULES:
        raise ValidationError(
            f"Rule count {result.final_count} exceeds maximum {MAX_RULES}"
        )

    if result.exceeds_budget:
        raise ValidationError(
            f"OptimizationResult exceeds_budget flag is True"
        )


def _validate_exalted_rule(rule: OptimizedRule, index: int) -> None:
    """Validate exalted rule structure.

    Args:
        rule: OptimizedRule to validate
        index: Rule index for error messages

    Raises:
        ValidationError: If validation fails
    """
    if not rule.item_types:
        raise ValidationError(
            f"Exalted rule at index {index} has empty item_types"
        )

    if not rule.affixes:
        raise ValidationError(
            f"Exalted rule at index {index} has empty affixes"
        )

    # Check for missing affix IDs
    for affix_id, name, tier in rule.affixes:
        if affix_id is None:
            raise MissingIDError(
                f"Exalted rule at index {index}: affix '{name}' T{tier} has no numeric ID. "
                f"Cannot generate valid AffixCondition."
            )

    # Check for mixed tiers
    tiers = {tier for _, _, tier in rule.affixes}
    if len(tiers) > 1:
        affix_desc = ", ".join(f"{name} T{tier}" for _, name, tier in sorted(rule.affixes))
        raise UnsupportedMixedAffixTierError(
            f"Exalted rule at index {index} has mixed affix tier requirements: {affix_desc}. "
            f"XML AffixCondition requires single comparisonValue for all affixes. "
            f"Tiers: {sorted(tiers)}"
        )


def _validate_idol_rule(rule: OptimizedRule, index: int) -> None:
    """Validate idol rule structure.

    Args:
        rule: OptimizedRule to validate
        index: Rule index for error messages

    Raises:
        ValidationError: If validation fails
    """
    if not rule.idol_sizes:
        raise ValidationError(
            f"Idol rule at index {index} has empty idol_sizes"
        )

    if not rule.modifiers:
        raise ValidationError(
            f"Idol rule at index {index} has empty modifiers"
        )

    # Check for missing modifier IDs
    for modifier_id, name, tier in rule.modifiers:
        if modifier_id is None:
            raise MissingIDError(
                f"Idol rule at index {index}: modifier '{name}' has no numeric ID. "
                f"Cannot generate valid AffixCondition."
            )


def _validate_unique_rule(rule: OptimizedRule, index: int) -> None:
    """Validate unique rule structure.

    Args:
        rule: OptimizedRule to validate
        index: Rule index for error messages

    Raises:
        ValidationError: If validation fails
    """
    if not rule.unique_items:
        raise ValidationError(
            f"Unique rule at index {index} has empty unique_items"
        )

    # Check for missing unique IDs
    for unique_id, name in rule.unique_items:
        if unique_id is None:
            raise MissingIDError(
                f"Unique rule at index {index}: unique '{name}' has no numeric ID. "
                f"Cannot generate valid UniqueModifiersCondition."
            )


def _validate_rules(rules: List[OptimizedRule]) -> None:
    """Validate all rules before generation.

    Args:
        rules: List of OptimizedRule objects

    Raises:
        ValidationError: If validation fails
        UnsupportedCategoryError: If unknown category encountered
    """
    for index, rule in enumerate(rules):
        if rule.category == "exalted":
            _validate_exalted_rule(rule, index)
        elif rule.category == "idol":
            _validate_idol_rule(rule, index)
        elif rule.category == "unique":
            _validate_unique_rule(rule, index)
        else:
            raise UnsupportedCategoryError(
                f"Rule at index {index} has unknown category: {rule.category}"
            )


def _create_rarity_condition(parent: ET.Element) -> None:
    """Create RarityCondition for exalted items.

    Args:
        parent: Parent conditions element
    """
    condition = ET.SubElement(parent, "Condition")
    condition.set("{http://www.w3.org/2001/XMLSchema-instance}type", "RarityCondition")
    rarity = ET.SubElement(condition, "rarity")
    rarity.text = "EXALTED"


def _create_subtype_condition_exalted(parent: ET.Element, rule: OptimizedRule, index: int) -> None:
    """Create SubTypeCondition for exalted equipment.

    Args:
        parent: Parent conditions element
        rule: OptimizedRule to serialize
        index: Rule index for error messages

    Raises:
        EquipmentTypeMappingError: If item_type cannot be mapped
    """
    condition = ET.SubElement(parent, "Condition")
    condition.set("{http://www.w3.org/2001/XMLSchema-instance}type", "SubTypeCondition")
    type_elem = ET.SubElement(condition, "type")

    # Map each item type
    for item_type, sub_type in rule.item_types:
        try:
            equipment_type = map_equipment_type(item_type, sub_type)
            eq_type_elem = ET.SubElement(type_elem, "EquipmentType")
            eq_type_elem.text = equipment_type
        except EquipmentTypeMappingError as e:
            raise XMLGenerationError(
                f"Exalted rule at index {index} (category={rule.category}, slot={rule.slot}): "
                f"Cannot map item_type {item_type}: {e}"
            )

    # subTypes always empty
    ET.SubElement(condition, "subTypes")


def _create_subtype_condition_idol(parent: ET.Element, rule: OptimizedRule, index: int) -> None:
    """Create SubTypeCondition for idol sizes.

    Args:
        parent: Parent conditions element
        rule: OptimizedRule to serialize
        index: Rule index for error messages

    Raises:
        IdolSizeMappingError: If idol size cannot be mapped
    """
    condition = ET.SubElement(parent, "Condition")
    condition.set("{http://www.w3.org/2001/XMLSchema-instance}type", "SubTypeCondition")
    type_elem = ET.SubElement(condition, "type")

    # Map each idol size
    for size in rule.idol_sizes:
        try:
            equipment_type = map_idol_size(size)
            eq_type_elem = ET.SubElement(type_elem, "EquipmentType")
            eq_type_elem.text = equipment_type
        except IdolSizeMappingError as e:
            raise XMLGenerationError(
                f"Idol rule at index {index}: Cannot map idol size '{size}': {e}"
            )

    # subTypes always empty
    ET.SubElement(condition, "subTypes")


def _create_affix_condition_exalted(parent: ET.Element, rule: OptimizedRule) -> None:
    """Create AffixCondition for exalted affixes.

    Args:
        parent: Parent conditions element
        rule: OptimizedRule to serialize

    Note:
        Assumes validation has already confirmed all affixes have same tier
        and all affix IDs are present.
    """
    condition = ET.SubElement(parent, "Condition")
    condition.set("{http://www.w3.org/2001/XMLSchema-instance}type", "AffixCondition")

    # Affixes
    affixes_elem = ET.SubElement(condition, "affixes")
    for affix_id, name, tier in sorted(rule.affixes):
        int_elem = ET.SubElement(affixes_elem, "int")
        int_elem.text = str(affix_id)

    # Tier requirement (all affixes have same tier after validation)
    tier = next(iter(rule.affixes))[2]

    comparsion = ET.SubElement(condition, "comparsion")
    comparsion.text = "MORE_OR_EQUAL"

    comparsion_value = ET.SubElement(condition, "comparsionValue")
    comparsion_value.text = str(tier)

    # Required count (all affixes required)
    min_on_same = ET.SubElement(condition, "minOnTheSameItem")
    min_on_same.text = str(len(rule.affixes))

    # Combined comparison
    combined_comp = ET.SubElement(condition, "combinedComparsion")
    combined_comp.text = "ANY"

    combined_value = ET.SubElement(condition, "combinedComparsionValue")
    combined_value.text = str(tier * len(rule.affixes))  # Total tier sum

    # Advanced flag
    advanced = ET.SubElement(condition, "advanced")
    advanced.text = "true"


def _create_affix_condition_idol(parent: ET.Element, rule: OptimizedRule) -> None:
    """Create AffixCondition for idol modifiers.

    Args:
        parent: Parent conditions element
        rule: OptimizedRule to serialize

    Note:
        Assumes validation has already confirmed all modifier IDs are present.
    """
    condition = ET.SubElement(parent, "Condition")
    condition.set("{http://www.w3.org/2001/XMLSchema-instance}type", "AffixCondition")

    # Modifiers (using affix system)
    affixes_elem = ET.SubElement(condition, "affixes")
    for modifier_id, name, tier in sorted(rule.modifiers):
        int_elem = ET.SubElement(affixes_elem, "int")
        int_elem.text = str(modifier_id)

    # Idols typically don't filter by tier
    comparsion = ET.SubElement(condition, "comparsion")
    comparsion.text = "ANY"

    comparsion_value = ET.SubElement(condition, "comparsionValue")
    comparsion_value.text = "0"

    # Required count - only 1 of the selected modifiers required for idols
    min_on_same = ET.SubElement(condition, "minOnTheSameItem")
    min_on_same.text = "1"

    # Combined comparison - count of modifier matches
    combined_comp = ET.SubElement(condition, "combinedComparsion")
    combined_comp.text = "ANY"

    combined_value = ET.SubElement(condition, "combinedComparsionValue")
    combined_value.text = "1"

    # Advanced flag
    advanced = ET.SubElement(condition, "advanced")
    advanced.text = "false"


def _create_unique_condition(parent: ET.Element, rule: OptimizedRule) -> None:
    """Create UniqueModifiersCondition for unique items.

    Args:
        parent: Parent conditions element
        rule: OptimizedRule to serialize

    Note:
        Assumes validation has already confirmed all unique IDs are present.
        Generates one Uniques container per unique item with minimal roll structure.
    """
    condition = ET.SubElement(parent, "Condition")
    condition.set("{http://www.w3.org/2001/XMLSchema-instance}type", "UniqueModifiersCondition")

    # Create one Uniques element per unique item
    for unique_id, name in sorted(rule.unique_items):
        uniques = ET.SubElement(condition, "Uniques")

        # UniqueId directly inside Uniques
        unique_id_elem = ET.SubElement(uniques, "UniqueId")
        unique_id_elem.text = str(unique_id)

        # Rolls container with minimal structure (2 rolls with nil values)
        rolls = ET.SubElement(uniques, "Rolls")

        for roll_id in range(2):
            roll = ET.SubElement(rolls, "UniqueModifierWithRollId")

            roll_id_elem = ET.SubElement(roll, "RollId")
            roll_id_elem.text = str(roll_id)

            modifier = ET.SubElement(roll, "Modifier")

            min_roll = ET.SubElement(modifier, "MinRoll")
            min_roll.set("{http://www.w3.org/2001/XMLSchema-instance}nil", "true")

            max_roll = ET.SubElement(modifier, "MaxRoll")
            max_roll.set("{http://www.w3.org/2001/XMLSchema-instance}nil", "true")


def _create_rule_element(rules_parent: ET.Element, rule: OptimizedRule, order: int, index: int) -> None:
    """Create XML Rule element from OptimizedRule.

    Args:
        rules_parent: Parent rules element
        rule: OptimizedRule to serialize
        order: Sequential order value
        index: Rule index for error messages
    """
    rule_elem = ET.SubElement(rules_parent, "Rule")

    # Type (always SHOW)
    type_elem = ET.SubElement(rule_elem, "type")
    type_elem.text = "SHOW"

    # Conditions
    conditions = ET.SubElement(rule_elem, "conditions")

    if rule.category == "exalted":
        _create_rarity_condition(conditions)
        _create_subtype_condition_exalted(conditions, rule, index)
        _create_affix_condition_exalted(conditions, rule)
    elif rule.category == "idol":
        _create_subtype_condition_idol(conditions, rule, index)
        _create_affix_condition_idol(conditions, rule)
    elif rule.category == "unique":
        _create_unique_condition(conditions, rule)

    # Style
    style = _get_style_for_category(rule.category)

    recolor = ET.SubElement(rule_elem, "recolor")
    recolor.text = "true" if style["recolor"] else "false"

    color = ET.SubElement(rule_elem, "color")
    color.text = str(style["color"])

    is_enabled = ET.SubElement(rule_elem, "isEnabled")
    is_enabled.text = "true"

    # Deprecated fields
    level_dep = ET.SubElement(rule_elem, "levelDependent_deprecated")
    level_dep.text = "false"

    min_lvl = ET.SubElement(rule_elem, "minLvl_deprecated")
    min_lvl.text = "0"

    max_lvl = ET.SubElement(rule_elem, "maxLvl_deprecated")
    max_lvl.text = "0"

    # Additional style fields
    emphasized = ET.SubElement(rule_elem, "emphasized")
    emphasized.text = "true" if style["emphasized"] else "false"

    name_override = ET.SubElement(rule_elem, "nameOverride")

    sound_id = ET.SubElement(rule_elem, "SoundId")
    sound_id.text = str(style["SoundId"])

    map_icon = ET.SubElement(rule_elem, "MapIconId")
    map_icon.text = str(style["MapIconId"])

    beam_override = ET.SubElement(rule_elem, "BeamOverride")
    beam_override.text = "true" if style["BeamOverride"] else "false"

    beam_size = ET.SubElement(rule_elem, "BeamSizeOverride")
    beam_size.text = style["BeamSizeOverride"]

    beam_color = ET.SubElement(rule_elem, "BeamColorOverride")
    beam_color.text = str(style["BeamColorOverride"])

    # Order
    order_elem = ET.SubElement(rule_elem, "Order")
    order_elem.text = str(order)


def generate(result: OptimizationResult, metadata: Optional[Dict[str, Any]] = None) -> str:
    """Generate Last Epoch ItemFilter XML from OptimizationResult.

    Args:
        result: OptimizationResult containing optimized rules
        metadata: Optional metadata dict with keys: name, filterIcon, filterIconColor,
                 description, lastModifiedInVersion, lootFilterVersion

    Returns:
        XML string with proper formatting

    Raises:
        ValidationError: If result validation fails
        XMLGenerationError: If XML generation fails
        EquipmentTypeMappingError: If item type mapping fails
        IdolSizeMappingError: If idol size mapping fails
        UnsupportedMixedAffixTierError: If mixed tier affixes detected
        MissingIDError: If required ID is missing
        UnsupportedCategoryError: If unknown category encountered
    """
    # Validate optimization result
    _validate_optimization_result(result)

    # Validate all rules
    _validate_rules(result.rules)

    # Prepare metadata
    if metadata is None:
        metadata = {}

    filter_name = metadata.get("name", DEFAULT_FILTER_NAME)
    filter_icon = metadata.get("filterIcon", DEFAULT_FILTER_ICON)
    filter_icon_color = metadata.get("filterIconColor", DEFAULT_FILTER_ICON_COLOR)
    description = metadata.get("description", "")
    game_version = metadata.get("lastModifiedInVersion", DEFAULT_GAME_VERSION)
    filter_version = metadata.get("lootFilterVersion", DEFAULT_FILTER_VERSION)

    # Create root element with namespace
    # Register 'i' prefix globally - this will be used for i:type attributes
    # and automatically add xmlns:i declaration to root
    ET.register_namespace("i", "http://www.w3.org/2001/XMLSchema-instance")
    root = ET.Element("ItemFilter")

    # Metadata
    name = ET.SubElement(root, "name")
    name.text = filter_name

    icon = ET.SubElement(root, "filterIcon")
    icon.text = str(filter_icon)

    icon_color = ET.SubElement(root, "filterIconColor")
    icon_color.text = str(filter_icon_color)

    desc = ET.SubElement(root, "description")
    if description:
        desc.text = description

    version = ET.SubElement(root, "lastModifiedInVersion")
    version.text = game_version

    loot_version = ET.SubElement(root, "lootFilterVersion")
    loot_version.text = str(filter_version)

    # Rules container
    rules_elem = ET.SubElement(root, "rules")

    # Generate rules with reversed Order (first rule gets N-1, last gets 0)
    total_rules = len(result.rules)
    for index, rule in enumerate(result.rules):
        order = total_rules - 1 - index  # Reverse Order
        _create_rule_element(rules_elem, rule, order=order, index=index)

    # Convert to string with proper formatting
    _indent(root)
    xml_string = ET.tostring(root, encoding="unicode", method="xml")

    # Add XML declaration
    xml_declaration = '<?xml version="1.0" encoding="utf-8"?>\n'
    return xml_declaration + xml_string


def _indent(elem: ET.Element, level: int = 0) -> None:
    """Add indentation to XML tree for pretty printing.

    Args:
        elem: Element to indent
        level: Current indentation level
    """
    indent = "  "
    i = "\n" + level * indent
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + indent
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for child in elem:
            _indent(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def save(result: OptimizationResult, path: str, metadata: Optional[Dict[str, Any]] = None) -> None:
    """Generate XML and save to file.

    Args:
        result: OptimizationResult containing optimized rules
        path: Output file path
        metadata: Optional metadata dict

    Raises:
        ValidationError: If result validation fails
        XMLGenerationError: If XML generation fails
        IOError: If file write fails
    """
    xml_content = generate(result, metadata)

    # Create parent directory if needed
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write UTF-8
    output_path.write_text(xml_content, encoding="utf-8")
