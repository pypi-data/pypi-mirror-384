from enum import Enum


class DateTypeId(str, Enum):
    ACCEPTED = "accepted"
    AVAILABLE = "available"
    COLLECTED = "collected"
    COPYRIGHTED = "copyrighted"
    CREATED = "created"
    ISSUED = "issued"
    OTHER = "other"
    SUBMITTED = "submitted"
    UPDATED = "updated"
    VALID = "valid"
    WITHDRAWN = "withdrawn"

    def __str__(self) -> str:
        return str(self.value)
