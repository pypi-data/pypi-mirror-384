from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

from dateutil.parser import isoparse
from typing import cast
from typing import Union
from uuid import UUID
import datetime


T = TypeVar("T", bound="ExperimentSettingsUpdateSchema")


@_attrs_define
class ExperimentSettingsUpdateSchema:
    """
    Attributes:
        id (Union[Unset, UUID]):
        experiment_id (Union[Unset, UUID]):
        auto_approve_personas (Union[None, Unset, bool]):
        updated_at (Union[Unset, datetime.datetime]):
        updated_by (Union[Unset, str]):
    """

    id: Union[Unset, UUID] = UNSET
    experiment_id: Union[Unset, UUID] = UNSET
    auto_approve_personas: Union[None, Unset, bool] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    updated_by: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        id: Union[Unset, str] = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        experiment_id: Union[Unset, str] = UNSET
        if not isinstance(self.experiment_id, Unset):
            experiment_id = str(self.experiment_id)

        auto_approve_personas: Union[None, Unset, bool]
        if isinstance(self.auto_approve_personas, Unset):
            auto_approve_personas = UNSET
        else:
            auto_approve_personas = self.auto_approve_personas

        updated_at: Union[Unset, str] = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        updated_by = self.updated_by

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if experiment_id is not UNSET:
            field_dict["experimentId"] = experiment_id
        if auto_approve_personas is not UNSET:
            field_dict["autoApprovePersonas"] = auto_approve_personas
        if updated_at is not UNSET:
            field_dict["updatedAt"] = updated_at
        if updated_by is not UNSET:
            field_dict["updatedBy"] = updated_by

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _id = d.pop("id", UNSET)
        id: Union[Unset, UUID]
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        _experiment_id = d.pop("experimentId", UNSET)
        experiment_id: Union[Unset, UUID]
        if isinstance(_experiment_id, Unset):
            experiment_id = UNSET
        else:
            experiment_id = UUID(_experiment_id)

        def _parse_auto_approve_personas(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        auto_approve_personas = _parse_auto_approve_personas(
            d.pop("autoApprovePersonas", UNSET)
        )

        _updated_at = d.pop("updatedAt", UNSET)
        updated_at: Union[Unset, datetime.datetime]
        if isinstance(_updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = isoparse(_updated_at)

        updated_by = d.pop("updatedBy", UNSET)

        experiment_settings_update_schema = cls(
            id=id,
            experiment_id=experiment_id,
            auto_approve_personas=auto_approve_personas,
            updated_at=updated_at,
            updated_by=updated_by,
        )

        return experiment_settings_update_schema
