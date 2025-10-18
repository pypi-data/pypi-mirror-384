import pytest
from data_validator.validator import Validator, ValidationError

def test_validator_success():
    """
    Test a successful validation scenario.
    """
    schema = {"name": {"type": str, "required": True, "min_length": 3}}
    validator = Validator(schema)
    data = {"name": "Alice"}
    assert validator.validate(data) == True

def test_validator_failure():
    """
    Test validation failure due to short string length.
    """
    schema = {"name": {"type": str, "required": True, "min_length": 3}}
    validator = Validator(schema)
    data = {"name": "Al"}
    with pytest.raises(ValidationError):
        validator.validate(data)
