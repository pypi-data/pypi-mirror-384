from enum import Enum


class PersonOrOrgType(str, Enum):
    ORGANIZATIONAL = "organizational"
    PERSONAL = "personal"

    def __str__(self) -> str:
        return str(self.value)
