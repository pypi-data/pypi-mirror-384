from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define
from attrs import field as _attrs_field


if TYPE_CHECKING:
    from ..models.metric_prompt_template_type_0_variables import (
        MetricPromptTemplateType0Variables,
    )


T = TypeVar("T", bound="MetricPromptTemplateType0")


@_attrs_define
class MetricPromptTemplateType0:
    """
    Attributes:
        template (str):
        variables (MetricPromptTemplateType0Variables):
    """

    template: str
    variables: "MetricPromptTemplateType0Variables"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        template = self.template

        variables = self.variables.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "template": template,
                "variables": variables,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.metric_prompt_template_type_0_variables import (
            MetricPromptTemplateType0Variables,
        )

        d = dict(src_dict)
        template = d.pop("template")

        variables = MetricPromptTemplateType0Variables.from_dict(d.pop("variables"))

        metric_prompt_template_type_0 = cls(
            template=template,
            variables=variables,
        )

        metric_prompt_template_type_0.additional_properties = d
        return metric_prompt_template_type_0

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
