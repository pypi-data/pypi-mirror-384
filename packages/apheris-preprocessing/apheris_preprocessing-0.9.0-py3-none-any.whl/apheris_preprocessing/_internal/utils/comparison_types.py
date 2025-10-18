from enum import Enum


class ComparisonType(Enum):
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_THAN_OR_EQUAL_TO = ">="
    LESS_THAN_OR_EQUAL_TO = "<="
    EQUAL_TO = "=="
    NOT_EQUAL_TO = "!="

    @staticmethod
    def get_supported_types():
        return [_type.value for _type in ComparisonType]
