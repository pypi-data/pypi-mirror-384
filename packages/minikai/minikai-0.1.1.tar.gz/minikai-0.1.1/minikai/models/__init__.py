"""Contains all the data models used in inputs/outputs"""

from .add_attachments_body import AddAttachmentsBody
from .create_group_command import CreateGroupCommand
from .create_mini_command import CreateMiniCommand
from .create_record_command import CreateRecordCommand
from .create_record_command_tags import CreateRecordCommandTags
from .document_file_dto import DocumentFileDto
from .document_file_metadata_dto import DocumentFileMetadataDto
from .form_field import FormField
from .form_field_dto import FormFieldDto
from .form_field_type import FormFieldType
from .group_dto import GroupDto
from .http_validation_problem_details import HttpValidationProblemDetails
from .http_validation_problem_details_errors import HttpValidationProblemDetailsErrors
from .json_node import JsonNode
from .json_node_options import JsonNodeOptions
from .mini_dto import MiniDto
from .mini_template_dto import MiniTemplateDto
from .paginated_list_of_record_dto import PaginatedListOfRecordDto
from .patch_mini_command import PatchMiniCommand
from .problem_details import ProblemDetails
from .record import Record
from .record_attachment import RecordAttachment
from .record_attachment_dto import RecordAttachmentDto
from .record_attachment_dto_metadata_type_0 import RecordAttachmentDtoMetadataType0
from .record_attachment_metadata_type_0 import RecordAttachmentMetadataType0
from .record_authorization import RecordAuthorization
from .record_authorization_dto import RecordAuthorizationDto
from .record_dto import RecordDto
from .record_dto_tags import RecordDtoTags
from .record_relation import RecordRelation
from .record_relation_dto import RecordRelationDto
from .record_tags import RecordTags
from .slim_mini_dto import SlimMiniDto
from .tool_dto import ToolDto
from .update_attachments_body import UpdateAttachmentsBody
from .update_group_command import UpdateGroupCommand
from .update_mini_command import UpdateMiniCommand
from .update_mini_template_workspaces_command import UpdateMiniTemplateWorkspacesCommand
from .update_record_command import UpdateRecordCommand
from .update_record_command_tags import UpdateRecordCommandTags
from .user_dto import UserDto
from .user_to_mini_dto import UserToMiniDto
from .workspace_dto import WorkspaceDto

__all__ = (
    "AddAttachmentsBody",
    "CreateGroupCommand",
    "CreateMiniCommand",
    "CreateRecordCommand",
    "CreateRecordCommandTags",
    "DocumentFileDto",
    "DocumentFileMetadataDto",
    "FormField",
    "FormFieldDto",
    "FormFieldType",
    "GroupDto",
    "HttpValidationProblemDetails",
    "HttpValidationProblemDetailsErrors",
    "JsonNode",
    "JsonNodeOptions",
    "MiniDto",
    "MiniTemplateDto",
    "PaginatedListOfRecordDto",
    "PatchMiniCommand",
    "ProblemDetails",
    "Record",
    "RecordAttachment",
    "RecordAttachmentDto",
    "RecordAttachmentDtoMetadataType0",
    "RecordAttachmentMetadataType0",
    "RecordAuthorization",
    "RecordAuthorizationDto",
    "RecordDto",
    "RecordDtoTags",
    "RecordRelation",
    "RecordRelationDto",
    "RecordTags",
    "SlimMiniDto",
    "ToolDto",
    "UpdateAttachmentsBody",
    "UpdateGroupCommand",
    "UpdateMiniCommand",
    "UpdateMiniTemplateWorkspacesCommand",
    "UpdateRecordCommand",
    "UpdateRecordCommandTags",
    "UserDto",
    "UserToMiniDto",
    "WorkspaceDto",
)
