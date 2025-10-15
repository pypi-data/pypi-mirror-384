import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.json_node import JsonNode
    from ..models.record_authorization_dto import RecordAuthorizationDto
    from ..models.record_relation_dto import RecordRelationDto
    from ..models.update_record_command_tags import UpdateRecordCommandTags


T = TypeVar("T", bound="UpdateRecordCommand")


@_attrs_define
class UpdateRecordCommand:
    """
    Attributes:
        id (Union[Unset, str]):
        title (Union[Unset, str]):
        description (Union[None, Unset, str]):
        event_date (Union[None, Unset, datetime.datetime]):
        schema (Union['JsonNode', None, Unset]):
        content (Union['JsonNode', None, Unset]):
        relations (Union[Unset, list['RecordRelationDto']]):
        external_uri (Union[None, Unset, str]):
        labels (Union[Unset, list[str]]):
        tags (Union[Unset, UpdateRecordCommandTags]):
        authorization (Union[Unset, RecordAuthorizationDto]):
        archived (Union[Unset, bool]):
    """

    id: Union[Unset, str] = UNSET
    title: Union[Unset, str] = UNSET
    description: Union[None, Unset, str] = UNSET
    event_date: Union[None, Unset, datetime.datetime] = UNSET
    schema: Union["JsonNode", None, Unset] = UNSET
    content: Union["JsonNode", None, Unset] = UNSET
    relations: Union[Unset, list["RecordRelationDto"]] = UNSET
    external_uri: Union[None, Unset, str] = UNSET
    labels: Union[Unset, list[str]] = UNSET
    tags: Union[Unset, "UpdateRecordCommandTags"] = UNSET
    authorization: Union[Unset, "RecordAuthorizationDto"] = UNSET
    archived: Union[Unset, bool] = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.json_node import JsonNode

        id = self.id

        title = self.title

        description: Union[None, Unset, str]
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        event_date: Union[None, Unset, str]
        if isinstance(self.event_date, Unset):
            event_date = UNSET
        elif isinstance(self.event_date, datetime.datetime):
            event_date = self.event_date.isoformat()
        else:
            event_date = self.event_date

        schema: Union[None, Unset, dict[str, Any]]
        if isinstance(self.schema, Unset):
            schema = UNSET
        elif isinstance(self.schema, JsonNode):
            schema = self.schema.to_dict()
        else:
            schema = self.schema

        content: Union[None, Unset, dict[str, Any]]
        if isinstance(self.content, Unset):
            content = UNSET
        elif isinstance(self.content, JsonNode):
            content = self.content.to_dict()
        else:
            content = self.content

        relations: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.relations, Unset):
            relations = []
            for relations_item_data in self.relations:
                relations_item = relations_item_data.to_dict()
                relations.append(relations_item)

        external_uri: Union[None, Unset, str]
        if isinstance(self.external_uri, Unset):
            external_uri = UNSET
        else:
            external_uri = self.external_uri

        labels: Union[Unset, list[str]] = UNSET
        if not isinstance(self.labels, Unset):
            labels = self.labels

        tags: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.tags, Unset):
            tags = self.tags.to_dict()

        authorization: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.authorization, Unset):
            authorization = self.authorization.to_dict()

        archived = self.archived

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if title is not UNSET:
            field_dict["title"] = title
        if description is not UNSET:
            field_dict["description"] = description
        if event_date is not UNSET:
            field_dict["eventDate"] = event_date
        if schema is not UNSET:
            field_dict["schema"] = schema
        if content is not UNSET:
            field_dict["content"] = content
        if relations is not UNSET:
            field_dict["relations"] = relations
        if external_uri is not UNSET:
            field_dict["externalUri"] = external_uri
        if labels is not UNSET:
            field_dict["labels"] = labels
        if tags is not UNSET:
            field_dict["tags"] = tags
        if authorization is not UNSET:
            field_dict["authorization"] = authorization
        if archived is not UNSET:
            field_dict["archived"] = archived

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.json_node import JsonNode
        from ..models.record_authorization_dto import RecordAuthorizationDto
        from ..models.record_relation_dto import RecordRelationDto
        from ..models.update_record_command_tags import UpdateRecordCommandTags

        d = dict(src_dict)
        id = d.pop("id", UNSET)

        title = d.pop("title", UNSET)

        def _parse_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_event_date(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                event_date_type_0 = isoparse(data)

                return event_date_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        event_date = _parse_event_date(d.pop("eventDate", UNSET))

        def _parse_schema(data: object) -> Union["JsonNode", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                schema_type_0 = JsonNode.from_dict(data)

                return schema_type_0
            except:  # noqa: E722
                pass
            return cast(Union["JsonNode", None, Unset], data)

        schema = _parse_schema(d.pop("schema", UNSET))

        def _parse_content(data: object) -> Union["JsonNode", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                content_type_0 = JsonNode.from_dict(data)

                return content_type_0
            except:  # noqa: E722
                pass
            return cast(Union["JsonNode", None, Unset], data)

        content = _parse_content(d.pop("content", UNSET))

        relations = []
        _relations = d.pop("relations", UNSET)
        for relations_item_data in _relations or []:
            relations_item = RecordRelationDto.from_dict(relations_item_data)

            relations.append(relations_item)

        def _parse_external_uri(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        external_uri = _parse_external_uri(d.pop("externalUri", UNSET))

        labels = cast(list[str], d.pop("labels", UNSET))

        _tags = d.pop("tags", UNSET)
        tags: Union[Unset, UpdateRecordCommandTags]
        if isinstance(_tags, Unset):
            tags = UNSET
        else:
            tags = UpdateRecordCommandTags.from_dict(_tags)

        _authorization = d.pop("authorization", UNSET)
        authorization: Union[Unset, RecordAuthorizationDto]
        if isinstance(_authorization, Unset):
            authorization = UNSET
        else:
            authorization = RecordAuthorizationDto.from_dict(_authorization)

        archived = d.pop("archived", UNSET)

        update_record_command = cls(
            id=id,
            title=title,
            description=description,
            event_date=event_date,
            schema=schema,
            content=content,
            relations=relations,
            external_uri=external_uri,
            labels=labels,
            tags=tags,
            authorization=authorization,
            archived=archived,
        )

        return update_record_command
