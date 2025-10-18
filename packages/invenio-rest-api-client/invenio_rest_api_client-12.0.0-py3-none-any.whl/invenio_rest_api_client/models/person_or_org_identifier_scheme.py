from enum import Enum


class PersonOrOrgIdentifierScheme(str, Enum):
    GND = "gnd"
    ISNI = "isni"
    ORCID = "orcid"
    ROR = "ror"

    def __str__(self) -> str:
        return str(self.value)
