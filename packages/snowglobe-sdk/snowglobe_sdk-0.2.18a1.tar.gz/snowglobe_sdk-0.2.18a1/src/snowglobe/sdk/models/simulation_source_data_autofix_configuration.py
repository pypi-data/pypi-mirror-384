from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

from typing import Union


T = TypeVar("T", bound="SimulationSourceDataAutofixConfiguration")


@_attrs_define
class SimulationSourceDataAutofixConfiguration:
    """
    Attributes:
        num_retries (float):
        model_name (str):
        temperature (Union[Unset, float]):
        top_p (Union[Unset, float]):
        seed (Union[Unset, float]):
    """

    num_retries: float
    model_name: str
    temperature: Union[Unset, float] = UNSET
    top_p: Union[Unset, float] = UNSET
    seed: Union[Unset, float] = UNSET

    def to_dict(self) -> dict[str, Any]:
        num_retries = self.num_retries

        model_name = self.model_name

        temperature = self.temperature

        top_p = self.top_p

        seed = self.seed

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "num_retries": num_retries,
                "model_name": model_name,
            }
        )
        if temperature is not UNSET:
            field_dict["temperature"] = temperature
        if top_p is not UNSET:
            field_dict["top_p"] = top_p
        if seed is not UNSET:
            field_dict["seed"] = seed

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        num_retries = d.pop("num_retries")

        model_name = d.pop("model_name")

        temperature = d.pop("temperature", UNSET)

        top_p = d.pop("top_p", UNSET)

        seed = d.pop("seed", UNSET)

        simulation_source_data_autofix_configuration = cls(
            num_retries=num_retries,
            model_name=model_name,
            temperature=temperature,
            top_p=top_p,
            seed=seed,
        )

        return simulation_source_data_autofix_configuration
