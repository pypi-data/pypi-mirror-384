from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define

from ..types import UNSET, Unset

from dateutil.parser import isoparse
from typing import cast
from typing import Union
from uuid import UUID
import datetime

if TYPE_CHECKING:
    from ..models.test_with_risk_evaluations_tactics_type_0_item import (
        TestWithRiskEvaluationsTacticsType0Item,
    )
    from ..models.test_with_risk_evaluations_turn_metadata_type_0_type_1 import (
        TestWithRiskEvaluationsTurnMetadataType0Type1,
    )
    from ..models.test_with_risk_evaluations_risk_evaluations_item import (
        TestWithRiskEvaluationsRiskEvaluationsItem,
    )


T = TypeVar("T", bound="TestWithRiskEvaluations")


@_attrs_define
class TestWithRiskEvaluations:
    """
    Attributes:
        id (UUID):
        persona_record_id (Union[None, UUID]):
        experiment_id (UUID):
        is_original (bool):
        created_at (datetime.datetime):
        retries (int):
        is_adapted_conversation (bool):
        state_updated_at (datetime.datetime):
        response_retries (int):
        prompt_retries (int):
        auto_fixed (bool):
        active_branch (bool):
        turn_metadata (Union['TestWithRiskEvaluationsTurnMetadataType0Type1', None, bool, float, list[Any], str]):
        conversation_group_id (Union[None, UUID]):
        risk_evaluations (list['TestWithRiskEvaluationsRiskEvaluationsItem']):
        score (Union[None, Unset, int]):
        score_comment (Union[None, Unset, str]):
        prompt (Union[None, Unset, str]):
        response (Union[None, Unset, str]):
        tactics (Union[None, Unset, list['TestWithRiskEvaluationsTacticsType0Item']]):
        persona (Union[None, Unset, str]):
        topic (Union[None, Unset, str]):
        risk_type (Union[None, Unset, str]):
        generation_method (Union[None, Unset, str]):
        parent_test_id (Union[None, UUID, Unset]):
        conversation_id (Union[None, UUID, Unset]):
        source_tactics (Union[Unset, list[Any]]):
        embedding (Union[None, Unset, list[float]]):
        current_depth (Union[None, Unset, int]):
        max_depth (Union[None, Unset, int]):
        original_test_id (Union[None, UUID, Unset]):
        state (Union[None, Unset, str]):
        prompt_state (Union[None, Unset, str]):
        response_state (Union[None, Unset, str]):
        validation_state (Union[None, Unset, str]):
    """

    id: UUID
    persona_record_id: Union[None, UUID]
    experiment_id: UUID
    is_original: bool
    created_at: datetime.datetime
    retries: int
    is_adapted_conversation: bool
    state_updated_at: datetime.datetime
    response_retries: int
    prompt_retries: int
    auto_fixed: bool
    active_branch: bool
    turn_metadata: Union[
        "TestWithRiskEvaluationsTurnMetadataType0Type1",
        None,
        bool,
        float,
        list[Any],
        str,
    ]
    conversation_group_id: Union[None, UUID]
    risk_evaluations: list["TestWithRiskEvaluationsRiskEvaluationsItem"]
    score: Union[None, Unset, int] = UNSET
    score_comment: Union[None, Unset, str] = UNSET
    prompt: Union[None, Unset, str] = UNSET
    response: Union[None, Unset, str] = UNSET
    tactics: Union[None, Unset, list["TestWithRiskEvaluationsTacticsType0Item"]] = UNSET
    persona: Union[None, Unset, str] = UNSET
    topic: Union[None, Unset, str] = UNSET
    risk_type: Union[None, Unset, str] = UNSET
    generation_method: Union[None, Unset, str] = UNSET
    parent_test_id: Union[None, UUID, Unset] = UNSET
    conversation_id: Union[None, UUID, Unset] = UNSET
    source_tactics: Union[Unset, list[Any]] = UNSET
    embedding: Union[None, Unset, list[float]] = UNSET
    current_depth: Union[None, Unset, int] = UNSET
    max_depth: Union[None, Unset, int] = UNSET
    original_test_id: Union[None, UUID, Unset] = UNSET
    state: Union[None, Unset, str] = UNSET
    prompt_state: Union[None, Unset, str] = UNSET
    response_state: Union[None, Unset, str] = UNSET
    validation_state: Union[None, Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.test_with_risk_evaluations_turn_metadata_type_0_type_1 import (
            TestWithRiskEvaluationsTurnMetadataType0Type1,
        )

        id = str(self.id)

        persona_record_id: Union[None, str]
        if isinstance(self.persona_record_id, UUID):
            persona_record_id = str(self.persona_record_id)
        else:
            persona_record_id = self.persona_record_id

        experiment_id = str(self.experiment_id)

        is_original = self.is_original

        created_at = self.created_at.isoformat()

        retries = self.retries

        is_adapted_conversation = self.is_adapted_conversation

        state_updated_at = self.state_updated_at.isoformat()

        response_retries = self.response_retries

        prompt_retries = self.prompt_retries

        auto_fixed = self.auto_fixed

        active_branch = self.active_branch

        turn_metadata: Union[None, bool, dict[str, Any], float, list[Any], str]
        if isinstance(
            self.turn_metadata, TestWithRiskEvaluationsTurnMetadataType0Type1
        ):
            turn_metadata = self.turn_metadata.to_dict()
        elif isinstance(self.turn_metadata, list):
            turn_metadata = self.turn_metadata

        else:
            turn_metadata = self.turn_metadata

        conversation_group_id: Union[None, str]
        if isinstance(self.conversation_group_id, UUID):
            conversation_group_id = str(self.conversation_group_id)
        else:
            conversation_group_id = self.conversation_group_id

        risk_evaluations = []
        for risk_evaluations_item_data in self.risk_evaluations:
            risk_evaluations_item = risk_evaluations_item_data.to_dict()
            risk_evaluations.append(risk_evaluations_item)

        score: Union[None, Unset, int]
        if isinstance(self.score, Unset):
            score = UNSET
        else:
            score = self.score

        score_comment: Union[None, Unset, str]
        if isinstance(self.score_comment, Unset):
            score_comment = UNSET
        else:
            score_comment = self.score_comment

        prompt: Union[None, Unset, str]
        if isinstance(self.prompt, Unset):
            prompt = UNSET
        else:
            prompt = self.prompt

        response: Union[None, Unset, str]
        if isinstance(self.response, Unset):
            response = UNSET
        else:
            response = self.response

        tactics: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.tactics, Unset):
            tactics = UNSET
        elif isinstance(self.tactics, list):
            tactics = []
            for tactics_type_0_item_data in self.tactics:
                tactics_type_0_item = tactics_type_0_item_data.to_dict()
                tactics.append(tactics_type_0_item)

        else:
            tactics = self.tactics

        persona: Union[None, Unset, str]
        if isinstance(self.persona, Unset):
            persona = UNSET
        else:
            persona = self.persona

        topic: Union[None, Unset, str]
        if isinstance(self.topic, Unset):
            topic = UNSET
        else:
            topic = self.topic

        risk_type: Union[None, Unset, str]
        if isinstance(self.risk_type, Unset):
            risk_type = UNSET
        else:
            risk_type = self.risk_type

        generation_method: Union[None, Unset, str]
        if isinstance(self.generation_method, Unset):
            generation_method = UNSET
        else:
            generation_method = self.generation_method

        parent_test_id: Union[None, Unset, str]
        if isinstance(self.parent_test_id, Unset):
            parent_test_id = UNSET
        elif isinstance(self.parent_test_id, UUID):
            parent_test_id = str(self.parent_test_id)
        else:
            parent_test_id = self.parent_test_id

        conversation_id: Union[None, Unset, str]
        if isinstance(self.conversation_id, Unset):
            conversation_id = UNSET
        elif isinstance(self.conversation_id, UUID):
            conversation_id = str(self.conversation_id)
        else:
            conversation_id = self.conversation_id

        source_tactics: Union[Unset, list[Any]] = UNSET
        if not isinstance(self.source_tactics, Unset):
            source_tactics = self.source_tactics

        embedding: Union[None, Unset, list[float]]
        if isinstance(self.embedding, Unset):
            embedding = UNSET
        elif isinstance(self.embedding, list):
            embedding = self.embedding

        else:
            embedding = self.embedding

        current_depth: Union[None, Unset, int]
        if isinstance(self.current_depth, Unset):
            current_depth = UNSET
        else:
            current_depth = self.current_depth

        max_depth: Union[None, Unset, int]
        if isinstance(self.max_depth, Unset):
            max_depth = UNSET
        else:
            max_depth = self.max_depth

        original_test_id: Union[None, Unset, str]
        if isinstance(self.original_test_id, Unset):
            original_test_id = UNSET
        elif isinstance(self.original_test_id, UUID):
            original_test_id = str(self.original_test_id)
        else:
            original_test_id = self.original_test_id

        state: Union[None, Unset, str]
        if isinstance(self.state, Unset):
            state = UNSET
        else:
            state = self.state

        prompt_state: Union[None, Unset, str]
        if isinstance(self.prompt_state, Unset):
            prompt_state = UNSET
        else:
            prompt_state = self.prompt_state

        response_state: Union[None, Unset, str]
        if isinstance(self.response_state, Unset):
            response_state = UNSET
        else:
            response_state = self.response_state

        validation_state: Union[None, Unset, str]
        if isinstance(self.validation_state, Unset):
            validation_state = UNSET
        else:
            validation_state = self.validation_state

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "id": id,
                "persona_record_id": persona_record_id,
                "experiment_id": experiment_id,
                "isOriginal": is_original,
                "created_at": created_at,
                "retries": retries,
                "isAdaptedConversation": is_adapted_conversation,
                "state_updated_at": state_updated_at,
                "response_retries": response_retries,
                "prompt_retries": prompt_retries,
                "auto_fixed": auto_fixed,
                "active_branch": active_branch,
                "turn_metadata": turn_metadata,
                "conversation_group_id": conversation_group_id,
                "risk_evaluations": risk_evaluations,
            }
        )
        if score is not UNSET:
            field_dict["score"] = score
        if score_comment is not UNSET:
            field_dict["score_comment"] = score_comment
        if prompt is not UNSET:
            field_dict["prompt"] = prompt
        if response is not UNSET:
            field_dict["response"] = response
        if tactics is not UNSET:
            field_dict["tactics"] = tactics
        if persona is not UNSET:
            field_dict["persona"] = persona
        if topic is not UNSET:
            field_dict["topic"] = topic
        if risk_type is not UNSET:
            field_dict["riskType"] = risk_type
        if generation_method is not UNSET:
            field_dict["generation_method"] = generation_method
        if parent_test_id is not UNSET:
            field_dict["parent_test_id"] = parent_test_id
        if conversation_id is not UNSET:
            field_dict["conversation_id"] = conversation_id
        if source_tactics is not UNSET:
            field_dict["sourceTactics"] = source_tactics
        if embedding is not UNSET:
            field_dict["embedding"] = embedding
        if current_depth is not UNSET:
            field_dict["currentDepth"] = current_depth
        if max_depth is not UNSET:
            field_dict["maxDepth"] = max_depth
        if original_test_id is not UNSET:
            field_dict["originalTestId"] = original_test_id
        if state is not UNSET:
            field_dict["state"] = state
        if prompt_state is not UNSET:
            field_dict["prompt_state"] = prompt_state
        if response_state is not UNSET:
            field_dict["response_state"] = response_state
        if validation_state is not UNSET:
            field_dict["validation_state"] = validation_state

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.test_with_risk_evaluations_tactics_type_0_item import (
            TestWithRiskEvaluationsTacticsType0Item,
        )
        from ..models.test_with_risk_evaluations_turn_metadata_type_0_type_1 import (
            TestWithRiskEvaluationsTurnMetadataType0Type1,
        )
        from ..models.test_with_risk_evaluations_risk_evaluations_item import (
            TestWithRiskEvaluationsRiskEvaluationsItem,
        )

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        def _parse_persona_record_id(data: object) -> Union[None, UUID]:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                persona_record_id_type_0 = UUID(data)

                return persona_record_id_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, UUID], data)

        persona_record_id = _parse_persona_record_id(d.pop("persona_record_id"))

        experiment_id = UUID(d.pop("experiment_id"))

        is_original = d.pop("isOriginal")

        created_at = isoparse(d.pop("created_at"))

        retries = d.pop("retries")

        is_adapted_conversation = d.pop("isAdaptedConversation")

        state_updated_at = isoparse(d.pop("state_updated_at"))

        response_retries = d.pop("response_retries")

        prompt_retries = d.pop("prompt_retries")

        auto_fixed = d.pop("auto_fixed")

        active_branch = d.pop("active_branch")

        def _parse_turn_metadata(
            data: object,
        ) -> Union[
            "TestWithRiskEvaluationsTurnMetadataType0Type1",
            None,
            bool,
            float,
            list[Any],
            str,
        ]:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                turn_metadata_type_0_type_1 = (
                    TestWithRiskEvaluationsTurnMetadataType0Type1.from_dict(data)
                )

                return turn_metadata_type_0_type_1
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, list):
                    raise TypeError()
                turn_metadata_type_0_type_2 = cast(list[Any], data)

                return turn_metadata_type_0_type_2
            except:  # noqa: E722
                pass
            return cast(
                Union[
                    "TestWithRiskEvaluationsTurnMetadataType0Type1",
                    None,
                    bool,
                    float,
                    list[Any],
                    str,
                ],
                data,
            )

        turn_metadata = _parse_turn_metadata(d.pop("turn_metadata"))

        def _parse_conversation_group_id(data: object) -> Union[None, UUID]:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                conversation_group_id_type_0 = UUID(data)

                return conversation_group_id_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, UUID], data)

        conversation_group_id = _parse_conversation_group_id(
            d.pop("conversation_group_id")
        )

        risk_evaluations = []
        _risk_evaluations = d.pop("risk_evaluations")
        for risk_evaluations_item_data in _risk_evaluations:
            risk_evaluations_item = (
                TestWithRiskEvaluationsRiskEvaluationsItem.from_dict(
                    risk_evaluations_item_data
                )
            )

            risk_evaluations.append(risk_evaluations_item)

        def _parse_score(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        score = _parse_score(d.pop("score", UNSET))

        def _parse_score_comment(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        score_comment = _parse_score_comment(d.pop("score_comment", UNSET))

        def _parse_prompt(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        prompt = _parse_prompt(d.pop("prompt", UNSET))

        def _parse_response(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        response = _parse_response(d.pop("response", UNSET))

        def _parse_tactics(
            data: object,
        ) -> Union[None, Unset, list["TestWithRiskEvaluationsTacticsType0Item"]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                tactics_type_0 = []
                _tactics_type_0 = data
                for tactics_type_0_item_data in _tactics_type_0:
                    tactics_type_0_item = (
                        TestWithRiskEvaluationsTacticsType0Item.from_dict(
                            tactics_type_0_item_data
                        )
                    )

                    tactics_type_0.append(tactics_type_0_item)

                return tactics_type_0
            except:  # noqa: E722
                pass
            return cast(
                Union[None, Unset, list["TestWithRiskEvaluationsTacticsType0Item"]],
                data,
            )

        tactics = _parse_tactics(d.pop("tactics", UNSET))

        def _parse_persona(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        persona = _parse_persona(d.pop("persona", UNSET))

        def _parse_topic(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        topic = _parse_topic(d.pop("topic", UNSET))

        def _parse_risk_type(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        risk_type = _parse_risk_type(d.pop("riskType", UNSET))

        def _parse_generation_method(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        generation_method = _parse_generation_method(d.pop("generation_method", UNSET))

        def _parse_parent_test_id(data: object) -> Union[None, UUID, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                parent_test_id_type_0 = UUID(data)

                return parent_test_id_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, UUID, Unset], data)

        parent_test_id = _parse_parent_test_id(d.pop("parent_test_id", UNSET))

        def _parse_conversation_id(data: object) -> Union[None, UUID, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                conversation_id_type_0 = UUID(data)

                return conversation_id_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, UUID, Unset], data)

        conversation_id = _parse_conversation_id(d.pop("conversation_id", UNSET))

        source_tactics = cast(list[Any], d.pop("sourceTactics", UNSET))

        def _parse_embedding(data: object) -> Union[None, Unset, list[float]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                embedding_type_0 = cast(list[float], data)

                return embedding_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[float]], data)

        embedding = _parse_embedding(d.pop("embedding", UNSET))

        def _parse_current_depth(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        current_depth = _parse_current_depth(d.pop("currentDepth", UNSET))

        def _parse_max_depth(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        max_depth = _parse_max_depth(d.pop("maxDepth", UNSET))

        def _parse_original_test_id(data: object) -> Union[None, UUID, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                original_test_id_type_0 = UUID(data)

                return original_test_id_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, UUID, Unset], data)

        original_test_id = _parse_original_test_id(d.pop("originalTestId", UNSET))

        def _parse_state(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        state = _parse_state(d.pop("state", UNSET))

        def _parse_prompt_state(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        prompt_state = _parse_prompt_state(d.pop("prompt_state", UNSET))

        def _parse_response_state(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        response_state = _parse_response_state(d.pop("response_state", UNSET))

        def _parse_validation_state(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        validation_state = _parse_validation_state(d.pop("validation_state", UNSET))

        test_with_risk_evaluations = cls(
            id=id,
            persona_record_id=persona_record_id,
            experiment_id=experiment_id,
            is_original=is_original,
            created_at=created_at,
            retries=retries,
            is_adapted_conversation=is_adapted_conversation,
            state_updated_at=state_updated_at,
            response_retries=response_retries,
            prompt_retries=prompt_retries,
            auto_fixed=auto_fixed,
            active_branch=active_branch,
            turn_metadata=turn_metadata,
            conversation_group_id=conversation_group_id,
            risk_evaluations=risk_evaluations,
            score=score,
            score_comment=score_comment,
            prompt=prompt,
            response=response,
            tactics=tactics,
            persona=persona,
            topic=topic,
            risk_type=risk_type,
            generation_method=generation_method,
            parent_test_id=parent_test_id,
            conversation_id=conversation_id,
            source_tactics=source_tactics,
            embedding=embedding,
            current_depth=current_depth,
            max_depth=max_depth,
            original_test_id=original_test_id,
            state=state,
            prompt_state=prompt_state,
            response_state=response_state,
            validation_state=validation_state,
        )

        return test_with_risk_evaluations
