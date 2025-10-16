from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateMiniCommand")


@_attrs_define
class UpdateMiniCommand:
    """
    Attributes:
        id (Union[Unset, int]):
        name (Union[Unset, str]):
        description (Union[None, Unset, str]):
        template_id (Union[None, Unset, str]):
        external_id (Union[None, Unset, str]):
        external_source (Union[None, Unset, str]):
    """

    id: Union[Unset, int] = UNSET
    name: Union[Unset, str] = UNSET
    description: Union[None, Unset, str] = UNSET
    template_id: Union[None, Unset, str] = UNSET
    external_id: Union[None, Unset, str] = UNSET
    external_source: Union[None, Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        description: Union[None, Unset, str]
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        template_id: Union[None, Unset, str]
        if isinstance(self.template_id, Unset):
            template_id = UNSET
        else:
            template_id = self.template_id

        external_id: Union[None, Unset, str]
        if isinstance(self.external_id, Unset):
            external_id = UNSET
        else:
            external_id = self.external_id

        external_source: Union[None, Unset, str]
        if isinstance(self.external_source, Unset):
            external_source = UNSET
        else:
            external_source = self.external_source

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if name is not UNSET:
            field_dict["name"] = name
        if description is not UNSET:
            field_dict["description"] = description
        if template_id is not UNSET:
            field_dict["templateId"] = template_id
        if external_id is not UNSET:
            field_dict["externalId"] = external_id
        if external_source is not UNSET:
            field_dict["externalSource"] = external_source

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        name = d.pop("name", UNSET)

        def _parse_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_template_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        template_id = _parse_template_id(d.pop("templateId", UNSET))

        def _parse_external_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        external_id = _parse_external_id(d.pop("externalId", UNSET))

        def _parse_external_source(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        external_source = _parse_external_source(d.pop("externalSource", UNSET))

        update_mini_command = cls(
            id=id,
            name=name,
            description=description,
            template_id=template_id,
            external_id=external_id,
            external_source=external_source,
        )

        return update_mini_command
