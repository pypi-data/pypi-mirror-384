"""TypedDict schemas for YouTrack API return types.

Using TypedDict with __annotations__ trick to support $type field.
"""

from typing import Any, NotRequired, TypedDict


class UserGroupDict(TypedDict):
    """YouTrack user group object."""

    id: str
    name: str
    description: NotRequired[str | None]


# Add $type field using __annotations__ since it's not a valid Python identifier
UserGroupDict.__annotations__['$type'] = NotRequired[str]


class IssueCommentDict(TypedDict):
    """YouTrack issue comment object."""

    id: str
    text: str
    deleted: NotRequired[bool]
    updated: NotRequired[int | None]
    author: NotRequired[dict[str, Any] | None]
    visibility: NotRequired[dict[str, Any] | None]


IssueCommentDict.__annotations__['$type'] = NotRequired[str]


class ProjectCustomFieldDict(TypedDict):
    """YouTrack project custom field object."""

    id: str
    field: NotRequired[dict[str, Any]]
    project: NotRequired[dict[str, Any]]
    bundle: NotRequired[dict[str, Any]]  # For enum/bundle fields
    canBeEmpty: NotRequired[bool]
    isPublic: NotRequired[bool]
    ordinal: NotRequired[int]
    emptyFieldText: NotRequired[str]


ProjectCustomFieldDict.__annotations__['$type'] = NotRequired[str]


class IssueDict(TypedDict):
    """YouTrack issue object."""

    id: str
    idReadable: NotRequired[str]
    summary: NotRequired[str]
    description: NotRequired[str | None]
    created: NotRequired[int]
    updated: NotRequired[int]
    resolved: NotRequired[int | None]
    project: NotRequired[dict[str, Any]]
    reporter: NotRequired[dict[str, Any] | None]
    assignee: NotRequired[dict[str, Any] | None]
    customFields: NotRequired[list[dict[str, Any]]]
    custom_fields: NotRequired[dict[str, str | None]]  # Processed custom fields
    tags: NotRequired[list[dict[str, Any]]]
    comments: NotRequired[list[dict[str, Any]]]
    attachments: NotRequired[list[dict[str, Any]]]


IssueDict.__annotations__['$type'] = NotRequired[str]


class CustomFieldSettingDict(TypedDict):
    """YouTrack custom field setting object."""

    id: str
    name: str
    localizedName: NotRequired[str | None]
    fieldType: NotRequired[dict[str, Any]]
    isPrivate: NotRequired[bool]
    isPublic: NotRequired[bool]
    aliases: NotRequired[list[str]]


CustomFieldSettingDict.__annotations__['$type'] = NotRequired[str]
