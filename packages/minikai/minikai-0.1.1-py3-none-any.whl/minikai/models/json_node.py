from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.json_node_options import JsonNodeOptions


T = TypeVar("T", bound="JsonNode")


@_attrs_define
class JsonNode:
    """The base class that represents a single node within a mutable JSON document.

    Attributes:
        options (Union['JsonNodeOptions', None, Unset]): Gets the options to control the behavior.
        parent (Union['JsonNode', None, Unset]): Gets the parent JsonNode.
                          If there is no parent, null is returned.
                          A parent can either be a JsonObject or a JsonArray.
        root (Union[Unset, JsonNode]): The base class that represents a single node within a mutable JSON document.
    """

    options: Union["JsonNodeOptions", None, Unset] = UNSET
    parent: Union["JsonNode", None, Unset] = UNSET
    root: Union[Unset, "JsonNode"] = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.json_node_options import JsonNodeOptions

        options: Union[None, Unset, dict[str, Any]]
        if isinstance(self.options, Unset):
            options = UNSET
        elif isinstance(self.options, JsonNodeOptions):
            options = self.options.to_dict()
        else:
            options = self.options

        parent: Union[None, Unset, dict[str, Any]]
        if isinstance(self.parent, Unset):
            parent = UNSET
        elif isinstance(self.parent, JsonNode):
            parent = self.parent.to_dict()
        else:
            parent = self.parent

        root: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.root, Unset):
            root = self.root.to_dict()

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if options is not UNSET:
            field_dict["options"] = options
        if parent is not UNSET:
            field_dict["parent"] = parent
        if root is not UNSET:
            field_dict["root"] = root

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.json_node_options import JsonNodeOptions

        d = dict(src_dict)

        def _parse_options(data: object) -> Union["JsonNodeOptions", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                options_type_0 = JsonNodeOptions.from_dict(data)

                return options_type_0
            except:  # noqa: E722
                pass
            return cast(Union["JsonNodeOptions", None, Unset], data)

        options = _parse_options(d.pop("options", UNSET))

        def _parse_parent(data: object) -> Union["JsonNode", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                parent_type_0 = JsonNode.from_dict(data)

                return parent_type_0
            except:  # noqa: E722
                pass
            return cast(Union["JsonNode", None, Unset], data)

        parent = _parse_parent(d.pop("parent", UNSET))

        _root = d.pop("root", UNSET)
        root: Union[Unset, JsonNode]
        if isinstance(_root, Unset):
            root = UNSET
        else:
            root = JsonNode.from_dict(_root)

        json_node = cls(
            options=options,
            parent=parent,
            root=root,
        )

        return json_node
