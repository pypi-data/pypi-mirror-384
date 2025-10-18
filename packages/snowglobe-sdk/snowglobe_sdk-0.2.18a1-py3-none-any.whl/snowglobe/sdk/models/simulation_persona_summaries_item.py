from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define


T = TypeVar("T", bound="SimulationPersonaSummariesItem")


@_attrs_define
class SimulationPersonaSummariesItem:
    """
    Attributes:
        persona (str):
        summary (str):
    """

    persona: str
    summary: str

    def to_dict(self) -> dict[str, Any]:
        persona = self.persona

        summary = self.summary

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "persona": persona,
                "summary": summary,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        persona = d.pop("persona")

        summary = d.pop("summary")

        simulation_persona_summaries_item = cls(
            persona=persona,
            summary=summary,
        )

        return simulation_persona_summaries_item
