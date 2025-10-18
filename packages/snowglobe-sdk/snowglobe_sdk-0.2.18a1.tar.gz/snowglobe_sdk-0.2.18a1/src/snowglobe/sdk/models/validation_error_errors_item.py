from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define
from attrs import field as _attrs_field


if TYPE_CHECKING:
    from ..models.validation_error_errors_item_params import (
        ValidationErrorErrorsItemParams,
    )


T = TypeVar("T", bound="ValidationErrorErrorsItem")


@_attrs_define
class ValidationErrorErrorsItem:
    """
    Attributes:
        instance_path (str):  Default: ''.
        schema_path (str):  Default: '#/required'.
        keyword (str):  Default: 'required'.
        params (ValidationErrorErrorsItemParams):
        message (str):  Default: "must have required property 'some property'".
    """

    params: "ValidationErrorErrorsItemParams"
    instance_path: str = ""
    schema_path: str = "#/required"
    keyword: str = "required"
    message: str = "must have required property 'some property'"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        instance_path = self.instance_path

        schema_path = self.schema_path

        keyword = self.keyword

        params = self.params.to_dict()

        message = self.message

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "instancePath": instance_path,
                "schemaPath": schema_path,
                "keyword": keyword,
                "params": params,
                "message": message,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.validation_error_errors_item_params import (
            ValidationErrorErrorsItemParams,
        )

        d = dict(src_dict)
        instance_path = d.pop("instancePath")

        schema_path = d.pop("schemaPath")

        keyword = d.pop("keyword")

        params = ValidationErrorErrorsItemParams.from_dict(d.pop("params"))

        message = d.pop("message")

        validation_error_errors_item = cls(
            instance_path=instance_path,
            schema_path=schema_path,
            keyword=keyword,
            params=params,
            message=message,
        )

        validation_error_errors_item.additional_properties = d
        return validation_error_errors_item

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
