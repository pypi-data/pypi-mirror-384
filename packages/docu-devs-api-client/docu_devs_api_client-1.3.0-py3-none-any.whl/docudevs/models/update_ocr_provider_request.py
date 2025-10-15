from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.update_ocr_provider_request_features_type_1 import UpdateOcrProviderRequestFeaturesType1


T = TypeVar("T", bound="UpdateOcrProviderRequest")


@_attrs_define
class UpdateOcrProviderRequest:
    """
    Attributes:
        name (Union[None, Unset, str]):
        endpoint (Union[None, Unset, str]):
        api_key (Union[None, Unset, str]):
        model_id (Union[None, Unset, str]):
        features (Union['UpdateOcrProviderRequestFeaturesType1', None, Unset]):
        status (Union[None, Unset, str]):
    """

    name: Union[None, Unset, str] = UNSET
    endpoint: Union[None, Unset, str] = UNSET
    api_key: Union[None, Unset, str] = UNSET
    model_id: Union[None, Unset, str] = UNSET
    features: Union["UpdateOcrProviderRequestFeaturesType1", None, Unset] = UNSET
    status: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.update_ocr_provider_request_features_type_1 import UpdateOcrProviderRequestFeaturesType1

        name: Union[None, Unset, str]
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        endpoint: Union[None, Unset, str]
        if isinstance(self.endpoint, Unset):
            endpoint = UNSET
        else:
            endpoint = self.endpoint

        api_key: Union[None, Unset, str]
        if isinstance(self.api_key, Unset):
            api_key = UNSET
        else:
            api_key = self.api_key

        model_id: Union[None, Unset, str]
        if isinstance(self.model_id, Unset):
            model_id = UNSET
        else:
            model_id = self.model_id

        features: Union[None, Unset, dict[str, Any]]
        if isinstance(self.features, Unset):
            features = UNSET
        elif isinstance(self.features, UpdateOcrProviderRequestFeaturesType1):
            features = self.features.to_dict()
        else:
            features = self.features

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
        if endpoint is not UNSET:
            field_dict["endpoint"] = endpoint
        if api_key is not UNSET:
            field_dict["apiKey"] = api_key
        if model_id is not UNSET:
            field_dict["modelId"] = model_id
        if features is not UNSET:
            field_dict["features"] = features
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.update_ocr_provider_request_features_type_1 import UpdateOcrProviderRequestFeaturesType1

        d = dict(src_dict)

        def _parse_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_endpoint(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        endpoint = _parse_endpoint(d.pop("endpoint", UNSET))

        def _parse_api_key(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        api_key = _parse_api_key(d.pop("apiKey", UNSET))

        def _parse_model_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        model_id = _parse_model_id(d.pop("modelId", UNSET))

        def _parse_features(data: object) -> Union["UpdateOcrProviderRequestFeaturesType1", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                features_type_1 = UpdateOcrProviderRequestFeaturesType1.from_dict(data)

                return features_type_1
            except:  # noqa: E722
                pass
            return cast(Union["UpdateOcrProviderRequestFeaturesType1", None, Unset], data)

        features = _parse_features(d.pop("features", UNSET))

        def _parse_status(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        status = _parse_status(d.pop("status", UNSET))

        update_ocr_provider_request = cls(
            name=name,
            endpoint=endpoint,
            api_key=api_key,
            model_id=model_id,
            features=features,
            status=status,
        )

        update_ocr_provider_request.additional_properties = d
        return update_ocr_provider_request

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
