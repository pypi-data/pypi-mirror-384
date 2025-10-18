from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define


T = TypeVar("T", bound="ConversationsItemMessagesItemTacticsItem")


@_attrs_define
class ConversationsItemMessagesItemTacticsItem:
    """
    Attributes:
        strategy (str):
        definition (str):
        intent (str):
    """

    strategy: str
    definition: str
    intent: str

    def to_dict(self) -> dict[str, Any]:
        strategy = self.strategy

        definition = self.definition

        intent = self.intent

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "strategy": strategy,
                "definition": definition,
                "intent": intent,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        strategy = d.pop("strategy")

        definition = d.pop("definition")

        intent = d.pop("intent")

        conversations_item_messages_item_tactics_item = cls(
            strategy=strategy,
            definition=definition,
            intent=intent,
        )

        return conversations_item_messages_item_tactics_item
