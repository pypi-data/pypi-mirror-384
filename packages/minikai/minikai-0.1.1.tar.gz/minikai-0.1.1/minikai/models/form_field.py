import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="FormField")


@_attrs_define
class FormField:
    """
    Attributes:
        key (Union[Unset, str]):
        value_string (Union[None, Unset, str]):
        value_number (Union[None, Unset, float]):
        value_date (Union[None, Unset, datetime.datetime]):
    """

    key: Union[Unset, str] = UNSET
    value_string: Union[None, Unset, str] = UNSET
    value_number: Union[None, Unset, float] = UNSET
    value_date: Union[None, Unset, datetime.datetime] = UNSET

    def to_dict(self) -> dict[str, Any]:
        key = self.key

        value_string: Union[None, Unset, str]
        if isinstance(self.value_string, Unset):
            value_string = UNSET
        else:
            value_string = self.value_string

        value_number: Union[None, Unset, float]
        if isinstance(self.value_number, Unset):
            value_number = UNSET
        else:
            value_number = self.value_number

        value_date: Union[None, Unset, str]
        if isinstance(self.value_date, Unset):
            value_date = UNSET
        elif isinstance(self.value_date, datetime.datetime):
            value_date = self.value_date.isoformat()
        else:
            value_date = self.value_date

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if key is not UNSET:
            field_dict["key"] = key
        if value_string is not UNSET:
            field_dict["valueString"] = value_string
        if value_number is not UNSET:
            field_dict["valueNumber"] = value_number
        if value_date is not UNSET:
            field_dict["valueDate"] = value_date

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        key = d.pop("key", UNSET)

        def _parse_value_string(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        value_string = _parse_value_string(d.pop("valueString", UNSET))

        def _parse_value_number(data: object) -> Union[None, Unset, float]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, float], data)

        value_number = _parse_value_number(d.pop("valueNumber", UNSET))

        def _parse_value_date(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                value_date_type_0 = isoparse(data)

                return value_date_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        value_date = _parse_value_date(d.pop("valueDate", UNSET))

        form_field = cls(
            key=key,
            value_string=value_string,
            value_number=value_number,
            value_date=value_date,
        )

        return form_field
