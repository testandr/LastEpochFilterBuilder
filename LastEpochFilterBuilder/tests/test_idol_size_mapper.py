"""Tests for idol_size_mapper.py

Phase 0B2: Idol size mapping validation.
"""

import pytest

from app.generator.idol_size_mapper import (
    IdolSizeMappingError,
    map_idol_size,
    map_idol_item_type,
)


class TestIdolSizeMappingConfirmed:
    """Test confirmed idol size mappings from parser IDOL_SIZES."""

    def test_minor_idol_1x1(self):
        """Minor Idol (1x1) maps to IDOL_1x1."""
        assert map_idol_size("Minor Idol (1x1)") == "IDOL_1x1"

    def test_humble_idol_1x2(self):
        """Humble Idol (1x2) maps to IDOL_2x1 (dimensions reversed in XML)."""
        assert map_idol_size("Humble Idol (1x2)") == "IDOL_2x1"

    def test_grand_idol_1x3(self):
        """Grand Idol (1x3) maps to IDOL_3x1 (dimensions reversed in XML)."""
        assert map_idol_size("Grand Idol (1x3)") == "IDOL_3x1"

    def test_adorned_idol_1x4(self):
        """Adorned Idol (1x4) maps to IDOL_4x1 (dimensions reversed in XML)."""
        assert map_idol_size("Adorned Idol (1x4)") == "IDOL_4x1"


class TestIdolSizeMappingDimensionExtraction:
    """Test dimension extraction from various formats."""

    def test_dimension_extraction_basic(self):
        """Extract dimensions from basic format (reversed for XML)."""
        assert map_idol_size("Some Idol (2x3)") == "IDOL_3x2"

    def test_dimension_extraction_ignores_name(self):
        """Idol name is ignored, only dimensions matter (reversed for XML)."""
        assert map_idol_size("Custom Name (1x1)") == "IDOL_1x1"
        assert map_idol_size("Another (1x2)") == "IDOL_2x1"

    def test_dimension_extraction_with_whitespace(self):
        """Handles leading/trailing whitespace."""
        assert map_idol_size("  Minor Idol (1x1)  ") == "IDOL_1x1"
        assert map_idol_size("\tGrand Idol (1x3)\n") == "IDOL_3x1"

    def test_dimension_extraction_two_digit_dimensions(self):
        """Handles two-digit dimensions (hypothetical future idols, reversed for XML)."""
        assert map_idol_size("Giant Idol (10x5)") == "IDOL_5x10"

    def test_dimension_pattern_strict(self):
        """Only accepts (WxH) pattern, not variations (reversed for XML)."""
        # Valid patterns
        assert map_idol_size("Idol (1x1)") == "IDOL_1x1"
        assert map_idol_size("Idol (2x2)") == "IDOL_2x2"


class TestIdolSizeMappingDeterministic:
    """Test deterministic behavior."""

    def test_same_input_same_output(self):
        """Multiple calls with same input return same result."""
        result1 = map_idol_size("Minor Idol (1x1)")
        result2 = map_idol_size("Minor Idol (1x1)")
        assert result1 == result2
        assert result1 == "IDOL_1x1"

    def test_all_confirmed_sizes_deterministic(self):
        """All confirmed parser idol sizes produce deterministic output."""
        confirmed = [
            "Minor Idol (1x1)",
            "Humble Idol (1x2)",
            "Grand Idol (1x3)",
            "Adorned Idol (1x4)",
        ]
        for size_str in confirmed:
            result = map_idol_size(size_str)
            assert isinstance(result, str)
            assert result.startswith("IDOL_")
            assert "x" in result


class TestIdolSizeMappingErrorCases:
    """Test explicit failure for invalid inputs."""

    def test_none_size_raises_error(self):
        """None size raises IdolSizeMappingError."""
        with pytest.raises(IdolSizeMappingError) as exc_info:
            map_idol_size(None)
        assert "None" in str(exc_info.value)

    def test_empty_size_raises_error(self):
        """Empty string raises IdolSizeMappingError."""
        with pytest.raises(IdolSizeMappingError):
            map_idol_size("")
        with pytest.raises(IdolSizeMappingError):
            map_idol_size("   ")

    def test_no_dimensions_raises_error(self):
        """String without (WxH) pattern raises error."""
        with pytest.raises(IdolSizeMappingError) as exc_info:
            map_idol_size("Minor Idol")
        assert "dimensions" in str(exc_info.value).lower()

    def test_invalid_dimension_format_raises_error(self):
        """Invalid dimension formats raise error."""
        invalid_formats = [
            "Idol 1x1",  # Missing parentheses
            "Idol (1-1)",  # Wrong separator
            "Idol (1*1)",  # Wrong separator
            "Idol (1 x 1)",  # Spaces not supported
        ]
        for invalid in invalid_formats:
            with pytest.raises(IdolSizeMappingError):
                map_idol_size(invalid)


class TestIdolSizeMappingXMLConformance:
    """Test XML enum conformance."""

    def test_format_all_uppercase(self):
        """IDOL prefix is uppercase."""
        result = map_idol_size("Minor Idol (1x1)")
        assert result.startswith("IDOL_")

    def test_format_dimension_separator(self):
        """Dimensions use lowercase 'x' separator."""
        result = map_idol_size("Minor Idol (1x1)")
        assert "x" in result
        assert "X" not in result

    def test_format_no_whitespace(self):
        """Output contains no whitespace."""
        confirmed = [
            "Minor Idol (1x1)",
            "Humble Idol (1x2)",
            "Grand Idol (1x3)",
            "Adorned Idol (1x4)",
        ]
        for size_str in confirmed:
            result = map_idol_size(size_str)
            assert " " not in result
            assert "\t" not in result
            assert "\n" not in result

    def test_format_structure(self):
        """Output follows IDOL_WxH structure exactly."""
        result = map_idol_size("Minor Idol (1x1)")
        assert result == "IDOL_1x1"
        parts = result.split("_")
        assert len(parts) == 2
        assert parts[0] == "IDOL"
        assert "x" in parts[1]


class TestIdolItemTypeMappingConfirmed:
    """Test numeric item_type to idol size mapping."""

    def test_item_type_26_minor_idol(self):
        """item_type 26 maps to IDOL_1x1."""
        assert map_idol_item_type(26) == "IDOL_1x1"

    def test_item_type_27_humble_idol(self):
        """item_type 27 maps to IDOL_2x1 (reversed dimensions)."""
        assert map_idol_item_type(27) == "IDOL_2x1"

    def test_item_type_29_grand_idol(self):
        """item_type 29 maps to IDOL_3x1 (reversed dimensions)."""
        assert map_idol_item_type(29) == "IDOL_3x1"

    def test_item_type_33_adorned_idol(self):
        """item_type 33 maps to IDOL_4x1 (reversed dimensions)."""
        assert map_idol_item_type(33) == "IDOL_4x1"


class TestIdolItemTypeMappingErrorCases:
    """Test error cases for numeric item_type mapping."""

    def test_none_item_type_raises_error(self):
        """None item_type raises IdolSizeMappingError."""
        with pytest.raises(IdolSizeMappingError) as exc_info:
            map_idol_item_type(None)
        assert "None" in str(exc_info.value)

    def test_unknown_idol_item_type_raises_error(self):
        """Unknown idol item_type in range raises explicit error."""
        unknown_idol_types = [25, 28, 30, 31, 32, 41]
        for item_type in unknown_idol_types:
            with pytest.raises(IdolSizeMappingError) as exc_info:
                map_idol_item_type(item_type)
            assert "unknown" in str(exc_info.value).lower() or "dimensions" in str(exc_info.value).lower()

    def test_non_idol_item_type_raises_error(self):
        """Non-idol item_type raises explicit error."""
        non_idol_types = [0, 1, 4, 21, 42, 99]
        for item_type in non_idol_types:
            with pytest.raises(IdolSizeMappingError) as exc_info:
                map_idol_item_type(item_type)
            assert "not an idol" in str(exc_info.value).lower()

    def test_negative_item_type_raises_error(self):
        """Negative item_type raises error."""
        with pytest.raises(IdolSizeMappingError):
            map_idol_item_type(-1)


class TestIdolSizeMappingNoSilentFallback:
    """Verify no silent fallback or guessing."""

    def test_no_generic_fallback(self):
        """Unknown sizes do NOT fall back to generic values."""
        with pytest.raises(IdolSizeMappingError):
            map_idol_size("Unknown Idol Name")
        # Mapper must NOT return generic strings like "IDOL" or "IDOL_UNKNOWN"

    def test_no_dimension_guessing(self):
        """Mapper does NOT guess dimensions from idol name."""
        with pytest.raises(IdolSizeMappingError):
            map_idol_size("Minor Idol")
        with pytest.raises(IdolSizeMappingError):
            map_idol_size("Huge Idol")


class TestIdolSizeMappingProjectCoverage:
    """Verify all project idol sizes are covered."""

    def test_all_parser_idols_covered(self):
        """All parser IDOL_SIZES are mappable via map_idol_size."""
        parser_idols = [
            "Minor Idol (1x1)",
            "Humble Idol (1x2)",
            "Grand Idol (1x3)",
            "Adorned Idol (1x4)",
        ]
        for size_str in parser_idols:
            result = map_idol_size(size_str)
            assert isinstance(result, str)
            assert result.startswith("IDOL_")

    def test_all_parser_item_types_covered(self):
        """All parser IDOL_SIZES item_type keys are mappable via map_idol_item_type."""
        parser_item_types = [26, 27, 29, 33]
        for item_type in parser_item_types:
            result = map_idol_item_type(item_type)
            assert isinstance(result, str)
            assert result.startswith("IDOL_")


class TestIdolSizeMappingConsistency:
    """Test consistency between map_idol_size and map_idol_item_type."""

    def test_item_type_26_matches_minor_idol_string(self):
        """item_type 26 produces same result as Minor Idol (1x1) string."""
        result_item_type = map_idol_item_type(26)
        result_size_str = map_idol_size("Minor Idol (1x1)")
        assert result_item_type == result_size_str == "IDOL_1x1"

    def test_item_type_27_matches_humble_idol_string(self):
        """item_type 27 produces same result as Humble Idol (1x2) string (reversed to IDOL_2x1)."""
        result_item_type = map_idol_item_type(27)
        result_size_str = map_idol_size("Humble Idol (1x2)")
        assert result_item_type == result_size_str == "IDOL_2x1"

    def test_item_type_29_matches_grand_idol_string(self):
        """item_type 29 produces same result as Grand Idol (1x3) string (reversed to IDOL_3x1)."""
        result_item_type = map_idol_item_type(29)
        result_size_str = map_idol_size("Grand Idol (1x3)")
        assert result_item_type == result_size_str == "IDOL_3x1"

    def test_item_type_33_matches_adorned_idol_string(self):
        """item_type 33 produces same result as Adorned Idol (1x4) string (reversed to IDOL_4x1)."""
        result_item_type = map_idol_item_type(33)
        result_size_str = map_idol_size("Adorned Idol (1x4)")
        assert result_item_type == result_size_str == "IDOL_4x1"
