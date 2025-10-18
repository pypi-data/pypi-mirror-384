from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define
from attrs import field as _attrs_field


if TYPE_CHECKING:
    from ..models.simulation_source_data_evaluation_configuration_additional_property import (
        SimulationSourceDataEvaluationConfigurationAdditionalProperty,
    )


T = TypeVar("T", bound="SimulationSourceDataEvaluationConfiguration")


@_attrs_define
class SimulationSourceDataEvaluationConfiguration:
    """ """

    additional_properties: dict[
        str, "SimulationSourceDataEvaluationConfigurationAdditionalProperty"
    ] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        field_dict: dict[str, Any] = {}
        for prop_name, prop in self.additional_properties.items():
            field_dict[prop_name] = prop.to_dict()

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.simulation_source_data_evaluation_configuration_additional_property import (
            SimulationSourceDataEvaluationConfigurationAdditionalProperty,
        )

        d = dict(src_dict)
        simulation_source_data_evaluation_configuration = cls()

        additional_properties = {}
        for prop_name, prop_dict in d.items():
            additional_property = (
                SimulationSourceDataEvaluationConfigurationAdditionalProperty.from_dict(
                    prop_dict
                )
            )

            additional_properties[prop_name] = additional_property

        simulation_source_data_evaluation_configuration.additional_properties = (
            additional_properties
        )
        return simulation_source_data_evaluation_configuration

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(
        self, key: str
    ) -> "SimulationSourceDataEvaluationConfigurationAdditionalProperty":
        return self.additional_properties[key]

    def __setitem__(
        self,
        key: str,
        value: "SimulationSourceDataEvaluationConfigurationAdditionalProperty",
    ) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
