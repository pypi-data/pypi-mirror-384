class StringValidator:

    @staticmethod
    def is_string(value) -> bool:
        return isinstance(value, str)

    @staticmethod
    def is_empty(value) -> bool:
        return not bool(value and value.strip())

    @staticmethod
    def is_not_empty(value) -> bool:
        return bool(value and value.strip())

    @staticmethod
    def has_min_length(value, min_length) -> bool:
        return len(value) >= min_length

    @staticmethod
    def has_max_length(value, max_length) -> bool:
        return len(value) <= max_length

    @staticmethod
    def has_length(value, length) -> bool:
        return len(value) == length

    @staticmethod
    def matches_pattern(value, pattern) -> bool:
        import re
        return bool(re.match(pattern, value))

    @staticmethod
    def exactly_match_pattern(value, pattern) -> bool:
        import re
        return bool(re.fullmatch(pattern, value))