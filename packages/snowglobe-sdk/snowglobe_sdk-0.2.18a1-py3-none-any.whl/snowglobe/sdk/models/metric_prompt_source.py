from enum import Enum


class MetricPromptSource(str, Enum):
    PROMPT = "PROMPT"
    PROMPT_TEMPLATE = "PROMPT_TEMPLATE"

    def __str__(self) -> str:
        return str(self.value)
