from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_llm_provider_request_kwargs_type_1 import CreateLlmProviderRequestKwargsType1


T = TypeVar("T", bound="CreateLlmProviderRequest")


@_attrs_define
class CreateLlmProviderRequest:
    """
    Attributes:
        name (str):
        api_url (str):
        model_type (str):
        api_key (str):
        deployment_name (Union[None, Unset, str]):
        kwargs (Union['CreateLlmProviderRequestKwargsType1', None, Unset]):
        status (Union[None, Unset, str]):
    """

    name: str
    api_url: str
    model_type: str
    api_key: str
    deployment_name: Union[None, Unset, str] = UNSET
    kwargs: Union["CreateLlmProviderRequestKwargsType1", None, Unset] = UNSET
    status: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.create_llm_provider_request_kwargs_type_1 import CreateLlmProviderRequestKwargsType1

        name = self.name

        api_url = self.api_url

        model_type = self.model_type

        api_key = self.api_key

        deployment_name: Union[None, Unset, str]
        if isinstance(self.deployment_name, Unset):
            deployment_name = UNSET
        else:
            deployment_name = self.deployment_name

        kwargs: Union[None, Unset, dict[str, Any]]
        if isinstance(self.kwargs, Unset):
            kwargs = UNSET
        elif isinstance(self.kwargs, CreateLlmProviderRequestKwargsType1):
            kwargs = self.kwargs.to_dict()
        else:
            kwargs = self.kwargs

        status: Union[None, Unset, str]
        if isinstance(self.status, Unset):
            status = UNSET
        else:
            status = self.status

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "apiUrl": api_url,
                "modelType": model_type,
                "apiKey": api_key,
            }
        )
        if deployment_name is not UNSET:
            field_dict["deploymentName"] = deployment_name
        if kwargs is not UNSET:
            field_dict["kwargs"] = kwargs
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_llm_provider_request_kwargs_type_1 import CreateLlmProviderRequestKwargsType1

        d = dict(src_dict)
        name = d.pop("name")

        api_url = d.pop("apiUrl")

        model_type = d.pop("modelType")

        api_key = d.pop("apiKey")

        def _parse_deployment_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        deployment_name = _parse_deployment_name(d.pop("deploymentName", UNSET))

        def _parse_kwargs(data: object) -> Union["CreateLlmProviderRequestKwargsType1", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                kwargs_type_1 = CreateLlmProviderRequestKwargsType1.from_dict(data)

                return kwargs_type_1
            except:  # noqa: E722
                pass
            return cast(Union["CreateLlmProviderRequestKwargsType1", None, Unset], data)

        kwargs = _parse_kwargs(d.pop("kwargs", UNSET))

        def _parse_status(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        status = _parse_status(d.pop("status", UNSET))

        create_llm_provider_request = cls(
            name=name,
            api_url=api_url,
            model_type=model_type,
            api_key=api_key,
            deployment_name=deployment_name,
            kwargs=kwargs,
            status=status,
        )

        create_llm_provider_request.additional_properties = d
        return create_llm_provider_request

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
