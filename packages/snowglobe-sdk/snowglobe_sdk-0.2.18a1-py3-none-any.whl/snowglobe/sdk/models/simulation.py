from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define

from ..types import UNSET, Unset

from ..models.simulation_state_type_0 import SimulationStateType0
from dateutil.parser import isoparse
from typing import cast
from typing import Union
from uuid import UUID
import datetime

if TYPE_CHECKING:
    from ..models.simulation_persona_summaries_item import (
        SimulationPersonaSummariesItem,
    )
    from ..models.simulation_statistics import SimulationStatistics
    from ..models.simulation_report_data_type_0 import SimulationReportDataType0
    from ..models.simulation_risks_item import SimulationRisksItem
    from ..models.simulation_source_data import SimulationSourceData


T = TypeVar("T", bound="Simulation")


@_attrs_define
class Simulation:
    """
    Attributes:
        id (UUID):
        name (str):
        role (str):
        state (Union[None, SimulationStateType0]):
        state_num (Union[None, int]):
        statistics (SimulationStatistics):
        is_completed (Union[None, bool]):
        state_updated_at (datetime.datetime):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
        is_template (bool):
        risks (list['SimulationRisksItem']):
        description (Union[None, Unset, str]):
        status (Union[None, Unset, str]):
        status_reason (Union[None, Unset, str]):
        generation_status (Union[None, Unset, str]):
        evaluation_status (Union[None, Unset, str]):
        validation_status (Union[None, Unset, str]):
        conversation_adaption_status (Union[None, Unset, str]):
        report_data (Union['SimulationReportDataType0', None, Unset]):
        source_data (Union[Unset, SimulationSourceData]):
        topic_tree (Union[Unset, list[list[Union[float, str]]]]):
        use_cases (Union[None, Unset, str]):
        user_description (Union[None, Unset, str]):
        created_by (Union[None, Unset, str]):
        started_at (Union[None, Unset, datetime.datetime]):
        completed_at (Union[None, Unset, datetime.datetime]):
        test_count (Union[None, Unset, int]):
        application_id (Union[None, Unset, str]):
        app_id (Union[None, UUID, Unset]):
        created_by_user (Union[None, Unset, str]):
        persona_summaries (Union[Unset, list['SimulationPersonaSummariesItem']]):
        marked_for_deletion_at (Union[None, Unset, datetime.datetime]):
    """

    id: UUID
    name: str
    role: str
    state: Union[None, SimulationStateType0]
    state_num: Union[None, int]
    statistics: "SimulationStatistics"
    is_completed: Union[None, bool]
    state_updated_at: datetime.datetime
    created_at: datetime.datetime
    updated_at: datetime.datetime
    is_template: bool
    risks: list["SimulationRisksItem"]
    description: Union[None, Unset, str] = UNSET
    status: Union[None, Unset, str] = UNSET
    status_reason: Union[None, Unset, str] = UNSET
    generation_status: Union[None, Unset, str] = UNSET
    evaluation_status: Union[None, Unset, str] = UNSET
    validation_status: Union[None, Unset, str] = UNSET
    conversation_adaption_status: Union[None, Unset, str] = UNSET
    report_data: Union["SimulationReportDataType0", None, Unset] = UNSET
    source_data: Union[Unset, "SimulationSourceData"] = UNSET
    topic_tree: Union[Unset, list[list[Union[float, str]]]] = UNSET
    use_cases: Union[None, Unset, str] = UNSET
    user_description: Union[None, Unset, str] = UNSET
    created_by: Union[None, Unset, str] = UNSET
    started_at: Union[None, Unset, datetime.datetime] = UNSET
    completed_at: Union[None, Unset, datetime.datetime] = UNSET
    test_count: Union[None, Unset, int] = UNSET
    application_id: Union[None, Unset, str] = UNSET
    app_id: Union[None, UUID, Unset] = UNSET
    created_by_user: Union[None, Unset, str] = UNSET
    persona_summaries: Union[Unset, list["SimulationPersonaSummariesItem"]] = UNSET
    marked_for_deletion_at: Union[None, Unset, datetime.datetime] = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.simulation_report_data_type_0 import SimulationReportDataType0

        id = str(self.id)

        name = self.name

        role = self.role

        state: Union[None, str]
        if isinstance(self.state, SimulationStateType0):
            state = self.state.value
        else:
            state = self.state

        state_num: Union[None, int]
        state_num = self.state_num

        statistics = self.statistics.to_dict()

        is_completed: Union[None, bool]
        is_completed = self.is_completed

        state_updated_at = self.state_updated_at.isoformat()

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        is_template = self.is_template

        risks = []
        for risks_item_data in self.risks:
            risks_item = risks_item_data.to_dict()
            risks.append(risks_item)

        description: Union[None, Unset, str]
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        status: Union[None, Unset, str]
        if isinstance(self.status, Unset):
            status = UNSET
        else:
            status = self.status

        status_reason: Union[None, Unset, str]
        if isinstance(self.status_reason, Unset):
            status_reason = UNSET
        else:
            status_reason = self.status_reason

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
        elif isinstance(self.report_data, SimulationReportDataType0):
            report_data = self.report_data.to_dict()
        else:
            report_data = self.report_data

        source_data: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.source_data, Unset):
            source_data = self.source_data.to_dict()

        topic_tree: Union[Unset, list[list[Union[float, str]]]] = UNSET
        if not isinstance(self.topic_tree, Unset):
            topic_tree = []
            for topic_tree_item_data in self.topic_tree:
                topic_tree_item = []
                for topic_tree_item_item_data in topic_tree_item_data:
                    topic_tree_item_item: Union[float, str]
                    topic_tree_item_item = topic_tree_item_item_data
                    topic_tree_item.append(topic_tree_item_item)

                topic_tree.append(topic_tree_item)

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
        elif isinstance(self.app_id, UUID):
            app_id = str(self.app_id)
        else:
            app_id = self.app_id

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

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "id": id,
                "name": name,
                "role": role,
                "state": state,
                "state_num": state_num,
                "statistics": statistics,
                "is_completed": is_completed,
                "state_updated_at": state_updated_at,
                "created_at": created_at,
                "updated_at": updated_at,
                "is_template": is_template,
                "risks": risks,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if status is not UNSET:
            field_dict["status"] = status
        if status_reason is not UNSET:
            field_dict["status_reason"] = status_reason
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
        if created_by_user is not UNSET:
            field_dict["created_by_user"] = created_by_user
        if persona_summaries is not UNSET:
            field_dict["persona_summaries"] = persona_summaries
        if marked_for_deletion_at is not UNSET:
            field_dict["marked_for_deletion_at"] = marked_for_deletion_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.simulation_persona_summaries_item import (
            SimulationPersonaSummariesItem,
        )
        from ..models.simulation_statistics import SimulationStatistics
        from ..models.simulation_report_data_type_0 import SimulationReportDataType0
        from ..models.simulation_risks_item import SimulationRisksItem
        from ..models.simulation_source_data import SimulationSourceData

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        role = d.pop("role")

        def _parse_state(data: object) -> Union[None, SimulationStateType0]:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                state_type_0 = SimulationStateType0(data)

                return state_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, SimulationStateType0], data)

        state = _parse_state(d.pop("state"))

        def _parse_state_num(data: object) -> Union[None, int]:
            if data is None:
                return data
            return cast(Union[None, int], data)

        state_num = _parse_state_num(d.pop("state_num"))

        statistics = SimulationStatistics.from_dict(d.pop("statistics"))

        def _parse_is_completed(data: object) -> Union[None, bool]:
            if data is None:
                return data
            return cast(Union[None, bool], data)

        is_completed = _parse_is_completed(d.pop("is_completed"))

        state_updated_at = isoparse(d.pop("state_updated_at"))

        created_at = isoparse(d.pop("created_at"))

        updated_at = isoparse(d.pop("updated_at"))

        is_template = d.pop("is_template")

        risks = []
        _risks = d.pop("risks")
        for risks_item_data in _risks:
            risks_item = SimulationRisksItem.from_dict(risks_item_data)

            risks.append(risks_item)

        def _parse_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_status(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        status = _parse_status(d.pop("status", UNSET))

        def _parse_status_reason(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        status_reason = _parse_status_reason(d.pop("status_reason", UNSET))

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
        ) -> Union["SimulationReportDataType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                report_data_type_0 = SimulationReportDataType0.from_dict(data)

                return report_data_type_0
            except:  # noqa: E722
                pass
            return cast(Union["SimulationReportDataType0", None, Unset], data)

        report_data = _parse_report_data(d.pop("report_data", UNSET))

        _source_data = d.pop("source_data", UNSET)
        source_data: Union[Unset, SimulationSourceData]
        if isinstance(_source_data, Unset):
            source_data = UNSET
        else:
            source_data = SimulationSourceData.from_dict(_source_data)

        topic_tree = []
        _topic_tree = d.pop("topic_tree", UNSET)
        for topic_tree_item_data in _topic_tree or []:
            topic_tree_item = []
            _topic_tree_item = topic_tree_item_data
            for topic_tree_item_item_data in _topic_tree_item:

                def _parse_topic_tree_item_item(data: object) -> Union[float, str]:
                    return cast(Union[float, str], data)

                topic_tree_item_item = _parse_topic_tree_item_item(
                    topic_tree_item_item_data
                )

                topic_tree_item.append(topic_tree_item_item)

            topic_tree.append(topic_tree_item)

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

        def _parse_app_id(data: object) -> Union[None, UUID, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                app_id_type_0 = UUID(data)

                return app_id_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, UUID, Unset], data)

        app_id = _parse_app_id(d.pop("app_id", UNSET))

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
            persona_summaries_item = SimulationPersonaSummariesItem.from_dict(
                persona_summaries_item_data
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

        simulation = cls(
            id=id,
            name=name,
            role=role,
            state=state,
            state_num=state_num,
            statistics=statistics,
            is_completed=is_completed,
            state_updated_at=state_updated_at,
            created_at=created_at,
            updated_at=updated_at,
            is_template=is_template,
            risks=risks,
            description=description,
            status=status,
            status_reason=status_reason,
            generation_status=generation_status,
            evaluation_status=evaluation_status,
            validation_status=validation_status,
            conversation_adaption_status=conversation_adaption_status,
            report_data=report_data,
            source_data=source_data,
            topic_tree=topic_tree,
            use_cases=use_cases,
            user_description=user_description,
            created_by=created_by,
            started_at=started_at,
            completed_at=completed_at,
            test_count=test_count,
            application_id=application_id,
            app_id=app_id,
            created_by_user=created_by_user,
            persona_summaries=persona_summaries,
            marked_for_deletion_at=marked_for_deletion_at,
        )

        return simulation
