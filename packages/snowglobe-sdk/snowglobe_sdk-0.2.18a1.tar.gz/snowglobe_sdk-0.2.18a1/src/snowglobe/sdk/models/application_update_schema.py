from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from dateutil.parser import isoparse
from typing import cast
from typing import Union
from uuid import UUID
import datetime

if TYPE_CHECKING:
    from ..models.application_update_schema_historical_data_type_0 import (
        ApplicationUpdateSchemaHistoricalDataType0,
    )
    from ..models.application_update_schema_settings_type_0 import (
        ApplicationUpdateSchemaSettingsType0,
    )
    from ..models.application_update_schema_connection_info_type_0 import (
        ApplicationUpdateSchemaConnectionInfoType0,
    )
    from ..models.application_update_schema_source_data_type_0 import (
        ApplicationUpdateSchemaSourceDataType0,
    )
    from ..models.application_update_schema_autofix_configuration_type_0 import (
        ApplicationUpdateSchemaAutofixConfigurationType0,
    )


T = TypeVar("T", bound="ApplicationUpdateSchema")


@_attrs_define
class ApplicationUpdateSchema:
    """
    Attributes:
        id (Union[Unset, UUID]):
        name (Union[Unset, str]):
        icon (Union[Unset, str]):
        description (Union[None, Unset, str]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
        created_by (Union[None, Unset, str]):
        settings (Union['ApplicationUpdateSchemaSettingsType0', None, Unset]):
        source_data (Union['ApplicationUpdateSchemaSourceDataType0', None, Unset]):
        historical_data (Union['ApplicationUpdateSchemaHistoricalDataType0', None, Unset]):
        connection_info (Union['ApplicationUpdateSchemaConnectionInfoType0', None, Unset]):
        autofix_configuration (Union['ApplicationUpdateSchemaAutofixConfigurationType0', None, Unset]):
        marked_for_deletion_at (Union[None, Unset, datetime.datetime]):
    """

    id: Union[Unset, UUID] = UNSET
    name: Union[Unset, str] = UNSET
    icon: Union[Unset, str] = UNSET
    description: Union[None, Unset, str] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    created_by: Union[None, Unset, str] = UNSET
    settings: Union["ApplicationUpdateSchemaSettingsType0", None, Unset] = UNSET
    source_data: Union["ApplicationUpdateSchemaSourceDataType0", None, Unset] = UNSET
    historical_data: Union[
        "ApplicationUpdateSchemaHistoricalDataType0", None, Unset
    ] = UNSET
    connection_info: Union[
        "ApplicationUpdateSchemaConnectionInfoType0", None, Unset
    ] = UNSET
    autofix_configuration: Union[
        "ApplicationUpdateSchemaAutofixConfigurationType0", None, Unset
    ] = UNSET
    marked_for_deletion_at: Union[None, Unset, datetime.datetime] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.application_update_schema_historical_data_type_0 import (
            ApplicationUpdateSchemaHistoricalDataType0,
        )
        from ..models.application_update_schema_settings_type_0 import (
            ApplicationUpdateSchemaSettingsType0,
        )
        from ..models.application_update_schema_connection_info_type_0 import (
            ApplicationUpdateSchemaConnectionInfoType0,
        )
        from ..models.application_update_schema_source_data_type_0 import (
            ApplicationUpdateSchemaSourceDataType0,
        )
        from ..models.application_update_schema_autofix_configuration_type_0 import (
            ApplicationUpdateSchemaAutofixConfigurationType0,
        )

        id: Union[Unset, str] = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        name = self.name

        icon = self.icon

        description: Union[None, Unset, str]
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        created_at: Union[Unset, str] = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Union[Unset, str] = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        created_by: Union[None, Unset, str]
        if isinstance(self.created_by, Unset):
            created_by = UNSET
        else:
            created_by = self.created_by

        settings: Union[None, Unset, dict[str, Any]]
        if isinstance(self.settings, Unset):
            settings = UNSET
        elif isinstance(self.settings, ApplicationUpdateSchemaSettingsType0):
            settings = self.settings.to_dict()
        else:
            settings = self.settings

        source_data: Union[None, Unset, dict[str, Any]]
        if isinstance(self.source_data, Unset):
            source_data = UNSET
        elif isinstance(self.source_data, ApplicationUpdateSchemaSourceDataType0):
            source_data = self.source_data.to_dict()
        else:
            source_data = self.source_data

        historical_data: Union[None, Unset, dict[str, Any]]
        if isinstance(self.historical_data, Unset):
            historical_data = UNSET
        elif isinstance(
            self.historical_data, ApplicationUpdateSchemaHistoricalDataType0
        ):
            historical_data = self.historical_data.to_dict()
        else:
            historical_data = self.historical_data

        connection_info: Union[None, Unset, dict[str, Any]]
        if isinstance(self.connection_info, Unset):
            connection_info = UNSET
        elif isinstance(
            self.connection_info, ApplicationUpdateSchemaConnectionInfoType0
        ):
            connection_info = self.connection_info.to_dict()
        else:
            connection_info = self.connection_info

        autofix_configuration: Union[None, Unset, dict[str, Any]]
        if isinstance(self.autofix_configuration, Unset):
            autofix_configuration = UNSET
        elif isinstance(
            self.autofix_configuration, ApplicationUpdateSchemaAutofixConfigurationType0
        ):
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
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if name is not UNSET:
            field_dict["name"] = name
        if icon is not UNSET:
            field_dict["icon"] = icon
        if description is not UNSET:
            field_dict["description"] = description
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
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
        from ..models.application_update_schema_historical_data_type_0 import (
            ApplicationUpdateSchemaHistoricalDataType0,
        )
        from ..models.application_update_schema_settings_type_0 import (
            ApplicationUpdateSchemaSettingsType0,
        )
        from ..models.application_update_schema_connection_info_type_0 import (
            ApplicationUpdateSchemaConnectionInfoType0,
        )
        from ..models.application_update_schema_source_data_type_0 import (
            ApplicationUpdateSchemaSourceDataType0,
        )
        from ..models.application_update_schema_autofix_configuration_type_0 import (
            ApplicationUpdateSchemaAutofixConfigurationType0,
        )

        d = dict(src_dict)
        _id = d.pop("id", UNSET)
        id: Union[Unset, UUID]
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        name = d.pop("name", UNSET)

        icon = d.pop("icon", UNSET)

        def _parse_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        description = _parse_description(d.pop("description", UNSET))

        _created_at = d.pop("created_at", UNSET)
        created_at: Union[Unset, datetime.datetime]
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        _updated_at = d.pop("updated_at", UNSET)
        updated_at: Union[Unset, datetime.datetime]
        if isinstance(_updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = isoparse(_updated_at)

        def _parse_created_by(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        created_by = _parse_created_by(d.pop("created_by", UNSET))

        def _parse_settings(
            data: object,
        ) -> Union["ApplicationUpdateSchemaSettingsType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                settings_type_0 = ApplicationUpdateSchemaSettingsType0.from_dict(data)

                return settings_type_0
            except:  # noqa: E722
                pass
            return cast(
                Union["ApplicationUpdateSchemaSettingsType0", None, Unset], data
            )

        settings = _parse_settings(d.pop("settings", UNSET))

        def _parse_source_data(
            data: object,
        ) -> Union["ApplicationUpdateSchemaSourceDataType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                source_data_type_0 = ApplicationUpdateSchemaSourceDataType0.from_dict(
                    data
                )

                return source_data_type_0
            except:  # noqa: E722
                pass
            return cast(
                Union["ApplicationUpdateSchemaSourceDataType0", None, Unset], data
            )

        source_data = _parse_source_data(d.pop("source_data", UNSET))

        def _parse_historical_data(
            data: object,
        ) -> Union["ApplicationUpdateSchemaHistoricalDataType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                historical_data_type_0 = (
                    ApplicationUpdateSchemaHistoricalDataType0.from_dict(data)
                )

                return historical_data_type_0
            except:  # noqa: E722
                pass
            return cast(
                Union["ApplicationUpdateSchemaHistoricalDataType0", None, Unset], data
            )

        historical_data = _parse_historical_data(d.pop("historical_data", UNSET))

        def _parse_connection_info(
            data: object,
        ) -> Union["ApplicationUpdateSchemaConnectionInfoType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                connection_info_type_0 = (
                    ApplicationUpdateSchemaConnectionInfoType0.from_dict(data)
                )

                return connection_info_type_0
            except:  # noqa: E722
                pass
            return cast(
                Union["ApplicationUpdateSchemaConnectionInfoType0", None, Unset], data
            )

        connection_info = _parse_connection_info(d.pop("connection_info", UNSET))

        def _parse_autofix_configuration(
            data: object,
        ) -> Union["ApplicationUpdateSchemaAutofixConfigurationType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                autofix_configuration_type_0 = (
                    ApplicationUpdateSchemaAutofixConfigurationType0.from_dict(data)
                )

                return autofix_configuration_type_0
            except:  # noqa: E722
                pass
            return cast(
                Union["ApplicationUpdateSchemaAutofixConfigurationType0", None, Unset],
                data,
            )

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

        application_update_schema = cls(
            id=id,
            name=name,
            icon=icon,
            description=description,
            created_at=created_at,
            updated_at=updated_at,
            created_by=created_by,
            settings=settings,
            source_data=source_data,
            historical_data=historical_data,
            connection_info=connection_info,
            autofix_configuration=autofix_configuration,
            marked_for_deletion_at=marked_for_deletion_at,
        )

        application_update_schema.additional_properties = d
        return application_update_schema

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
