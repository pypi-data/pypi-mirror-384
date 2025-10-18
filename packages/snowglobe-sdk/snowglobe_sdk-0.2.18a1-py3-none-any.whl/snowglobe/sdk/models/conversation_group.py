from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define

from ..types import UNSET, Unset

from dateutil.parser import isoparse
from typing import cast
from typing import Union
from uuid import UUID
import datetime

if TYPE_CHECKING:
    from ..models.conversation_group_findings_type_0 import (
        ConversationGroupFindingsType0,
    )


T = TypeVar("T", bound="ConversationGroup")


@_attrs_define
class ConversationGroup:
    """
    Attributes:
        id (UUID):
        experiment_id (Union[None, UUID]):
        name (str):
        persona_record_id (Union[None, UUID]):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
        description (Union[None, Unset, str]):
        findings (Union['ConversationGroupFindingsType0', None, Unset]):
    """

    id: UUID
    experiment_id: Union[None, UUID]
    name: str
    persona_record_id: Union[None, UUID]
    created_at: datetime.datetime
    updated_at: datetime.datetime
    description: Union[None, Unset, str] = UNSET
    findings: Union["ConversationGroupFindingsType0", None, Unset] = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.conversation_group_findings_type_0 import (
            ConversationGroupFindingsType0,
        )

        id = str(self.id)

        experiment_id: Union[None, str]
        if isinstance(self.experiment_id, UUID):
            experiment_id = str(self.experiment_id)
        else:
            experiment_id = self.experiment_id

        name = self.name

        persona_record_id: Union[None, str]
        if isinstance(self.persona_record_id, UUID):
            persona_record_id = str(self.persona_record_id)
        else:
            persona_record_id = self.persona_record_id

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        description: Union[None, Unset, str]
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        findings: Union[None, Unset, dict[str, Any]]
        if isinstance(self.findings, Unset):
            findings = UNSET
        elif isinstance(self.findings, ConversationGroupFindingsType0):
            findings = self.findings.to_dict()
        else:
            findings = self.findings

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "id": id,
                "experiment_id": experiment_id,
                "name": name,
                "persona_record_id": persona_record_id,
                "createdAt": created_at,
                "updatedAt": updated_at,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if findings is not UNSET:
            field_dict["findings"] = findings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.conversation_group_findings_type_0 import (
            ConversationGroupFindingsType0,
        )

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        def _parse_experiment_id(data: object) -> Union[None, UUID]:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                experiment_id_type_0 = UUID(data)

                return experiment_id_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, UUID], data)

        experiment_id = _parse_experiment_id(d.pop("experiment_id"))

        name = d.pop("name")

        def _parse_persona_record_id(data: object) -> Union[None, UUID]:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                persona_record_id_type_0 = UUID(data)

                return persona_record_id_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, UUID], data)

        persona_record_id = _parse_persona_record_id(d.pop("persona_record_id"))

        created_at = isoparse(d.pop("createdAt"))

        updated_at = isoparse(d.pop("updatedAt"))

        def _parse_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_findings(
            data: object,
        ) -> Union["ConversationGroupFindingsType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                findings_type_0 = ConversationGroupFindingsType0.from_dict(data)

                return findings_type_0
            except:  # noqa: E722
                pass
            return cast(Union["ConversationGroupFindingsType0", None, Unset], data)

        findings = _parse_findings(d.pop("findings", UNSET))

        conversation_group = cls(
            id=id,
            experiment_id=experiment_id,
            name=name,
            persona_record_id=persona_record_id,
            created_at=created_at,
            updated_at=updated_at,
            description=description,
            findings=findings,
        )

        return conversation_group
