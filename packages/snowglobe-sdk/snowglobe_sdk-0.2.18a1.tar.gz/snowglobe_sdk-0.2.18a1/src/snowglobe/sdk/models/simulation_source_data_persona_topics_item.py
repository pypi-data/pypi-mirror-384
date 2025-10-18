from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

from typing import Union
from uuid import UUID


T = TypeVar("T", bound="SimulationSourceDataPersonaTopicsItem")


@_attrs_define
class SimulationSourceDataPersonaTopicsItem:
    """
    Attributes:
        persona (str):
        topic (str):
        id (Union[Unset, UUID]):
        generation_source (Union[Unset, str]):
        risk_type (Union[Unset, str]):
    """

    persona: str
    topic: str
    id: Union[Unset, UUID] = UNSET
    generation_source: Union[Unset, str] = UNSET
    risk_type: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        persona = self.persona

        topic = self.topic

        id: Union[Unset, str] = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        generation_source = self.generation_source

        risk_type = self.risk_type

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "persona": persona,
                "topic": topic,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if generation_source is not UNSET:
            field_dict["generation_source"] = generation_source
        if risk_type is not UNSET:
            field_dict["risk_type"] = risk_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        persona = d.pop("persona")

        topic = d.pop("topic")

        _id = d.pop("id", UNSET)
        id: Union[Unset, UUID]
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        generation_source = d.pop("generation_source", UNSET)

        risk_type = d.pop("risk_type", UNSET)

        simulation_source_data_persona_topics_item = cls(
            persona=persona,
            topic=topic,
            id=id,
            generation_source=generation_source,
            risk_type=risk_type,
        )

        return simulation_source_data_persona_topics_item
