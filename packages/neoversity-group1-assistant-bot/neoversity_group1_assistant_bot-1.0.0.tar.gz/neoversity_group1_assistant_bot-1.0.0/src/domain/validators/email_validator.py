from ..validators.string_validator import StringValidator

class EmailValidator:
    """Handles the logic for validating email strings."""

    _pattern = r'^[a-zA-Z0-9._%+-]+@(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$'

    @staticmethod
    def validate(email: str) -> str | bool:
        if not StringValidator.is_string(email):
            return "Email must be a string"
        if not StringValidator.is_not_empty(email):
            return "Email cannot be empty or whitespace"
        if not StringValidator.has_max_length(email, 100):
            return "Email cannot exceed 100 characters. Current length: {}".format(len(email))
        if not StringValidator.matches_pattern(email, EmailValidator._pattern):
            return "Email format is invalid. Current value: {}".format(email)
        return True
