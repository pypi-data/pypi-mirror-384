from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import Union


T = TypeVar("T", bound="ExperimentCreateSchemaSourceDataType0PersonaTopicsItem")


@_attrs_define
class ExperimentCreateSchemaSourceDataType0PersonaTopicsItem:
    """
    Attributes:
        persona (str):
        topic (str):
        generation_source (Union[Unset, str]):
        risk_type (Union[Unset, str]):
    """

    persona: str
    topic: str
    generation_source: Union[Unset, str] = UNSET
    risk_type: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        persona = self.persona

        topic = self.topic

        generation_source = self.generation_source

        risk_type = self.risk_type

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "persona": persona,
                "topic": topic,
            }
        )
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

        generation_source = d.pop("generation_source", UNSET)

        risk_type = d.pop("risk_type", UNSET)

        experiment_create_schema_source_data_type_0_persona_topics_item = cls(
            persona=persona,
            topic=topic,
            generation_source=generation_source,
            risk_type=risk_type,
        )

        experiment_create_schema_source_data_type_0_persona_topics_item.additional_properties = d
        return experiment_create_schema_source_data_type_0_persona_topics_item

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
