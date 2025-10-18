from enum import Enum


class AccessRecord(str, Enum):
    PUBLIC = "public"
    RESTRICTED = "restricted"

    def __str__(self) -> str:
        return str(self.value)
