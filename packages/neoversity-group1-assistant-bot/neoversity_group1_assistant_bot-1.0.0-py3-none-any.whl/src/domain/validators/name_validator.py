from ..validators.string_validator import StringValidator


class NameValidator:
    @staticmethod
    def validate(value: str) -> str | bool:
        if not StringValidator.is_string(value):
            return "Name must be a string"
        if not StringValidator.is_not_empty(value):
            return "Name cannot be empty or whitespace"
        if not StringValidator.has_max_length(value, 25):
            return "Name cannot exceed 25 characters"
        return True
