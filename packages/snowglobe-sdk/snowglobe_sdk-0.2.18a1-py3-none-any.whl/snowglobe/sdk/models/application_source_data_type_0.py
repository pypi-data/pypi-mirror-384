from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define


from typing import cast


T = TypeVar("T", bound="ApplicationSourceDataType0")


@_attrs_define
class ApplicationSourceDataType0:
    """
    Attributes:
        docs (list[str]):
    """

    docs: list[str]

    def to_dict(self) -> dict[str, Any]:
        docs = self.docs

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "docs": docs,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        docs = cast(list[str], d.pop("docs"))

        application_source_data_type_0 = cls(
            docs=docs,
        )

        return application_source_data_type_0
