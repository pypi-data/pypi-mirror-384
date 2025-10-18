from ..validators.string_validator import StringValidator

class AddressValidator:

    @staticmethod
    def validate(value: str) -> bool | str:
        if not StringValidator.is_string(value):
            return "Address must be a string"
        if not StringValidator.is_not_empty(value):
            return "Address cannot be empty or whitespace"
        if not StringValidator.has_max_length(value, 200):
            return "Address cannot exceed 200 characters"
        return True
