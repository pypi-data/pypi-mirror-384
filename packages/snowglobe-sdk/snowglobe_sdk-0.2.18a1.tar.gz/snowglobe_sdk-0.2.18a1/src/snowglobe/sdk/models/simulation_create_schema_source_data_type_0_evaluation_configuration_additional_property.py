from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import Union

if TYPE_CHECKING:
    from ..models.simulation_create_schema_source_data_type_0_evaluation_configuration_additional_property_metadata import (
        SimulationCreateSchemaSourceDataType0EvaluationConfigurationAdditionalPropertyMetadata,
    )


T = TypeVar(
    "T",
    bound="SimulationCreateSchemaSourceDataType0EvaluationConfigurationAdditionalProperty",
)


@_attrs_define
class SimulationCreateSchemaSourceDataType0EvaluationConfigurationAdditionalProperty:
    """
    Attributes:
        id (str):
        name (str):
        version (int):
        metadata (Union[Unset, SimulationCreateSchemaSourceDataType0EvaluationConfigurationAdditionalPropertyMetadata]):
    """

    id: str
    name: str
    version: int
    metadata: Union[
        Unset,
        "SimulationCreateSchemaSourceDataType0EvaluationConfigurationAdditionalPropertyMetadata",
    ] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        version = self.version

        metadata: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "version": version,
            }
        )
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.simulation_create_schema_source_data_type_0_evaluation_configuration_additional_property_metadata import (
            SimulationCreateSchemaSourceDataType0EvaluationConfigurationAdditionalPropertyMetadata,
        )

        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        version = d.pop("version")

        _metadata = d.pop("metadata", UNSET)
        metadata: Union[
            Unset,
            SimulationCreateSchemaSourceDataType0EvaluationConfigurationAdditionalPropertyMetadata,
        ]
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = SimulationCreateSchemaSourceDataType0EvaluationConfigurationAdditionalPropertyMetadata.from_dict(
                _metadata
            )

        simulation_create_schema_source_data_type_0_evaluation_configuration_additional_property = cls(
            id=id,
            name=name,
            version=version,
            metadata=metadata,
        )

        simulation_create_schema_source_data_type_0_evaluation_configuration_additional_property.additional_properties = d
        return simulation_create_schema_source_data_type_0_evaluation_configuration_additional_property

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
