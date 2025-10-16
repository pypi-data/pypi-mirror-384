from enum import Enum


class Targets(Enum):
    """Enum class for the available targets of the measurements."""

    GHI = "ghi"
    GTI = "gti"
    PROD = "prod"
    DNI = "dni"
    DHI = "dhi"

    def __get__(self, instance, owner):
        return self.value
