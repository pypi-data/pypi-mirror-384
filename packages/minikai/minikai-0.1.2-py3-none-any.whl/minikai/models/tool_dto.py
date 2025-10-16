from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="ToolDto")


@_attrs_define
class ToolDto:
    """
    Attributes:
        id (Union[Unset, int]):
        name (Union[Unset, str]):
        description (Union[Unset, str]):
        endpoint (Union[Unset, str]):
        schema (Union[Unset, str]):
    """

    id: Union[Unset, int] = UNSET
    name: Union[Unset, str] = UNSET
    description: Union[Unset, str] = UNSET
    endpoint: Union[Unset, str] = UNSET
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        description = self.description

        endpoint = self.endpoint

        schema = self.schema

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if name is not UNSET:
            field_dict["name"] = name
        if description is not UNSET:
            field_dict["description"] = description
        if endpoint is not UNSET:
            field_dict["endpoint"] = endpoint
        if schema is not UNSET:
            field_dict["schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        name = d.pop("name", UNSET)

        description = d.pop("description", UNSET)

        endpoint = d.pop("endpoint", UNSET)

        schema = d.pop("schema", UNSET)

        tool_dto = cls(
            id=id,
            name=name,
            description=description,
            endpoint=endpoint,
            schema=schema,
        )

        return tool_dto
