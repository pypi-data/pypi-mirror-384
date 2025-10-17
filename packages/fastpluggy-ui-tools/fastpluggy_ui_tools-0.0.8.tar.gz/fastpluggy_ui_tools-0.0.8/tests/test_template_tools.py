import base64
from typing import Optional

import pytest
from pydantic import BaseModel
from pydantic.v1 import BaseSettings

from fastpluggy.core.tools.template_tools import pydantic_model_dump, b64encode_filter


# Define test classes
class MyModel(BaseModel):
    name: str
    age: int

class MySettings(BaseSettings):
    app_name: Optional[str] = ""
    debug: bool

def test_pydantic_model_dump_with_base_model():
    model_instance = MyModel(name="Alice", age=30)
    result = pydantic_model_dump(model_instance)
    assert result == {"name": "Alice", "age": 30}, "Failed to correctly dump a BaseModel instance."

def test_pydantic_model_dump_with_base_settings():
    settings_instance = MySettings(app_name="MyApp", debug=True)
    result = pydantic_model_dump(settings_instance)
    assert result == {"app_name": "MyApp", "debug": True}, "Failed to correctly dump a BaseSettings instance."

def test_pydantic_model_dump_with_invalid_type():
    invalid_instance = {"not": "a pydantic model"}  # Not a Pydantic model
    with pytest.raises(ValueError, match="Provided object is not a Pydantic model or settings model."):
        pydantic_model_dump(invalid_instance)

def test_pydantic_model_dump_with_empty_model():
    empty_model = MyModel(name="", age=0)
    result = pydantic_model_dump(empty_model)
    assert result == {"name": "", "age": 0}, "Failed to correctly dump an empty BaseModel instance."

def test_pydantic_model_dump_with_partial_settings():
    partial_settings = MySettings(debug=False)  # `app_name` not provided, will use default if any
    result = pydantic_model_dump(partial_settings)
    assert result == {"app_name": '', "debug": False}, "Failed to correctly dump partially provided BaseSettings instance."


def test_b64encode_filter_with_valid_data():
    """Test b64encode_filter with valid binary data."""
    data = b"hello world"
    expected_result = base64.b64encode(data).decode('utf-8')
    assert b64encode_filter(data) == expected_result

def test_b64encode_filter_with_empty_input():
    """Test b64encode_filter with empty input."""
    assert b64encode_filter(b"") == ''

def test_b64encode_filter_with_none():
    """Test b64encode_filter when input is None."""
    assert b64encode_filter(None) == ''

def test_b64encode_filter_with_non_binary_input():
    """Test b64encode_filter raises TypeError for non-binary input."""
    with pytest.raises(TypeError):
        b64encode_filter("string input")