from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

from typing import cast, Union


T = TypeVar("T", bound="RiskEvaluationBatchCreateRequestItem")


@_attrs_define
class RiskEvaluationBatchCreateRequestItem:
    """
    Attributes:
        judge_prompt (Union[None, Unset, str]):
        judge_response (Union[None, Unset, str]):
        risk_triggered (Union[None, Unset, bool]):
        risk_type (Union[None, Unset, str]):
        confidence (Union[None, Unset, int]):
    """

    judge_prompt: Union[None, Unset, str] = UNSET
    judge_response: Union[None, Unset, str] = UNSET
    risk_triggered: Union[None, Unset, bool] = UNSET
    risk_type: Union[None, Unset, str] = UNSET
    confidence: Union[None, Unset, int] = UNSET

    def to_dict(self) -> dict[str, Any]:
        judge_prompt: Union[None, Unset, str]
        if isinstance(self.judge_prompt, Unset):
            judge_prompt = UNSET
        else:
            judge_prompt = self.judge_prompt

        judge_response: Union[None, Unset, str]
        if isinstance(self.judge_response, Unset):
            judge_response = UNSET
        else:
            judge_response = self.judge_response

        risk_triggered: Union[None, Unset, bool]
        if isinstance(self.risk_triggered, Unset):
            risk_triggered = UNSET
        else:
            risk_triggered = self.risk_triggered

        risk_type: Union[None, Unset, str]
        if isinstance(self.risk_type, Unset):
            risk_type = UNSET
        else:
            risk_type = self.risk_type

        confidence: Union[None, Unset, int]
        if isinstance(self.confidence, Unset):
            confidence = UNSET
        else:
            confidence = self.confidence

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if judge_prompt is not UNSET:
            field_dict["judge_prompt"] = judge_prompt
        if judge_response is not UNSET:
            field_dict["judge_response"] = judge_response
        if risk_triggered is not UNSET:
            field_dict["risk_triggered"] = risk_triggered
        if risk_type is not UNSET:
            field_dict["risk_type"] = risk_type
        if confidence is not UNSET:
            field_dict["confidence"] = confidence

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_judge_prompt(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        judge_prompt = _parse_judge_prompt(d.pop("judge_prompt", UNSET))

        def _parse_judge_response(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        judge_response = _parse_judge_response(d.pop("judge_response", UNSET))

        def _parse_risk_triggered(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        risk_triggered = _parse_risk_triggered(d.pop("risk_triggered", UNSET))

        def _parse_risk_type(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        risk_type = _parse_risk_type(d.pop("risk_type", UNSET))

        def _parse_confidence(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        confidence = _parse_confidence(d.pop("confidence", UNSET))

        risk_evaluation_batch_create_request_item = cls(
            judge_prompt=judge_prompt,
            judge_response=judge_response,
            risk_triggered=risk_triggered,
            risk_type=risk_type,
            confidence=confidence,
        )

        return risk_evaluation_batch_create_request_item
