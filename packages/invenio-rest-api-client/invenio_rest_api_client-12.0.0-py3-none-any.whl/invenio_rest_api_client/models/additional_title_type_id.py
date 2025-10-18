from enum import Enum


class AdditionalTitleTypeId(str, Enum):
    ALTERNATIVE_TITLE = "alternative-title"
    OTHER = "other"
    SUBTITLE = "subtitle"
    TRANSLATED_TITLE = "translated-title"

    def __str__(self) -> str:
        return str(self.value)
