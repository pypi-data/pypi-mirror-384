from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast
from typing import Union
from typing import Literal
from uuid import UUID

if TYPE_CHECKING:
    from ..models.experiment_update_schema_risks_item_metadata_type_0 import (
        ExperimentUpdateSchemaRisksItemMetadataType0,
    )


T = TypeVar("T", bound="ExperimentUpdateSchemaRisksItem")


@_attrs_define
class ExperimentUpdateSchemaRisksItem:
    """
    Attributes:
        id (UUID):
        name (str):
        type_ (Union[Literal['CODE'], Literal['LLM'], Literal['PRECONFIGURED']]):
        version (int):
        metadata (Union['ExperimentUpdateSchemaRisksItemMetadataType0', None, Unset]):
    """

    id: UUID
    name: str
    type_: Union[Literal["CODE"], Literal["LLM"], Literal["PRECONFIGURED"]]
    version: int
    metadata: Union["ExperimentUpdateSchemaRisksItemMetadataType0", None, Unset] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.experiment_update_schema_risks_item_metadata_type_0 import (
            ExperimentUpdateSchemaRisksItemMetadataType0,
        )

        id = str(self.id)

        name = self.name

        type_: Union[Literal["CODE"], Literal["LLM"], Literal["PRECONFIGURED"]]
        type_ = self.type_

        version = self.version

        metadata: Union[None, Unset, dict[str, Any]]
        if isinstance(self.metadata, Unset):
            metadata = UNSET
        elif isinstance(self.metadata, ExperimentUpdateSchemaRisksItemMetadataType0):
            metadata = self.metadata.to_dict()
        else:
            metadata = self.metadata

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "type": type_,
                "version": version,
            }
        )
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.experiment_update_schema_risks_item_metadata_type_0 import (
            ExperimentUpdateSchemaRisksItemMetadataType0,
        )

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        def _parse_type_(
            data: object,
        ) -> Union[Literal["CODE"], Literal["LLM"], Literal["PRECONFIGURED"]]:
            type_type_0 = cast(Literal["LLM"], data)
            if type_type_0 != "LLM":
                raise ValueError(
                    f"type_type_0 must match const 'LLM', got '{type_type_0}'"
                )
            return type_type_0
            type_type_1 = cast(Literal["CODE"], data)
            if type_type_1 != "CODE":
                raise ValueError(
                    f"type_type_1 must match const 'CODE', got '{type_type_1}'"
                )
            return type_type_1
            type_type_2 = cast(Literal["PRECONFIGURED"], data)
            if type_type_2 != "PRECONFIGURED":
                raise ValueError(
                    f"type_type_2 must match const 'PRECONFIGURED', got '{type_type_2}'"
                )
            return type_type_2

        type_ = _parse_type_(d.pop("type"))

        version = d.pop("version")

        def _parse_metadata(
            data: object,
        ) -> Union["ExperimentUpdateSchemaRisksItemMetadataType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_type_0 = (
                    ExperimentUpdateSchemaRisksItemMetadataType0.from_dict(data)
                )

                return metadata_type_0
            except:  # noqa: E722
                pass
            return cast(
                Union["ExperimentUpdateSchemaRisksItemMetadataType0", None, Unset], data
            )

        metadata = _parse_metadata(d.pop("metadata", UNSET))

        experiment_update_schema_risks_item = cls(
            id=id,
            name=name,
            type_=type_,
            version=version,
            metadata=metadata,
        )

        experiment_update_schema_risks_item.additional_properties = d
        return experiment_update_schema_risks_item

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
