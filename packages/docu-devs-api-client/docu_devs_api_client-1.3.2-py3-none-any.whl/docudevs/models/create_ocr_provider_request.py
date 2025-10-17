from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_ocr_provider_request_features_type_1 import CreateOcrProviderRequestFeaturesType1


T = TypeVar("T", bound="CreateOcrProviderRequest")


@_attrs_define
class CreateOcrProviderRequest:
    """
    Attributes:
        name (str):
        endpoint (str):
        api_key (str):
        model_id (str):
        features (Union['CreateOcrProviderRequestFeaturesType1', None, Unset]):
        status (Union[None, Unset, str]):
    """

    name: str
    endpoint: str
    api_key: str
    model_id: str
    features: Union["CreateOcrProviderRequestFeaturesType1", None, Unset] = UNSET
    status: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.create_ocr_provider_request_features_type_1 import CreateOcrProviderRequestFeaturesType1

        name = self.name

        endpoint = self.endpoint

        api_key = self.api_key

        model_id = self.model_id

        features: Union[None, Unset, dict[str, Any]]
        if isinstance(self.features, Unset):
            features = UNSET
        elif isinstance(self.features, CreateOcrProviderRequestFeaturesType1):
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
        field_dict.update(
            {
                "name": name,
                "endpoint": endpoint,
                "apiKey": api_key,
                "modelId": model_id,
            }
        )
        if features is not UNSET:
            field_dict["features"] = features
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_ocr_provider_request_features_type_1 import CreateOcrProviderRequestFeaturesType1

        d = dict(src_dict)
        name = d.pop("name")

        endpoint = d.pop("endpoint")

        api_key = d.pop("apiKey")

        model_id = d.pop("modelId")

        def _parse_features(data: object) -> Union["CreateOcrProviderRequestFeaturesType1", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                features_type_1 = CreateOcrProviderRequestFeaturesType1.from_dict(data)

                return features_type_1
            except:  # noqa: E722
                pass
            return cast(Union["CreateOcrProviderRequestFeaturesType1", None, Unset], data)

        features = _parse_features(d.pop("features", UNSET))

        def _parse_status(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        status = _parse_status(d.pop("status", UNSET))

        create_ocr_provider_request = cls(
            name=name,
            endpoint=endpoint,
            api_key=api_key,
            model_id=model_id,
            features=features,
            status=status,
        )

        create_ocr_provider_request.additional_properties = d
        return create_ocr_provider_request

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
