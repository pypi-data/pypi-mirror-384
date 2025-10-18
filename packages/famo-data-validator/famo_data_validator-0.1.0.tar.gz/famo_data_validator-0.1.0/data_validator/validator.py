import re
from typing import Any, Dict, Callable, List
from .errors import ValidationError

try:
    import validators  # optional, for email/url validation
except ImportError:
    validators = None

class Validator:
    """
    Professional data validator class that validates dictionaries / JSON-like objects
    and returns the cleaned/validated data.

    Features:
    - Type checking
    - Required fields
    - String: min_length, max_length, regex, email, url
    - Numeric: min_value, max_value, positive, negative, multiple_of
    - Boolean type
    - List: min_length, max_length, unique, item_type
    - Nested dict validation
    - Enum / choices
    - Custom validator functions
    - Default values

    Args:
        schema (Dict[str, Dict[str, Any]]): Dictionary of field names and rules.

    Example schema:
        schema = {
            "name": {"type": str, "required": True, "min_length": 3},
            "age": {"type": int, "min_value": 0, "default": 18},
            "email": {"type": str, "email": True},
            "tags": {"type": list, "min_length": 1, "item_type": str, "default": []},
            "status": {"type": str, "choices": ["active", "inactive"], "default": "active"}
        }
    """

    def __init__(self, schema: Dict[str, Dict[str, Any]]):
        self.schema = schema

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the input data against the schema and return cleaned data.

        Args:
            data (dict): Input dictionary to validate.

        Returns:
            Dict[str, Any]: Validated and cleaned data with defaults applied.

        Raises:
            ValidationError: If any validation fails.
        """
        errors = {}
        validated_data = {}

        for field, rules in self.schema.items():
            value = data.get(field, rules.get("default"))

            # Required check
            if rules.get("required") and value is None:
                errors[field] = "This field is required."
                continue

            # Skip None for optional fields
            if value is None:
                validated_data[field] = value
                continue

            # Type check
            expected_type = rules.get("type")
            if expected_type and not isinstance(value, expected_type):
                errors[field] = f"Expected type {expected_type.__name__}, got {type(value).__name__}"
                continue

            # String validations
            if isinstance(value, str):
                if "min_length" in rules and len(value) < rules["min_length"]:
                    errors[field] = f"Minimum length is {rules['min_length']}"
                if "max_length" in rules and len(value) > rules["max_length"]:
                    errors[field] = f"Maximum length is {rules['max_length']}"
                if "regex" in rules and not re.match(rules["regex"], value):
                    errors[field] = f"Value does not match pattern: {rules['regex']}"
                if rules.get("email") and validators and not validators.email(value):
                    errors[field] = "Invalid email address."
                if rules.get("url") and validators and not validators.url(value):
                    errors[field] = "Invalid URL."

            # Numeric validations
            if isinstance(value, (int, float)):
                if "min_value" in rules and value < rules["min_value"]:
                    errors[field] = f"Minimum value is {rules['min_value']}"
                if "max_value" in rules and value > rules["max_value"]:
                    errors[field] = f"Maximum value is {rules['max_value']}"
                if rules.get("positive") and value <= 0:
                    errors[field] = "Value must be positive."
                if rules.get("negative") and value >= 0:
                    errors[field] = "Value must be negative."
                if "multiple_of" in rules and value % rules["multiple_of"] != 0:
                    errors[field] = f"Value must be multiple of {rules['multiple_of']}"

            # Boolean type
            if expected_type == bool and not isinstance(value, bool):
                errors[field] = "Value must be boolean."

            # List validations
            if isinstance(value, list):
                if "min_length" in rules and len(value) < rules["min_length"]:
                    errors[field] = f"Minimum length is {rules['min_length']}"
                if "max_length" in rules and len(value) > rules["max_length"]:
                    errors[field] = f"Maximum length is {rules['max_length']}"
                if rules.get("unique") and len(set(value)) != len(value):
                    errors[field] = "List elements must be unique."
                if "item_type" in rules:
                    for i, item in enumerate(value):
                        if not isinstance(item, rules["item_type"]):
                            errors[field] = f"Item at index {i} must be {rules['item_type'].__name__}"
                # Nested list of dicts
                if "schema" in rules:
                    sub_validator = Validator(rules["schema"])
                    validated_list = []
                    for i, item in enumerate(value):
                        try:
                            validated_item = sub_validator.validate(item)
                            validated_list.append(validated_item)
                        except ValidationError as ve:
                            errors[field] = {f"index_{i}": ve.errors}
                    value = validated_list  # replace with validated sublist

            # Nested dict validation
            if isinstance(value, dict) and "schema" in rules:
                sub_validator = Validator(rules["schema"])
                try:
                    value = sub_validator.validate(value)
                except ValidationError as ve:
                    errors[field] = ve.errors

            # Choices / Enum validation
            if "choices" in rules and value not in rules["choices"]:
                errors[field] = f"Value must be one of {rules['choices']}"

            # Custom function validation
            if "custom" in rules and callable(rules["custom"]):
                try:
                    valid = rules["custom"](value)
                    if not valid:
                        errors[field] = "Custom validation failed."
                except Exception as e:
                    errors[field] = f"Custom validation error: {str(e)}"

            # If no error, assign validated value
            if field not in errors:
                validated_data[field] = value

        if errors:
            raise ValidationError(errors)

        return validated_data
