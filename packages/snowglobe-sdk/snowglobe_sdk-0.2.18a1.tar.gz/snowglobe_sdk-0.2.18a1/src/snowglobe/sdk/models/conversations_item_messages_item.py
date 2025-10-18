from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define

from ..types import UNSET, Unset

from typing import Union

if TYPE_CHECKING:
    from ..models.conversations_item_messages_item_tactics_item import (
        ConversationsItemMessagesItemTacticsItem,
    )


T = TypeVar("T", bound="ConversationsItemMessagesItem")


@_attrs_define
class ConversationsItemMessagesItem:
    """
    Attributes:
        role (str):
        content (str):
        test_id (str):
        tactics (Union[Unset, list['ConversationsItemMessagesItemTacticsItem']]):
        judge_result (Union[Unset, str]):
        is_original (Union[Unset, bool]):
        original_test_id (Union[Unset, str]):
    """

    role: str
    content: str
    test_id: str
    tactics: Union[Unset, list["ConversationsItemMessagesItemTacticsItem"]] = UNSET
    judge_result: Union[Unset, str] = UNSET
    is_original: Union[Unset, bool] = UNSET
    original_test_id: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        role = self.role

        content = self.content

        test_id = self.test_id

        tactics: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.tactics, Unset):
            tactics = []
            for tactics_item_data in self.tactics:
                tactics_item = tactics_item_data.to_dict()
                tactics.append(tactics_item)

        judge_result = self.judge_result

        is_original = self.is_original

        original_test_id = self.original_test_id

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "role": role,
                "content": content,
                "testId": test_id,
            }
        )
        if tactics is not UNSET:
            field_dict["tactics"] = tactics
        if judge_result is not UNSET:
            field_dict["judgeResult"] = judge_result
        if is_original is not UNSET:
            field_dict["isOriginal"] = is_original
        if original_test_id is not UNSET:
            field_dict["originalTestId"] = original_test_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.conversations_item_messages_item_tactics_item import (
            ConversationsItemMessagesItemTacticsItem,
        )

        d = dict(src_dict)
        role = d.pop("role")

        content = d.pop("content")

        test_id = d.pop("testId")

        tactics = []
        _tactics = d.pop("tactics", UNSET)
        for tactics_item_data in _tactics or []:
            tactics_item = ConversationsItemMessagesItemTacticsItem.from_dict(
                tactics_item_data
            )

            tactics.append(tactics_item)

        judge_result = d.pop("judgeResult", UNSET)

        is_original = d.pop("isOriginal", UNSET)

        original_test_id = d.pop("originalTestId", UNSET)

        conversations_item_messages_item = cls(
            role=role,
            content=content,
            test_id=test_id,
            tactics=tactics,
            judge_result=judge_result,
            is_original=is_original,
            original_test_id=original_test_id,
        )

        return conversations_item_messages_item
