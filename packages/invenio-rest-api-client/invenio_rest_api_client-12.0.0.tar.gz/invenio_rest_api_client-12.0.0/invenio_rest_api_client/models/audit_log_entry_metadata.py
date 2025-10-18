from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AuditLogEntryMetadata")


@_attrs_define
class AuditLogEntryMetadata:
    """Additional metadata about the log entry

    Attributes:
        ip_address (Union[Unset, str]): IP address from which the action was performed
        session (Union[Unset, str]): Session identifier
        parent_pid (Union[Unset, str]): Parent persistent identifier Example: 1av3p-t2p41.
        revision_id (Union[Unset, int]): Revision ID of the resource Example: 110.
    """

    ip_address: Union[Unset, str] = UNSET
    session: Union[Unset, str] = UNSET
    parent_pid: Union[Unset, str] = UNSET
    revision_id: Union[Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        ip_address = self.ip_address

        session = self.session

        parent_pid = self.parent_pid

        revision_id = self.revision_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if ip_address is not UNSET:
            field_dict["ip_address"] = ip_address
        if session is not UNSET:
            field_dict["session"] = session
        if parent_pid is not UNSET:
            field_dict["parent_pid"] = parent_pid
        if revision_id is not UNSET:
            field_dict["revision_id"] = revision_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        ip_address = d.pop("ip_address", UNSET)

        session = d.pop("session", UNSET)

        parent_pid = d.pop("parent_pid", UNSET)

        revision_id = d.pop("revision_id", UNSET)

        audit_log_entry_metadata = cls(
            ip_address=ip_address,
            session=session,
            parent_pid=parent_pid,
            revision_id=revision_id,
        )

        audit_log_entry_metadata.additional_properties = d
        return audit_log_entry_metadata

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
