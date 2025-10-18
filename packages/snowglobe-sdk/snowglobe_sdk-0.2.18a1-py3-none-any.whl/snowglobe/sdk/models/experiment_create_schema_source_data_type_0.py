from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast
from typing import Union

if TYPE_CHECKING:
    from ..models.experiment_create_schema_source_data_type_0_schedule import (
        ExperimentCreateSchemaSourceDataType0Schedule,
    )
    from ..models.experiment_create_schema_source_data_type_0_persona_topics_item import (
        ExperimentCreateSchemaSourceDataType0PersonaTopicsItem,
    )
    from ..models.experiment_create_schema_source_data_type_0_generation_configuration import (
        ExperimentCreateSchemaSourceDataType0GenerationConfiguration,
    )
    from ..models.experiment_create_schema_source_data_type_0_docs import (
        ExperimentCreateSchemaSourceDataType0Docs,
    )
    from ..models.experiment_create_schema_source_data_type_0_autofix_configuration import (
        ExperimentCreateSchemaSourceDataType0AutofixConfiguration,
    )
    from ..models.experiment_create_schema_source_data_type_0_evaluation_configuration import (
        ExperimentCreateSchemaSourceDataType0EvaluationConfiguration,
    )


T = TypeVar("T", bound="ExperimentCreateSchemaSourceDataType0")


@_attrs_define
class ExperimentCreateSchemaSourceDataType0:
    """
    Attributes:
        docs (ExperimentCreateSchemaSourceDataType0Docs):
        personas (list[str]):
        topics (list[str]):
        generation_configuration (ExperimentCreateSchemaSourceDataType0GenerationConfiguration):
        evaluation_configuration (Union[Unset, ExperimentCreateSchemaSourceDataType0EvaluationConfiguration]):
        persona_topics (Union[Unset, list['ExperimentCreateSchemaSourceDataType0PersonaTopicsItem']]):
        schedule (Union[Unset, ExperimentCreateSchemaSourceDataType0Schedule]):
        autofix_configuration (Union[Unset, ExperimentCreateSchemaSourceDataType0AutofixConfiguration]):
    """

    docs: "ExperimentCreateSchemaSourceDataType0Docs"
    personas: list[str]
    topics: list[str]
    generation_configuration: (
        "ExperimentCreateSchemaSourceDataType0GenerationConfiguration"
    )
    evaluation_configuration: Union[
        Unset, "ExperimentCreateSchemaSourceDataType0EvaluationConfiguration"
    ] = UNSET
    persona_topics: Union[
        Unset, list["ExperimentCreateSchemaSourceDataType0PersonaTopicsItem"]
    ] = UNSET
    schedule: Union[Unset, "ExperimentCreateSchemaSourceDataType0Schedule"] = UNSET
    autofix_configuration: Union[
        Unset, "ExperimentCreateSchemaSourceDataType0AutofixConfiguration"
    ] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        docs = self.docs.to_dict()

        personas = self.personas

        topics = self.topics

        generation_configuration = self.generation_configuration.to_dict()

        evaluation_configuration: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.evaluation_configuration, Unset):
            evaluation_configuration = self.evaluation_configuration.to_dict()

        persona_topics: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.persona_topics, Unset):
            persona_topics = []
            for persona_topics_item_data in self.persona_topics:
                persona_topics_item = persona_topics_item_data.to_dict()
                persona_topics.append(persona_topics_item)

        schedule: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.schedule, Unset):
            schedule = self.schedule.to_dict()

        autofix_configuration: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.autofix_configuration, Unset):
            autofix_configuration = self.autofix_configuration.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "docs": docs,
                "personas": personas,
                "topics": topics,
                "generation_configuration": generation_configuration,
            }
        )
        if evaluation_configuration is not UNSET:
            field_dict["evaluation_configuration"] = evaluation_configuration
        if persona_topics is not UNSET:
            field_dict["persona_topics"] = persona_topics
        if schedule is not UNSET:
            field_dict["schedule"] = schedule
        if autofix_configuration is not UNSET:
            field_dict["autofix_configuration"] = autofix_configuration

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.experiment_create_schema_source_data_type_0_schedule import (
            ExperimentCreateSchemaSourceDataType0Schedule,
        )
        from ..models.experiment_create_schema_source_data_type_0_persona_topics_item import (
            ExperimentCreateSchemaSourceDataType0PersonaTopicsItem,
        )
        from ..models.experiment_create_schema_source_data_type_0_generation_configuration import (
            ExperimentCreateSchemaSourceDataType0GenerationConfiguration,
        )
        from ..models.experiment_create_schema_source_data_type_0_docs import (
            ExperimentCreateSchemaSourceDataType0Docs,
        )
        from ..models.experiment_create_schema_source_data_type_0_autofix_configuration import (
            ExperimentCreateSchemaSourceDataType0AutofixConfiguration,
        )
        from ..models.experiment_create_schema_source_data_type_0_evaluation_configuration import (
            ExperimentCreateSchemaSourceDataType0EvaluationConfiguration,
        )

        d = dict(src_dict)
        docs = ExperimentCreateSchemaSourceDataType0Docs.from_dict(d.pop("docs"))

        personas = cast(list[str], d.pop("personas"))

        topics = cast(list[str], d.pop("topics"))

        generation_configuration = (
            ExperimentCreateSchemaSourceDataType0GenerationConfiguration.from_dict(
                d.pop("generation_configuration")
            )
        )

        _evaluation_configuration = d.pop("evaluation_configuration", UNSET)
        evaluation_configuration: Union[
            Unset, ExperimentCreateSchemaSourceDataType0EvaluationConfiguration
        ]
        if isinstance(_evaluation_configuration, Unset):
            evaluation_configuration = UNSET
        else:
            evaluation_configuration = (
                ExperimentCreateSchemaSourceDataType0EvaluationConfiguration.from_dict(
                    _evaluation_configuration
                )
            )

        persona_topics = []
        _persona_topics = d.pop("persona_topics", UNSET)
        for persona_topics_item_data in _persona_topics or []:
            persona_topics_item = (
                ExperimentCreateSchemaSourceDataType0PersonaTopicsItem.from_dict(
                    persona_topics_item_data
                )
            )

            persona_topics.append(persona_topics_item)

        _schedule = d.pop("schedule", UNSET)
        schedule: Union[Unset, ExperimentCreateSchemaSourceDataType0Schedule]
        if isinstance(_schedule, Unset):
            schedule = UNSET
        else:
            schedule = ExperimentCreateSchemaSourceDataType0Schedule.from_dict(
                _schedule
            )

        _autofix_configuration = d.pop("autofix_configuration", UNSET)
        autofix_configuration: Union[
            Unset, ExperimentCreateSchemaSourceDataType0AutofixConfiguration
        ]
        if isinstance(_autofix_configuration, Unset):
            autofix_configuration = UNSET
        else:
            autofix_configuration = (
                ExperimentCreateSchemaSourceDataType0AutofixConfiguration.from_dict(
                    _autofix_configuration
                )
            )

        experiment_create_schema_source_data_type_0 = cls(
            docs=docs,
            personas=personas,
            topics=topics,
            generation_configuration=generation_configuration,
            evaluation_configuration=evaluation_configuration,
            persona_topics=persona_topics,
            schedule=schedule,
            autofix_configuration=autofix_configuration,
        )

        experiment_create_schema_source_data_type_0.additional_properties = d
        return experiment_create_schema_source_data_type_0

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
