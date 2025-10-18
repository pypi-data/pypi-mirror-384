from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import Union

if TYPE_CHECKING:
    from ..models.simulation_update_schema_source_data_type_0_generation_configuration_conversation import (
        SimulationUpdateSchemaSourceDataType0GenerationConfigurationConversation,
    )
    from ..models.simulation_update_schema_source_data_type_0_generation_configuration_message import (
        SimulationUpdateSchemaSourceDataType0GenerationConfigurationMessage,
    )


T = TypeVar("T", bound="SimulationUpdateSchemaSourceDataType0GenerationConfiguration")


@_attrs_define
class SimulationUpdateSchemaSourceDataType0GenerationConfiguration:
    """
    Attributes:
        conversation (Union[Unset, SimulationUpdateSchemaSourceDataType0GenerationConfigurationConversation]):
        message (Union[Unset, SimulationUpdateSchemaSourceDataType0GenerationConfigurationMessage]):
        branching_factor (Union[Unset, float]):
        max_personas (Union[Unset, float]):
        max_topics (Union[Unset, float]):
    """

    conversation: Union[
        Unset,
        "SimulationUpdateSchemaSourceDataType0GenerationConfigurationConversation",
    ] = UNSET
    message: Union[
        Unset, "SimulationUpdateSchemaSourceDataType0GenerationConfigurationMessage"
    ] = UNSET
    branching_factor: Union[Unset, float] = UNSET
    max_personas: Union[Unset, float] = UNSET
    max_topics: Union[Unset, float] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        conversation: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.conversation, Unset):
            conversation = self.conversation.to_dict()

        message: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.message, Unset):
            message = self.message.to_dict()

        branching_factor = self.branching_factor

        max_personas = self.max_personas

        max_topics = self.max_topics

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if conversation is not UNSET:
            field_dict["conversation"] = conversation
        if message is not UNSET:
            field_dict["message"] = message
        if branching_factor is not UNSET:
            field_dict["branching_factor"] = branching_factor
        if max_personas is not UNSET:
            field_dict["max_personas"] = max_personas
        if max_topics is not UNSET:
            field_dict["max_topics"] = max_topics

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.simulation_update_schema_source_data_type_0_generation_configuration_conversation import (
            SimulationUpdateSchemaSourceDataType0GenerationConfigurationConversation,
        )
        from ..models.simulation_update_schema_source_data_type_0_generation_configuration_message import (
            SimulationUpdateSchemaSourceDataType0GenerationConfigurationMessage,
        )

        d = dict(src_dict)
        _conversation = d.pop("conversation", UNSET)
        conversation: Union[
            Unset,
            SimulationUpdateSchemaSourceDataType0GenerationConfigurationConversation,
        ]
        if isinstance(_conversation, Unset):
            conversation = UNSET
        else:
            conversation = SimulationUpdateSchemaSourceDataType0GenerationConfigurationConversation.from_dict(
                _conversation
            )

        _message = d.pop("message", UNSET)
        message: Union[
            Unset, SimulationUpdateSchemaSourceDataType0GenerationConfigurationMessage
        ]
        if isinstance(_message, Unset):
            message = UNSET
        else:
            message = SimulationUpdateSchemaSourceDataType0GenerationConfigurationMessage.from_dict(
                _message
            )

        branching_factor = d.pop("branching_factor", UNSET)

        max_personas = d.pop("max_personas", UNSET)

        max_topics = d.pop("max_topics", UNSET)

        simulation_update_schema_source_data_type_0_generation_configuration = cls(
            conversation=conversation,
            message=message,
            branching_factor=branching_factor,
            max_personas=max_personas,
            max_topics=max_topics,
        )

        simulation_update_schema_source_data_type_0_generation_configuration.additional_properties = d
        return simulation_update_schema_source_data_type_0_generation_configuration

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
