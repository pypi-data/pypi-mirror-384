from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from dateutil.parser import isoparse
from typing import cast
from typing import Union
from typing import Literal
from uuid import UUID
import datetime

if TYPE_CHECKING:
    from ..models.experiment_update_schema_statistics_type_0 import (
        ExperimentUpdateSchemaStatisticsType0,
    )
    from ..models.experiment_update_schema_persona_summaries_item import (
        ExperimentUpdateSchemaPersonaSummariesItem,
    )
    from ..models.experiment_update_schema_source_data_type_0 import (
        ExperimentUpdateSchemaSourceDataType0,
    )
    from ..models.experiment_update_schema_report_data_type_0 import (
        ExperimentUpdateSchemaReportDataType0,
    )
    from ..models.experiment_update_schema_risks_item import (
        ExperimentUpdateSchemaRisksItem,
    )


T = TypeVar("T", bound="ExperimentUpdateSchema")


@_attrs_define
class ExperimentUpdateSchema:
    """
    Attributes:
        id (Union[Unset, UUID]):
        name (Union[Unset, str]):
        description (Union[None, Unset, str]):
        role (Union[Unset, str]):
        state (Union[Literal['ADAPTATION_COMPLETE'], Literal['ADAPTATION_FAILED'], Literal['ADAPTATION_IN_PROGRESS'],
            Literal['ADAPTATION_WAITING_TO_START'], Literal['DRAFT'], Literal['EVALUATION_COMPLETE'],
            Literal['EVALUATION_FAILED'], Literal['EVALUATION_IN_PROGRESS'], Literal['EVALUATION_PARTIALLY_COMPLETE'],
            Literal['EXPERIMENT_COMPLETED'], Literal['EXPERIMENT_FAILED'], Literal['EXPERIMENT_PARTIALLY_COMPLETE'],
            Literal['EXPERIMENT_STARTED'], Literal['GENERATION_COMPLETE'], Literal['GENERATION_FAILED'],
            Literal['GENERATION_IN_PROGRESS'], Literal['QUEUED'], Literal['VALIDATION_COMPLETE'],
            Literal['VALIDATION_FAILED'], Literal['VALIDATION_IN_PROGRESS'], Literal['VALIDATION_PARTIALLY_COMPLETE'], None,
            Unset]):
        state_num (Union[None, Unset, int]):
        status (Union[None, Unset, str]):
        statistics (Union['ExperimentUpdateSchemaStatisticsType0', None, Unset]):
        status_reason (Union[None, Unset, str]):
        is_completed (Union[None, Unset, bool]):
        generation_status (Union[None, Unset, str]):
        evaluation_status (Union[None, Unset, str]):
        validation_status (Union[None, Unset, str]):
        conversation_adaption_status (Union[None, Unset, str]):
        report_data (Union['ExperimentUpdateSchemaReportDataType0', None, Unset]):
        source_data (Union['ExperimentUpdateSchemaSourceDataType0', None, Unset]):
        topic_tree (Union[None, Unset, list[list[Union[float, str]]]]):
        use_cases (Union[None, Unset, str]):
        user_description (Union[None, Unset, str]):
        state_updated_at (Union[Unset, datetime.datetime]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
        created_by (Union[None, Unset, str]):
        started_at (Union[None, Unset, datetime.datetime]):
        completed_at (Union[None, Unset, datetime.datetime]):
        test_count (Union[None, Unset, int]):
        application_id (Union[None, Unset, str]):
        app_id (Union[None, Unset, str]):
        is_template (Union[Unset, bool]):
        created_by_user (Union[None, Unset, str]):
        persona_summaries (Union[Unset, list['ExperimentUpdateSchemaPersonaSummariesItem']]):
        marked_for_deletion_at (Union[None, Unset, datetime.datetime]):
        risks (Union[Unset, list['ExperimentUpdateSchemaRisksItem']]):
    """

    id: Union[Unset, UUID] = UNSET
    name: Union[Unset, str] = UNSET
    description: Union[None, Unset, str] = UNSET
    role: Union[Unset, str] = UNSET
    state: Union[
        Literal["ADAPTATION_COMPLETE"],
        Literal["ADAPTATION_FAILED"],
        Literal["ADAPTATION_IN_PROGRESS"],
        Literal["ADAPTATION_WAITING_TO_START"],
        Literal["DRAFT"],
        Literal["EVALUATION_COMPLETE"],
        Literal["EVALUATION_FAILED"],
        Literal["EVALUATION_IN_PROGRESS"],
        Literal["EVALUATION_PARTIALLY_COMPLETE"],
        Literal["EXPERIMENT_COMPLETED"],
        Literal["EXPERIMENT_FAILED"],
        Literal["EXPERIMENT_PARTIALLY_COMPLETE"],
        Literal["EXPERIMENT_STARTED"],
        Literal["GENERATION_COMPLETE"],
        Literal["GENERATION_FAILED"],
        Literal["GENERATION_IN_PROGRESS"],
        Literal["QUEUED"],
        Literal["VALIDATION_COMPLETE"],
        Literal["VALIDATION_FAILED"],
        Literal["VALIDATION_IN_PROGRESS"],
        Literal["VALIDATION_PARTIALLY_COMPLETE"],
        None,
        Unset,
    ] = UNSET
    state_num: Union[None, Unset, int] = UNSET
    status: Union[None, Unset, str] = UNSET
    statistics: Union["ExperimentUpdateSchemaStatisticsType0", None, Unset] = UNSET
    status_reason: Union[None, Unset, str] = UNSET
    is_completed: Union[None, Unset, bool] = UNSET
    generation_status: Union[None, Unset, str] = UNSET
    evaluation_status: Union[None, Unset, str] = UNSET
    validation_status: Union[None, Unset, str] = UNSET
    conversation_adaption_status: Union[None, Unset, str] = UNSET
    report_data: Union["ExperimentUpdateSchemaReportDataType0", None, Unset] = UNSET
    source_data: Union["ExperimentUpdateSchemaSourceDataType0", None, Unset] = UNSET
    topic_tree: Union[None, Unset, list[list[Union[float, str]]]] = UNSET
    use_cases: Union[None, Unset, str] = UNSET
    user_description: Union[None, Unset, str] = UNSET
    state_updated_at: Union[Unset, datetime.datetime] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    created_by: Union[None, Unset, str] = UNSET
    started_at: Union[None, Unset, datetime.datetime] = UNSET
    completed_at: Union[None, Unset, datetime.datetime] = UNSET
    test_count: Union[None, Unset, int] = UNSET
    application_id: Union[None, Unset, str] = UNSET
    app_id: Union[None, Unset, str] = UNSET
    is_template: Union[Unset, bool] = UNSET
    created_by_user: Union[None, Unset, str] = UNSET
    persona_summaries: Union[
        Unset, list["ExperimentUpdateSchemaPersonaSummariesItem"]
    ] = UNSET
    marked_for_deletion_at: Union[None, Unset, datetime.datetime] = UNSET
    risks: Union[Unset, list["ExperimentUpdateSchemaRisksItem"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.experiment_update_schema_statistics_type_0 import (
            ExperimentUpdateSchemaStatisticsType0,
        )
        from ..models.experiment_update_schema_source_data_type_0 import (
            ExperimentUpdateSchemaSourceDataType0,
        )
        from ..models.experiment_update_schema_report_data_type_0 import (
            ExperimentUpdateSchemaReportDataType0,
        )

        id: Union[Unset, str] = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        name = self.name

        description: Union[None, Unset, str]
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        role = self.role

        state: Union[
            Literal["ADAPTATION_COMPLETE"],
            Literal["ADAPTATION_FAILED"],
            Literal["ADAPTATION_IN_PROGRESS"],
            Literal["ADAPTATION_WAITING_TO_START"],
            Literal["DRAFT"],
            Literal["EVALUATION_COMPLETE"],
            Literal["EVALUATION_FAILED"],
            Literal["EVALUATION_IN_PROGRESS"],
            Literal["EVALUATION_PARTIALLY_COMPLETE"],
            Literal["EXPERIMENT_COMPLETED"],
            Literal["EXPERIMENT_FAILED"],
            Literal["EXPERIMENT_PARTIALLY_COMPLETE"],
            Literal["EXPERIMENT_STARTED"],
            Literal["GENERATION_COMPLETE"],
            Literal["GENERATION_FAILED"],
            Literal["GENERATION_IN_PROGRESS"],
            Literal["QUEUED"],
            Literal["VALIDATION_COMPLETE"],
            Literal["VALIDATION_FAILED"],
            Literal["VALIDATION_IN_PROGRESS"],
            Literal["VALIDATION_PARTIALLY_COMPLETE"],
            None,
            Unset,
        ]
        if isinstance(self.state, Unset):
            state = UNSET
        else:
            state = self.state

        state_num: Union[None, Unset, int]
        if isinstance(self.state_num, Unset):
            state_num = UNSET
        else:
            state_num = self.state_num

        status: Union[None, Unset, str]
        if isinstance(self.status, Unset):
            status = UNSET
        else:
            status = self.status

        statistics: Union[None, Unset, dict[str, Any]]
        if isinstance(self.statistics, Unset):
            statistics = UNSET
        elif isinstance(self.statistics, ExperimentUpdateSchemaStatisticsType0):
            statistics = self.statistics.to_dict()
        else:
            statistics = self.statistics

        status_reason: Union[None, Unset, str]
        if isinstance(self.status_reason, Unset):
            status_reason = UNSET
        else:
            status_reason = self.status_reason

        is_completed: Union[None, Unset, bool]
        if isinstance(self.is_completed, Unset):
            is_completed = UNSET
        else:
            is_completed = self.is_completed

        generation_status: Union[None, Unset, str]
        if isinstance(self.generation_status, Unset):
            generation_status = UNSET
        else:
            generation_status = self.generation_status

        evaluation_status: Union[None, Unset, str]
        if isinstance(self.evaluation_status, Unset):
            evaluation_status = UNSET
        else:
            evaluation_status = self.evaluation_status

        validation_status: Union[None, Unset, str]
        if isinstance(self.validation_status, Unset):
            validation_status = UNSET
        else:
            validation_status = self.validation_status

        conversation_adaption_status: Union[None, Unset, str]
        if isinstance(self.conversation_adaption_status, Unset):
            conversation_adaption_status = UNSET
        else:
            conversation_adaption_status = self.conversation_adaption_status

        report_data: Union[None, Unset, dict[str, Any]]
        if isinstance(self.report_data, Unset):
            report_data = UNSET
        elif isinstance(self.report_data, ExperimentUpdateSchemaReportDataType0):
            report_data = self.report_data.to_dict()
        else:
            report_data = self.report_data

        source_data: Union[None, Unset, dict[str, Any]]
        if isinstance(self.source_data, Unset):
            source_data = UNSET
        elif isinstance(self.source_data, ExperimentUpdateSchemaSourceDataType0):
            source_data = self.source_data.to_dict()
        else:
            source_data = self.source_data

        topic_tree: Union[None, Unset, list[list[Union[float, str]]]]
        if isinstance(self.topic_tree, Unset):
            topic_tree = UNSET
        elif isinstance(self.topic_tree, list):
            topic_tree = []
            for topic_tree_type_0_item_data in self.topic_tree:
                topic_tree_type_0_item = []
                for topic_tree_type_0_item_item_data in topic_tree_type_0_item_data:
                    topic_tree_type_0_item_item: Union[float, str]
                    topic_tree_type_0_item_item = topic_tree_type_0_item_item_data
                    topic_tree_type_0_item.append(topic_tree_type_0_item_item)

                topic_tree.append(topic_tree_type_0_item)

        else:
            topic_tree = self.topic_tree

        use_cases: Union[None, Unset, str]
        if isinstance(self.use_cases, Unset):
            use_cases = UNSET
        else:
            use_cases = self.use_cases

        user_description: Union[None, Unset, str]
        if isinstance(self.user_description, Unset):
            user_description = UNSET
        else:
            user_description = self.user_description

        state_updated_at: Union[Unset, str] = UNSET
        if not isinstance(self.state_updated_at, Unset):
            state_updated_at = self.state_updated_at.isoformat()

        created_at: Union[Unset, str] = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Union[Unset, str] = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        created_by: Union[None, Unset, str]
        if isinstance(self.created_by, Unset):
            created_by = UNSET
        else:
            created_by = self.created_by

        started_at: Union[None, Unset, str]
        if isinstance(self.started_at, Unset):
            started_at = UNSET
        elif isinstance(self.started_at, datetime.datetime):
            started_at = self.started_at.isoformat()
        else:
            started_at = self.started_at

        completed_at: Union[None, Unset, str]
        if isinstance(self.completed_at, Unset):
            completed_at = UNSET
        elif isinstance(self.completed_at, datetime.datetime):
            completed_at = self.completed_at.isoformat()
        else:
            completed_at = self.completed_at

        test_count: Union[None, Unset, int]
        if isinstance(self.test_count, Unset):
            test_count = UNSET
        else:
            test_count = self.test_count

        application_id: Union[None, Unset, str]
        if isinstance(self.application_id, Unset):
            application_id = UNSET
        else:
            application_id = self.application_id

        app_id: Union[None, Unset, str]
        if isinstance(self.app_id, Unset):
            app_id = UNSET
        else:
            app_id = self.app_id

        is_template = self.is_template

        created_by_user: Union[None, Unset, str]
        if isinstance(self.created_by_user, Unset):
            created_by_user = UNSET
        else:
            created_by_user = self.created_by_user

        persona_summaries: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.persona_summaries, Unset):
            persona_summaries = []
            for persona_summaries_item_data in self.persona_summaries:
                persona_summaries_item = persona_summaries_item_data.to_dict()
                persona_summaries.append(persona_summaries_item)

        marked_for_deletion_at: Union[None, Unset, str]
        if isinstance(self.marked_for_deletion_at, Unset):
            marked_for_deletion_at = UNSET
        elif isinstance(self.marked_for_deletion_at, datetime.datetime):
            marked_for_deletion_at = self.marked_for_deletion_at.isoformat()
        else:
            marked_for_deletion_at = self.marked_for_deletion_at

        risks: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.risks, Unset):
            risks = []
            for risks_item_data in self.risks:
                risks_item = risks_item_data.to_dict()
                risks.append(risks_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if name is not UNSET:
            field_dict["name"] = name
        if description is not UNSET:
            field_dict["description"] = description
        if role is not UNSET:
            field_dict["role"] = role
        if state is not UNSET:
            field_dict["state"] = state
        if state_num is not UNSET:
            field_dict["state_num"] = state_num
        if status is not UNSET:
            field_dict["status"] = status
        if statistics is not UNSET:
            field_dict["statistics"] = statistics
        if status_reason is not UNSET:
            field_dict["status_reason"] = status_reason
        if is_completed is not UNSET:
            field_dict["is_completed"] = is_completed
        if generation_status is not UNSET:
            field_dict["generation_status"] = generation_status
        if evaluation_status is not UNSET:
            field_dict["evaluation_status"] = evaluation_status
        if validation_status is not UNSET:
            field_dict["validation_status"] = validation_status
        if conversation_adaption_status is not UNSET:
            field_dict["conversation_adaption_status"] = conversation_adaption_status
        if report_data is not UNSET:
            field_dict["report_data"] = report_data
        if source_data is not UNSET:
            field_dict["source_data"] = source_data
        if topic_tree is not UNSET:
            field_dict["topic_tree"] = topic_tree
        if use_cases is not UNSET:
            field_dict["use_cases"] = use_cases
        if user_description is not UNSET:
            field_dict["user_description"] = user_description
        if state_updated_at is not UNSET:
            field_dict["state_updated_at"] = state_updated_at
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if created_by is not UNSET:
            field_dict["created_by"] = created_by
        if started_at is not UNSET:
            field_dict["started_at"] = started_at
        if completed_at is not UNSET:
            field_dict["completed_at"] = completed_at
        if test_count is not UNSET:
            field_dict["test_count"] = test_count
        if application_id is not UNSET:
            field_dict["application_id"] = application_id
        if app_id is not UNSET:
            field_dict["app_id"] = app_id
        if is_template is not UNSET:
            field_dict["is_template"] = is_template
        if created_by_user is not UNSET:
            field_dict["created_by_user"] = created_by_user
        if persona_summaries is not UNSET:
            field_dict["persona_summaries"] = persona_summaries
        if marked_for_deletion_at is not UNSET:
            field_dict["marked_for_deletion_at"] = marked_for_deletion_at
        if risks is not UNSET:
            field_dict["risks"] = risks

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.experiment_update_schema_statistics_type_0 import (
            ExperimentUpdateSchemaStatisticsType0,
        )
        from ..models.experiment_update_schema_persona_summaries_item import (
            ExperimentUpdateSchemaPersonaSummariesItem,
        )
        from ..models.experiment_update_schema_source_data_type_0 import (
            ExperimentUpdateSchemaSourceDataType0,
        )
        from ..models.experiment_update_schema_report_data_type_0 import (
            ExperimentUpdateSchemaReportDataType0,
        )
        from ..models.experiment_update_schema_risks_item import (
            ExperimentUpdateSchemaRisksItem,
        )

        d = dict(src_dict)
        _id = d.pop("id", UNSET)
        id: Union[Unset, UUID]
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        name = d.pop("name", UNSET)

        def _parse_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        description = _parse_description(d.pop("description", UNSET))

        role = d.pop("role", UNSET)

        def _parse_state(
            data: object,
        ) -> Union[
            Literal["ADAPTATION_COMPLETE"],
            Literal["ADAPTATION_FAILED"],
            Literal["ADAPTATION_IN_PROGRESS"],
            Literal["ADAPTATION_WAITING_TO_START"],
            Literal["DRAFT"],
            Literal["EVALUATION_COMPLETE"],
            Literal["EVALUATION_FAILED"],
            Literal["EVALUATION_IN_PROGRESS"],
            Literal["EVALUATION_PARTIALLY_COMPLETE"],
            Literal["EXPERIMENT_COMPLETED"],
            Literal["EXPERIMENT_FAILED"],
            Literal["EXPERIMENT_PARTIALLY_COMPLETE"],
            Literal["EXPERIMENT_STARTED"],
            Literal["GENERATION_COMPLETE"],
            Literal["GENERATION_FAILED"],
            Literal["GENERATION_IN_PROGRESS"],
            Literal["QUEUED"],
            Literal["VALIDATION_COMPLETE"],
            Literal["VALIDATION_FAILED"],
            Literal["VALIDATION_IN_PROGRESS"],
            Literal["VALIDATION_PARTIALLY_COMPLETE"],
            None,
            Unset,
        ]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            state_type_0_type_0 = cast(Literal["DRAFT"], data)
            if state_type_0_type_0 != "DRAFT":
                raise ValueError(
                    f"state_type_0_type_0 must match const 'DRAFT', got '{state_type_0_type_0}'"
                )
            return state_type_0_type_0
            state_type_0_type_1 = cast(Literal["QUEUED"], data)
            if state_type_0_type_1 != "QUEUED":
                raise ValueError(
                    f"state_type_0_type_1 must match const 'QUEUED', got '{state_type_0_type_1}'"
                )
            return state_type_0_type_1
            state_type_0_type_2 = cast(Literal["EXPERIMENT_STARTED"], data)
            if state_type_0_type_2 != "EXPERIMENT_STARTED":
                raise ValueError(
                    f"state_type_0_type_2 must match const 'EXPERIMENT_STARTED', got '{state_type_0_type_2}'"
                )
            return state_type_0_type_2
            state_type_0_type_3 = cast(Literal["GENERATION_IN_PROGRESS"], data)
            if state_type_0_type_3 != "GENERATION_IN_PROGRESS":
                raise ValueError(
                    f"state_type_0_type_3 must match const 'GENERATION_IN_PROGRESS', got '{state_type_0_type_3}'"
                )
            return state_type_0_type_3
            state_type_0_type_4 = cast(Literal["GENERATION_FAILED"], data)
            if state_type_0_type_4 != "GENERATION_FAILED":
                raise ValueError(
                    f"state_type_0_type_4 must match const 'GENERATION_FAILED', got '{state_type_0_type_4}'"
                )
            return state_type_0_type_4
            state_type_0_type_5 = cast(Literal["GENERATION_COMPLETE"], data)
            if state_type_0_type_5 != "GENERATION_COMPLETE":
                raise ValueError(
                    f"state_type_0_type_5 must match const 'GENERATION_COMPLETE', got '{state_type_0_type_5}'"
                )
            return state_type_0_type_5
            state_type_0_type_6 = cast(Literal["EVALUATION_IN_PROGRESS"], data)
            if state_type_0_type_6 != "EVALUATION_IN_PROGRESS":
                raise ValueError(
                    f"state_type_0_type_6 must match const 'EVALUATION_IN_PROGRESS', got '{state_type_0_type_6}'"
                )
            return state_type_0_type_6
            state_type_0_type_7 = cast(Literal["EVALUATION_COMPLETE"], data)
            if state_type_0_type_7 != "EVALUATION_COMPLETE":
                raise ValueError(
                    f"state_type_0_type_7 must match const 'EVALUATION_COMPLETE', got '{state_type_0_type_7}'"
                )
            return state_type_0_type_7
            state_type_0_type_8 = cast(Literal["EVALUATION_PARTIALLY_COMPLETE"], data)
            if state_type_0_type_8 != "EVALUATION_PARTIALLY_COMPLETE":
                raise ValueError(
                    f"state_type_0_type_8 must match const 'EVALUATION_PARTIALLY_COMPLETE', got '{state_type_0_type_8}'"
                )
            return state_type_0_type_8
            state_type_0_type_9 = cast(Literal["EVALUATION_FAILED"], data)
            if state_type_0_type_9 != "EVALUATION_FAILED":
                raise ValueError(
                    f"state_type_0_type_9 must match const 'EVALUATION_FAILED', got '{state_type_0_type_9}'"
                )
            return state_type_0_type_9
            state_type_0_type_10 = cast(Literal["VALIDATION_IN_PROGRESS"], data)
            if state_type_0_type_10 != "VALIDATION_IN_PROGRESS":
                raise ValueError(
                    f"state_type_0_type_10 must match const 'VALIDATION_IN_PROGRESS', got '{state_type_0_type_10}'"
                )
            return state_type_0_type_10
            state_type_0_type_11 = cast(Literal["VALIDATION_COMPLETE"], data)
            if state_type_0_type_11 != "VALIDATION_COMPLETE":
                raise ValueError(
                    f"state_type_0_type_11 must match const 'VALIDATION_COMPLETE', got '{state_type_0_type_11}'"
                )
            return state_type_0_type_11
            state_type_0_type_12 = cast(Literal["VALIDATION_PARTIALLY_COMPLETE"], data)
            if state_type_0_type_12 != "VALIDATION_PARTIALLY_COMPLETE":
                raise ValueError(
                    f"state_type_0_type_12 must match const 'VALIDATION_PARTIALLY_COMPLETE', got '{state_type_0_type_12}'"
                )
            return state_type_0_type_12
            state_type_0_type_13 = cast(Literal["VALIDATION_FAILED"], data)
            if state_type_0_type_13 != "VALIDATION_FAILED":
                raise ValueError(
                    f"state_type_0_type_13 must match const 'VALIDATION_FAILED', got '{state_type_0_type_13}'"
                )
            return state_type_0_type_13
            state_type_0_type_14 = cast(Literal["ADAPTATION_WAITING_TO_START"], data)
            if state_type_0_type_14 != "ADAPTATION_WAITING_TO_START":
                raise ValueError(
                    f"state_type_0_type_14 must match const 'ADAPTATION_WAITING_TO_START', got '{state_type_0_type_14}'"
                )
            return state_type_0_type_14
            state_type_0_type_15 = cast(Literal["ADAPTATION_IN_PROGRESS"], data)
            if state_type_0_type_15 != "ADAPTATION_IN_PROGRESS":
                raise ValueError(
                    f"state_type_0_type_15 must match const 'ADAPTATION_IN_PROGRESS', got '{state_type_0_type_15}'"
                )
            return state_type_0_type_15
            state_type_0_type_16 = cast(Literal["ADAPTATION_COMPLETE"], data)
            if state_type_0_type_16 != "ADAPTATION_COMPLETE":
                raise ValueError(
                    f"state_type_0_type_16 must match const 'ADAPTATION_COMPLETE', got '{state_type_0_type_16}'"
                )
            return state_type_0_type_16
            state_type_0_type_17 = cast(Literal["ADAPTATION_FAILED"], data)
            if state_type_0_type_17 != "ADAPTATION_FAILED":
                raise ValueError(
                    f"state_type_0_type_17 must match const 'ADAPTATION_FAILED', got '{state_type_0_type_17}'"
                )
            return state_type_0_type_17
            state_type_0_type_18 = cast(Literal["EXPERIMENT_COMPLETED"], data)
            if state_type_0_type_18 != "EXPERIMENT_COMPLETED":
                raise ValueError(
                    f"state_type_0_type_18 must match const 'EXPERIMENT_COMPLETED', got '{state_type_0_type_18}'"
                )
            return state_type_0_type_18
            state_type_0_type_19 = cast(Literal["EXPERIMENT_FAILED"], data)
            if state_type_0_type_19 != "EXPERIMENT_FAILED":
                raise ValueError(
                    f"state_type_0_type_19 must match const 'EXPERIMENT_FAILED', got '{state_type_0_type_19}'"
                )
            return state_type_0_type_19
            state_type_0_type_20 = cast(Literal["EXPERIMENT_PARTIALLY_COMPLETE"], data)
            if state_type_0_type_20 != "EXPERIMENT_PARTIALLY_COMPLETE":
                raise ValueError(
                    f"state_type_0_type_20 must match const 'EXPERIMENT_PARTIALLY_COMPLETE', got '{state_type_0_type_20}'"
                )
            return state_type_0_type_20
            return cast(
                Union[
                    Literal["ADAPTATION_COMPLETE"],
                    Literal["ADAPTATION_FAILED"],
                    Literal["ADAPTATION_IN_PROGRESS"],
                    Literal["ADAPTATION_WAITING_TO_START"],
                    Literal["DRAFT"],
                    Literal["EVALUATION_COMPLETE"],
                    Literal["EVALUATION_FAILED"],
                    Literal["EVALUATION_IN_PROGRESS"],
                    Literal["EVALUATION_PARTIALLY_COMPLETE"],
                    Literal["EXPERIMENT_COMPLETED"],
                    Literal["EXPERIMENT_FAILED"],
                    Literal["EXPERIMENT_PARTIALLY_COMPLETE"],
                    Literal["EXPERIMENT_STARTED"],
                    Literal["GENERATION_COMPLETE"],
                    Literal["GENERATION_FAILED"],
                    Literal["GENERATION_IN_PROGRESS"],
                    Literal["QUEUED"],
                    Literal["VALIDATION_COMPLETE"],
                    Literal["VALIDATION_FAILED"],
                    Literal["VALIDATION_IN_PROGRESS"],
                    Literal["VALIDATION_PARTIALLY_COMPLETE"],
                    None,
                    Unset,
                ],
                data,
            )

        state = _parse_state(d.pop("state", UNSET))

        def _parse_state_num(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        state_num = _parse_state_num(d.pop("state_num", UNSET))

        def _parse_status(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        status = _parse_status(d.pop("status", UNSET))

        def _parse_statistics(
            data: object,
        ) -> Union["ExperimentUpdateSchemaStatisticsType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                statistics_type_0 = ExperimentUpdateSchemaStatisticsType0.from_dict(
                    data
                )

                return statistics_type_0
            except:  # noqa: E722
                pass
            return cast(
                Union["ExperimentUpdateSchemaStatisticsType0", None, Unset], data
            )

        statistics = _parse_statistics(d.pop("statistics", UNSET))

        def _parse_status_reason(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        status_reason = _parse_status_reason(d.pop("status_reason", UNSET))

        def _parse_is_completed(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        is_completed = _parse_is_completed(d.pop("is_completed", UNSET))

        def _parse_generation_status(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        generation_status = _parse_generation_status(d.pop("generation_status", UNSET))

        def _parse_evaluation_status(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        evaluation_status = _parse_evaluation_status(d.pop("evaluation_status", UNSET))

        def _parse_validation_status(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        validation_status = _parse_validation_status(d.pop("validation_status", UNSET))

        def _parse_conversation_adaption_status(
            data: object,
        ) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        conversation_adaption_status = _parse_conversation_adaption_status(
            d.pop("conversation_adaption_status", UNSET)
        )

        def _parse_report_data(
            data: object,
        ) -> Union["ExperimentUpdateSchemaReportDataType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                report_data_type_0 = ExperimentUpdateSchemaReportDataType0.from_dict(
                    data
                )

                return report_data_type_0
            except:  # noqa: E722
                pass
            return cast(
                Union["ExperimentUpdateSchemaReportDataType0", None, Unset], data
            )

        report_data = _parse_report_data(d.pop("report_data", UNSET))

        def _parse_source_data(
            data: object,
        ) -> Union["ExperimentUpdateSchemaSourceDataType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                source_data_type_0 = ExperimentUpdateSchemaSourceDataType0.from_dict(
                    data
                )

                return source_data_type_0
            except:  # noqa: E722
                pass
            return cast(
                Union["ExperimentUpdateSchemaSourceDataType0", None, Unset], data
            )

        source_data = _parse_source_data(d.pop("source_data", UNSET))

        def _parse_topic_tree(
            data: object,
        ) -> Union[None, Unset, list[list[Union[float, str]]]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                topic_tree_type_0 = []
                _topic_tree_type_0 = data
                for topic_tree_type_0_item_data in _topic_tree_type_0:
                    topic_tree_type_0_item = []
                    _topic_tree_type_0_item = topic_tree_type_0_item_data
                    for topic_tree_type_0_item_item_data in _topic_tree_type_0_item:

                        def _parse_topic_tree_type_0_item_item(
                            data: object,
                        ) -> Union[float, str]:
                            return cast(Union[float, str], data)

                        topic_tree_type_0_item_item = (
                            _parse_topic_tree_type_0_item_item(
                                topic_tree_type_0_item_item_data
                            )
                        )

                        topic_tree_type_0_item.append(topic_tree_type_0_item_item)

                    topic_tree_type_0.append(topic_tree_type_0_item)

                return topic_tree_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[list[Union[float, str]]]], data)

        topic_tree = _parse_topic_tree(d.pop("topic_tree", UNSET))

        def _parse_use_cases(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        use_cases = _parse_use_cases(d.pop("use_cases", UNSET))

        def _parse_user_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        user_description = _parse_user_description(d.pop("user_description", UNSET))

        _state_updated_at = d.pop("state_updated_at", UNSET)
        state_updated_at: Union[Unset, datetime.datetime]
        if isinstance(_state_updated_at, Unset):
            state_updated_at = UNSET
        else:
            state_updated_at = isoparse(_state_updated_at)

        _created_at = d.pop("created_at", UNSET)
        created_at: Union[Unset, datetime.datetime]
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        _updated_at = d.pop("updated_at", UNSET)
        updated_at: Union[Unset, datetime.datetime]
        if isinstance(_updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = isoparse(_updated_at)

        def _parse_created_by(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        created_by = _parse_created_by(d.pop("created_by", UNSET))

        def _parse_started_at(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                started_at_type_0 = isoparse(data)

                return started_at_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        started_at = _parse_started_at(d.pop("started_at", UNSET))

        def _parse_completed_at(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                completed_at_type_0 = isoparse(data)

                return completed_at_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        completed_at = _parse_completed_at(d.pop("completed_at", UNSET))

        def _parse_test_count(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        test_count = _parse_test_count(d.pop("test_count", UNSET))

        def _parse_application_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        application_id = _parse_application_id(d.pop("application_id", UNSET))

        def _parse_app_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        app_id = _parse_app_id(d.pop("app_id", UNSET))

        is_template = d.pop("is_template", UNSET)

        def _parse_created_by_user(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        created_by_user = _parse_created_by_user(d.pop("created_by_user", UNSET))

        persona_summaries = []
        _persona_summaries = d.pop("persona_summaries", UNSET)
        for persona_summaries_item_data in _persona_summaries or []:
            persona_summaries_item = (
                ExperimentUpdateSchemaPersonaSummariesItem.from_dict(
                    persona_summaries_item_data
                )
            )

            persona_summaries.append(persona_summaries_item)

        def _parse_marked_for_deletion_at(
            data: object,
        ) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                marked_for_deletion_at_type_0 = isoparse(data)

                return marked_for_deletion_at_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        marked_for_deletion_at = _parse_marked_for_deletion_at(
            d.pop("marked_for_deletion_at", UNSET)
        )

        risks = []
        _risks = d.pop("risks", UNSET)
        for risks_item_data in _risks or []:
            risks_item = ExperimentUpdateSchemaRisksItem.from_dict(risks_item_data)

            risks.append(risks_item)

        experiment_update_schema = cls(
            id=id,
            name=name,
            description=description,
            role=role,
            state=state,
            state_num=state_num,
            status=status,
            statistics=statistics,
            status_reason=status_reason,
            is_completed=is_completed,
            generation_status=generation_status,
            evaluation_status=evaluation_status,
            validation_status=validation_status,
            conversation_adaption_status=conversation_adaption_status,
            report_data=report_data,
            source_data=source_data,
            topic_tree=topic_tree,
            use_cases=use_cases,
            user_description=user_description,
            state_updated_at=state_updated_at,
            created_at=created_at,
            updated_at=updated_at,
            created_by=created_by,
            started_at=started_at,
            completed_at=completed_at,
            test_count=test_count,
            application_id=application_id,
            app_id=app_id,
            is_template=is_template,
            created_by_user=created_by_user,
            persona_summaries=persona_summaries,
            marked_for_deletion_at=marked_for_deletion_at,
            risks=risks,
        )

        experiment_update_schema.additional_properties = d
        return experiment_update_schema

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
