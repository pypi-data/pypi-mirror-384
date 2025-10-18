from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define

from ..types import UNSET, Unset

from ..models.simulation_risks_item_type import SimulationRisksItemType
from typing import cast
from typing import Union
from uuid import UUID

if TYPE_CHECKING:
    from ..models.simulation_risks_item_metadata_type_0 import (
        SimulationRisksItemMetadataType0,
    )


T = TypeVar("T", bound="SimulationRisksItem")


@_attrs_define
class SimulationRisksItem:
    """
    Attributes:
        id (UUID):
        name (str):
        type_ (SimulationRisksItemType):
        version (int):
        metadata (Union['SimulationRisksItemMetadataType0', None, Unset]):
    """

    id: UUID
    name: str
    type_: SimulationRisksItemType
    version: int
    metadata: Union["SimulationRisksItemMetadataType0", None, Unset] = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.simulation_risks_item_metadata_type_0 import (
            SimulationRisksItemMetadataType0,
        )

        id = str(self.id)

        name = self.name

        type_ = self.type_.value

        version = self.version

        metadata: Union[None, Unset, dict[str, Any]]
        if isinstance(self.metadata, Unset):
            metadata = UNSET
        elif isinstance(self.metadata, SimulationRisksItemMetadataType0):
            metadata = self.metadata.to_dict()
        else:
            metadata = self.metadata

        field_dict: dict[str, Any] = {}

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
        from ..models.simulation_risks_item_metadata_type_0 import (
            SimulationRisksItemMetadataType0,
        )

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        type_ = SimulationRisksItemType(d.pop("type"))

        version = d.pop("version")

        def _parse_metadata(
            data: object,
        ) -> Union["SimulationRisksItemMetadataType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_type_0 = SimulationRisksItemMetadataType0.from_dict(data)

                return metadata_type_0
            except:  # noqa: E722
                pass
            return cast(Union["SimulationRisksItemMetadataType0", None, Unset], data)

        metadata = _parse_metadata(d.pop("metadata", UNSET))

        simulation_risks_item = cls(
            id=id,
            name=name,
            type_=type_,
            version=version,
            metadata=metadata,
        )

        return simulation_risks_item
