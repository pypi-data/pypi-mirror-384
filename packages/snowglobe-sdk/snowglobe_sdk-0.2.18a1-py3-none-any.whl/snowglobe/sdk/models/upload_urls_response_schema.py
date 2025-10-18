from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define
from attrs import field as _attrs_field


if TYPE_CHECKING:
    from ..models.upload_urls_response_schema_urls_item import (
        UploadUrlsResponseSchemaUrlsItem,
    )


T = TypeVar("T", bound="UploadUrlsResponseSchema")


@_attrs_define
class UploadUrlsResponseSchema:
    """
    Attributes:
        urls (list['UploadUrlsResponseSchemaUrlsItem']):
    """

    urls: list["UploadUrlsResponseSchemaUrlsItem"]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        urls = []
        for urls_item_data in self.urls:
            urls_item = urls_item_data.to_dict()
            urls.append(urls_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "urls": urls,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.upload_urls_response_schema_urls_item import (
            UploadUrlsResponseSchemaUrlsItem,
        )

        d = dict(src_dict)
        urls = []
        _urls = d.pop("urls")
        for urls_item_data in _urls:
            urls_item = UploadUrlsResponseSchemaUrlsItem.from_dict(urls_item_data)

            urls.append(urls_item)

        upload_urls_response_schema = cls(
            urls=urls,
        )

        upload_urls_response_schema.additional_properties = d
        return upload_urls_response_schema

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
