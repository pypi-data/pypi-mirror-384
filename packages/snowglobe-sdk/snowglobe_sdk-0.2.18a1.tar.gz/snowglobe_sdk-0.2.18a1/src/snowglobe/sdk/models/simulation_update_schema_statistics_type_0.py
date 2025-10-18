from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field


T = TypeVar("T", bound="SimulationUpdateSchemaStatisticsType0")


@_attrs_define
class SimulationUpdateSchemaStatisticsType0:
    """
    Attributes:
        conversation_count (float):
        root_conversation_count (float):
        adapted_conversations_count (float):
        total_tests_count (float):
        original_tests_count (float):
        adaptability_tests_count (float):
        incomplete_tests_count (float):
        incomplete_original_tests_count (float):
        complete_original_tests_count (float):
        incomplete_adaptability_tests_count (float):
        unevaluated_tests_count (float):
        incomplete_evaluations_count (float):
        original_evaluations_count (float):
        target_total_evaluations (float):
        total_evaluations_count (float):
        target_original_total_evaluations (float):
    """

    conversation_count: float
    root_conversation_count: float
    adapted_conversations_count: float
    total_tests_count: float
    original_tests_count: float
    adaptability_tests_count: float
    incomplete_tests_count: float
    incomplete_original_tests_count: float
    complete_original_tests_count: float
    incomplete_adaptability_tests_count: float
    unevaluated_tests_count: float
    incomplete_evaluations_count: float
    original_evaluations_count: float
    target_total_evaluations: float
    total_evaluations_count: float
    target_original_total_evaluations: float
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        conversation_count = self.conversation_count

        root_conversation_count = self.root_conversation_count

        adapted_conversations_count = self.adapted_conversations_count

        total_tests_count = self.total_tests_count

        original_tests_count = self.original_tests_count

        adaptability_tests_count = self.adaptability_tests_count

        incomplete_tests_count = self.incomplete_tests_count

        incomplete_original_tests_count = self.incomplete_original_tests_count

        complete_original_tests_count = self.complete_original_tests_count

        incomplete_adaptability_tests_count = self.incomplete_adaptability_tests_count

        unevaluated_tests_count = self.unevaluated_tests_count

        incomplete_evaluations_count = self.incomplete_evaluations_count

        original_evaluations_count = self.original_evaluations_count

        target_total_evaluations = self.target_total_evaluations

        total_evaluations_count = self.total_evaluations_count

        target_original_total_evaluations = self.target_original_total_evaluations

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "conversation_count": conversation_count,
                "root_conversation_count": root_conversation_count,
                "adapted_conversations_count": adapted_conversations_count,
                "total_tests_count": total_tests_count,
                "original_tests_count": original_tests_count,
                "adaptability_tests_count": adaptability_tests_count,
                "incomplete_tests_count": incomplete_tests_count,
                "incomplete_original_tests_count": incomplete_original_tests_count,
                "complete_original_tests_count": complete_original_tests_count,
                "incomplete_adaptability_tests_count": incomplete_adaptability_tests_count,
                "unevaluated_tests_count": unevaluated_tests_count,
                "incomplete_evaluations_count": incomplete_evaluations_count,
                "original_evaluations_count": original_evaluations_count,
                "target_total_evaluations": target_total_evaluations,
                "total_evaluations_count": total_evaluations_count,
                "target_original_total_evaluations": target_original_total_evaluations,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        conversation_count = d.pop("conversation_count")

        root_conversation_count = d.pop("root_conversation_count")

        adapted_conversations_count = d.pop("adapted_conversations_count")

        total_tests_count = d.pop("total_tests_count")

        original_tests_count = d.pop("original_tests_count")

        adaptability_tests_count = d.pop("adaptability_tests_count")

        incomplete_tests_count = d.pop("incomplete_tests_count")

        incomplete_original_tests_count = d.pop("incomplete_original_tests_count")

        complete_original_tests_count = d.pop("complete_original_tests_count")

        incomplete_adaptability_tests_count = d.pop(
            "incomplete_adaptability_tests_count"
        )

        unevaluated_tests_count = d.pop("unevaluated_tests_count")

        incomplete_evaluations_count = d.pop("incomplete_evaluations_count")

        original_evaluations_count = d.pop("original_evaluations_count")

        target_total_evaluations = d.pop("target_total_evaluations")

        total_evaluations_count = d.pop("total_evaluations_count")

        target_original_total_evaluations = d.pop("target_original_total_evaluations")

        simulation_update_schema_statistics_type_0 = cls(
            conversation_count=conversation_count,
            root_conversation_count=root_conversation_count,
            adapted_conversations_count=adapted_conversations_count,
            total_tests_count=total_tests_count,
            original_tests_count=original_tests_count,
            adaptability_tests_count=adaptability_tests_count,
            incomplete_tests_count=incomplete_tests_count,
            incomplete_original_tests_count=incomplete_original_tests_count,
            complete_original_tests_count=complete_original_tests_count,
            incomplete_adaptability_tests_count=incomplete_adaptability_tests_count,
            unevaluated_tests_count=unevaluated_tests_count,
            incomplete_evaluations_count=incomplete_evaluations_count,
            original_evaluations_count=original_evaluations_count,
            target_total_evaluations=target_total_evaluations,
            total_evaluations_count=total_evaluations_count,
            target_original_total_evaluations=target_original_total_evaluations,
        )

        simulation_update_schema_statistics_type_0.additional_properties = d
        return simulation_update_schema_statistics_type_0

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
