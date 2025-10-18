from enum import Enum


class IdentifierScheme(str, Enum):
    ADS = "ads"
    ARK = "ark"
    ARXIV = "arxiv"
    CROSSREFFUNDERID = "crossreffunderid"
    DOI = "doi"
    EAN13 = "ean13"
    EISSN = "eissn"
    GRID = "grid"
    HANDLE = "handle"
    IGSN = "igsn"
    ISBN = "isbn"
    ISNI = "isni"
    ISSN = "issn"
    ISTC = "istc"
    LISSN = "lissn"
    LSID = "lsid"
    OTHER = "other"
    PMID = "pmid"
    PURL = "purl"
    UPC = "upc"
    URL = "url"
    URN = "urn"
    W3ID = "w3id"

    def __str__(self) -> str:
        return str(self.value)
