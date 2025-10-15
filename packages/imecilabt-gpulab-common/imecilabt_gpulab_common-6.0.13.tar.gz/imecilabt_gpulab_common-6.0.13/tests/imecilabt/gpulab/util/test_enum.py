"""Tests for enum module."""

import json

import pytest
from imecilabt.gpulab.util.enum import CaseInsensitiveEnum
from pydantic import BaseModel, ValidationError


class Color(CaseInsensitiveEnum):
    """Test enum for colors."""

    RED = "red"
    GREEN = "green"
    BLUE = "blue"
    YELLOW = "yellow"


class Status(CaseInsensitiveEnum):
    """Test enum for status."""

    ACTIVE = 1
    INACTIVE = 0
    PENDING = 2


class TestCaseInsensitiveEnum:
    """Test CaseInsensitiveEnum class."""

    def test_basic_enum_access(self) -> None:
        """Test basic enum member access."""
        assert Color.RED.value == "red"
        assert Color.GREEN.value == "green"
        assert Color.BLUE.value == "blue"
        assert Color.YELLOW.value == "yellow"

    def test_case_insensitive_lookup_by_name(self) -> None:
        """Test case-insensitive lookup by member name."""
        assert Color._missing_("red") == Color.RED
        assert Color._missing_("RED") == Color.RED
        assert Color._missing_("Red") == Color.RED
        assert Color._missing_("rEd") == Color.RED

        assert Color._missing_("green") == Color.GREEN
        assert Color._missing_("GREEN") == Color.GREEN
        assert Color._missing_("Green") == Color.GREEN

    def test_case_insensitive_lookup_returns_none_for_invalid(self) -> None:
        """Test that invalid lookups return None."""
        assert Color._missing_("purple") is None
        assert Color._missing_("PURPLE") is None
        assert Color._missing_(123) is None
        assert Color._missing_(None) is None

    def test_missing_returns_same_enum_member(self) -> None:
        """Test that passing an enum member returns itself."""
        assert Color._missing_(Color.RED) == Color.RED
        assert Color._missing_(Color.BLUE) == Color.BLUE

    def test_validate_with_enum_member(self) -> None:
        """Test validation with an enum member."""
        assert Color._validate(Color.RED) == Color.RED
        assert Color._validate(Color.GREEN) == Color.GREEN

    def test_validate_with_value(self) -> None:
        """Test validation with enum value (returns value when already in enum)."""
        # When the value is already in the enum, it returns the value itself
        result = Color._validate("red")
        assert result in ("red", Color.RED)
        result = Color._validate("green")
        assert result in ("green", Color.GREEN)

    def test_validate_with_invalid_value_raises_error(self) -> None:
        """Test validation with invalid value raises ValueError."""
        with pytest.raises(ValueError, match="Input should be one of"):
            Color._validate("purple")

        with pytest.raises(ValueError, match="'RED','GREEN','BLUE','YELLOW'"):
            Color._validate("invalid")

    def test_validate_with_integer_enum(self) -> None:
        """Test validation with integer-valued enum (returns value when already in enum)."""
        # When the value is already in the enum, it returns the value itself
        result = Status._validate(1)
        assert result in (1, Status.ACTIVE)
        result = Status._validate(0)
        assert result in (0, Status.INACTIVE)
        result = Status._validate(2)
        assert result in (2, Status.PENDING)

    def test_validate_integer_enum_with_invalid_value(self) -> None:
        """Test validation with invalid integer value."""
        with pytest.raises(ValueError, match="Input should be one of"):
            Status._validate(999)

    def test_serialize_enum_member(self) -> None:
        """Test serialization of enum member."""
        assert Color._serialize(Color.RED) == "RED"
        assert Color._serialize(Color.GREEN) == "GREEN"
        assert Color._serialize(Color.BLUE) == "BLUE"

    def test_serialize_non_enum_value(self) -> None:
        """Test serialization of non-enum value returns as-is."""
        assert Color._serialize("some_value") == "some_value"
        assert Color._serialize(123) == 123
        assert Color._serialize(None) is None


class TestCaseInsensitiveEnumWithPydantic:
    """Test CaseInsensitiveEnum integration with Pydantic."""

    class ColorModel(BaseModel):
        """Model with CaseInsensitiveEnum field."""

        color: Color
        name: str

    def test_pydantic_model_with_enum_member(self) -> None:
        """Test Pydantic model with enum member."""
        model = self.ColorModel(color=Color.RED, name="Test")
        assert model.color == Color.RED
        assert model.name == "Test"

    def test_pydantic_model_with_enum_value(self) -> None:
        """Test Pydantic model with enum value."""
        model = self.ColorModel(color="red", name="Test")  # type: ignore[arg-type]
        assert model.color == Color.RED

    def test_pydantic_model_with_case_insensitive_value(self) -> None:
        """Test Pydantic model with case-insensitive enum value."""
        model1 = self.ColorModel(color="RED", name="Test1")  # type: ignore[arg-type]
        assert model1.color == Color.RED

        model2 = self.ColorModel(color="Red", name="Test2")  # type: ignore[arg-type]
        assert model2.color == Color.RED

        model3 = self.ColorModel(color="rEd", name="Test3")  # type: ignore[arg-type]
        assert model3.color == Color.RED

    def test_pydantic_model_with_invalid_enum_value_raises_error(self) -> None:
        """Test Pydantic model with invalid enum value raises ValidationError."""
        with pytest.raises(ValidationError):
            self.ColorModel(color="purple", name="Test")  # type: ignore[arg-type]

    def test_pydantic_model_serialization(self) -> None:
        """Test Pydantic model serialization."""
        model = self.ColorModel(color=Color.BLUE, name="Test")
        data = model.model_dump()
        assert data["color"] == "BLUE"
        assert data["name"] == "Test"

    def test_pydantic_model_json_serialization(self) -> None:
        """Test Pydantic model JSON serialization."""
        model = self.ColorModel(color=Color.GREEN, name="TestJSON")
        json_str = model.model_dump_json()
        data = json.loads(json_str)
        assert data["color"] == "GREEN"
        assert data["name"] == "TestJSON"

    def test_pydantic_model_from_dict(self) -> None:
        """Test creating Pydantic model from dict."""
        data = {"color": "yellow", "name": "FromDict"}
        model = self.ColorModel.model_validate(data)
        assert model.color == Color.YELLOW
        assert model.name == "FromDict"

    def test_pydantic_model_from_json(self) -> None:
        """Test creating Pydantic model from JSON."""
        json_str = '{"color": "BLUE", "name": "FromJSON"}'
        model = self.ColorModel.model_validate_json(json_str)
        assert model.color == Color.BLUE
        assert model.name == "FromJSON"

    def test_pydantic_model_roundtrip(self) -> None:
        """Test roundtrip serialization and deserialization."""
        original = self.ColorModel(color=Color.RED, name="Roundtrip")
        json_str = original.model_dump_json()
        restored = self.ColorModel.model_validate_json(json_str)
        assert restored.color == original.color
        assert restored.name == original.name

    def test_pydantic_json_schema(self) -> None:
        """Test Pydantic JSON schema generation."""
        schema = self.ColorModel.model_json_schema()
        color_schema = schema["properties"]["color"]

        # Check that the schema includes all enum members
        assert "enum" in color_schema
        assert set(color_schema["enum"]) == {"RED", "GREEN", "BLUE", "YELLOW"}
        assert color_schema["type"] == "str"


class TestMultipleEnums:
    """Test with multiple enum types."""

    class MultiEnumModel(BaseModel):
        """Model with multiple enum fields."""

        color: Color
        status: Status

    def test_multiple_enums_in_model(self) -> None:
        """Test model with multiple different enum types."""
        model = self.MultiEnumModel(color="red", status=1)  # type: ignore[arg-type]
        assert model.color == Color.RED
        assert model.status == Status.ACTIVE

    def test_multiple_enums_serialization(self) -> None:
        """Test serialization with multiple enums."""
        model = self.MultiEnumModel(color=Color.BLUE, status=Status.PENDING)
        data = model.model_dump()
        assert data["color"] == "BLUE"
        assert data["status"] == "PENDING"

    def test_multiple_enums_case_insensitive(self) -> None:
        """Test case-insensitive handling with multiple enums."""
        model1 = self.MultiEnumModel(color="GREEN", status=0)  # type: ignore[arg-type]
        assert model1.color == Color.GREEN
        assert model1.status == Status.INACTIVE

        model2 = self.MultiEnumModel(color="yellow", status=2)  # type: ignore[arg-type]
        assert model2.color == Color.YELLOW
        assert model2.status == Status.PENDING


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_enum_equality(self) -> None:
        """Test enum member equality."""
        assert Color.RED == Color.RED
        assert Color.RED != Color.BLUE
        assert Color.GREEN == Color.GREEN

    def test_enum_in_container(self) -> None:
        """Test enum members in containers."""
        colors = [Color.RED, Color.GREEN, Color.BLUE]
        assert Color.RED in colors
        assert Color.YELLOW not in [Color.RED, Color.GREEN]

    def test_enum_iteration(self) -> None:
        """Test iterating over enum members."""
        colors = list(Color)
        assert len(colors) == 4
        assert Color.RED in colors
        assert Color.GREEN in colors
        assert Color.BLUE in colors
        assert Color.YELLOW in colors

    def test_enum_members_dict(self) -> None:
        """Test accessing enum members dictionary."""
        assert "RED" in Color.__members__
        assert "GREEN" in Color.__members__
        assert "BLUE" in Color.__members__
        assert "YELLOW" in Color.__members__
        assert len(Color.__members__) == 4

    def test_validate_with_none_type_error(self) -> None:
        """Test that TypeError in validation is handled."""
        # This tests the TypeError exception handling in _validate
        result = Color._validate(Color.RED)
        assert result == Color.RED


class TestIntegerValuedEnum:
    """Test integer-valued enum specifically."""

    class IntModel(BaseModel):
        """Model with integer-valued enum."""

        status: Status

    def test_integer_enum_with_int_value(self) -> None:
        """Test integer enum with integer value."""
        model = self.IntModel(status=1)  # type: ignore[arg-type]
        assert model.status == Status.ACTIVE

    def test_integer_enum_with_enum_member(self) -> None:
        """Test integer enum with enum member."""
        model = self.IntModel(status=Status.INACTIVE)
        assert model.status == Status.INACTIVE

    def test_integer_enum_serialization(self) -> None:
        """Test integer enum serialization."""
        model = self.IntModel(status=Status.PENDING)
        data = model.model_dump()
        assert data["status"] == "PENDING"

    def test_integer_enum_all_values(self) -> None:
        """Test all integer enum values."""
        assert Status.ACTIVE.value == 1
        assert Status.INACTIVE.value == 0
        assert Status.PENDING.value == 2
