from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="DocumentFileDto")


@_attrs_define
class DocumentFileDto:
    """
    Attributes:
        id (Union[Unset, int]):
        file_id (Union[Unset, str]):
        doc_file_id (Union[Unset, str]):
        name (Union[None, Unset, str]):
        content_type (Union[None, Unset, str]):
        file_extension (Union[None, Unset, str]):
        size (Union[Unset, int]):
        workspace_id (Union[None, Unset, str]):
    """

    id: Union[Unset, int] = UNSET
    file_id: Union[Unset, str] = UNSET
    doc_file_id: Union[Unset, str] = UNSET
    name: Union[None, Unset, str] = UNSET
    content_type: Union[None, Unset, str] = UNSET
    file_extension: Union[None, Unset, str] = UNSET
    size: Union[Unset, int] = UNSET
    workspace_id: Union[None, Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        file_id = self.file_id

        doc_file_id = self.doc_file_id

        name: Union[None, Unset, str]
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        content_type: Union[None, Unset, str]
        if isinstance(self.content_type, Unset):
            content_type = UNSET
        else:
            content_type = self.content_type

        file_extension: Union[None, Unset, str]
        if isinstance(self.file_extension, Unset):
            file_extension = UNSET
        else:
            file_extension = self.file_extension

        size = self.size

        workspace_id: Union[None, Unset, str]
        if isinstance(self.workspace_id, Unset):
            workspace_id = UNSET
        else:
            workspace_id = self.workspace_id

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if file_id is not UNSET:
            field_dict["fileId"] = file_id
        if doc_file_id is not UNSET:
            field_dict["docFileId"] = doc_file_id
        if name is not UNSET:
            field_dict["name"] = name
        if content_type is not UNSET:
            field_dict["contentType"] = content_type
        if file_extension is not UNSET:
            field_dict["fileExtension"] = file_extension
        if size is not UNSET:
            field_dict["size"] = size
        if workspace_id is not UNSET:
            field_dict["workspaceId"] = workspace_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        file_id = d.pop("fileId", UNSET)

        doc_file_id = d.pop("docFileId", UNSET)

        def _parse_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_content_type(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        content_type = _parse_content_type(d.pop("contentType", UNSET))

        def _parse_file_extension(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        file_extension = _parse_file_extension(d.pop("fileExtension", UNSET))

        size = d.pop("size", UNSET)

        def _parse_workspace_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        workspace_id = _parse_workspace_id(d.pop("workspaceId", UNSET))

        document_file_dto = cls(
            id=id,
            file_id=file_id,
            doc_file_id=doc_file_id,
            name=name,
            content_type=content_type,
            file_extension=file_extension,
            size=size,
            workspace_id=workspace_id,
        )

        return document_file_dto
