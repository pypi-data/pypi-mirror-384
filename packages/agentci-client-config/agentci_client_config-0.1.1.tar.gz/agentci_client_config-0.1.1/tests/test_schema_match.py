"""Tests for schema matching functionality."""

import pytest
from agentci.client_config import SchemaField, StringMatch


class TestSchemaField:
    """Test SchemaField validation and constraints."""

    def test_basic_types(self):
        """Test basic type definitions."""
        str_field = SchemaField(type="str")
        assert str_field.type == "str"
        assert str_field.required is True

        int_field = SchemaField(type="int")
        assert int_field.type == "int"

    def test_optional_field(self):
        """Test optional field definition."""
        field = SchemaField(type="str", required=False)
        assert field.required is False

    def test_default_value(self):
        """Test field with default value."""
        field = SchemaField(type="int", default=30)
        assert field.default == 30

    def test_enum_constraint(self):
        """Test enum/literal constraint."""
        field = SchemaField(type="str", enum=["active", "inactive", "pending"])
        assert field.enum == ["active", "inactive", "pending"]

    def test_string_length_constraints(self):
        """Test string length validation constraints."""
        field = SchemaField(type="str", min_length=3, max_length=20)
        assert field.min_length == 3
        assert field.max_length == 20

    def test_string_length_on_non_string_fails(self):
        """Test that string length constraints on non-string types fail."""
        with pytest.raises(ValueError):
            SchemaField(type="int", min_length=3)

    def test_number_bounds(self):
        """Test number min/max constraints."""
        field = SchemaField(type="int", min=0, max=120)
        assert field.min == 0
        assert field.max == 120

    def test_number_bounds_on_non_number_fails(self):
        """Test that number bounds on non-number types fail."""
        with pytest.raises(ValueError):
            SchemaField(type="str", min=0)

    def test_array_size_constraints(self):
        """Test array size validation."""
        field = SchemaField(type="list[str]", min_items=1, max_items=10)
        assert field.min_items == 1
        assert field.max_items == 10

    def test_array_size_on_non_array_fails(self):
        """Test that array size constraints on non-array types fail."""
        with pytest.raises(ValueError):
            SchemaField(type="str", min_items=1)

    def test_nested_schema_for_list_items(self):
        """Test nested schema definition for list items."""
        field = SchemaField(
            type="list",
            items={
                "id": SchemaField(type="int"),
                "name": SchemaField(type="str"),
            },
        )
        assert field.items is not None
        assert "id" in field.items
        assert "name" in field.items

    def test_items_on_non_list_fails(self):
        """Test that items constraint on non-list types fails."""
        with pytest.raises(ValueError):
            SchemaField(type="str", items={"id": SchemaField(type="int")})

    def test_union_types(self):
        """Test union type specification."""
        field = SchemaField(type=["str", "int", "float"])
        assert field.type == ["str", "int", "float"]

    def test_nested_object_schema(self):
        """Test nested schema definition using type as dict."""
        field = SchemaField(
            type={
                "id": SchemaField(type="int"),
                "name": SchemaField(type="str"),
                "email": SchemaField(type="str", required=False),
            },
        )
        assert field.type is not None
        assert isinstance(field.type, dict)
        assert "id" in field.type
        assert "name" in field.type
        assert "email" in field.type
        assert field.type["email"].required is False

    def test_deeply_nested_object_schema(self):
        """Test deeply nested schema definition."""
        field = SchemaField(
            type={
                "user": SchemaField(
                    type={
                        "id": SchemaField(type="int"),
                        "profile": SchemaField(
                            type={
                                "name": SchemaField(type="str"),
                                "age": SchemaField(type="int"),
                            }
                        ),
                    }
                ),
            },
        )
        assert isinstance(field.type, dict)
        assert "user" in field.type
        assert isinstance(field.type["user"].type, dict)
        assert "profile" in field.type["user"].type
        assert isinstance(field.type["user"].type["profile"].type, dict)

    def test_field_without_type(self):
        """Test SchemaField without type (nested object definition)."""
        # When type is None, it's likely a nested object definition
        # Validator should skip constraint validation in this case
        field = SchemaField(required=False, default=None)
        assert field.type is None
        assert field.required is False


class TestStringMatchWithSchema:
    """Test StringMatch with schema matching strategy."""

    def test_basic_schema(self):
        """Test basic schema matching configuration."""
        schema_match = StringMatch(
            schema={
                "temperature": SchemaField(type="float"),
                "condition": SchemaField(type="str"),
                "humidity": SchemaField(type="int"),
            }
        )
        assert schema_match.schema is not None
        assert len(schema_match.schema) == 3

    def test_schema_with_optional_fields(self):
        """Test schema with optional fields."""
        schema_match = StringMatch(
            schema={
                "name": SchemaField(type="str"),
                "age": SchemaField(type="int"),
                "email": SchemaField(type="str", required=False),
            }
        )
        assert schema_match.schema["email"].required is False

    def test_schema_with_validation_constraints(self):
        """Test schema with validation constraints."""
        schema_match = StringMatch(
            schema={
                "username": SchemaField(type="str", min_length=3, max_length=20),
                "age": SchemaField(type="int", min=0, max=120),
                "status": SchemaField(type="str", enum=["active", "inactive"]),
            }
        )
        assert schema_match.schema["username"].min_length == 3
        assert schema_match.schema["age"].min == 0
        assert schema_match.schema["status"].enum == ["active", "inactive"]

    def test_schema_with_list_items(self):
        """Test schema with list of objects."""
        schema_match = StringMatch(
            schema={
                "products": SchemaField(
                    type="list",
                    items={
                        "id": SchemaField(type="int"),
                        "name": SchemaField(type="str"),
                        "price": SchemaField(type="float"),
                    },
                )
            }
        )
        assert schema_match.schema["products"].items is not None
        assert "id" in schema_match.schema["products"].items

    def test_schema_mutually_exclusive_with_other_strategies(self):
        """Test that schema cannot be combined with other strategies."""
        with pytest.raises(ValueError):
            StringMatch(
                exact="test",
                schema={"field": SchemaField(type="str")},
            )

        with pytest.raises(ValueError):
            StringMatch(
                contains="test",
                schema={"field": SchemaField(type="str")},
            )

    def test_schema_as_only_strategy(self):
        """Test that schema can be the only strategy."""
        schema_match = StringMatch(
            schema={"field": SchemaField(type="str")}
        )
        assert schema_match.schema is not None
        assert schema_match.exact is None
        assert schema_match.contains is None


class TestSchemaFieldValue:
    """Test SchemaField with value matching."""

    def test_exact_string_value(self):
        """Test exact string match on field value."""
        field = SchemaField(type="str", value="operational")
        assert field.value is not None
        assert isinstance(field.value, StringMatch)
        assert field.value.exact == "operational"

    def test_substring_value(self):
        """Test substring matching on field value."""
        field = SchemaField(
            type="str",
            value=StringMatch(contains="timeout")
        )
        assert field.value is not None
        assert field.value.contains == "timeout"

    def test_regex_value(self):
        """Test regex matching on field value."""
        field = SchemaField(
            type="str",
            value=StringMatch(match=r"^\d{3}-\d{3}-\d{4}$")
        )
        assert field.value is not None
        assert field.value.match == r"^\d{3}-\d{3}-\d{4}$"

    def test_semantic_similarity_value(self):
        """Test semantic similarity on field value."""
        field = SchemaField(
            type="str",
            value=StringMatch(similar="Welcome!", threshold=0.8)
        )
        assert field.value is not None
        assert field.value.similar == "Welcome!"
        assert field.value.threshold == 0.8

    def test_value_with_type_constraints(self):
        """Test combining value matching with type constraints."""
        field = SchemaField(
            type="str",
            min_length=3,
            max_length=20,
            value=StringMatch(contains="test")
        )
        assert field.min_length == 3
        assert field.max_length == 20
        assert field.value.contains == "test"
