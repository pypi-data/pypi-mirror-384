from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

from dateutil.parser import isoparse
from typing import cast
from typing import Union
from uuid import UUID
import datetime


T = TypeVar("T", bound="RiskEvaluationsItem")


@_attrs_define
class RiskEvaluationsItem:
    """
    Attributes:
        id (UUID):
        test_id (UUID):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
        retries (int):
        risk_type (Union[None, Unset, str]):
        confidence (Union[None, Unset, int]):
        judge_prompt (Union[None, Unset, str]):
        judge_response (Union[None, Unset, str]):
        risk_triggered (Union[None, Unset, bool]):
        state (Union[None, Unset, str]):
    """

    id: UUID
    test_id: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime
    retries: int
    risk_type: Union[None, Unset, str] = UNSET
    confidence: Union[None, Unset, int] = UNSET
    judge_prompt: Union[None, Unset, str] = UNSET
    judge_response: Union[None, Unset, str] = UNSET
    risk_triggered: Union[None, Unset, bool] = UNSET
    state: Union[None, Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        test_id = str(self.test_id)

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        retries = self.retries

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

        state: Union[None, Unset, str]
        if isinstance(self.state, Unset):
            state = UNSET
        else:
            state = self.state

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "id": id,
                "test_id": test_id,
                "created_at": created_at,
                "updated_at": updated_at,
                "retries": retries,
            }
        )
        if risk_type is not UNSET:
            field_dict["risk_type"] = risk_type
        if confidence is not UNSET:
            field_dict["confidence"] = confidence
        if judge_prompt is not UNSET:
            field_dict["judge_prompt"] = judge_prompt
        if judge_response is not UNSET:
            field_dict["judge_response"] = judge_response
        if risk_triggered is not UNSET:
            field_dict["risk_triggered"] = risk_triggered
        if state is not UNSET:
            field_dict["state"] = state

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        test_id = UUID(d.pop("test_id"))

        created_at = isoparse(d.pop("created_at"))

        updated_at = isoparse(d.pop("updated_at"))

        retries = d.pop("retries")

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

        def _parse_state(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        state = _parse_state(d.pop("state", UNSET))

        risk_evaluations_item = cls(
            id=id,
            test_id=test_id,
            created_at=created_at,
            updated_at=updated_at,
            retries=retries,
            risk_type=risk_type,
            confidence=confidence,
            judge_prompt=judge_prompt,
            judge_response=judge_response,
            risk_triggered=risk_triggered,
            state=state,
        )

        return risk_evaluations_item
