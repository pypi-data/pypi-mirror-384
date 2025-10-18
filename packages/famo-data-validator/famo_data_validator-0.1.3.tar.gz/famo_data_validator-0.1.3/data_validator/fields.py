import re
from typing import Callable, Optional, List
from .errors import ValidationError

try:
    import validators
except ImportError:
    validators = None


class BaseField:
    """
    Base class for all field types.
    Handles common attributes such as required, default values, and custom validators.
    """

    def __init__(
        self,
        required: bool = True,
        default: Optional = None,
        validators_list: Optional[List[Callable]] = None,
        custom: Optional[Callable] = None,
    ):
        self.required = required
        self.default = default
        self.validators_list = validators_list or []
        self.custom = custom

    def validate(self, value, field_name: str = None):
        """
        Validate the field value.

        Args:
            value: Value to validate.
            field_name (str): Field name for error messages.

        Returns:
            Validated value.

        Raises:
            ValidationError: If validation fails.
        """
        raise NotImplementedError("Each field must implement the validate method.")

    def run_validators(self, value, field_name: str):
        """Run custom and list-based validators."""
        for v in self.validators_list:
            if callable(v) and not v(value):
                raise ValidationError({field_name: f"Validator {v.__name__} failed for value {value}"})
        if self.custom and not self.custom(value):
            raise ValidationError({field_name: "Custom validation failed"})


class CharField(BaseField):
    """
    String field with optional length, regex, and choices validation.
    """

    def __init__(self, min_length: int = None, max_length: int = None, regex: str = None, choices: list = None, **kwargs):
        super().__init__(**kwargs)
        self.min_length = min_length
        self.max_length = max_length
        self.regex = regex
        self.choices = choices

    def validate(self, value, field_name: str = None):
        field_name = field_name or "field"
        if not isinstance(value, str):
            raise ValidationError({field_name: "Expected string value"})
        if self.min_length and len(value) < self.min_length:
            raise ValidationError({field_name: f"Minimum length is {self.min_length}"})
        if self.max_length and len(value) > self.max_length:
            raise ValidationError({field_name: f"Maximum length is {self.max_length}"})
        if self.regex and not re.match(self.regex, value):
            raise ValidationError({field_name: f"Value does not match regex: {self.regex}"})
        if self.choices and value not in self.choices:
            raise ValidationError({field_name: f"Value must be one of {self.choices}"})
        self.run_validators(value, field_name)
        return value


class IntegerField(BaseField):
    """Integer field with optional min/max, positive/negative, multiple_of validation."""

    def __init__(self, min_value: int = None, max_value: int = None, positive: bool = False, negative: bool = False,
                 multiple_of: int = None, **kwargs):
        super().__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value
        self.positive = positive
        self.negative = negative
        self.multiple_of = multiple_of

    def validate(self, value, field_name: str = None):
        field_name = field_name or "field"
        if not isinstance(value, int):
            raise ValidationError({field_name: "Expected integer value"})
        if self.min_value is not None and value < self.min_value:
            raise ValidationError({field_name: f"Minimum value is {self.min_value}"})
        if self.max_value is not None and value > self.max_value:
            raise ValidationError({field_name: f"Maximum value is {self.max_value}"})
        if self.positive and value <= 0:
            raise ValidationError({field_name: "Value must be positive"})
        if self.negative and value >= 0:
            raise ValidationError({field_name: "Value must be negative"})
        if self.multiple_of and value % self.multiple_of != 0:
            raise ValidationError({field_name: f"Value must be multiple of {self.multiple_of}"})
        self.run_validators(value, field_name)
        return value


class FloatField(BaseField):
    """Floating-point field with optional min/max validation."""

    def __init__(self, min_value: float = None, max_value: float = None, **kwargs):
        super().__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value

    def validate(self, value, field_name: str = None):
        field_name = field_name or "field"
        if not isinstance(value, (float, int)):
            raise ValidationError({field_name: "Expected float value"})
        if self.min_value is not None and value < self.min_value:
            raise ValidationError({field_name: f"Minimum value is {self.min_value}"})
        if self.max_value is not None and value > self.max_value:
            raise ValidationError({field_name: f"Maximum value is {self.max_value}"})
        self.run_validators(value, field_name)
        return value


class BooleanField(BaseField):
    """Boolean field."""

    def validate(self, value, field_name: str = None):
        field_name = field_name or "field"
        if not isinstance(value, bool):
            raise ValidationError({field_name: "Expected boolean value"})
        self.run_validators(value, field_name)
        return value


class EmailField(CharField):
    """String field validated as an email."""

    def validate(self, value, field_name: str = None):
        value = super().validate(value, field_name)
        if validators and not validators.email(value):
            raise ValidationError({field_name: "Invalid email address"})
        return value


class URLField(CharField):
    """String field validated as a URL."""

    def validate(self, value, field_name: str = None):
        value = super().validate(value, field_name)
        if validators and not validators.url(value):
            raise ValidationError({field_name: "Invalid URL"})
        return value


class ListField(BaseField):
    """List field with optional item validation, uniqueness, min/max length."""

    def __init__(self, item_field: BaseField = None, min_length: int = None, max_length: int = None, unique: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.item_field = item_field
        self.min_length = min_length
        self.max_length = max_length
        self.unique = unique

    def validate(self, value, field_name: str = None):
        field_name = field_name or "field"
        if not isinstance(value, list):
            raise ValidationError({field_name: "Expected list"})
        if self.min_length is not None and len(value) < self.min_length:
            raise ValidationError({field_name: f"Minimum length is {self.min_length}"})
        if self.max_length is not None and len(value) > self.max_length:
            raise ValidationError({field_name: f"Maximum length is {self.max_length}"})
        if self.unique and len(set(value)) != len(value):
            raise ValidationError({field_name: "List elements must be unique"})
        if self.item_field:
            validated_list = []
            for i, item in enumerate(value):
                try:
                    validated_list.append(self.item_field.validate(item, field_name=f"{field_name}[{i}]"))
                except ValidationError as e:
                    raise ValidationError(e.errors)
            value = validated_list
        self.run_validators(value, field_name)
        return value


class DictField(BaseField):
    """Dictionary field validated via a nested Serializer."""

    def __init__(self, serializer=None, **kwargs):
        super().__init__(**kwargs)
        self.serializer = serializer

    def validate(self, value, field_name: str = None):
        field_name = field_name or "field"
        if not isinstance(value, dict):
            raise ValidationError({field_name: "Expected dict"})
        if self.serializer:
            serializer_instance = self.serializer(data=value)
            serializer_instance.is_valid(raise_exception=True)
            value = serializer_instance.validated_data
        self.run_validators(value, field_name)
        return value
