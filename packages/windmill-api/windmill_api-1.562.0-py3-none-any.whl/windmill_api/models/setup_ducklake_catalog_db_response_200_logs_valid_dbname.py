from enum import Enum


class SetupDucklakeCatalogDbResponse200LogsValidDbname(str, Enum):
    FAIL = "FAIL"
    OK = "OK"
    SKIP = "SKIP"

    def __str__(self) -> str:
        return str(self.value)
