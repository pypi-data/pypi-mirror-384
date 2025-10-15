import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.record_attachment_dto_metadata_type_0 import RecordAttachmentDtoMetadataType0


T = TypeVar("T", bound="RecordAttachmentDto")


@_attrs_define
class RecordAttachmentDto:
    """
    Attributes:
        id (Union[Unset, str]):
        file_name (Union[Unset, str]):
        content_type (Union[Unset, str]):
        size (Union[Unset, int]):
        checksum (Union[None, Unset, str]):
        uri (Union[Unset, str]):
        created_at (Union[None, Unset, datetime.datetime]):
        updated_at (Union[None, Unset, datetime.datetime]):
        created_by (Union[None, Unset, str]):
        updated_by (Union[None, Unset, str]):
        metadata (Union['RecordAttachmentDtoMetadataType0', None, Unset]):
    """

    id: Union[Unset, str] = UNSET
    file_name: Union[Unset, str] = UNSET
    content_type: Union[Unset, str] = UNSET
    size: Union[Unset, int] = UNSET
    checksum: Union[None, Unset, str] = UNSET
    uri: Union[Unset, str] = UNSET
    created_at: Union[None, Unset, datetime.datetime] = UNSET
    updated_at: Union[None, Unset, datetime.datetime] = UNSET
    created_by: Union[None, Unset, str] = UNSET
    updated_by: Union[None, Unset, str] = UNSET
    metadata: Union["RecordAttachmentDtoMetadataType0", None, Unset] = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.record_attachment_dto_metadata_type_0 import RecordAttachmentDtoMetadataType0

        id = self.id

        file_name = self.file_name

        content_type = self.content_type

        size = self.size

        checksum: Union[None, Unset, str]
        if isinstance(self.checksum, Unset):
            checksum = UNSET
        else:
            checksum = self.checksum

        uri = self.uri

        created_at: Union[None, Unset, str]
        if isinstance(self.created_at, Unset):
            created_at = UNSET
        elif isinstance(self.created_at, datetime.datetime):
            created_at = self.created_at.isoformat()
        else:
            created_at = self.created_at

        updated_at: Union[None, Unset, str]
        if isinstance(self.updated_at, Unset):
            updated_at = UNSET
        elif isinstance(self.updated_at, datetime.datetime):
            updated_at = self.updated_at.isoformat()
        else:
            updated_at = self.updated_at

        created_by: Union[None, Unset, str]
        if isinstance(self.created_by, Unset):
            created_by = UNSET
        else:
            created_by = self.created_by

        updated_by: Union[None, Unset, str]
        if isinstance(self.updated_by, Unset):
            updated_by = UNSET
        else:
            updated_by = self.updated_by

        metadata: Union[None, Unset, dict[str, Any]]
        if isinstance(self.metadata, Unset):
            metadata = UNSET
        elif isinstance(self.metadata, RecordAttachmentDtoMetadataType0):
            metadata = self.metadata.to_dict()
        else:
            metadata = self.metadata

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if file_name is not UNSET:
            field_dict["fileName"] = file_name
        if content_type is not UNSET:
            field_dict["contentType"] = content_type
        if size is not UNSET:
            field_dict["size"] = size
        if checksum is not UNSET:
            field_dict["checksum"] = checksum
        if uri is not UNSET:
            field_dict["uri"] = uri
        if created_at is not UNSET:
            field_dict["createdAt"] = created_at
        if updated_at is not UNSET:
            field_dict["updatedAt"] = updated_at
        if created_by is not UNSET:
            field_dict["createdBy"] = created_by
        if updated_by is not UNSET:
            field_dict["updatedBy"] = updated_by
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.record_attachment_dto_metadata_type_0 import RecordAttachmentDtoMetadataType0

        d = dict(src_dict)
        id = d.pop("id", UNSET)

        file_name = d.pop("fileName", UNSET)

        content_type = d.pop("contentType", UNSET)

        size = d.pop("size", UNSET)

        def _parse_checksum(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        checksum = _parse_checksum(d.pop("checksum", UNSET))

        uri = d.pop("uri", UNSET)

        def _parse_created_at(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                created_at_type_0 = isoparse(data)

                return created_at_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        created_at = _parse_created_at(d.pop("createdAt", UNSET))

        def _parse_updated_at(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                updated_at_type_0 = isoparse(data)

                return updated_at_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        updated_at = _parse_updated_at(d.pop("updatedAt", UNSET))

        def _parse_created_by(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        created_by = _parse_created_by(d.pop("createdBy", UNSET))

        def _parse_updated_by(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        updated_by = _parse_updated_by(d.pop("updatedBy", UNSET))

        def _parse_metadata(data: object) -> Union["RecordAttachmentDtoMetadataType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_type_0 = RecordAttachmentDtoMetadataType0.from_dict(data)

                return metadata_type_0
            except:  # noqa: E722
                pass
            return cast(Union["RecordAttachmentDtoMetadataType0", None, Unset], data)

        metadata = _parse_metadata(d.pop("metadata", UNSET))

        record_attachment_dto = cls(
            id=id,
            file_name=file_name,
            content_type=content_type,
            size=size,
            checksum=checksum,
            uri=uri,
            created_at=created_at,
            updated_at=updated_at,
            created_by=created_by,
            updated_by=updated_by,
            metadata=metadata,
        )

        return record_attachment_dto
