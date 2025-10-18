from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import Union

if TYPE_CHECKING:
    from ..models.agent_update_schema_connection_info_type_0_extra_headers_item import (
        AgentUpdateSchemaConnectionInfoType0ExtraHeadersItem,
    )
    from ..models.agent_update_schema_connection_info_type_0_extra_body_item import (
        AgentUpdateSchemaConnectionInfoType0ExtraBodyItem,
    )


T = TypeVar("T", bound="AgentUpdateSchemaConnectionInfoType0")


@_attrs_define
class AgentUpdateSchemaConnectionInfoType0:
    """
    Attributes:
        api_key_ref (str):
        model_name (str):
        system_prompt (str):
        provider (Union[Unset, str]):
        endpoint (Union[Unset, str]):
        temperature (Union[Unset, float]):
        seed (Union[Unset, float]):
        top_p (Union[Unset, float]):
        extra_body (Union[Unset, list['AgentUpdateSchemaConnectionInfoType0ExtraBodyItem']]):
        extra_headers (Union[Unset, list['AgentUpdateSchemaConnectionInfoType0ExtraHeadersItem']]):
    """

    api_key_ref: str
    model_name: str
    system_prompt: str
    provider: Union[Unset, str] = UNSET
    endpoint: Union[Unset, str] = UNSET
    temperature: Union[Unset, float] = UNSET
    seed: Union[Unset, float] = UNSET
    top_p: Union[Unset, float] = UNSET
    extra_body: Union[
        Unset, list["AgentUpdateSchemaConnectionInfoType0ExtraBodyItem"]
    ] = UNSET
    extra_headers: Union[
        Unset, list["AgentUpdateSchemaConnectionInfoType0ExtraHeadersItem"]
    ] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        api_key_ref = self.api_key_ref

        model_name = self.model_name

        system_prompt = self.system_prompt

        provider = self.provider

        endpoint = self.endpoint

        temperature = self.temperature

        seed = self.seed

        top_p = self.top_p

        extra_body: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.extra_body, Unset):
            extra_body = []
            for extra_body_item_data in self.extra_body:
                extra_body_item = extra_body_item_data.to_dict()
                extra_body.append(extra_body_item)

        extra_headers: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.extra_headers, Unset):
            extra_headers = []
            for extra_headers_item_data in self.extra_headers:
                extra_headers_item = extra_headers_item_data.to_dict()
                extra_headers.append(extra_headers_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "api_key_ref": api_key_ref,
                "model_name": model_name,
                "system_prompt": system_prompt,
            }
        )
        if provider is not UNSET:
            field_dict["provider"] = provider
        if endpoint is not UNSET:
            field_dict["endpoint"] = endpoint
        if temperature is not UNSET:
            field_dict["temperature"] = temperature
        if seed is not UNSET:
            field_dict["seed"] = seed
        if top_p is not UNSET:
            field_dict["top_p"] = top_p
        if extra_body is not UNSET:
            field_dict["extra_body"] = extra_body
        if extra_headers is not UNSET:
            field_dict["extra_headers"] = extra_headers

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_update_schema_connection_info_type_0_extra_headers_item import (
            AgentUpdateSchemaConnectionInfoType0ExtraHeadersItem,
        )
        from ..models.agent_update_schema_connection_info_type_0_extra_body_item import (
            AgentUpdateSchemaConnectionInfoType0ExtraBodyItem,
        )

        d = dict(src_dict)
        api_key_ref = d.pop("api_key_ref")

        model_name = d.pop("model_name")

        system_prompt = d.pop("system_prompt")

        provider = d.pop("provider", UNSET)

        endpoint = d.pop("endpoint", UNSET)

        temperature = d.pop("temperature", UNSET)

        seed = d.pop("seed", UNSET)

        top_p = d.pop("top_p", UNSET)

        extra_body = []
        _extra_body = d.pop("extra_body", UNSET)
        for extra_body_item_data in _extra_body or []:
            extra_body_item = (
                AgentUpdateSchemaConnectionInfoType0ExtraBodyItem.from_dict(
                    extra_body_item_data
                )
            )

            extra_body.append(extra_body_item)

        extra_headers = []
        _extra_headers = d.pop("extra_headers", UNSET)
        for extra_headers_item_data in _extra_headers or []:
            extra_headers_item = (
                AgentUpdateSchemaConnectionInfoType0ExtraHeadersItem.from_dict(
                    extra_headers_item_data
                )
            )

            extra_headers.append(extra_headers_item)

        agent_update_schema_connection_info_type_0 = cls(
            api_key_ref=api_key_ref,
            model_name=model_name,
            system_prompt=system_prompt,
            provider=provider,
            endpoint=endpoint,
            temperature=temperature,
            seed=seed,
            top_p=top_p,
            extra_body=extra_body,
            extra_headers=extra_headers,
        )

        agent_update_schema_connection_info_type_0.additional_properties = d
        return agent_update_schema_connection_info_type_0

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
