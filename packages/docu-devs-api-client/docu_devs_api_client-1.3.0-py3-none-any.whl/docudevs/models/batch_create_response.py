from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="BatchCreateResponse")


@_attrs_define
class BatchCreateResponse:
    """
    Attributes:
        job_guid (str):
        max_concurrency (int):
    """

    job_guid: str
    max_concurrency: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        job_guid = self.job_guid

        max_concurrency = self.max_concurrency

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "jobGuid": job_guid,
                "maxConcurrency": max_concurrency,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        job_guid = d.pop("jobGuid")

        max_concurrency = d.pop("maxConcurrency")

        batch_create_response = cls(
            job_guid=job_guid,
            max_concurrency=max_concurrency,
        )

        batch_create_response.additional_properties = d
        return batch_create_response

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
