from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

from typing import Union


T = TypeVar("T", bound="RiskLlmConfigurationType0")


@_attrs_define
class RiskLlmConfigurationType0:
    """
    Attributes:
        temperature (Union[Unset, float]):
        seed (Union[Unset, float]):
        history_limit (Union[Unset, float]):
        top_p (Union[Unset, float]):
    """

    temperature: Union[Unset, float] = UNSET
    seed: Union[Unset, float] = UNSET
    history_limit: Union[Unset, float] = UNSET
    top_p: Union[Unset, float] = UNSET

    def to_dict(self) -> dict[str, Any]:
        temperature = self.temperature

        seed = self.seed

        history_limit = self.history_limit

        top_p = self.top_p

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if temperature is not UNSET:
            field_dict["temperature"] = temperature
        if seed is not UNSET:
            field_dict["seed"] = seed
        if history_limit is not UNSET:
            field_dict["history_limit"] = history_limit
        if top_p is not UNSET:
            field_dict["top_p"] = top_p

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        temperature = d.pop("temperature", UNSET)

        seed = d.pop("seed", UNSET)

        history_limit = d.pop("history_limit", UNSET)

        top_p = d.pop("top_p", UNSET)

        risk_llm_configuration_type_0 = cls(
            temperature=temperature,
            seed=seed,
            history_limit=history_limit,
            top_p=top_p,
        )

        return risk_llm_configuration_type_0
