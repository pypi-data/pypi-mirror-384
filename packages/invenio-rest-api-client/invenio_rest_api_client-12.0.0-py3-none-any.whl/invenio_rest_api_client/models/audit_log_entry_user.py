from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AuditLogEntryUser")


@_attrs_define
class AuditLogEntryUser:
    """User who performed the action

    Attributes:
        id (Union[Unset, str]): User ID Example: 2.
        username (Union[Unset, str]): Username Example: user.
        email (Union[Unset, str]): User email address Example: user@demo.org.
    """

    id: Union[Unset, str] = UNSET
    username: Union[Unset, str] = UNSET
    email: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        username = self.username

        email = self.email

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if username is not UNSET:
            field_dict["username"] = username
        if email is not UNSET:
            field_dict["email"] = email

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        username = d.pop("username", UNSET)

        email = d.pop("email", UNSET)

        audit_log_entry_user = cls(
            id=id,
            username=username,
            email=email,
        )

        audit_log_entry_user.additional_properties = d
        return audit_log_entry_user

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
