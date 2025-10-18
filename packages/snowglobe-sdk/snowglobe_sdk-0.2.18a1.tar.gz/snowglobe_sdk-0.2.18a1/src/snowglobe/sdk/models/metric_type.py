from enum import Enum


class MetricType(str, Enum):
    CODE = "CODE"
    LLM = "LLM"
    PRECONFIGURED = "PRECONFIGURED"

    def __str__(self) -> str:
        return str(self.value)
