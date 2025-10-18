from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import Union

if TYPE_CHECKING:
    from ..models.simulation_download_data_schema_item_messages_item_snowglobe_data import (
        SimulationDownloadDataSchemaItemMessagesItemSnowglobeData,
    )


T = TypeVar("T", bound="SimulationDownloadDataSchemaItemMessagesItem")


@_attrs_define
class SimulationDownloadDataSchemaItemMessagesItem:
    """
    Attributes:
        role (str):
        content (str):
        snowglobe_data (Union[Unset, SimulationDownloadDataSchemaItemMessagesItemSnowglobeData]):
    """

    role: str
    content: str
    snowglobe_data: Union[
        Unset, "SimulationDownloadDataSchemaItemMessagesItemSnowglobeData"
    ] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        role = self.role

        content = self.content

        snowglobe_data: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.snowglobe_data, Unset):
            snowglobe_data = self.snowglobe_data.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "role": role,
                "content": content,
            }
        )
        if snowglobe_data is not UNSET:
            field_dict["snowglobe_data"] = snowglobe_data

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.simulation_download_data_schema_item_messages_item_snowglobe_data import (
            SimulationDownloadDataSchemaItemMessagesItemSnowglobeData,
        )

        d = dict(src_dict)
        role = d.pop("role")

        content = d.pop("content")

        _snowglobe_data = d.pop("snowglobe_data", UNSET)
        snowglobe_data: Union[
            Unset, SimulationDownloadDataSchemaItemMessagesItemSnowglobeData
        ]
        if isinstance(_snowglobe_data, Unset):
            snowglobe_data = UNSET
        else:
            snowglobe_data = (
                SimulationDownloadDataSchemaItemMessagesItemSnowglobeData.from_dict(
                    _snowglobe_data
                )
            )

        simulation_download_data_schema_item_messages_item = cls(
            role=role,
            content=content,
            snowglobe_data=snowglobe_data,
        )

        simulation_download_data_schema_item_messages_item.additional_properties = d
        return simulation_download_data_schema_item_messages_item

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
