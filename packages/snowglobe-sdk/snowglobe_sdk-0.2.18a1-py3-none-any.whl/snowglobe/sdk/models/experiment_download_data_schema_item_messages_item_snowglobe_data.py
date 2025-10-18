from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast
from typing import Union

if TYPE_CHECKING:
    from ..models.experiment_download_data_schema_item_messages_item_snowglobe_data_risk_evaluations_item import (
        ExperimentDownloadDataSchemaItemMessagesItemSnowglobeDataRiskEvaluationsItem,
    )


T = TypeVar("T", bound="ExperimentDownloadDataSchemaItemMessagesItemSnowglobeData")


@_attrs_define
class ExperimentDownloadDataSchemaItemMessagesItemSnowglobeData:
    """
    Attributes:
        test_id (str):
        parent_test_id (Union[None, Unset, str]):
        risk_evaluations (Union[Unset,
            list['ExperimentDownloadDataSchemaItemMessagesItemSnowglobeDataRiskEvaluationsItem']]):
    """

    test_id: str
    parent_test_id: Union[None, Unset, str] = UNSET
    risk_evaluations: Union[
        Unset,
        list[
            "ExperimentDownloadDataSchemaItemMessagesItemSnowglobeDataRiskEvaluationsItem"
        ],
    ] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        test_id = self.test_id

        parent_test_id: Union[None, Unset, str]
        if isinstance(self.parent_test_id, Unset):
            parent_test_id = UNSET
        else:
            parent_test_id = self.parent_test_id

        risk_evaluations: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.risk_evaluations, Unset):
            risk_evaluations = []
            for risk_evaluations_item_data in self.risk_evaluations:
                risk_evaluations_item = risk_evaluations_item_data.to_dict()
                risk_evaluations.append(risk_evaluations_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "test_id": test_id,
            }
        )
        if parent_test_id is not UNSET:
            field_dict["parent_test_id"] = parent_test_id
        if risk_evaluations is not UNSET:
            field_dict["risk_evaluations"] = risk_evaluations

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.experiment_download_data_schema_item_messages_item_snowglobe_data_risk_evaluations_item import (
            ExperimentDownloadDataSchemaItemMessagesItemSnowglobeDataRiskEvaluationsItem,
        )

        d = dict(src_dict)
        test_id = d.pop("test_id")

        def _parse_parent_test_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        parent_test_id = _parse_parent_test_id(d.pop("parent_test_id", UNSET))

        risk_evaluations = []
        _risk_evaluations = d.pop("risk_evaluations", UNSET)
        for risk_evaluations_item_data in _risk_evaluations or []:
            risk_evaluations_item = ExperimentDownloadDataSchemaItemMessagesItemSnowglobeDataRiskEvaluationsItem.from_dict(
                risk_evaluations_item_data
            )

            risk_evaluations.append(risk_evaluations_item)

        experiment_download_data_schema_item_messages_item_snowglobe_data = cls(
            test_id=test_id,
            parent_test_id=parent_test_id,
            risk_evaluations=risk_evaluations,
        )

        experiment_download_data_schema_item_messages_item_snowglobe_data.additional_properties = d
        return experiment_download_data_schema_item_messages_item_snowglobe_data

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
