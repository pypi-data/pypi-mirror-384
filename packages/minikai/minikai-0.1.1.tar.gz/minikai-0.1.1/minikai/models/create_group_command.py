from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateGroupCommand")


@_attrs_define
class CreateGroupCommand:
    """
    Attributes:
        name (Union[Unset, str]):
        user_ids (Union[None, Unset, list[str]]):
        mini_ids (Union[None, Unset, list[int]]):
    """

    name: Union[Unset, str] = UNSET
    user_ids: Union[None, Unset, list[str]] = UNSET
    mini_ids: Union[None, Unset, list[int]] = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        user_ids: Union[None, Unset, list[str]]
        if isinstance(self.user_ids, Unset):
            user_ids = UNSET
        elif isinstance(self.user_ids, list):
            user_ids = self.user_ids

        else:
            user_ids = self.user_ids

        mini_ids: Union[None, Unset, list[int]]
        if isinstance(self.mini_ids, Unset):
            mini_ids = UNSET
        elif isinstance(self.mini_ids, list):
            mini_ids = self.mini_ids

        else:
            mini_ids = self.mini_ids

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if user_ids is not UNSET:
            field_dict["userIds"] = user_ids
        if mini_ids is not UNSET:
            field_dict["miniIds"] = mini_ids

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name", UNSET)

        def _parse_user_ids(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                user_ids_type_0 = cast(list[str], data)

                return user_ids_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        user_ids = _parse_user_ids(d.pop("userIds", UNSET))

        def _parse_mini_ids(data: object) -> Union[None, Unset, list[int]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                mini_ids_type_0 = cast(list[int], data)

                return mini_ids_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[int]], data)

        mini_ids = _parse_mini_ids(d.pop("miniIds", UNSET))

        create_group_command = cls(
            name=name,
            user_ids=user_ids,
            mini_ids=mini_ids,
        )

        return create_group_command
