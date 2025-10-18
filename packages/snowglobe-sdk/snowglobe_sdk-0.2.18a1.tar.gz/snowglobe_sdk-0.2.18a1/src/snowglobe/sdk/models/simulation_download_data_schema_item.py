from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define
from attrs import field as _attrs_field


if TYPE_CHECKING:
    from ..models.simulation_download_data_schema_item_messages_item import (
        SimulationDownloadDataSchemaItemMessagesItem,
    )


T = TypeVar("T", bound="SimulationDownloadDataSchemaItem")


@_attrs_define
class SimulationDownloadDataSchemaItem:
    """
    Attributes:
        conversation_id (str):
        persona (str):
        use_case (str):
        messages (list['SimulationDownloadDataSchemaItemMessagesItem']):
    """

    conversation_id: str
    persona: str
    use_case: str
    messages: list["SimulationDownloadDataSchemaItemMessagesItem"]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        conversation_id = self.conversation_id

        persona = self.persona

        use_case = self.use_case

        messages = []
        for messages_item_data in self.messages:
            messages_item = messages_item_data.to_dict()
            messages.append(messages_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "conversation_id": conversation_id,
                "persona": persona,
                "use_case": use_case,
                "messages": messages,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.simulation_download_data_schema_item_messages_item import (
            SimulationDownloadDataSchemaItemMessagesItem,
        )

        d = dict(src_dict)
        conversation_id = d.pop("conversation_id")

        persona = d.pop("persona")

        use_case = d.pop("use_case")

        messages = []
        _messages = d.pop("messages")
        for messages_item_data in _messages:
            messages_item = SimulationDownloadDataSchemaItemMessagesItem.from_dict(
                messages_item_data
            )

            messages.append(messages_item)

        simulation_download_data_schema_item = cls(
            conversation_id=conversation_id,
            persona=persona,
            use_case=use_case,
            messages=messages,
        )

        simulation_download_data_schema_item.additional_properties = d
        return simulation_download_data_schema_item

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
