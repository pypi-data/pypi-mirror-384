from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import Union


T = TypeVar(
    "T",
    bound="SimulationUpdateSchemaSourceDataType0GenerationConfigurationConversation",
)


@_attrs_define
class SimulationUpdateSchemaSourceDataType0GenerationConfigurationConversation:
    """
    Attributes:
        min_length (Union[Unset, float]):
        max_length (Union[Unset, float]):
        length_distribution (Union[Unset, str]):
    """

    min_length: Union[Unset, float] = UNSET
    max_length: Union[Unset, float] = UNSET
    length_distribution: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        min_length = self.min_length

        max_length = self.max_length

        length_distribution = self.length_distribution

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if min_length is not UNSET:
            field_dict["min_length"] = min_length
        if max_length is not UNSET:
            field_dict["max_length"] = max_length
        if length_distribution is not UNSET:
            field_dict["length_distribution"] = length_distribution

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        min_length = d.pop("min_length", UNSET)

        max_length = d.pop("max_length", UNSET)

        length_distribution = d.pop("length_distribution", UNSET)

        simulation_update_schema_source_data_type_0_generation_configuration_conversation = cls(
            min_length=min_length,
            max_length=max_length,
            length_distribution=length_distribution,
        )

        simulation_update_schema_source_data_type_0_generation_configuration_conversation.additional_properties = d
        return simulation_update_schema_source_data_type_0_generation_configuration_conversation

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
