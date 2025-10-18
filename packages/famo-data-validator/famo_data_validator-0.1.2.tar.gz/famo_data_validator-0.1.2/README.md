# Famo Data Validator

**Famo Data Validator** is a Python library for validating dictionaries and lists of dictionaries using a schema-based approach.
It supports default values, required fields, custom validation, and schema generation.

---

## Features

* Validate **single objects** or **multiple objects** (`many=True`)
* Built-in field types: `CharField`, `IntegerField`, `EmailField`, `ListField`
* Required fields and default values
* Custom validation support
* Generate schema dynamically for documentation
* Fully typed and IDE-friendly

---

## Installation

```bash
pip install famo-data-validator
```

Or install the latest version from GitHub:

```bash
pip install git+https://github.com/famo-codes/data-validator.git
```

---

## Examples

### 1. Single Object Validation

```python
from data_validator.serializer import Serializer
from data_validator.fields import CharField, IntegerField, EmailField, ListField

class UserSerializer(Serializer):
    name = CharField(min_length=3, max_length=50, required=True)
    age = IntegerField(min_value=0, max_value=120, default=18)
    email = EmailField(required=True)
    tags = ListField(item_field=CharField(), min_length=1, default=[])
    status = CharField(choices=["active", "inactive"], default="active")

user_data = {"name": "Alice", "email": "alice@example.com", "tags": ["python"]}
serializer = UserSerializer(data=user_data)
serializer.is_valid(raise_exception=True)
print(serializer.validated_data)
```

**Output:**

```python
{
    "name": "Alice",
    "age": 18,
    "email": "alice@example.com",
    "tags": ["python"],
    "status": "active"
}
```

---

### 2. Multiple Objects Validation

```python
users = [
    {"name": "Alice", "email": "alice@example.com", "tags": ["python"]},
    {"name": "Bob", "email": "bob@example.com", "tags": ["backend"]}
]

serializer_many = UserSerializer(data=users, many=True)
serializer_many.is_valid(raise_exception=True)
print(serializer_many.validated_data)
```

**Output:**

```python
[
    {"name": "Alice", "age": 18, "email": "alice@example.com", "tags": ["python"], "status": "active"},
    {"name": "Bob", "age": 18, "email": "bob@example.com", "tags": ["backend"], "status": "active"}
]
```

---

### 3. Generate Schema for Documentation

```python
import json

schema = UserSerializer().get_schema()
print(json.dumps(schema, indent=4))
```

**Sample Output:**

```python
{
    "name": {"type": "CharField", "required": True, "default": None, "min_length": 3, "max_length": 50},
    "age": {"type": "IntegerField", "required": True, "default": 18, "min_value": 0, "max_value": 120},
    "email": {"type": "EmailField", "required": True, "default": None},
    "tags": {"type": "ListField", "required": True, "default": [], "item_field": "<CharField instance>", "min_length": 1},
    "status": {"type": "CharField", "required": True, "default": "active", "choices": ["active", "inactive"]}
}
```

---

### 4. Custom Validator Example

```python
from data_validator.fields import IntegerField, ValidationError

class PositiveIntegerField(IntegerField):
    def validate(self, value, field_name=None):
        value = super().validate(value, field_name)
        if value <= 0:
            raise ValidationError({field_name: "Value must be positive"})
        return value

class ProductSerializer(Serializer):
    price = PositiveIntegerField(required=True)

product_data = {"price": 50}
serializer = ProductSerializer(data=product_data)
serializer.is_valid(raise_exception=True)
print(serializer.validated_data)
```

**Output:**

```python
{"price": 50}
```

---

### 5. Handling Validation Errors

```python
invalid_data = {"name": "A", "email": "invalid_email"}
serializer = UserSerializer(data=invalid_data)

if not serializer.is_valid():
    print(serializer.errors)
```

**Sample Output:**

```python
{
    "name": "Minimum length is 3",
    "email": "Invalid email address"
}
```

---

## License

MIT License

Copyright (c) 2025 Famo

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


```
```
