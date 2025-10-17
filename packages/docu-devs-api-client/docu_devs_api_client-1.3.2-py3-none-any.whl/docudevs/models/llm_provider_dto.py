from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="LlmProviderDto")


@_attrs_define
class LlmProviderDto:
    """
    Attributes:
        id (int):
        name (str):
        api_url (str):
        model_type (str):
        kwargs (Any):
        status (str):
        deployment_name (Union[None, Unset, str]):
        created_at (Union[None, Unset, str]):
        updated_at (Union[None, Unset, str]):
    """

    id: int
    name: str
    api_url: str
    model_type: str
    kwargs: Any
    status: str
    deployment_name: Union[None, Unset, str] = UNSET
    created_at: Union[None, Unset, str] = UNSET
    updated_at: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        api_url = self.api_url

        model_type = self.model_type

        kwargs = self.kwargs

        status = self.status

        deployment_name: Union[None, Unset, str]
        if isinstance(self.deployment_name, Unset):
            deployment_name = UNSET
        else:
            deployment_name = self.deployment_name

        created_at: Union[None, Unset, str]
        if isinstance(self.created_at, Unset):
            created_at = UNSET
        else:
            created_at = self.created_at

        updated_at: Union[None, Unset, str]
        if isinstance(self.updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = self.updated_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "apiUrl": api_url,
                "modelType": model_type,
                "kwargs": kwargs,
                "status": status,
            }
        )
        if deployment_name is not UNSET:
            field_dict["deploymentName"] = deployment_name
        if created_at is not UNSET:
            field_dict["createdAt"] = created_at
        if updated_at is not UNSET:
            field_dict["updatedAt"] = updated_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        api_url = d.pop("apiUrl")

        model_type = d.pop("modelType")

        kwargs = d.pop("kwargs")

        status = d.pop("status")

        def _parse_deployment_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        deployment_name = _parse_deployment_name(d.pop("deploymentName", UNSET))

        def _parse_created_at(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        created_at = _parse_created_at(d.pop("createdAt", UNSET))

        def _parse_updated_at(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        updated_at = _parse_updated_at(d.pop("updatedAt", UNSET))

        llm_provider_dto = cls(
            id=id,
            name=name,
            api_url=api_url,
            model_type=model_type,
            kwargs=kwargs,
            status=status,
            deployment_name=deployment_name,
            created_at=created_at,
            updated_at=updated_at,
        )

        llm_provider_dto.additional_properties = d
        return llm_provider_dto

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
