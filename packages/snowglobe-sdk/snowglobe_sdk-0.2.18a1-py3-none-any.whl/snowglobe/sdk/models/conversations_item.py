from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define


from uuid import UUID

if TYPE_CHECKING:
    from ..models.conversations_item_messages_item import ConversationsItemMessagesItem


T = TypeVar("T", bound="ConversationsItem")


@_attrs_define
class ConversationsItem:
    """
    Attributes:
        experiment_id (str):
        topic (str):
        persona (str):
        persona_record_id (UUID):
        messages (list['ConversationsItemMessagesItem']):
    """

    experiment_id: str
    topic: str
    persona: str
    persona_record_id: UUID
    messages: list["ConversationsItemMessagesItem"]

    def to_dict(self) -> dict[str, Any]:
        experiment_id = self.experiment_id

        topic = self.topic

        persona = self.persona

        persona_record_id = str(self.persona_record_id)

        messages = []
        for messages_item_data in self.messages:
            messages_item = messages_item_data.to_dict()
            messages.append(messages_item)

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "experimentId": experiment_id,
                "topic": topic,
                "persona": persona,
                "persona_record_id": persona_record_id,
                "messages": messages,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.conversations_item_messages_item import (
            ConversationsItemMessagesItem,
        )

        d = dict(src_dict)
        experiment_id = d.pop("experimentId")

        topic = d.pop("topic")

        persona = d.pop("persona")

        persona_record_id = UUID(d.pop("persona_record_id"))

        messages = []
        _messages = d.pop("messages")
        for messages_item_data in _messages:
            messages_item = ConversationsItemMessagesItem.from_dict(messages_item_data)

            messages.append(messages_item)

        conversations_item = cls(
            experiment_id=experiment_id,
            topic=topic,
            persona=persona,
            persona_record_id=persona_record_id,
            messages=messages,
        )

        return conversations_item
