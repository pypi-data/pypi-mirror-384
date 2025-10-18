from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field


T = TypeVar(
    "T",
    bound="ExperimentDownloadDataSchemaItemMessagesItemSnowglobeDataRiskEvaluationsItem",
)


@_attrs_define
class ExperimentDownloadDataSchemaItemMessagesItemSnowglobeDataRiskEvaluationsItem:
    """
    Attributes:
        id (str):
        test_id (str):
        risk_type (str):
        confidence (float):
        judge_response (str):
        risk_triggered (bool):
        created_at (str):
        updated_at (str):
        state (str):
        retries (float):
    """

    id: str
    test_id: str
    risk_type: str
    confidence: float
    judge_response: str
    risk_triggered: bool
    created_at: str
    updated_at: str
    state: str
    retries: float
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        test_id = self.test_id

        risk_type = self.risk_type

        confidence = self.confidence

        judge_response = self.judge_response

        risk_triggered = self.risk_triggered

        created_at = self.created_at

        updated_at = self.updated_at

        state = self.state

        retries = self.retries

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "test_id": test_id,
                "risk_type": risk_type,
                "confidence": confidence,
                "judge_response": judge_response,
                "risk_triggered": risk_triggered,
                "created_at": created_at,
                "updated_at": updated_at,
                "state": state,
                "retries": retries,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        test_id = d.pop("test_id")

        risk_type = d.pop("risk_type")

        confidence = d.pop("confidence")

        judge_response = d.pop("judge_response")

        risk_triggered = d.pop("risk_triggered")

        created_at = d.pop("created_at")

        updated_at = d.pop("updated_at")

        state = d.pop("state")

        retries = d.pop("retries")

        experiment_download_data_schema_item_messages_item_snowglobe_data_risk_evaluations_item = cls(
            id=id,
            test_id=test_id,
            risk_type=risk_type,
            confidence=confidence,
            judge_response=judge_response,
            risk_triggered=risk_triggered,
            created_at=created_at,
            updated_at=updated_at,
            state=state,
            retries=retries,
        )

        experiment_download_data_schema_item_messages_item_snowglobe_data_risk_evaluations_item.additional_properties = d
        return experiment_download_data_schema_item_messages_item_snowglobe_data_risk_evaluations_item

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
