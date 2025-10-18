from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define

from ..types import UNSET, Unset

from typing import cast
from typing import Union

if TYPE_CHECKING:
    from ..models.simulation_source_data_evaluation_configuration_additional_property_metadata_type_0 import (
        SimulationSourceDataEvaluationConfigurationAdditionalPropertyMetadataType0,
    )


T = TypeVar("T", bound="SimulationSourceDataEvaluationConfigurationAdditionalProperty")


@_attrs_define
class SimulationSourceDataEvaluationConfigurationAdditionalProperty:
    """
    Attributes:
        id (str):
        name (str):
        version (float):
        metadata (Union['SimulationSourceDataEvaluationConfigurationAdditionalPropertyMetadataType0', None, Unset]):
    """

    id: str
    name: str
    version: float
    metadata: Union[
        "SimulationSourceDataEvaluationConfigurationAdditionalPropertyMetadataType0",
        None,
        Unset,
    ] = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.simulation_source_data_evaluation_configuration_additional_property_metadata_type_0 import (
            SimulationSourceDataEvaluationConfigurationAdditionalPropertyMetadataType0,
        )

        id = self.id

        name = self.name

        version = self.version

        metadata: Union[None, Unset, dict[str, Any]]
        if isinstance(self.metadata, Unset):
            metadata = UNSET
        elif isinstance(
            self.metadata,
            SimulationSourceDataEvaluationConfigurationAdditionalPropertyMetadataType0,
        ):
            metadata = self.metadata.to_dict()
        else:
            metadata = self.metadata

        field_dict: dict[str, Any] = {}

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
        from ..models.simulation_source_data_evaluation_configuration_additional_property_metadata_type_0 import (
            SimulationSourceDataEvaluationConfigurationAdditionalPropertyMetadataType0,
        )

        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        version = d.pop("version")

        def _parse_metadata(
            data: object,
        ) -> Union[
            "SimulationSourceDataEvaluationConfigurationAdditionalPropertyMetadataType0",
            None,
            Unset,
        ]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_type_0 = SimulationSourceDataEvaluationConfigurationAdditionalPropertyMetadataType0.from_dict(
                    data
                )

                return metadata_type_0
            except:  # noqa: E722
                pass
            return cast(
                Union[
                    "SimulationSourceDataEvaluationConfigurationAdditionalPropertyMetadataType0",
                    None,
                    Unset,
                ],
                data,
            )

        metadata = _parse_metadata(d.pop("metadata", UNSET))

        simulation_source_data_evaluation_configuration_additional_property = cls(
            id=id,
            name=name,
            version=version,
            metadata=metadata,
        )

        return simulation_source_data_evaluation_configuration_additional_property
