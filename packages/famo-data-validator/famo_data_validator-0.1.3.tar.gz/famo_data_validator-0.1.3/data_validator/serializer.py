from typing import Dict, Any, List, Union, Generic, TypeVar
from .fields import BaseField
from .errors import ValidationError

T = TypeVar("T", bound=Dict[str, Any])  # Single object type


class Serializer(Generic[T]):
    """
    A general-purpose serializer for validating dictionaries or lists of dictionaries.

    Attributes:
        data (dict or list of dict): Input data to validate.
            - If many=False (default), pass a single dictionary.
            - If many=True, pass a list of dictionaries.
        many (bool): Whether the serializer expects multiple objects.
        validated_data (dict or list of dict): Returns validated data after validation.
        errors (dict): Validation errors, if any.
    """

    data: Union[T, List[T], None]
    many: bool
    validated_data: Union[T, List[T], None]
    errors: dict

    def __init__(self, data: Union[T, List[T]] = None, many: bool = False):
        """
        Initialize the serializer.

        Args:
            data (dict or list of dict): Input data to validate.
            many (bool): Whether to validate multiple items.
        """
        self.data = data
        self.many = many
        self.validated_data = None
        self.errors = {}
        self.fields: Dict[str, BaseField] = {}
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if isinstance(attr, BaseField):
                self.fields[attr_name] = attr

    def is_valid(self, raise_exception: bool = False) -> bool:
        """
        Validate input data.

        Args:
            raise_exception (bool): Raise ValidationError if validation fails.

        Returns:
            bool: True if valid, False otherwise.

        Raises:
            ValidationError: If validation fails and raise_exception=True.
        """
        try:
            if self.many:
                if not isinstance(self.data, list):
                    raise ValidationError({"non_field_errors": "Expected a list of items when many=True"})
                self.validated_data = [self._validate_item(item) for item in self.data]
            else:
                if not isinstance(self.data, dict):
                    raise ValidationError({"non_field_errors": "Expected a dictionary when many=False"})
                self.validated_data = self._validate_item(self.data)
            return True
        except ValidationError as e:
            self.errors = e.errors
            if raise_exception:
                raise e
            return False

    def _validate_item(self, item: dict) -> dict:
        """
        Validate a single dictionary against the serializer fields.

        Args:
            item (dict): Input dictionary.

        Returns:
            dict: Validated dictionary.

        Raises:
            ValidationError: If any field fails validation.
        """
        errors = {}
        validated_data = {}

        for name, field in self.fields.items():
            value = item.get(name, field.default)
            if value is None and field.required:
                errors[name] = "This field is required"
                continue
            if value is None:
                validated_data[name] = value
                continue
            try:
                validated_value = field.validate(value, field_name=name)
                validated_data[name] = validated_value
            except ValidationError as e:
                if isinstance(e.errors, dict):
                    errors.update(e.errors)
                else:
                    errors[name] = str(e)

        if errors:
            raise ValidationError(errors)

        return validated_data

    def get_schema(self) -> Dict[str, dict]:
        """
        Return a schema dictionary for documentation.

        Each field includes:
            - type
            - required
            - default
            - additional arguments like min_length, max_value, choices, etc.

        Returns:
            dict: Mapping field names to attributes.
        """
        schema = {}
        for name, field in self.fields.items():
            field_schema = {
                "type": type(field).__name__,
                "required": getattr(field, "required", True),
                "default": getattr(field, "default", None),
            }
            # Include all other user-set attributes dynamically
            for key, value in field.__dict__.items():
                if key not in ["required", "default", "validators_list", "custom"]:
                    field_schema[key] = value
            schema[name] = field_schema
        return schema
