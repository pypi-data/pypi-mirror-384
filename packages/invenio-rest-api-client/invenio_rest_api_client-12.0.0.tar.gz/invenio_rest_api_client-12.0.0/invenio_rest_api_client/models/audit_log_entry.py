import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.audit_log_entry_links import AuditLogEntryLinks
    from ..models.audit_log_entry_metadata import AuditLogEntryMetadata
    from ..models.audit_log_entry_resource import AuditLogEntryResource
    from ..models.audit_log_entry_user import AuditLogEntryUser


T = TypeVar("T", bound="AuditLogEntry")


@_attrs_define
class AuditLogEntry:
    """Conflict - Resource already exists or operation conflicts

    Attributes:
        id (Union[Unset, str]): Unique identifier for the log entry Example: 9913abd2-1a7c-42cb-a73e-e48a9e1bf4f2.
        created (Union[Unset, datetime.datetime]): Timestamp when the log entry was created Example:
            2025-06-20T08:05:27.730677+00:00.
        action (Union[Unset, str]): Action performed Example: record.publish.
        resource (Union[Unset, AuditLogEntryResource]): Resource affected by the action
        metadata (Union[Unset, AuditLogEntryMetadata]): Additional metadata about the log entry
        user (Union[Unset, AuditLogEntryUser]): User who performed the action
        links (Union[Unset, AuditLogEntryLinks]): Links related to the log entry
    """

    id: Union[Unset, str] = UNSET
    created: Union[Unset, datetime.datetime] = UNSET
    action: Union[Unset, str] = UNSET
    resource: Union[Unset, "AuditLogEntryResource"] = UNSET
    metadata: Union[Unset, "AuditLogEntryMetadata"] = UNSET
    user: Union[Unset, "AuditLogEntryUser"] = UNSET
    links: Union[Unset, "AuditLogEntryLinks"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        created: Union[Unset, str] = UNSET
        if not isinstance(self.created, Unset):
            created = self.created.isoformat()

        action = self.action

        resource: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.resource, Unset):
            resource = self.resource.to_dict()

        metadata: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        user: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.user, Unset):
            user = self.user.to_dict()

        links: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.links, Unset):
            links = self.links.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if created is not UNSET:
            field_dict["created"] = created
        if action is not UNSET:
            field_dict["action"] = action
        if resource is not UNSET:
            field_dict["resource"] = resource
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if user is not UNSET:
            field_dict["user"] = user
        if links is not UNSET:
            field_dict["links"] = links

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.audit_log_entry_links import AuditLogEntryLinks
        from ..models.audit_log_entry_metadata import AuditLogEntryMetadata
        from ..models.audit_log_entry_resource import AuditLogEntryResource
        from ..models.audit_log_entry_user import AuditLogEntryUser

        d = dict(src_dict)
        id = d.pop("id", UNSET)

        _created = d.pop("created", UNSET)
        created: Union[Unset, datetime.datetime]
        if isinstance(_created, Unset):
            created = UNSET
        else:
            created = isoparse(_created)

        action = d.pop("action", UNSET)

        _resource = d.pop("resource", UNSET)
        resource: Union[Unset, AuditLogEntryResource]
        if isinstance(_resource, Unset):
            resource = UNSET
        else:
            resource = AuditLogEntryResource.from_dict(_resource)

        _metadata = d.pop("metadata", UNSET)
        metadata: Union[Unset, AuditLogEntryMetadata]
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = AuditLogEntryMetadata.from_dict(_metadata)

        _user = d.pop("user", UNSET)
        user: Union[Unset, AuditLogEntryUser]
        if isinstance(_user, Unset):
            user = UNSET
        else:
            user = AuditLogEntryUser.from_dict(_user)

        _links = d.pop("links", UNSET)
        links: Union[Unset, AuditLogEntryLinks]
        if isinstance(_links, Unset):
            links = UNSET
        else:
            links = AuditLogEntryLinks.from_dict(_links)

        audit_log_entry = cls(
            id=id,
            created=created,
            action=action,
            resource=resource,
            metadata=metadata,
            user=user,
            links=links,
        )

        audit_log_entry.additional_properties = d
        return audit_log_entry

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
