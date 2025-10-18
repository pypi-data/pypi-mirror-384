from enum import Enum


class RiskPromptSource(str, Enum):
    PROMPT = "PROMPT"
    PROMPT_TEMPLATE = "PROMPT_TEMPLATE"

    def __str__(self) -> str:
        return str(self.value)
