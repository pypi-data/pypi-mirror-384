from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.update_llm_provider_request_kwargs_type_1 import UpdateLlmProviderRequestKwargsType1


T = TypeVar("T", bound="UpdateLlmProviderRequest")


@_attrs_define
class UpdateLlmProviderRequest:
    """
    Attributes:
        name (Union[None, Unset, str]):
        api_url (Union[None, Unset, str]):
        model_type (Union[None, Unset, str]):
        deployment_name (Union[None, Unset, str]):
        kwargs (Union['UpdateLlmProviderRequestKwargsType1', None, Unset]):
        api_key (Union[None, Unset, str]):
        status (Union[None, Unset, str]):
    """

    name: Union[None, Unset, str] = UNSET
    api_url: Union[None, Unset, str] = UNSET
    model_type: Union[None, Unset, str] = UNSET
    deployment_name: Union[None, Unset, str] = UNSET
    kwargs: Union["UpdateLlmProviderRequestKwargsType1", None, Unset] = UNSET
    api_key: Union[None, Unset, str] = UNSET
    status: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.update_llm_provider_request_kwargs_type_1 import UpdateLlmProviderRequestKwargsType1

        name: Union[None, Unset, str]
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        api_url: Union[None, Unset, str]
        if isinstance(self.api_url, Unset):
            api_url = UNSET
        else:
            api_url = self.api_url

        model_type: Union[None, Unset, str]
        if isinstance(self.model_type, Unset):
            model_type = UNSET
        else:
            model_type = self.model_type

        deployment_name: Union[None, Unset, str]
        if isinstance(self.deployment_name, Unset):
            deployment_name = UNSET
        else:
            deployment_name = self.deployment_name

        kwargs: Union[None, Unset, dict[str, Any]]
        if isinstance(self.kwargs, Unset):
            kwargs = UNSET
        elif isinstance(self.kwargs, UpdateLlmProviderRequestKwargsType1):
            kwargs = self.kwargs.to_dict()
        else:
            kwargs = self.kwargs

        api_key: Union[None, Unset, str]
        if isinstance(self.api_key, Unset):
            api_key = UNSET
        else:
            api_key = self.api_key

        status: Union[None, Unset, str]
        if isinstance(self.status, Unset):
            status = UNSET
        else:
            status = self.status

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if api_url is not UNSET:
            field_dict["apiUrl"] = api_url
        if model_type is not UNSET:
            field_dict["modelType"] = model_type
        if deployment_name is not UNSET:
            field_dict["deploymentName"] = deployment_name
        if kwargs is not UNSET:
            field_dict["kwargs"] = kwargs
        if api_key is not UNSET:
            field_dict["apiKey"] = api_key
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.update_llm_provider_request_kwargs_type_1 import UpdateLlmProviderRequestKwargsType1

        d = dict(src_dict)

        def _parse_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_api_url(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        api_url = _parse_api_url(d.pop("apiUrl", UNSET))

        def _parse_model_type(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        model_type = _parse_model_type(d.pop("modelType", UNSET))

        def _parse_deployment_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        deployment_name = _parse_deployment_name(d.pop("deploymentName", UNSET))

        def _parse_kwargs(data: object) -> Union["UpdateLlmProviderRequestKwargsType1", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                kwargs_type_1 = UpdateLlmProviderRequestKwargsType1.from_dict(data)

                return kwargs_type_1
            except:  # noqa: E722
                pass
            return cast(Union["UpdateLlmProviderRequestKwargsType1", None, Unset], data)

        kwargs = _parse_kwargs(d.pop("kwargs", UNSET))

        def _parse_api_key(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        api_key = _parse_api_key(d.pop("apiKey", UNSET))

        def _parse_status(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        status = _parse_status(d.pop("status", UNSET))

        update_llm_provider_request = cls(
            name=name,
            api_url=api_url,
            model_type=model_type,
            deployment_name=deployment_name,
            kwargs=kwargs,
            api_key=api_key,
            status=status,
        )

        update_llm_provider_request.additional_properties = d
        return update_llm_provider_request

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
