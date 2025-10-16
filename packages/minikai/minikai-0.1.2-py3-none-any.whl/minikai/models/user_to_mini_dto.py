from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="UserToMiniDto")


@_attrs_define
class UserToMiniDto:
    """
    Attributes:
        user_id (Union[Unset, str]):
        mini_id (Union[Unset, int]):
        mini_name (Union[Unset, str]):
        mini_description (Union[None, Unset, str]):
    """

    user_id: Union[Unset, str] = UNSET
    mini_id: Union[Unset, int] = UNSET
    mini_name: Union[Unset, str] = UNSET
    mini_description: Union[None, Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        user_id = self.user_id

        mini_id = self.mini_id

        mini_name = self.mini_name

        mini_description: Union[None, Unset, str]
        if isinstance(self.mini_description, Unset):
            mini_description = UNSET
        else:
            mini_description = self.mini_description

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if user_id is not UNSET:
            field_dict["userId"] = user_id
        if mini_id is not UNSET:
            field_dict["miniId"] = mini_id
        if mini_name is not UNSET:
            field_dict["miniName"] = mini_name
        if mini_description is not UNSET:
            field_dict["miniDescription"] = mini_description

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        user_id = d.pop("userId", UNSET)

        mini_id = d.pop("miniId", UNSET)

        mini_name = d.pop("miniName", UNSET)

        def _parse_mini_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        mini_description = _parse_mini_description(d.pop("miniDescription", UNSET))

        user_to_mini_dto = cls(
            user_id=user_id,
            mini_id=mini_id,
            mini_name=mini_name,
            mini_description=mini_description,
        )

        return user_to_mini_dto
