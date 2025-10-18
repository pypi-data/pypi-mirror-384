from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast
from typing import Union

if TYPE_CHECKING:
    from ..models.experiment_create_schema_source_data_type_0 import (
        ExperimentCreateSchemaSourceDataType0,
    )
    from ..models.experiment_create_schema_risks_item import (
        ExperimentCreateSchemaRisksItem,
    )


T = TypeVar("T", bound="ExperimentCreateSchema")


@_attrs_define
class ExperimentCreateSchema:
    """
    Attributes:
        name (str):
        role (str):
        is_template (bool):
        description (Union[None, Unset, str]):
        source_data (Union['ExperimentCreateSchemaSourceDataType0', None, Unset]):
        user_description (Union[None, Unset, str]):
        use_cases (Union[None, Unset, str]):
        generation_status (Union[None, Unset, str]):
        evaluation_status (Union[None, Unset, str]):
        validation_status (Union[None, Unset, str]):
        app_id (Union[None, Unset, str]):
        application_id (Union[None, Unset, str]):
        risks (Union[Unset, list['ExperimentCreateSchemaRisksItem']]):
    """

    name: str
    role: str
    is_template: bool
    description: Union[None, Unset, str] = UNSET
    source_data: Union["ExperimentCreateSchemaSourceDataType0", None, Unset] = UNSET
    user_description: Union[None, Unset, str] = UNSET
    use_cases: Union[None, Unset, str] = UNSET
    generation_status: Union[None, Unset, str] = UNSET
    evaluation_status: Union[None, Unset, str] = UNSET
    validation_status: Union[None, Unset, str] = UNSET
    app_id: Union[None, Unset, str] = UNSET
    application_id: Union[None, Unset, str] = UNSET
    risks: Union[Unset, list["ExperimentCreateSchemaRisksItem"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.experiment_create_schema_source_data_type_0 import (
            ExperimentCreateSchemaSourceDataType0,
        )

        name = self.name

        role = self.role

        is_template = self.is_template

        description: Union[None, Unset, str]
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        source_data: Union[None, Unset, dict[str, Any]]
        if isinstance(self.source_data, Unset):
            source_data = UNSET
        elif isinstance(self.source_data, ExperimentCreateSchemaSourceDataType0):
            source_data = self.source_data.to_dict()
        else:
            source_data = self.source_data

        user_description: Union[None, Unset, str]
        if isinstance(self.user_description, Unset):
            user_description = UNSET
        else:
            user_description = self.user_description

        use_cases: Union[None, Unset, str]
        if isinstance(self.use_cases, Unset):
            use_cases = UNSET
        else:
            use_cases = self.use_cases

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

        app_id: Union[None, Unset, str]
        if isinstance(self.app_id, Unset):
            app_id = UNSET
        else:
            app_id = self.app_id

        application_id: Union[None, Unset, str]
        if isinstance(self.application_id, Unset):
            application_id = UNSET
        else:
            application_id = self.application_id

        risks: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.risks, Unset):
            risks = []
            for risks_item_data in self.risks:
                risks_item = risks_item_data.to_dict()
                risks.append(risks_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "role": role,
                "is_template": is_template,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if source_data is not UNSET:
            field_dict["source_data"] = source_data
        if user_description is not UNSET:
            field_dict["user_description"] = user_description
        if use_cases is not UNSET:
            field_dict["use_cases"] = use_cases
        if generation_status is not UNSET:
            field_dict["generation_status"] = generation_status
        if evaluation_status is not UNSET:
            field_dict["evaluation_status"] = evaluation_status
        if validation_status is not UNSET:
            field_dict["validation_status"] = validation_status
        if app_id is not UNSET:
            field_dict["app_id"] = app_id
        if application_id is not UNSET:
            field_dict["application_id"] = application_id
        if risks is not UNSET:
            field_dict["risks"] = risks

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.experiment_create_schema_source_data_type_0 import (
            ExperimentCreateSchemaSourceDataType0,
        )
        from ..models.experiment_create_schema_risks_item import (
            ExperimentCreateSchemaRisksItem,
        )

        d = dict(src_dict)
        name = d.pop("name")

        role = d.pop("role")

        is_template = d.pop("is_template")

        def _parse_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_source_data(
            data: object,
        ) -> Union["ExperimentCreateSchemaSourceDataType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                source_data_type_0 = ExperimentCreateSchemaSourceDataType0.from_dict(
                    data
                )

                return source_data_type_0
            except:  # noqa: E722
                pass
            return cast(
                Union["ExperimentCreateSchemaSourceDataType0", None, Unset], data
            )

        source_data = _parse_source_data(d.pop("source_data", UNSET))

        def _parse_user_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        user_description = _parse_user_description(d.pop("user_description", UNSET))

        def _parse_use_cases(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        use_cases = _parse_use_cases(d.pop("use_cases", UNSET))

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

        def _parse_app_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        app_id = _parse_app_id(d.pop("app_id", UNSET))

        def _parse_application_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        application_id = _parse_application_id(d.pop("application_id", UNSET))

        risks = []
        _risks = d.pop("risks", UNSET)
        for risks_item_data in _risks or []:
            risks_item = ExperimentCreateSchemaRisksItem.from_dict(risks_item_data)

            risks.append(risks_item)

        experiment_create_schema = cls(
            name=name,
            role=role,
            is_template=is_template,
            description=description,
            source_data=source_data,
            user_description=user_description,
            use_cases=use_cases,
            generation_status=generation_status,
            evaluation_status=evaluation_status,
            validation_status=validation_status,
            app_id=app_id,
            application_id=application_id,
            risks=risks,
        )

        experiment_create_schema.additional_properties = d
        return experiment_create_schema

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
