from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="RecordAuthorizationDto")


@_attrs_define
class RecordAuthorizationDto:
    """
    Attributes:
        users (Union[Unset, list[str]]):
        minis (Union[Unset, list[str]]):
        organizations (Union[Unset, list[str]]):
        sessions (Union[Unset, list[str]]):
    """

    users: Union[Unset, list[str]] = UNSET
    minis: Union[Unset, list[str]] = UNSET
    organizations: Union[Unset, list[str]] = UNSET
    sessions: Union[Unset, list[str]] = UNSET

    def to_dict(self) -> dict[str, Any]:
        users: Union[Unset, list[str]] = UNSET
        if not isinstance(self.users, Unset):
            users = self.users

        minis: Union[Unset, list[str]] = UNSET
        if not isinstance(self.minis, Unset):
            minis = self.minis

        organizations: Union[Unset, list[str]] = UNSET
        if not isinstance(self.organizations, Unset):
            organizations = self.organizations

        sessions: Union[Unset, list[str]] = UNSET
        if not isinstance(self.sessions, Unset):
            sessions = self.sessions

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if users is not UNSET:
            field_dict["users"] = users
        if minis is not UNSET:
            field_dict["minis"] = minis
        if organizations is not UNSET:
            field_dict["organizations"] = organizations
        if sessions is not UNSET:
            field_dict["sessions"] = sessions

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        users = cast(list[str], d.pop("users", UNSET))

        minis = cast(list[str], d.pop("minis", UNSET))

        organizations = cast(list[str], d.pop("organizations", UNSET))

        sessions = cast(list[str], d.pop("sessions", UNSET))

        record_authorization_dto = cls(
            users=users,
            minis=minis,
            organizations=organizations,
            sessions=sessions,
        )

        return record_authorization_dto
