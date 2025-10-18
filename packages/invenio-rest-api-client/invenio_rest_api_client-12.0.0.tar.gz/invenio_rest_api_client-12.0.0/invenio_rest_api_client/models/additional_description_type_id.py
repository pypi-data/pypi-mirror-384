from enum import Enum


class AdditionalDescriptionTypeId(str, Enum):
    ABSTRACT = "abstract"
    METHODS = "methods"
    OTHER = "other"
    SERIES_INFORMATION = "series-information"
    TABLE_OF_CONTENTS = "table-of-contents"
    TECHNICAL_INFO = "technical-info"

    def __str__(self) -> str:
        return str(self.value)
