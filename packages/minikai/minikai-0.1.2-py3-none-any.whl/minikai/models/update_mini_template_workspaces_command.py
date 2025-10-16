from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateMiniTemplateWorkspacesCommand")


@_attrs_define
class UpdateMiniTemplateWorkspacesCommand:
    """
    Attributes:
        mini_template_id (Union[Unset, str]):
        workspace_ids (Union[Unset, list[str]]):
    """

    mini_template_id: Union[Unset, str] = UNSET
    workspace_ids: Union[Unset, list[str]] = UNSET

    def to_dict(self) -> dict[str, Any]:
        mini_template_id = self.mini_template_id

        workspace_ids: Union[Unset, list[str]] = UNSET
        if not isinstance(self.workspace_ids, Unset):
            workspace_ids = self.workspace_ids

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if mini_template_id is not UNSET:
            field_dict["miniTemplateId"] = mini_template_id
        if workspace_ids is not UNSET:
            field_dict["workspaceIds"] = workspace_ids

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        mini_template_id = d.pop("miniTemplateId", UNSET)

        workspace_ids = cast(list[str], d.pop("workspaceIds", UNSET))

        update_mini_template_workspaces_command = cls(
            mini_template_id=mini_template_id,
            workspace_ids=workspace_ids,
        )

        return update_mini_template_workspaces_command
