from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

from typing import Union


T = TypeVar("T", bound="ApplicationConnectionInfoType0ExtraBodyItem")


@_attrs_define
class ApplicationConnectionInfoType0ExtraBodyItem:
    """
    Attributes:
        key (str):
        value (Any):
        type_ (Union[Unset, str]):
    """

    key: str
    value: Any
    type_: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        key = self.key

        value = self.value

        type_ = self.type_

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "key": key,
                "value": value,
            }
        )
        if type_ is not UNSET:
            field_dict["type"] = type_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        key = d.pop("key")

        value = d.pop("value")

        type_ = d.pop("type", UNSET)

        application_connection_info_type_0_extra_body_item = cls(
            key=key,
            value=value,
            type_=type_,
        )

        return application_connection_info_type_0_extra_body_item
