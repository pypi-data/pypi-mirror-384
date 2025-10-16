from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="DocumentFileMetadataDto")


@_attrs_define
class DocumentFileMetadataDto:
    """
    Attributes:
        content_hash (Union[None, Unset, str]):
    """

    content_hash: Union[None, Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        content_hash: Union[None, Unset, str]
        if isinstance(self.content_hash, Unset):
            content_hash = UNSET
        else:
            content_hash = self.content_hash

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if content_hash is not UNSET:
            field_dict["contentHash"] = content_hash

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_content_hash(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        content_hash = _parse_content_hash(d.pop("contentHash", UNSET))

        document_file_metadata_dto = cls(
            content_hash=content_hash,
        )

        return document_file_metadata_dto
