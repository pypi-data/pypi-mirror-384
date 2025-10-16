import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="RecordRelationDto")


@_attrs_define
class RecordRelationDto:
    """
    Attributes:
        id (Union[Unset, str]):
        relationship (Union[Unset, str]):
        since (Union[None, Unset, datetime.datetime]):
    """

    id: Union[Unset, str] = UNSET
    relationship: Union[Unset, str] = UNSET
    since: Union[None, Unset, datetime.datetime] = UNSET

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        relationship = self.relationship

        since: Union[None, Unset, str]
        if isinstance(self.since, Unset):
            since = UNSET
        elif isinstance(self.since, datetime.datetime):
            since = self.since.isoformat()
        else:
            since = self.since

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if relationship is not UNSET:
            field_dict["relationship"] = relationship
        if since is not UNSET:
            field_dict["since"] = since

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        relationship = d.pop("relationship", UNSET)

        def _parse_since(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                since_type_0 = isoparse(data)

                return since_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        since = _parse_since(d.pop("since", UNSET))

        record_relation_dto = cls(
            id=id,
            relationship=relationship,
            since=since,
        )

        return record_relation_dto
