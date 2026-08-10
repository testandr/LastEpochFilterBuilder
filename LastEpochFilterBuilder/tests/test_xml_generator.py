"""Tests for XML Generator.

Tests XML serialization of OptimizedRule objects into Last Epoch ItemFilter XML.
"""

import pytest
import xml.etree.ElementTree as ET
from pathlib import Path
from tempfile import TemporaryDirectory

from app.generator.xml_generator import (
    generate,
    save,
    XMLGenerationError,
    UnsupportedMixedAffixTierError,
    MissingIDError,
    UnsupportedCategoryError,
    ValidationError,
    MAX_RULES,
)
from app.generator.rule_models import OptimizationResult, OptimizedRule
from app.generator.equipment_type_mapper import EquipmentTypeMappingError
from app.generator.idol_size_mapper import IdolSizeMappingError


# Helper to create test OptimizedRule
def create_exalted_rule(
    affixes=None,
    item_types=None,
    order_priority=100,
    score=10.0
):
    """Create test exalted rule."""
    if affixes is None:
        affixes = frozenset([(502, "Health", 6)])
    if item_types is None:
        item_types = [(4, None)]  # GLOVES

    return OptimizedRule(
        category="exalted",
        semantic_priority=order_priority,
        score=score,
        build_count=5,
        occurrence_count=10,
        source_count=3,
        sources={"build1", "build2"},
        slot="gloves",
        item_types=item_types,
        affixes=affixes,
        idol_sizes=[],
        modifiers=frozenset(),
        unique_items=frozenset(),
        max_tier=6,
        avg_tier=6.0,
        reason="Test exalted rule",
        merged_count=1,
    )


def create_idol_rule(
    modifiers=None,
    idol_sizes=None,
    order_priority=70,
    score=8.0
):
    """Create test idol rule."""
    if modifiers is None:
        modifiers = frozenset([(114, "Minion Damage", 1)])
    if idol_sizes is None:
        idol_sizes = ["Minor Idol (1x1)"]

    return OptimizedRule(
        category="idol",
        semantic_priority=order_priority,
        score=score,
        build_count=3,
        occurrence_count=5,
        source_count=2,
        sources={"build1"},
        slot=None,
        item_types=[],
        affixes=frozenset(),
        idol_sizes=idol_sizes,
        modifiers=modifiers,
        unique_items=frozenset(),
        max_tier=0,
        avg_tier=0.0,
        reason="Test idol rule",
        merged_count=1,
    )


def create_unique_rule(
    unique_items=None,
    order_priority=30,
    score=5.0
):
    """Create test unique rule."""
    if unique_items is None:
        unique_items = frozenset([(300, "Test Unique")])

    return OptimizedRule(
        category="unique",
        semantic_priority=order_priority,
        score=score,
        build_count=2,
        occurrence_count=3,
        source_count=1,
        sources={"build1"},
        slot=None,
        item_types=[],
        affixes=frozenset(),
        idol_sizes=[],
        modifiers=frozenset(),
        unique_items=unique_items,
        max_tier=0,
        avg_tier=0.0,
        reason="Test unique rule",
        merged_count=1,
    )


class TestXMLGeneration:
    """Test basic XML generation."""

    def test_empty_successful_result_produces_valid_xml(self):
        """Empty OptimizationResult with success=True produces valid ItemFilter."""
        result = OptimizationResult(
            rules=[],
            original_count=0,
            optimized_count=0,
            final_count=0,
            success=True,
            exceeds_budget=False,
        )

        xml = generate(result)

        # Parse to verify valid XML
        root = ET.fromstring(xml)
        assert root.tag == "ItemFilter"
        assert root.find("name") is not None
        assert root.find("rules") is not None

        rules = root.find("rules")
        assert len(rules) == 0

    def test_metadata_generated_correctly(self):
        """Custom metadata is included in output."""
        result = OptimizationResult(
            rules=[],
            final_count=0,
            success=True,
        )

        metadata = {
            "name": "Custom Filter Name",
            "filterIcon": 5,
            "filterIconColor": 3,
            "description": "Test description",
            "lastModifiedInVersion": "1.5.0",
            "lootFilterVersion": 1,
        }

        xml = generate(result, metadata)
        root = ET.fromstring(xml)

        assert root.find("name").text == "Custom Filter Name"
        assert root.find("filterIcon").text == "5"
        assert root.find("filterIconColor").text == "3"
        assert root.find("description").text == "Test description"
        assert root.find("lastModifiedInVersion").text == "1.5.0"
        assert root.find("lootFilterVersion").text == "1"

    def test_sequential_order_values(self):
        """Rules assigned reversed Order values (first rule highest, last rule 0)."""
        rule1 = create_exalted_rule()
        rule2 = create_exalted_rule()
        rule3 = create_exalted_rule()

        result = OptimizationResult(
            rules=[rule1, rule2, rule3],
            final_count=3,
            success=True,
        )

        xml = generate(result)
        root = ET.fromstring(xml)

        rules = root.find("rules").findall("Rule")
        assert len(rules) == 3

        # Order is reversed: first rule gets 2, last rule gets 0
        assert rules[0].find("Order").text == "2"
        assert rules[1].find("Order").text == "1"
        assert rules[2].find("Order").text == "0"

    def test_optimizer_order_preserved(self):
        """Rule order from OptimizationResult is preserved."""
        # Create rules with different priorities
        rule1 = create_exalted_rule(order_priority=100, score=10.0)
        rule2 = create_idol_rule(order_priority=70, score=8.0)
        rule3 = create_unique_rule(order_priority=30, score=5.0)

        # Rules are already sorted by optimizer
        result = OptimizationResult(
            rules=[rule1, rule2, rule3],
            final_count=3,
            success=True,
        )

        xml = generate(result)
        root = ET.fromstring(xml)

        rules = root.find("rules").findall("Rule")

        # First rule should have Order 2 (reversed) and be exalted
        conditions = rules[0].find("conditions")
        assert conditions.find(".//Condition[@{http://www.w3.org/2001/XMLSchema-instance}type='RarityCondition']") is not None
        assert rules[0].find("Order").text == "2"

        # Second rule should have Order 1 and be idol
        # Third rule should have Order 0 and be unique
        assert rules[1].find("Order").text == "1"
        assert rules[2].find("Order").text == "0"


class TestExaltedRules:
    """Test exalted rule generation."""

    def test_exalted_rarity_condition(self):
        """Exalted rules include RarityCondition with EXALTED."""
        rule = create_exalted_rule()
        result = OptimizationResult(rules=[rule], final_count=1, success=True)

        xml = generate(result)
        root = ET.fromstring(xml)

        rarity_cond = root.find(".//Condition[@{http://www.w3.org/2001/XMLSchema-instance}type='RarityCondition']")
        assert rarity_cond is not None
        assert rarity_cond.find("rarity").text == "EXALTED"

    def test_exalted_subtype_single_equipment_type(self):
        """Exalted SubTypeCondition with single equipment type."""
        rule = create_exalted_rule(item_types=[(4, None)])  # GLOVES
        result = OptimizationResult(rules=[rule], final_count=1, success=True)

        xml = generate(result)
        root = ET.fromstring(xml)

        subtype_cond = root.find(".//Condition[@{http://www.w3.org/2001/XMLSchema-instance}type='SubTypeCondition']")
        assert subtype_cond is not None

        equipment_types = subtype_cond.findall(".//EquipmentType")
        assert len(equipment_types) == 1
        assert equipment_types[0].text == "GLOVES"

    def test_exalted_subtype_multiple_item_types(self):
        """Exalted SubTypeCondition with multiple equipment types."""
        rule = create_exalted_rule(
            item_types=[(0, None), (3, None), (4, None)]  # HELMET, BOOTS, GLOVES
        )
        result = OptimizationResult(rules=[rule], final_count=1, success=True)

        xml = generate(result)
        root = ET.fromstring(xml)

        subtype_cond = root.find(".//Condition[@{http://www.w3.org/2001/XMLSchema-instance}type='SubTypeCondition']")
        equipment_types = subtype_cond.findall(".//EquipmentType")

        assert len(equipment_types) == 3
        types = {eq.text for eq in equipment_types}
        assert types == {"HELMET", "BOOTS", "GLOVES"}

    def test_exalted_affix_condition_uses_numeric_ids(self):
        """Exalted AffixCondition uses numeric affix IDs."""
        rule = create_exalted_rule(
            affixes=frozenset([(502, "Health", 6), (25, "Strength", 6)])
        )
        result = OptimizationResult(rules=[rule], final_count=1, success=True)

        xml = generate(result)
        root = ET.fromstring(xml)

        affix_cond = root.find(".//Condition[@{http://www.w3.org/2001/XMLSchema-instance}type='AffixCondition']")
        assert affix_cond is not None

        affixes = affix_cond.find("affixes")
        affix_ids = [int(a.text) for a in affixes.findall("int")]

        assert set(affix_ids) == {502, 25}

    def test_same_tier_affixes_serialize_correctly(self):
        """Same-tier affixes produce single comparisonValue."""
        rule = create_exalted_rule(
            affixes=frozenset([(502, "Health", 7), (25, "Strength", 7), (14, "Armor", 7)])
        )
        result = OptimizationResult(rules=[rule], final_count=1, success=True)

        xml = generate(result)
        root = ET.fromstring(xml)

        affix_cond = root.find(".//Condition[@{http://www.w3.org/2001/XMLSchema-instance}type='AffixCondition']")

        assert affix_cond.find("comparsion").text == "MORE_OR_EQUAL"
        assert affix_cond.find("comparsionValue").text == "7"
        assert affix_cond.find("minOnTheSameItem").text == "3"
        assert affix_cond.find("advanced").text == "true"

    def test_mixed_affix_tiers_fail_explicitly(self):
        """Mixed affix tiers raise UnsupportedMixedAffixTierError."""
        rule = create_exalted_rule(
            affixes=frozenset([(502, "Health", 6), (25, "Strength", 7)])
        )
        result = OptimizationResult(rules=[rule], final_count=1, success=True)

        with pytest.raises(UnsupportedMixedAffixTierError) as exc_info:
            generate(result)

        assert "mixed affix tier requirements" in str(exc_info.value).lower()
        assert "Armor T6" in str(exc_info.value) or "Health T6" in str(exc_info.value)
        assert "T7" in str(exc_info.value)

    def test_missing_affix_id_fails(self):
        """Missing affix ID raises MissingIDError."""
        rule = create_exalted_rule(
            affixes=frozenset([(None, "Health", 6)])
        )
        result = OptimizationResult(rules=[rule], final_count=1, success=True)

        with pytest.raises(MissingIDError) as exc_info:
            generate(result)

        assert "no numeric id" in str(exc_info.value).lower()

    def test_unsupported_fist_fails_explicitly(self):
        """Unsupported Fist weapon (item_type 11) fails with clear error."""
        rule = create_exalted_rule(item_types=[(11, None)])
        result = OptimizationResult(rules=[rule], final_count=1, success=True)

        with pytest.raises(XMLGenerationError) as exc_info:
            generate(result)

        assert "11" in str(exc_info.value)
        assert "Fist" in str(exc_info.value) or "fist" in str(exc_info.value).lower()

    def test_unsupported_crossbow_fails_explicitly(self):
        """Unsupported Crossbow (item_type 24) fails with clear error."""
        rule = create_exalted_rule(item_types=[(24, None)])
        result = OptimizationResult(rules=[rule], final_count=1, success=True)

        with pytest.raises(XMLGenerationError) as exc_info:
            generate(result)

        assert "24" in str(exc_info.value)
        assert "Crossbow" in str(exc_info.value) or "crossbow" in str(exc_info.value).lower()


class TestIdolRules:
    """Test idol rule generation."""

    def test_idol_size_mapping(self):
        """Idol sizes mapped to reversed IDOL_HxW format."""
        rule = create_idol_rule(idol_sizes=["Minor Idol (1x1)", "Grand Idol (1x3)"])
        result = OptimizationResult(rules=[rule], final_count=1, success=True)

        xml = generate(result)
        root = ET.fromstring(xml)

        subtype_cond = root.find(".//Condition[@{http://www.w3.org/2001/XMLSchema-instance}type='SubTypeCondition']")
        equipment_types = subtype_cond.findall(".//EquipmentType")

        types = {eq.text for eq in equipment_types}
        # Real XML uses reversed dimensions: (1x3) -> IDOL_3x1
        assert types == {"IDOL_1x1", "IDOL_3x1"}

    def test_idol_modifier_numeric_ids(self):
        """Idol modifiers use numeric IDs."""
        rule = create_idol_rule(
            modifiers=frozenset([(114, "Minion Damage", 1), (319, "Minion Health", 1)])
        )
        result = OptimizationResult(rules=[rule], final_count=1, success=True)

        xml = generate(result)
        root = ET.fromstring(xml)

        affix_cond = root.find(".//Condition[@{http://www.w3.org/2001/XMLSchema-instance}type='AffixCondition']")
        affixes = affix_cond.find("affixes")
        modifier_ids = [int(a.text) for a in affixes.findall("int")]

        assert set(modifier_ids) == {114, 319}

    def test_missing_idol_modifier_id_fails(self):
        """Missing idol modifier ID raises MissingIDError."""
        rule = create_idol_rule(modifiers=frozenset([(None, "Minion Damage", 1)]))
        result = OptimizationResult(rules=[rule], final_count=1, success=True)

        with pytest.raises(MissingIDError) as exc_info:
            generate(result)

        assert "no numeric id" in str(exc_info.value).lower()


class TestUniqueRules:
    """Test unique rule generation."""

    def test_unique_uses_unique_id(self):
        """UniqueModifiersCondition uses numeric UniqueId."""
        rule = create_unique_rule(unique_items=frozenset([(300, "Test Unique")]))
        result = OptimizationResult(rules=[rule], final_count=1, success=True)

        xml = generate(result)
        root = ET.fromstring(xml)

        unique_cond = root.find(".//Condition[@{http://www.w3.org/2001/XMLSchema-instance}type='UniqueModifiersCondition']")
        assert unique_cond is not None

        unique_id = unique_cond.find(".//UniqueId")
        assert unique_id.text == "300"

    def test_multiple_uniques_in_one_rule(self):
        """Multiple unique_items serialize as multiple Uniques elements."""
        rule = create_unique_rule(
            unique_items=frozenset([
                (300, "Unique A"),
                (296, "Unique B"),
                (144, "Unique C"),
            ])
        )
        result = OptimizationResult(rules=[rule], final_count=1, success=True)

        xml = generate(result)
        root = ET.fromstring(xml)

        unique_cond = root.find(".//Condition[@{http://www.w3.org/2001/XMLSchema-instance}type='UniqueModifiersCondition']")
        uniques = unique_cond.findall("Uniques")

        assert len(uniques) == 3

        unique_ids = {int(u.find("UniqueId").text) for u in uniques}
        assert unique_ids == {300, 296, 144}

    def test_missing_unique_id_fails(self):
        """Missing unique ID raises MissingIDError."""
        rule = create_unique_rule(unique_items=frozenset([(None, "Test Unique")]))
        result = OptimizationResult(rules=[rule], final_count=1, success=True)

        with pytest.raises(MissingIDError) as exc_info:
            generate(result)

        assert "no numeric id" in str(exc_info.value).lower()


class TestValidation:
    """Test validation logic."""

    def test_unknown_category_fails(self):
        """Unknown category raises UnsupportedCategoryError."""
        rule = create_exalted_rule()
        rule.category = "legendary"  # Unknown category
        result = OptimizationResult(rules=[rule], final_count=1, success=True)

        with pytest.raises(UnsupportedCategoryError) as exc_info:
            generate(result)

        assert "legendary" in str(exc_info.value).lower()

    def test_optimization_result_success_false_rejected(self):
        """OptimizationResult with success=False rejected."""
        result = OptimizationResult(
            rules=[],
            final_count=0,
            success=False,
            message="Optimization failed",
        )

        with pytest.raises(ValidationError) as exc_info:
            generate(result)

        assert "success is false" in str(exc_info.value).lower()

    def test_140_rules_accepted(self):
        """140 rules passes validation."""
        rules = [create_exalted_rule() for _ in range(140)]
        result = OptimizationResult(
            rules=rules,
            final_count=140,
            success=True,
        )

        # Should not raise
        xml = generate(result)
        assert xml is not None

    def test_141_rules_rejected_by_validation(self):
        """141 rules rejected by validation."""
        rules = [create_exalted_rule() for _ in range(141)]
        result = OptimizationResult(
            rules=rules,
            final_count=141,
            success=True,
        )

        with pytest.raises(ValidationError) as exc_info:
            generate(result)

        assert "141" in str(exc_info.value)
        assert "140" in str(exc_info.value)


class TestDeterminism:
    """Test deterministic output."""

    def test_deterministic_xml_output(self):
        """Same input produces identical XML."""
        rule = create_exalted_rule()
        result = OptimizationResult(rules=[rule], final_count=1, success=True)

        xml1 = generate(result)
        xml2 = generate(result)

        assert xml1 == xml2

    def test_input_not_mutated(self):
        """Generate does not mutate OptimizationResult."""
        rule = create_exalted_rule(
            affixes=frozenset([(502, "Health", 6)]),
            item_types=[(4, None)]
        )
        result = OptimizationResult(rules=[rule], final_count=1, success=True)

        original_rules_count = len(result.rules)
        original_affixes = result.rules[0].affixes

        generate(result)

        assert len(result.rules) == original_rules_count
        assert result.rules[0].affixes == original_affixes


class TestSaveFunction:
    """Test save() function."""

    def test_save_writes_utf8_valid_xml(self):
        """save() writes valid UTF-8 XML file."""
        rule = create_exalted_rule()
        result = OptimizationResult(rules=[rule], final_count=1, success=True)

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_filter.xml"

            save(result, str(output_path))

            assert output_path.exists()

            # Read and parse
            content = output_path.read_text(encoding="utf-8")
            root = ET.fromstring(content)

            assert root.tag == "ItemFilter"

    def test_save_creates_parent_directory(self):
        """save() creates parent directory if needed."""
        rule = create_exalted_rule()
        result = OptimizationResult(rules=[rule], final_count=1, success=True)

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "test_filter.xml"

            save(result, str(output_path))

            assert output_path.exists()


class TestXMLStructure:
    """Test XML structure details."""

    def test_xml_declaration_present(self):
        """XML declaration is present."""
        result = OptimizationResult(rules=[], final_count=0, success=True)
        xml = generate(result)

        assert xml.startswith('<?xml version="1.0"')

    def test_namespace_attribute_present(self):
        """Root element has xmlns:i namespace."""
        rule = create_exalted_rule()
        result = OptimizationResult(rules=[rule], final_count=1, success=True)
        xml = generate(result)

        # Check that the namespace declaration is in the generated XML string
        assert 'xmlns:i="http://www.w3.org/2001/XMLSchema-instance"' in xml

    def test_all_common_fields_present(self):
        """All common rule fields are present."""
        rule = create_exalted_rule()
        result = OptimizationResult(rules=[rule], final_count=1, success=True)

        xml = generate(result)
        root = ET.fromstring(xml)

        rule_elem = root.find(".//Rule")

        # Required fields
        assert rule_elem.find("type") is not None
        assert rule_elem.find("conditions") is not None
        assert rule_elem.find("recolor") is not None
        assert rule_elem.find("color") is not None
        assert rule_elem.find("isEnabled") is not None
        assert rule_elem.find("levelDependent_deprecated") is not None
        assert rule_elem.find("minLvl_deprecated") is not None
        assert rule_elem.find("maxLvl_deprecated") is not None
        assert rule_elem.find("emphasized") is not None
        assert rule_elem.find("nameOverride") is not None
        assert rule_elem.find("SoundId") is not None
        assert rule_elem.find("MapIconId") is not None
        assert rule_elem.find("BeamOverride") is not None
        assert rule_elem.find("BeamSizeOverride") is not None
        assert rule_elem.find("BeamColorOverride") is not None
        assert rule_elem.find("Order") is not None

    def test_style_exalted_applied(self):
        """Exalted rules use exalted style defaults."""
        rule = create_exalted_rule()
        result = OptimizationResult(rules=[rule], final_count=1, success=True)

        xml = generate(result)
        root = ET.fromstring(xml)

        rule_elem = root.find(".//Rule")

        assert rule_elem.find("recolor").text == "true"
        assert rule_elem.find("color").text == "2"

    def test_style_idol_applied(self):
        """Idol rules use idol style defaults."""
        rule = create_idol_rule()
        result = OptimizationResult(rules=[rule], final_count=1, success=True)

        xml = generate(result)
        root = ET.fromstring(xml)

        rule_elem = root.find(".//Rule")

        assert rule_elem.find("recolor").text == "true"
        assert rule_elem.find("color").text == "4"

    def test_style_unique_applied(self):
        """Unique rules use unique style defaults."""
        rule = create_unique_rule()
        result = OptimizationResult(rules=[rule], final_count=1, success=True)

        xml = generate(result)
        root = ET.fromstring(xml)

        rule_elem = root.find(".//Rule")

        assert rule_elem.find("recolor").text == "false"
        assert rule_elem.find("color").text == "0"


class TestMapperErrorPropagation:
    """Test that mapper errors propagate as meaningful XML generation errors."""

    def test_equipment_type_mapper_error_propagates(self):
        """EquipmentTypeMappingError wrapped in XMLGenerationError."""
        rule = create_exalted_rule(item_types=[(999, None)])  # Unknown type
        result = OptimizationResult(rules=[rule], final_count=1, success=True)

        with pytest.raises(XMLGenerationError) as exc_info:
            generate(result)

        assert "999" in str(exc_info.value)

    def test_idol_size_mapper_error_propagates(self):
        """IdolSizeMappingError wrapped in XMLGenerationError."""
        rule = create_idol_rule(idol_sizes=["Invalid Idol"])
        result = OptimizationResult(rules=[rule], final_count=1, success=True)

        with pytest.raises(XMLGenerationError) as exc_info:
            generate(result)

        assert "Invalid Idol" in str(exc_info.value)


class TestRealWorldScenarios:
    """Test realistic multi-rule scenarios."""

    def test_mixed_category_rules(self):
        """Mix of exalted, idol, and unique rules."""
        exalted = create_exalted_rule(order_priority=100)
        idol = create_idol_rule(order_priority=70)
        unique = create_unique_rule(order_priority=30)

        result = OptimizationResult(
            rules=[exalted, idol, unique],
            final_count=3,
            success=True,
        )

        xml = generate(result)
        root = ET.fromstring(xml)

        rules = root.find("rules").findall("Rule")
        assert len(rules) == 3

        # Verify each rule type has correct conditions
        assert rules[0].find(".//Condition[@{http://www.w3.org/2001/XMLSchema-instance}type='RarityCondition']") is not None
        # Order is reversed: first rule gets 2
        assert rules[0].find("Order").text == "2"

        assert rules[1].find("Order").text == "1"
        assert rules[2].find("Order").text == "0"

    def test_weapon_equipment_types(self):
        """Weapon equipment types map correctly."""
        rule = create_exalted_rule(
            item_types=[
                (5, None),   # ONE_HANDED_AXE
                (16, None),  # TWO_HANDED_SWORD
                (23, None),  # BOW
            ]
        )
        result = OptimizationResult(rules=[rule], final_count=1, success=True)

        xml = generate(result)
        root = ET.fromstring(xml)

        equipment_types = root.findall(".//EquipmentType")
        types = {eq.text for eq in equipment_types}

        assert "ONE_HANDED_AXE" in types
        assert "TWO_HANDED_SWORD" in types
        assert "BOW" in types

    def test_offhand_equipment_types(self):
        """Off-hand equipment types map correctly."""
        rule = create_exalted_rule(
            item_types=[
                (17, None),  # QUIVER
                (18, None),  # SHIELD
                (19, None),  # CATALYST
            ]
        )
        result = OptimizationResult(rules=[rule], final_count=1, success=True)

        xml = generate(result)
        root = ET.fromstring(xml)

        equipment_types = root.findall(".//EquipmentType")
        types = {eq.text for eq in equipment_types}

        assert "QUIVER" in types
        assert "SHIELD" in types


class TestRealXMLConformance:
    """Regression tests for confirmed real Last Epoch XML behavior."""

    def test_namespace_uses_i_prefix_only(self):
        """Generator uses xmlns:i namespace exactly like real game XML."""
        rule = create_exalted_rule()
        result = OptimizationResult(rules=[rule], final_count=1, success=True)

        xml = generate(result)

        # Should contain xmlns:i declaration
        assert 'xmlns:i="http://www.w3.org/2001/XMLSchema-instance"' in xml

        # Should NOT contain additional xsi namespace
        assert 'xmlns:xsi=' not in xml

        # Should use i:type for condition types
        assert 'i:type="RarityCondition"' in xml

    def test_condition_uses_i_type_attribute(self):
        """Conditions use i:type attribute matching real XML."""
        rule = create_exalted_rule()
        result = OptimizationResult(rules=[rule], final_count=1, success=True)

        xml = generate(result)
        root = ET.fromstring(xml)

        # Find conditions with i:type
        rarity_cond = root.find(".//Condition[@{http://www.w3.org/2001/XMLSchema-instance}type='RarityCondition']")
        assert rarity_cond is not None

        subtype_cond = root.find(".//Condition[@{http://www.w3.org/2001/XMLSchema-instance}type='SubTypeCondition']")
        assert subtype_cond is not None

        affix_cond = root.find(".//Condition[@{http://www.w3.org/2001/XMLSchema-instance}type='AffixCondition']")
        assert affix_cond is not None

    def test_order_reversed_first_rule_highest(self):
        """Rule Order values reversed: first rule gets N-1, last gets 0."""
        rules = [create_exalted_rule() for _ in range(5)]
        result = OptimizationResult(rules=rules, final_count=5, success=True)

        xml = generate(result)
        root = ET.fromstring(xml)

        rule_elements = root.find("rules").findall("Rule")
        assert len(rule_elements) == 5

        # First rule: Order = 4
        assert rule_elements[0].find("Order").text == "4"

        # Middle rule: Order = 2
        assert rule_elements[2].find("Order").text == "2"

        # Last rule: Order = 0
        assert rule_elements[4].find("Order").text == "0"

    def test_grand_idol_1x3_maps_to_IDOL_3x1(self):
        """Grand Idol (1x3) maps to IDOL_3x1 (reversed dimensions)."""
        rule = create_idol_rule(idol_sizes=["Grand Idol (1x3)"])
        result = OptimizationResult(rules=[rule], final_count=1, success=True)

        xml = generate(result)
        root = ET.fromstring(xml)

        subtype_cond = root.find(".//Condition[@{http://www.w3.org/2001/XMLSchema-instance}type='SubTypeCondition']")
        equipment_types = subtype_cond.findall(".//EquipmentType")

        types = {eq.text for eq in equipment_types}
        assert "IDOL_3x1" in types
        assert "IDOL_1x3" not in types

    def test_exalted_affix_condition_structure(self):
        """Exalted AffixCondition matches real XML field structure."""
        # Single affix with tier 6
        rule = create_exalted_rule(affixes=[(100, "Test Affix", 6)])
        result = OptimizationResult(rules=[rule], final_count=1, success=True)

        xml = generate(result)
        root = ET.fromstring(xml)

        affix_cond = root.find(".//Condition[@{http://www.w3.org/2001/XMLSchema-instance}type='AffixCondition']")

        # Verify field order and values match real XML
        assert affix_cond.find("affixes") is not None
        assert affix_cond.find("comparsion").text == "MORE_OR_EQUAL"
        assert affix_cond.find("comparsionValue").text == "6"
        assert affix_cond.find("minOnTheSameItem").text == "1"
        assert affix_cond.find("combinedComparsion").text == "ANY"
        assert affix_cond.find("combinedComparsionValue").text == "6"
        assert affix_cond.find("advanced").text == "true"

    def test_exalted_multiple_affixes_combined_value(self):
        """Multiple exalted affixes: combinedComparsionValue = tier * count."""
        # 3 affixes at tier 6
        affixes = [
            (100, "Affix1", 6),
            (101, "Affix2", 6),
            (102, "Affix3", 6),
        ]
        rule = create_exalted_rule(affixes=affixes)
        result = OptimizationResult(rules=[rule], final_count=1, success=True)

        xml = generate(result)
        root = ET.fromstring(xml)

        affix_cond = root.find(".//Condition[@{http://www.w3.org/2001/XMLSchema-instance}type='AffixCondition']")

        assert affix_cond.find("minOnTheSameItem").text == "3"
        assert affix_cond.find("combinedComparsionValue").text == "18"  # 6 * 3

    def test_idol_affix_condition_structure(self):
        """Idol AffixCondition matches real XML structure."""
        rule = create_idol_rule(
            modifiers=[(200, "Idol Mod 1", 0), (201, "Idol Mod 2", 0)]
        )
        result = OptimizationResult(rules=[rule], final_count=1, success=True)

        xml = generate(result)
        root = ET.fromstring(xml)

        affix_cond = root.find(".//Condition[@{http://www.w3.org/2001/XMLSchema-instance}type='AffixCondition']")

        # Match real XML idol example
        assert affix_cond.find("comparsion").text == "ANY"
        assert affix_cond.find("comparsionValue").text == "0"
        assert affix_cond.find("minOnTheSameItem").text == "1"
        assert affix_cond.find("combinedComparsion").text == "ANY"
        assert affix_cond.find("combinedComparsionValue").text == "1"
        assert affix_cond.find("advanced").text == "false"

