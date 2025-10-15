from flexai.tool import TYPE_UNSPECIFIED, Tool, format_primitive_type, format_type


def example_function() -> str:
    """A simple test function to use with Tool."""
    return "test result"


def test_tool_from_function():
    tool = Tool.from_function(example_function)
    assert tool.name == "example_function"
    assert tool.description == "A simple test function to use with Tool."
    assert tool.params == ()
    assert tool.return_type == "str"
    assert tool.fn() == "test result"


def test_format_primitive_type_all_mapped_types():
    """Test format_primitive_type with all types in TYPE_MAP."""
    assert format_primitive_type(str) == "string"
    assert format_primitive_type(int) == "number"
    assert format_primitive_type(float) == "number"
    assert format_primitive_type(bool) == "boolean"
    assert format_primitive_type(list) == "array"
    assert format_primitive_type(dict) == "object"
    assert format_primitive_type(type(None)) == "null"


def test_format_primitive_type_unmapped_type():
    """Test format_primitive_type with unmapped type."""

    class CustomType:
        pass

    assert format_primitive_type(CustomType) == TYPE_UNSPECIFIED
    assert format_primitive_type(tuple) == TYPE_UNSPECIFIED


def test_format_type_single_types():
    """Test format_type with single primitive types."""
    assert format_type(str) == "string"
    assert format_type(int) == "number"
    assert format_type(bool) == "boolean"


def test_format_type_union_types():
    """Test format_type with union types."""
    union_type = str | int
    result = format_type(union_type)
    assert isinstance(result, tuple)
    assert set(result) == {"string", "number"}

    # Test union with None
    optional_str = str | None
    result = format_type(optional_str)
    assert isinstance(result, tuple)
    assert set(result) == {"string", "null"}


def test_format_type_complex_union():
    """Test format_type with complex union types."""
    complex_union = str | int | bool | list
    result = format_type(complex_union)
    assert isinstance(result, tuple)
    assert set(result) == {"string", "number", "boolean", "array"}


def test_format_type_unmapped_types():
    """Test format_type with unmapped types and union containing unmapped types."""

    class CustomType:
        pass

    # Single unmapped type
    assert format_type(CustomType) == TYPE_UNSPECIFIED

    # Union with unmapped type
    union_with_unmapped = str | CustomType
    result = format_type(union_with_unmapped)
    assert isinstance(result, tuple)
    assert set(result) == {"string", TYPE_UNSPECIFIED}
