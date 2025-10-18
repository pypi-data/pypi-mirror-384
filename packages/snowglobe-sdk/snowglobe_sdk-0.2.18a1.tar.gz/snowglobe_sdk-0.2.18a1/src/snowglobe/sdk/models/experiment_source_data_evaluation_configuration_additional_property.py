from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define

from ..types import UNSET, Unset

from typing import cast
from typing import Union

if TYPE_CHECKING:
    from ..models.experiment_source_data_evaluation_configuration_additional_property_metadata_type_0 import (
        ExperimentSourceDataEvaluationConfigurationAdditionalPropertyMetadataType0,
    )


T = TypeVar("T", bound="ExperimentSourceDataEvaluationConfigurationAdditionalProperty")


@_attrs_define
class ExperimentSourceDataEvaluationConfigurationAdditionalProperty:
    """
    Attributes:
        id (str):
        name (str):
        version (float):
        metadata (Union['ExperimentSourceDataEvaluationConfigurationAdditionalPropertyMetadataType0', None, Unset]):
    """

    id: str
    name: str
    version: float
    metadata: Union[
        "ExperimentSourceDataEvaluationConfigurationAdditionalPropertyMetadataType0",
        None,
        Unset,
    ] = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.experiment_source_data_evaluation_configuration_additional_property_metadata_type_0 import (
            ExperimentSourceDataEvaluationConfigurationAdditionalPropertyMetadataType0,
        )

        id = self.id

        name = self.name

        version = self.version

        metadata: Union[None, Unset, dict[str, Any]]
        if isinstance(self.metadata, Unset):
            metadata = UNSET
        elif isinstance(
            self.metadata,
            ExperimentSourceDataEvaluationConfigurationAdditionalPropertyMetadataType0,
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
        from ..models.experiment_source_data_evaluation_configuration_additional_property_metadata_type_0 import (
            ExperimentSourceDataEvaluationConfigurationAdditionalPropertyMetadataType0,
        )

        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        version = d.pop("version")

        def _parse_metadata(
            data: object,
        ) -> Union[
            "ExperimentSourceDataEvaluationConfigurationAdditionalPropertyMetadataType0",
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
                metadata_type_0 = ExperimentSourceDataEvaluationConfigurationAdditionalPropertyMetadataType0.from_dict(
                    data
                )

                return metadata_type_0
            except:  # noqa: E722
                pass
            return cast(
                Union[
                    "ExperimentSourceDataEvaluationConfigurationAdditionalPropertyMetadataType0",
                    None,
                    Unset,
                ],
                data,
            )

        metadata = _parse_metadata(d.pop("metadata", UNSET))

        experiment_source_data_evaluation_configuration_additional_property = cls(
            id=id,
            name=name,
            version=version,
            metadata=metadata,
        )

        return experiment_source_data_evaluation_configuration_additional_property
