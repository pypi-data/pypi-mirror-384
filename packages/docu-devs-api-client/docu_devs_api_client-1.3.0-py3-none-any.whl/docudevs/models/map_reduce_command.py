from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.map_reduce_header_command import MapReduceHeaderCommand


T = TypeVar("T", bound="MapReduceCommand")


@_attrs_define
class MapReduceCommand:
    """
    Attributes:
        enabled (bool):
        pages_per_chunk (Union[None, Unset, int]):
        overlap_pages (Union[None, Unset, int]):
        dedup_key (Union[None, Unset, str]):
        header (Union[Unset, MapReduceHeaderCommand]):
    """

    enabled: bool
    pages_per_chunk: Union[None, Unset, int] = UNSET
    overlap_pages: Union[None, Unset, int] = UNSET
    dedup_key: Union[None, Unset, str] = UNSET
    header: Union[Unset, "MapReduceHeaderCommand"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        enabled = self.enabled

        pages_per_chunk: Union[None, Unset, int]
        if isinstance(self.pages_per_chunk, Unset):
            pages_per_chunk = UNSET
        else:
            pages_per_chunk = self.pages_per_chunk

        overlap_pages: Union[None, Unset, int]
        if isinstance(self.overlap_pages, Unset):
            overlap_pages = UNSET
        else:
            overlap_pages = self.overlap_pages

        dedup_key: Union[None, Unset, str]
        if isinstance(self.dedup_key, Unset):
            dedup_key = UNSET
        else:
            dedup_key = self.dedup_key

        header: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.header, Unset):
            header = self.header.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "enabled": enabled,
            }
        )
        if pages_per_chunk is not UNSET:
            field_dict["pagesPerChunk"] = pages_per_chunk
        if overlap_pages is not UNSET:
            field_dict["overlapPages"] = overlap_pages
        if dedup_key is not UNSET:
            field_dict["dedupKey"] = dedup_key
        if header is not UNSET:
            field_dict["header"] = header

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.map_reduce_header_command import MapReduceHeaderCommand

        d = dict(src_dict)
        enabled = d.pop("enabled")

        def _parse_pages_per_chunk(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        pages_per_chunk = _parse_pages_per_chunk(d.pop("pagesPerChunk", UNSET))

        def _parse_overlap_pages(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        overlap_pages = _parse_overlap_pages(d.pop("overlapPages", UNSET))

        def _parse_dedup_key(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        dedup_key = _parse_dedup_key(d.pop("dedupKey", UNSET))

        _header = d.pop("header", UNSET)
        header: Union[Unset, MapReduceHeaderCommand]
        if isinstance(_header, Unset):
            header = UNSET
        else:
            header = MapReduceHeaderCommand.from_dict(_header)

        map_reduce_command = cls(
            enabled=enabled,
            pages_per_chunk=pages_per_chunk,
            overlap_pages=overlap_pages,
            dedup_key=dedup_key,
            header=header,
        )

        map_reduce_command.additional_properties = d
        return map_reduce_command

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
