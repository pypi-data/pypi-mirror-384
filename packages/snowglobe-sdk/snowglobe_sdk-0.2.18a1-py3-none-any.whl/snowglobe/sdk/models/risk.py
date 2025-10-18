from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define

from ..types import UNSET, Unset

from ..models.risk_prompt_source import RiskPromptSource
from ..models.risk_type import RiskType
from dateutil.parser import isoparse
from typing import cast
from typing import Union
from uuid import UUID
import datetime

if TYPE_CHECKING:
    from ..models.risk_llm_configuration_type_0 import RiskLlmConfigurationType0
    from ..models.risk_prompt_template_type_0 import RiskPromptTemplateType0


T = TypeVar("T", bound="Risk")


@_attrs_define
class Risk:
    """
    Attributes:
        id (UUID):
        name (str):
        created_at (datetime.datetime):
        created_by (str):
        type_ (RiskType):
        prompt_source (RiskPromptSource):
        version (int):
        lineage_id (UUID):
        is_published (bool):
        description (Union[None, Unset, str]):
        legacy_judge_description (Union[None, Unset, str]):
        model_name (Union[None, Unset, str]):
        prompt (Union[None, Unset, str]):
        prompt_template (Union['RiskPromptTemplateType0', None, Unset]):
        llm_configuration (Union['RiskLlmConfigurationType0', None, Unset]):
        draft_version (Union[None, Unset, int]):
    """

    id: UUID
    name: str
    created_at: datetime.datetime
    created_by: str
    type_: RiskType
    prompt_source: RiskPromptSource
    version: int
    lineage_id: UUID
    is_published: bool
    description: Union[None, Unset, str] = UNSET
    legacy_judge_description: Union[None, Unset, str] = UNSET
    model_name: Union[None, Unset, str] = UNSET
    prompt: Union[None, Unset, str] = UNSET
    prompt_template: Union["RiskPromptTemplateType0", None, Unset] = UNSET
    llm_configuration: Union["RiskLlmConfigurationType0", None, Unset] = UNSET
    draft_version: Union[None, Unset, int] = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.risk_llm_configuration_type_0 import RiskLlmConfigurationType0
        from ..models.risk_prompt_template_type_0 import RiskPromptTemplateType0

        id = str(self.id)

        name = self.name

        created_at = self.created_at.isoformat()

        created_by = self.created_by

        type_ = self.type_.value

        prompt_source = self.prompt_source.value

        version = self.version

        lineage_id = str(self.lineage_id)

        is_published = self.is_published

        description: Union[None, Unset, str]
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        legacy_judge_description: Union[None, Unset, str]
        if isinstance(self.legacy_judge_description, Unset):
            legacy_judge_description = UNSET
        else:
            legacy_judge_description = self.legacy_judge_description

        model_name: Union[None, Unset, str]
        if isinstance(self.model_name, Unset):
            model_name = UNSET
        else:
            model_name = self.model_name

        prompt: Union[None, Unset, str]
        if isinstance(self.prompt, Unset):
            prompt = UNSET
        else:
            prompt = self.prompt

        prompt_template: Union[None, Unset, dict[str, Any]]
        if isinstance(self.prompt_template, Unset):
            prompt_template = UNSET
        elif isinstance(self.prompt_template, RiskPromptTemplateType0):
            prompt_template = self.prompt_template.to_dict()
        else:
            prompt_template = self.prompt_template

        llm_configuration: Union[None, Unset, dict[str, Any]]
        if isinstance(self.llm_configuration, Unset):
            llm_configuration = UNSET
        elif isinstance(self.llm_configuration, RiskLlmConfigurationType0):
            llm_configuration = self.llm_configuration.to_dict()
        else:
            llm_configuration = self.llm_configuration

        draft_version: Union[None, Unset, int]
        if isinstance(self.draft_version, Unset):
            draft_version = UNSET
        else:
            draft_version = self.draft_version

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "id": id,
                "name": name,
                "createdAt": created_at,
                "createdBy": created_by,
                "type": type_,
                "promptSource": prompt_source,
                "version": version,
                "lineageId": lineage_id,
                "isPublished": is_published,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if legacy_judge_description is not UNSET:
            field_dict["legacyJudgeDescription"] = legacy_judge_description
        if model_name is not UNSET:
            field_dict["modelName"] = model_name
        if prompt is not UNSET:
            field_dict["prompt"] = prompt
        if prompt_template is not UNSET:
            field_dict["promptTemplate"] = prompt_template
        if llm_configuration is not UNSET:
            field_dict["llmConfiguration"] = llm_configuration
        if draft_version is not UNSET:
            field_dict["draftVersion"] = draft_version

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.risk_llm_configuration_type_0 import RiskLlmConfigurationType0
        from ..models.risk_prompt_template_type_0 import RiskPromptTemplateType0

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        created_at = isoparse(d.pop("createdAt"))

        created_by = d.pop("createdBy")

        type_ = RiskType(d.pop("type"))

        prompt_source = RiskPromptSource(d.pop("promptSource"))

        version = d.pop("version")

        lineage_id = UUID(d.pop("lineageId"))

        is_published = d.pop("isPublished")

        def _parse_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_legacy_judge_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        legacy_judge_description = _parse_legacy_judge_description(
            d.pop("legacyJudgeDescription", UNSET)
        )

        def _parse_model_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        model_name = _parse_model_name(d.pop("modelName", UNSET))

        def _parse_prompt(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        prompt = _parse_prompt(d.pop("prompt", UNSET))

        def _parse_prompt_template(
            data: object,
        ) -> Union["RiskPromptTemplateType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                prompt_template_type_0 = RiskPromptTemplateType0.from_dict(data)

                return prompt_template_type_0
            except:  # noqa: E722
                pass
            return cast(Union["RiskPromptTemplateType0", None, Unset], data)

        prompt_template = _parse_prompt_template(d.pop("promptTemplate", UNSET))

        def _parse_llm_configuration(
            data: object,
        ) -> Union["RiskLlmConfigurationType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                llm_configuration_type_0 = RiskLlmConfigurationType0.from_dict(data)

                return llm_configuration_type_0
            except:  # noqa: E722
                pass
            return cast(Union["RiskLlmConfigurationType0", None, Unset], data)

        llm_configuration = _parse_llm_configuration(d.pop("llmConfiguration", UNSET))

        def _parse_draft_version(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        draft_version = _parse_draft_version(d.pop("draftVersion", UNSET))

        risk = cls(
            id=id,
            name=name,
            created_at=created_at,
            created_by=created_by,
            type_=type_,
            prompt_source=prompt_source,
            version=version,
            lineage_id=lineage_id,
            is_published=is_published,
            description=description,
            legacy_judge_description=legacy_judge_description,
            model_name=model_name,
            prompt=prompt,
            prompt_template=prompt_template,
            llm_configuration=llm_configuration,
            draft_version=draft_version,
        )

        return risk
