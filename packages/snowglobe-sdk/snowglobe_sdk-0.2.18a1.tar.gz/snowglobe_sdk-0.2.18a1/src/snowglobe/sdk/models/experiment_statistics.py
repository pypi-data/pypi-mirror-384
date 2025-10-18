from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

from typing import Union


T = TypeVar("T", bound="ExperimentStatistics")


@_attrs_define
class ExperimentStatistics:
    """
    Attributes:
        conversation_count (Union[Unset, float]):
        root_conversation_count (Union[Unset, float]):
        adapted_conversations_count (Union[Unset, float]):
        total_tests_count (Union[Unset, float]):
        original_tests_count (Union[Unset, float]):
        adaptability_tests_count (Union[Unset, float]):
        incomplete_tests_count (Union[Unset, float]):
        incomplete_original_tests_count (Union[Unset, float]):
        complete_original_tests_count (Union[Unset, float]):
        incomplete_adaptability_tests_count (Union[Unset, float]):
        unevaluated_tests_count (Union[Unset, float]):
        incomplete_evaluations_count (Union[Unset, float]):
        original_evaluations_count (Union[Unset, float]):
        target_total_evaluations (Union[Unset, float]):
        total_evaluations_count (Union[Unset, float]):
        target_original_total_evaluations (Union[Unset, float]):
    """

    conversation_count: Union[Unset, float] = UNSET
    root_conversation_count: Union[Unset, float] = UNSET
    adapted_conversations_count: Union[Unset, float] = UNSET
    total_tests_count: Union[Unset, float] = UNSET
    original_tests_count: Union[Unset, float] = UNSET
    adaptability_tests_count: Union[Unset, float] = UNSET
    incomplete_tests_count: Union[Unset, float] = UNSET
    incomplete_original_tests_count: Union[Unset, float] = UNSET
    complete_original_tests_count: Union[Unset, float] = UNSET
    incomplete_adaptability_tests_count: Union[Unset, float] = UNSET
    unevaluated_tests_count: Union[Unset, float] = UNSET
    incomplete_evaluations_count: Union[Unset, float] = UNSET
    original_evaluations_count: Union[Unset, float] = UNSET
    target_total_evaluations: Union[Unset, float] = UNSET
    total_evaluations_count: Union[Unset, float] = UNSET
    target_original_total_evaluations: Union[Unset, float] = UNSET

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

        field_dict.update({})
        if conversation_count is not UNSET:
            field_dict["conversation_count"] = conversation_count
        if root_conversation_count is not UNSET:
            field_dict["root_conversation_count"] = root_conversation_count
        if adapted_conversations_count is not UNSET:
            field_dict["adapted_conversations_count"] = adapted_conversations_count
        if total_tests_count is not UNSET:
            field_dict["total_tests_count"] = total_tests_count
        if original_tests_count is not UNSET:
            field_dict["original_tests_count"] = original_tests_count
        if adaptability_tests_count is not UNSET:
            field_dict["adaptability_tests_count"] = adaptability_tests_count
        if incomplete_tests_count is not UNSET:
            field_dict["incomplete_tests_count"] = incomplete_tests_count
        if incomplete_original_tests_count is not UNSET:
            field_dict["incomplete_original_tests_count"] = (
                incomplete_original_tests_count
            )
        if complete_original_tests_count is not UNSET:
            field_dict["complete_original_tests_count"] = complete_original_tests_count
        if incomplete_adaptability_tests_count is not UNSET:
            field_dict["incomplete_adaptability_tests_count"] = (
                incomplete_adaptability_tests_count
            )
        if unevaluated_tests_count is not UNSET:
            field_dict["unevaluated_tests_count"] = unevaluated_tests_count
        if incomplete_evaluations_count is not UNSET:
            field_dict["incomplete_evaluations_count"] = incomplete_evaluations_count
        if original_evaluations_count is not UNSET:
            field_dict["original_evaluations_count"] = original_evaluations_count
        if target_total_evaluations is not UNSET:
            field_dict["target_total_evaluations"] = target_total_evaluations
        if total_evaluations_count is not UNSET:
            field_dict["total_evaluations_count"] = total_evaluations_count
        if target_original_total_evaluations is not UNSET:
            field_dict["target_original_total_evaluations"] = (
                target_original_total_evaluations
            )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        conversation_count = d.pop("conversation_count", UNSET)

        root_conversation_count = d.pop("root_conversation_count", UNSET)

        adapted_conversations_count = d.pop("adapted_conversations_count", UNSET)

        total_tests_count = d.pop("total_tests_count", UNSET)

        original_tests_count = d.pop("original_tests_count", UNSET)

        adaptability_tests_count = d.pop("adaptability_tests_count", UNSET)

        incomplete_tests_count = d.pop("incomplete_tests_count", UNSET)

        incomplete_original_tests_count = d.pop(
            "incomplete_original_tests_count", UNSET
        )

        complete_original_tests_count = d.pop("complete_original_tests_count", UNSET)

        incomplete_adaptability_tests_count = d.pop(
            "incomplete_adaptability_tests_count", UNSET
        )

        unevaluated_tests_count = d.pop("unevaluated_tests_count", UNSET)

        incomplete_evaluations_count = d.pop("incomplete_evaluations_count", UNSET)

        original_evaluations_count = d.pop("original_evaluations_count", UNSET)

        target_total_evaluations = d.pop("target_total_evaluations", UNSET)

        total_evaluations_count = d.pop("total_evaluations_count", UNSET)

        target_original_total_evaluations = d.pop(
            "target_original_total_evaluations", UNSET
        )

        experiment_statistics = cls(
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

        return experiment_statistics
