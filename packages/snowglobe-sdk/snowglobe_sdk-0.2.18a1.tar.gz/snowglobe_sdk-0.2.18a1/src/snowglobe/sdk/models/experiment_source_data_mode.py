from enum import Enum


class ExperimentSourceDataMode(str, Enum):
    RED_MODE = "RED_MODE"
    STANDARD = "STANDARD"

    def __str__(self) -> str:
        return str(self.value)
