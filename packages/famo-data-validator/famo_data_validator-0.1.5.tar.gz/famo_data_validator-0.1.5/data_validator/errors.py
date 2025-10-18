class ValidationError(Exception):
    """
    Exception raised when validation fails for one or more fields.

    Attributes:
        errors (dict): Dictionary mapping field names to error messages.
    """

    def __init__(self, errors: dict):
        """
        Initialize ValidationError with a dictionary of errors.

        Args:
            errors (dict): A mapping of field names to error messages.
        """
        self.errors = errors
        super().__init__(errors)
