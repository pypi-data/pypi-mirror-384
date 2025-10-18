from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field


T = TypeVar("T", bound="UploadUrlsResponseSchemaUrlsItem")


@_attrs_define
class UploadUrlsResponseSchemaUrlsItem:
    """
    Attributes:
        id (str):
        url (str):
        expires_in_seconds (float):
    """

    id: str
    url: str
    expires_in_seconds: float
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        url = self.url

        expires_in_seconds = self.expires_in_seconds

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "url": url,
                "expiresInSeconds": expires_in_seconds,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        url = d.pop("url")

        expires_in_seconds = d.pop("expiresInSeconds")

        upload_urls_response_schema_urls_item = cls(
            id=id,
            url=url,
            expires_in_seconds=expires_in_seconds,
        )

        upload_urls_response_schema_urls_item.additional_properties = d
        return upload_urls_response_schema_urls_item

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
