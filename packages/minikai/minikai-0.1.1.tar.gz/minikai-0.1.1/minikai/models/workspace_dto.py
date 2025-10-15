from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="WorkspaceDto")


@_attrs_define
class WorkspaceDto:
    """
    Attributes:
        id (Union[Unset, int]):
        workspace_id (Union[Unset, str]):
        name (Union[Unset, str]):
        organization_id (Union[None, Unset, str]):
    """

    id: Union[Unset, int] = UNSET
    workspace_id: Union[Unset, str] = UNSET
    name: Union[Unset, str] = UNSET
    organization_id: Union[None, Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        workspace_id = self.workspace_id

        name = self.name

        organization_id: Union[None, Unset, str]
        if isinstance(self.organization_id, Unset):
            organization_id = UNSET
        else:
            organization_id = self.organization_id

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if workspace_id is not UNSET:
            field_dict["workspaceId"] = workspace_id
        if name is not UNSET:
            field_dict["name"] = name
        if organization_id is not UNSET:
            field_dict["organizationId"] = organization_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        workspace_id = d.pop("workspaceId", UNSET)

        name = d.pop("name", UNSET)

        def _parse_organization_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        organization_id = _parse_organization_id(d.pop("organizationId", UNSET))

        workspace_dto = cls(
            id=id,
            workspace_id=workspace_id,
            name=name,
            organization_id=organization_id,
        )

        return workspace_dto
