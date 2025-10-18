from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

from typing import Union


T = TypeVar("T", bound="SimulationSourceDataGenerationConfigurationMessage")


@_attrs_define
class SimulationSourceDataGenerationConfigurationMessage:
    """
    Attributes:
        min_length (Union[Unset, float]):
        max_length (Union[Unset, float]):
        length_distribution (Union[Unset, str]):
    """

    min_length: Union[Unset, float] = UNSET
    max_length: Union[Unset, float] = UNSET
    length_distribution: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        min_length = self.min_length

        max_length = self.max_length

        length_distribution = self.length_distribution

        field_dict: dict[str, Any] = {}

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

        simulation_source_data_generation_configuration_message = cls(
            min_length=min_length,
            max_length=max_length,
            length_distribution=length_distribution,
        )

        return simulation_source_data_generation_configuration_message
