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
    from ..models.agent_connection_info_type_0 import AgentConnectionInfoType0
    from ..models.agent_settings_type_0 import AgentSettingsType0
    from ..models.agent_autofix_configuration_type_0 import (
        AgentAutofixConfigurationType0,
    )
    from ..models.agent_historical_data_type_0 import AgentHistoricalDataType0
    from ..models.agent_source_data_type_0 import AgentSourceDataType0


T = TypeVar("T", bound="Agent")


@_attrs_define
class Agent:
    """
    Attributes:
        id (UUID):
        name (str):
        icon (str):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
        description (Union[None, Unset, str]):
        created_by (Union[None, Unset, str]):
        settings (Union['AgentSettingsType0', None, Unset]):
        source_data (Union['AgentSourceDataType0', None, Unset]):
        historical_data (Union['AgentHistoricalDataType0', None, Unset]):
        connection_info (Union['AgentConnectionInfoType0', None, Unset]):
        autofix_configuration (Union['AgentAutofixConfigurationType0', None, Unset]):
        marked_for_deletion_at (Union[None, Unset, datetime.datetime]):
    """

    id: UUID
    name: str
    icon: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    description: Union[None, Unset, str] = UNSET
    created_by: Union[None, Unset, str] = UNSET
    settings: Union["AgentSettingsType0", None, Unset] = UNSET
    source_data: Union["AgentSourceDataType0", None, Unset] = UNSET
    historical_data: Union["AgentHistoricalDataType0", None, Unset] = UNSET
    connection_info: Union["AgentConnectionInfoType0", None, Unset] = UNSET
    autofix_configuration: Union["AgentAutofixConfigurationType0", None, Unset] = UNSET
    marked_for_deletion_at: Union[None, Unset, datetime.datetime] = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.agent_connection_info_type_0 import AgentConnectionInfoType0
        from ..models.agent_settings_type_0 import AgentSettingsType0
        from ..models.agent_autofix_configuration_type_0 import (
            AgentAutofixConfigurationType0,
        )
        from ..models.agent_historical_data_type_0 import AgentHistoricalDataType0
        from ..models.agent_source_data_type_0 import AgentSourceDataType0

        id = str(self.id)

        name = self.name

        icon = self.icon

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        description: Union[None, Unset, str]
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        created_by: Union[None, Unset, str]
        if isinstance(self.created_by, Unset):
            created_by = UNSET
        else:
            created_by = self.created_by

        settings: Union[None, Unset, dict[str, Any]]
        if isinstance(self.settings, Unset):
            settings = UNSET
        elif isinstance(self.settings, AgentSettingsType0):
            settings = self.settings.to_dict()
        else:
            settings = self.settings

        source_data: Union[None, Unset, dict[str, Any]]
        if isinstance(self.source_data, Unset):
            source_data = UNSET
        elif isinstance(self.source_data, AgentSourceDataType0):
            source_data = self.source_data.to_dict()
        else:
            source_data = self.source_data

        historical_data: Union[None, Unset, dict[str, Any]]
        if isinstance(self.historical_data, Unset):
            historical_data = UNSET
        elif isinstance(self.historical_data, AgentHistoricalDataType0):
            historical_data = self.historical_data.to_dict()
        else:
            historical_data = self.historical_data

        connection_info: Union[None, Unset, dict[str, Any]]
        if isinstance(self.connection_info, Unset):
            connection_info = UNSET
        elif isinstance(self.connection_info, AgentConnectionInfoType0):
            connection_info = self.connection_info.to_dict()
        else:
            connection_info = self.connection_info

        autofix_configuration: Union[None, Unset, dict[str, Any]]
        if isinstance(self.autofix_configuration, Unset):
            autofix_configuration = UNSET
        elif isinstance(self.autofix_configuration, AgentAutofixConfigurationType0):
            autofix_configuration = self.autofix_configuration.to_dict()
        else:
            autofix_configuration = self.autofix_configuration

        marked_for_deletion_at: Union[None, Unset, str]
        if isinstance(self.marked_for_deletion_at, Unset):
            marked_for_deletion_at = UNSET
        elif isinstance(self.marked_for_deletion_at, datetime.datetime):
            marked_for_deletion_at = self.marked_for_deletion_at.isoformat()
        else:
            marked_for_deletion_at = self.marked_for_deletion_at

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "id": id,
                "name": name,
                "icon": icon,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if created_by is not UNSET:
            field_dict["created_by"] = created_by
        if settings is not UNSET:
            field_dict["settings"] = settings
        if source_data is not UNSET:
            field_dict["source_data"] = source_data
        if historical_data is not UNSET:
            field_dict["historical_data"] = historical_data
        if connection_info is not UNSET:
            field_dict["connection_info"] = connection_info
        if autofix_configuration is not UNSET:
            field_dict["autofix_configuration"] = autofix_configuration
        if marked_for_deletion_at is not UNSET:
            field_dict["marked_for_deletion_at"] = marked_for_deletion_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_connection_info_type_0 import AgentConnectionInfoType0
        from ..models.agent_settings_type_0 import AgentSettingsType0
        from ..models.agent_autofix_configuration_type_0 import (
            AgentAutofixConfigurationType0,
        )
        from ..models.agent_historical_data_type_0 import AgentHistoricalDataType0
        from ..models.agent_source_data_type_0 import AgentSourceDataType0

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        icon = d.pop("icon")

        created_at = isoparse(d.pop("created_at"))

        updated_at = isoparse(d.pop("updated_at"))

        def _parse_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_created_by(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        created_by = _parse_created_by(d.pop("created_by", UNSET))

        def _parse_settings(data: object) -> Union["AgentSettingsType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                settings_type_0 = AgentSettingsType0.from_dict(data)

                return settings_type_0
            except:  # noqa: E722
                pass
            return cast(Union["AgentSettingsType0", None, Unset], data)

        settings = _parse_settings(d.pop("settings", UNSET))

        def _parse_source_data(
            data: object,
        ) -> Union["AgentSourceDataType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                source_data_type_0 = AgentSourceDataType0.from_dict(data)

                return source_data_type_0
            except:  # noqa: E722
                pass
            return cast(Union["AgentSourceDataType0", None, Unset], data)

        source_data = _parse_source_data(d.pop("source_data", UNSET))

        def _parse_historical_data(
            data: object,
        ) -> Union["AgentHistoricalDataType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                historical_data_type_0 = AgentHistoricalDataType0.from_dict(data)

                return historical_data_type_0
            except:  # noqa: E722
                pass
            return cast(Union["AgentHistoricalDataType0", None, Unset], data)

        historical_data = _parse_historical_data(d.pop("historical_data", UNSET))

        def _parse_connection_info(
            data: object,
        ) -> Union["AgentConnectionInfoType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                connection_info_type_0 = AgentConnectionInfoType0.from_dict(data)

                return connection_info_type_0
            except:  # noqa: E722
                pass
            return cast(Union["AgentConnectionInfoType0", None, Unset], data)

        connection_info = _parse_connection_info(d.pop("connection_info", UNSET))

        def _parse_autofix_configuration(
            data: object,
        ) -> Union["AgentAutofixConfigurationType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                autofix_configuration_type_0 = AgentAutofixConfigurationType0.from_dict(
                    data
                )

                return autofix_configuration_type_0
            except:  # noqa: E722
                pass
            return cast(Union["AgentAutofixConfigurationType0", None, Unset], data)

        autofix_configuration = _parse_autofix_configuration(
            d.pop("autofix_configuration", UNSET)
        )

        def _parse_marked_for_deletion_at(
            data: object,
        ) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                marked_for_deletion_at_type_0 = isoparse(data)

                return marked_for_deletion_at_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        marked_for_deletion_at = _parse_marked_for_deletion_at(
            d.pop("marked_for_deletion_at", UNSET)
        )

        agent = cls(
            id=id,
            name=name,
            icon=icon,
            created_at=created_at,
            updated_at=updated_at,
            description=description,
            created_by=created_by,
            settings=settings,
            source_data=source_data,
            historical_data=historical_data,
            connection_info=connection_info,
            autofix_configuration=autofix_configuration,
            marked_for_deletion_at=marked_for_deletion_at,
        )

        return agent
