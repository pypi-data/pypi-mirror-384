from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.experiment_source_data_attack_styles import (
    ExperimentSourceDataAttackStyles,
)
from ..models.experiment_source_data_mode import ExperimentSourceDataMode
from typing import cast
from typing import Union

if TYPE_CHECKING:
    from ..models.experiment_source_data_docs import ExperimentSourceDataDocs
    from ..models.experiment_source_data_schedule import ExperimentSourceDataSchedule
    from ..models.experiment_source_data_autofix_configuration import (
        ExperimentSourceDataAutofixConfiguration,
    )
    from ..models.experiment_source_data_generation_configuration import (
        ExperimentSourceDataGenerationConfiguration,
    )
    from ..models.experiment_source_data_persona_topics_item import (
        ExperimentSourceDataPersonaTopicsItem,
    )
    from ..models.experiment_source_data_evaluation_configuration import (
        ExperimentSourceDataEvaluationConfiguration,
    )


T = TypeVar("T", bound="ExperimentSourceData")


@_attrs_define
class ExperimentSourceData:
    """
    Attributes:
        docs (ExperimentSourceDataDocs):
        generation_configuration (ExperimentSourceDataGenerationConfiguration):
        personas (Union[Unset, list[str]]):
        topics (Union[Unset, list[str]]):
        evaluation_configuration (Union[Unset, ExperimentSourceDataEvaluationConfiguration]):
        persona_topics (Union[Unset, list['ExperimentSourceDataPersonaTopicsItem']]):
        schedule (Union[Unset, ExperimentSourceDataSchedule]):
        autofix_configuration (Union[Unset, ExperimentSourceDataAutofixConfiguration]):
        mode (Union[Unset, ExperimentSourceDataMode]):
        attack_styles (Union[Unset, ExperimentSourceDataAttackStyles]):
    """

    docs: "ExperimentSourceDataDocs"
    generation_configuration: "ExperimentSourceDataGenerationConfiguration"
    personas: Union[Unset, list[str]] = UNSET
    topics: Union[Unset, list[str]] = UNSET
    evaluation_configuration: Union[
        Unset, "ExperimentSourceDataEvaluationConfiguration"
    ] = UNSET
    persona_topics: Union[Unset, list["ExperimentSourceDataPersonaTopicsItem"]] = UNSET
    schedule: Union[Unset, "ExperimentSourceDataSchedule"] = UNSET
    autofix_configuration: Union[Unset, "ExperimentSourceDataAutofixConfiguration"] = (
        UNSET
    )
    mode: Union[Unset, ExperimentSourceDataMode] = UNSET
    attack_styles: Union[Unset, ExperimentSourceDataAttackStyles] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        docs = self.docs.to_dict()

        generation_configuration = self.generation_configuration.to_dict()

        personas: Union[Unset, list[str]] = UNSET
        if not isinstance(self.personas, Unset):
            personas = self.personas

        topics: Union[Unset, list[str]] = UNSET
        if not isinstance(self.topics, Unset):
            topics = self.topics

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

        mode: Union[Unset, str] = UNSET
        if not isinstance(self.mode, Unset):
            mode = self.mode.value

        attack_styles: Union[Unset, str] = UNSET
        if not isinstance(self.attack_styles, Unset):
            attack_styles = self.attack_styles.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "docs": docs,
                "generation_configuration": generation_configuration,
            }
        )
        if personas is not UNSET:
            field_dict["personas"] = personas
        if topics is not UNSET:
            field_dict["topics"] = topics
        if evaluation_configuration is not UNSET:
            field_dict["evaluation_configuration"] = evaluation_configuration
        if persona_topics is not UNSET:
            field_dict["persona_topics"] = persona_topics
        if schedule is not UNSET:
            field_dict["schedule"] = schedule
        if autofix_configuration is not UNSET:
            field_dict["autofix_configuration"] = autofix_configuration
        if mode is not UNSET:
            field_dict["mode"] = mode
        if attack_styles is not UNSET:
            field_dict["attackStyles"] = attack_styles

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.experiment_source_data_docs import ExperimentSourceDataDocs
        from ..models.experiment_source_data_schedule import (
            ExperimentSourceDataSchedule,
        )
        from ..models.experiment_source_data_autofix_configuration import (
            ExperimentSourceDataAutofixConfiguration,
        )
        from ..models.experiment_source_data_generation_configuration import (
            ExperimentSourceDataGenerationConfiguration,
        )
        from ..models.experiment_source_data_persona_topics_item import (
            ExperimentSourceDataPersonaTopicsItem,
        )
        from ..models.experiment_source_data_evaluation_configuration import (
            ExperimentSourceDataEvaluationConfiguration,
        )

        d = dict(src_dict)
        docs = ExperimentSourceDataDocs.from_dict(d.pop("docs"))

        generation_configuration = (
            ExperimentSourceDataGenerationConfiguration.from_dict(
                d.pop("generation_configuration")
            )
        )

        personas = cast(list[str], d.pop("personas", UNSET))

        topics = cast(list[str], d.pop("topics", UNSET))

        _evaluation_configuration = d.pop("evaluation_configuration", UNSET)
        evaluation_configuration: Union[
            Unset, ExperimentSourceDataEvaluationConfiguration
        ]
        if isinstance(_evaluation_configuration, Unset):
            evaluation_configuration = UNSET
        else:
            evaluation_configuration = (
                ExperimentSourceDataEvaluationConfiguration.from_dict(
                    _evaluation_configuration
                )
            )

        persona_topics = []
        _persona_topics = d.pop("persona_topics", UNSET)
        for persona_topics_item_data in _persona_topics or []:
            persona_topics_item = ExperimentSourceDataPersonaTopicsItem.from_dict(
                persona_topics_item_data
            )

            persona_topics.append(persona_topics_item)

        _schedule = d.pop("schedule", UNSET)
        schedule: Union[Unset, ExperimentSourceDataSchedule]
        if isinstance(_schedule, Unset):
            schedule = UNSET
        else:
            schedule = ExperimentSourceDataSchedule.from_dict(_schedule)

        _autofix_configuration = d.pop("autofix_configuration", UNSET)
        autofix_configuration: Union[Unset, ExperimentSourceDataAutofixConfiguration]
        if isinstance(_autofix_configuration, Unset):
            autofix_configuration = UNSET
        else:
            autofix_configuration = ExperimentSourceDataAutofixConfiguration.from_dict(
                _autofix_configuration
            )

        _mode = d.pop("mode", UNSET)
        mode: Union[Unset, ExperimentSourceDataMode]
        if isinstance(_mode, Unset):
            mode = UNSET
        else:
            mode = ExperimentSourceDataMode(_mode)

        _attack_styles = d.pop("attackStyles", UNSET)
        attack_styles: Union[Unset, ExperimentSourceDataAttackStyles]
        if isinstance(_attack_styles, Unset):
            attack_styles = UNSET
        else:
            attack_styles = ExperimentSourceDataAttackStyles(_attack_styles)

        experiment_source_data = cls(
            docs=docs,
            generation_configuration=generation_configuration,
            personas=personas,
            topics=topics,
            evaluation_configuration=evaluation_configuration,
            persona_topics=persona_topics,
            schedule=schedule,
            autofix_configuration=autofix_configuration,
            mode=mode,
            attack_styles=attack_styles,
        )

        experiment_source_data.additional_properties = d
        return experiment_source_data

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
