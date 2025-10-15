from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="MapReduceHeaderCommand")


@_attrs_define
class MapReduceHeaderCommand:
    """
    Attributes:
        enabled (bool):
        page_limit (Union[None, Unset, int]):
        include_in_rows (Union[None, Unset, bool]):
        schema (Union[None, Unset, str]):
        schema_file_name (Union[None, Unset, str]):
        prompt (Union[None, Unset, str]):
        prompt_file_name (Union[None, Unset, str]):
        row_prompt_augmentation (Union[None, Unset, str]):
    """

    enabled: bool
    page_limit: Union[None, Unset, int] = UNSET
    include_in_rows: Union[None, Unset, bool] = UNSET
    schema: Union[None, Unset, str] = UNSET
    schema_file_name: Union[None, Unset, str] = UNSET
    prompt: Union[None, Unset, str] = UNSET
    prompt_file_name: Union[None, Unset, str] = UNSET
    row_prompt_augmentation: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        enabled = self.enabled

        page_limit: Union[None, Unset, int]
        if isinstance(self.page_limit, Unset):
            page_limit = UNSET
        else:
            page_limit = self.page_limit

        include_in_rows: Union[None, Unset, bool]
        if isinstance(self.include_in_rows, Unset):
            include_in_rows = UNSET
        else:
            include_in_rows = self.include_in_rows

        schema: Union[None, Unset, str]
        if isinstance(self.schema, Unset):
            schema = UNSET
        else:
            schema = self.schema

        schema_file_name: Union[None, Unset, str]
        if isinstance(self.schema_file_name, Unset):
            schema_file_name = UNSET
        else:
            schema_file_name = self.schema_file_name

        prompt: Union[None, Unset, str]
        if isinstance(self.prompt, Unset):
            prompt = UNSET
        else:
            prompt = self.prompt

        prompt_file_name: Union[None, Unset, str]
        if isinstance(self.prompt_file_name, Unset):
            prompt_file_name = UNSET
        else:
            prompt_file_name = self.prompt_file_name

        row_prompt_augmentation: Union[None, Unset, str]
        if isinstance(self.row_prompt_augmentation, Unset):
            row_prompt_augmentation = UNSET
        else:
            row_prompt_augmentation = self.row_prompt_augmentation

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "enabled": enabled,
            }
        )
        if page_limit is not UNSET:
            field_dict["pageLimit"] = page_limit
        if include_in_rows is not UNSET:
            field_dict["includeInRows"] = include_in_rows
        if schema is not UNSET:
            field_dict["schema"] = schema
        if schema_file_name is not UNSET:
            field_dict["schemaFileName"] = schema_file_name
        if prompt is not UNSET:
            field_dict["prompt"] = prompt
        if prompt_file_name is not UNSET:
            field_dict["promptFileName"] = prompt_file_name
        if row_prompt_augmentation is not UNSET:
            field_dict["rowPromptAugmentation"] = row_prompt_augmentation

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        enabled = d.pop("enabled")

        def _parse_page_limit(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        page_limit = _parse_page_limit(d.pop("pageLimit", UNSET))

        def _parse_include_in_rows(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        include_in_rows = _parse_include_in_rows(d.pop("includeInRows", UNSET))

        def _parse_schema(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        schema = _parse_schema(d.pop("schema", UNSET))

        def _parse_schema_file_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        schema_file_name = _parse_schema_file_name(d.pop("schemaFileName", UNSET))

        def _parse_prompt(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        prompt = _parse_prompt(d.pop("prompt", UNSET))

        def _parse_prompt_file_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        prompt_file_name = _parse_prompt_file_name(d.pop("promptFileName", UNSET))

        def _parse_row_prompt_augmentation(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        row_prompt_augmentation = _parse_row_prompt_augmentation(d.pop("rowPromptAugmentation", UNSET))

        map_reduce_header_command = cls(
            enabled=enabled,
            page_limit=page_limit,
            include_in_rows=include_in_rows,
            schema=schema,
            schema_file_name=schema_file_name,
            prompt=prompt,
            prompt_file_name=prompt_file_name,
            row_prompt_augmentation=row_prompt_augmentation,
        )

        map_reduce_header_command.additional_properties = d
        return map_reduce_header_command

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
