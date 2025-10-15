from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.tool_dto import ToolDto
    from ..models.workspace_dto import WorkspaceDto


T = TypeVar("T", bound="MiniTemplateDto")


@_attrs_define
class MiniTemplateDto:
    """
    Attributes:
        id (Union[Unset, str]):
        name (Union[Unset, str]):
        description (Union[None, Unset, str]):
        instructions (Union[None, Unset, str]):
        workspaces (Union[Unset, list['WorkspaceDto']]):
        tools (Union[Unset, list['ToolDto']]):
    """

    id: Union[Unset, str] = UNSET
    name: Union[Unset, str] = UNSET
    description: Union[None, Unset, str] = UNSET
    instructions: Union[None, Unset, str] = UNSET
    workspaces: Union[Unset, list["WorkspaceDto"]] = UNSET
    tools: Union[Unset, list["ToolDto"]] = UNSET

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        description: Union[None, Unset, str]
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        instructions: Union[None, Unset, str]
        if isinstance(self.instructions, Unset):
            instructions = UNSET
        else:
            instructions = self.instructions

        workspaces: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.workspaces, Unset):
            workspaces = []
            for workspaces_item_data in self.workspaces:
                workspaces_item = workspaces_item_data.to_dict()
                workspaces.append(workspaces_item)

        tools: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.tools, Unset):
            tools = []
            for tools_item_data in self.tools:
                tools_item = tools_item_data.to_dict()
                tools.append(tools_item)

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if name is not UNSET:
            field_dict["name"] = name
        if description is not UNSET:
            field_dict["description"] = description
        if instructions is not UNSET:
            field_dict["instructions"] = instructions
        if workspaces is not UNSET:
            field_dict["workspaces"] = workspaces
        if tools is not UNSET:
            field_dict["tools"] = tools

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.tool_dto import ToolDto
        from ..models.workspace_dto import WorkspaceDto

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

        def _parse_instructions(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        instructions = _parse_instructions(d.pop("instructions", UNSET))

        workspaces = []
        _workspaces = d.pop("workspaces", UNSET)
        for workspaces_item_data in _workspaces or []:
            workspaces_item = WorkspaceDto.from_dict(workspaces_item_data)

            workspaces.append(workspaces_item)

        tools = []
        _tools = d.pop("tools", UNSET)
        for tools_item_data in _tools or []:
            tools_item = ToolDto.from_dict(tools_item_data)

            tools.append(tools_item)

        mini_template_dto = cls(
            id=id,
            name=name,
            description=description,
            instructions=instructions,
            workspaces=workspaces,
            tools=tools,
        )

        return mini_template_dto
