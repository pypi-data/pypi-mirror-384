from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.record_dto import RecordDto


T = TypeVar("T", bound="PaginatedListOfRecordDto")


@_attrs_define
class PaginatedListOfRecordDto:
    """
    Attributes:
        items (Union[Unset, list['RecordDto']]):
        page_number (Union[Unset, int]):
        total_pages (Union[Unset, int]):
        total_count (Union[Unset, int]):
        has_previous_page (Union[Unset, bool]):
        has_next_page (Union[Unset, bool]):
    """

    items: Union[Unset, list["RecordDto"]] = UNSET
    page_number: Union[Unset, int] = UNSET
    total_pages: Union[Unset, int] = UNSET
    total_count: Union[Unset, int] = UNSET
    has_previous_page: Union[Unset, bool] = UNSET
    has_next_page: Union[Unset, bool] = UNSET

    def to_dict(self) -> dict[str, Any]:
        items: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.items, Unset):
            items = []
            for items_item_data in self.items:
                items_item = items_item_data.to_dict()
                items.append(items_item)

        page_number = self.page_number

        total_pages = self.total_pages

        total_count = self.total_count

        has_previous_page = self.has_previous_page

        has_next_page = self.has_next_page

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if items is not UNSET:
            field_dict["items"] = items
        if page_number is not UNSET:
            field_dict["pageNumber"] = page_number
        if total_pages is not UNSET:
            field_dict["totalPages"] = total_pages
        if total_count is not UNSET:
            field_dict["totalCount"] = total_count
        if has_previous_page is not UNSET:
            field_dict["hasPreviousPage"] = has_previous_page
        if has_next_page is not UNSET:
            field_dict["hasNextPage"] = has_next_page

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.record_dto import RecordDto

        d = dict(src_dict)
        items = []
        _items = d.pop("items", UNSET)
        for items_item_data in _items or []:
            items_item = RecordDto.from_dict(items_item_data)

            items.append(items_item)

        page_number = d.pop("pageNumber", UNSET)

        total_pages = d.pop("totalPages", UNSET)

        total_count = d.pop("totalCount", UNSET)

        has_previous_page = d.pop("hasPreviousPage", UNSET)

        has_next_page = d.pop("hasNextPage", UNSET)

        paginated_list_of_record_dto = cls(
            items=items,
            page_number=page_number,
            total_pages=total_pages,
            total_count=total_count,
            has_previous_page=has_previous_page,
            has_next_page=has_next_page,
        )

        return paginated_list_of_record_dto
