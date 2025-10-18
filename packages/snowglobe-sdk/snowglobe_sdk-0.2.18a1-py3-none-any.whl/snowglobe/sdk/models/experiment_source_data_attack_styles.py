from enum import Enum


class ExperimentSourceDataAttackStyles(str, Enum):
    DAN = "DAN"
    OWASP_TOP_10 = "OWASP_TOP_10"

    def __str__(self) -> str:
        return str(self.value)
