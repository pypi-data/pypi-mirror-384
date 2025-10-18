from enum import Enum


class FileTransferType(str, Enum):
    F = "F"
    L = "L"
    M = "M"
    R = "R"

    def __str__(self) -> str:
        return str(self.value)
