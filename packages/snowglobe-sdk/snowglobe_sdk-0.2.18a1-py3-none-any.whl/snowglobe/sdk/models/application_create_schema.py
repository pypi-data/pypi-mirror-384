from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast
from typing import Union

if TYPE_CHECKING:
    from ..models.application_create_schema_connection_info_type_0 import (
        ApplicationCreateSchemaConnectionInfoType0,
    )
    from ..models.application_create_schema_historical_data_type_0 import (
        ApplicationCreateSchemaHistoricalDataType0,
    )
    from ..models.application_create_schema_settings_type_0 import (
        ApplicationCreateSchemaSettingsType0,
    )
    from ..models.application_create_schema_source_data_type_0 import (
        ApplicationCreateSchemaSourceDataType0,
    )


T = TypeVar("T", bound="ApplicationCreateSchema")


@_attrs_define
class ApplicationCreateSchema:
    """
    Attributes:
        name (str):
        icon (str):
        description (Union[None, Unset, str]):
        settings (Union['ApplicationCreateSchemaSettingsType0', None, Unset]):
        source_data (Union['ApplicationCreateSchemaSourceDataType0', None, Unset]):
        historical_data (Union['ApplicationCreateSchemaHistoricalDataType0', None, Unset]):
        connection_info (Union['ApplicationCreateSchemaConnectionInfoType0', None, Unset]):
    """

    name: str
    icon: str
    description: Union[None, Unset, str] = UNSET
    settings: Union["ApplicationCreateSchemaSettingsType0", None, Unset] = UNSET
    source_data: Union["ApplicationCreateSchemaSourceDataType0", None, Unset] = UNSET
    historical_data: Union[
        "ApplicationCreateSchemaHistoricalDataType0", None, Unset
    ] = UNSET
    connection_info: Union[
        "ApplicationCreateSchemaConnectionInfoType0", None, Unset
    ] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.application_create_schema_connection_info_type_0 import (
            ApplicationCreateSchemaConnectionInfoType0,
        )
        from ..models.application_create_schema_historical_data_type_0 import (
            ApplicationCreateSchemaHistoricalDataType0,
        )
        from ..models.application_create_schema_settings_type_0 import (
            ApplicationCreateSchemaSettingsType0,
        )
        from ..models.application_create_schema_source_data_type_0 import (
            ApplicationCreateSchemaSourceDataType0,
        )

        name = self.name

        icon = self.icon

        description: Union[None, Unset, str]
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        settings: Union[None, Unset, dict[str, Any]]
        if isinstance(self.settings, Unset):
            settings = UNSET
        elif isinstance(self.settings, ApplicationCreateSchemaSettingsType0):
            settings = self.settings.to_dict()
        else:
            settings = self.settings

        source_data: Union[None, Unset, dict[str, Any]]
        if isinstance(self.source_data, Unset):
            source_data = UNSET
        elif isinstance(self.source_data, ApplicationCreateSchemaSourceDataType0):
            source_data = self.source_data.to_dict()
        else:
            source_data = self.source_data

        historical_data: Union[None, Unset, dict[str, Any]]
        if isinstance(self.historical_data, Unset):
            historical_data = UNSET
        elif isinstance(
            self.historical_data, ApplicationCreateSchemaHistoricalDataType0
        ):
            historical_data = self.historical_data.to_dict()
        else:
            historical_data = self.historical_data

        connection_info: Union[None, Unset, dict[str, Any]]
        if isinstance(self.connection_info, Unset):
            connection_info = UNSET
        elif isinstance(
            self.connection_info, ApplicationCreateSchemaConnectionInfoType0
        ):
            connection_info = self.connection_info.to_dict()
        else:
            connection_info = self.connection_info

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "icon": icon,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if settings is not UNSET:
            field_dict["settings"] = settings
        if source_data is not UNSET:
            field_dict["source_data"] = source_data
        if historical_data is not UNSET:
            field_dict["historical_data"] = historical_data
        if connection_info is not UNSET:
            field_dict["connection_info"] = connection_info

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.application_create_schema_connection_info_type_0 import (
            ApplicationCreateSchemaConnectionInfoType0,
        )
        from ..models.application_create_schema_historical_data_type_0 import (
            ApplicationCreateSchemaHistoricalDataType0,
        )
        from ..models.application_create_schema_settings_type_0 import (
            ApplicationCreateSchemaSettingsType0,
        )
        from ..models.application_create_schema_source_data_type_0 import (
            ApplicationCreateSchemaSourceDataType0,
        )

        d = dict(src_dict)
        name = d.pop("name")

        icon = d.pop("icon")

        def _parse_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_settings(
            data: object,
        ) -> Union["ApplicationCreateSchemaSettingsType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                settings_type_0 = ApplicationCreateSchemaSettingsType0.from_dict(data)

                return settings_type_0
            except:  # noqa: E722
                pass
            return cast(
                Union["ApplicationCreateSchemaSettingsType0", None, Unset], data
            )

        settings = _parse_settings(d.pop("settings", UNSET))

        def _parse_source_data(
            data: object,
        ) -> Union["ApplicationCreateSchemaSourceDataType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                source_data_type_0 = ApplicationCreateSchemaSourceDataType0.from_dict(
                    data
                )

                return source_data_type_0
            except:  # noqa: E722
                pass
            return cast(
                Union["ApplicationCreateSchemaSourceDataType0", None, Unset], data
            )

        source_data = _parse_source_data(d.pop("source_data", UNSET))

        def _parse_historical_data(
            data: object,
        ) -> Union["ApplicationCreateSchemaHistoricalDataType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                historical_data_type_0 = (
                    ApplicationCreateSchemaHistoricalDataType0.from_dict(data)
                )

                return historical_data_type_0
            except:  # noqa: E722
                pass
            return cast(
                Union["ApplicationCreateSchemaHistoricalDataType0", None, Unset], data
            )

        historical_data = _parse_historical_data(d.pop("historical_data", UNSET))

        def _parse_connection_info(
            data: object,
        ) -> Union["ApplicationCreateSchemaConnectionInfoType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                connection_info_type_0 = (
                    ApplicationCreateSchemaConnectionInfoType0.from_dict(data)
                )

                return connection_info_type_0
            except:  # noqa: E722
                pass
            return cast(
                Union["ApplicationCreateSchemaConnectionInfoType0", None, Unset], data
            )

        connection_info = _parse_connection_info(d.pop("connection_info", UNSET))

        application_create_schema = cls(
            name=name,
            icon=icon,
            description=description,
            settings=settings,
            source_data=source_data,
            historical_data=historical_data,
            connection_info=connection_info,
        )

        application_create_schema.additional_properties = d
        return application_create_schema

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
