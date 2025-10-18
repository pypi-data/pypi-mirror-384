from ..validators.string_validator import StringValidator


class TagValidator:

    @staticmethod
    def validate(value: str) -> bool | str:
        if not StringValidator.is_string(value):
            return "Tag must be a string"
        if not StringValidator.is_not_empty(value):
            return "Tag cannot be empty"
        if not StringValidator.has_max_length(value, 50):
            return "Tag too long (max 50 characters)"
        return True
