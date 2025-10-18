from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AuditLogEntryLinks")


@_attrs_define
class AuditLogEntryLinks:
    """Links related to the log entry

    Attributes:
        self_ (Union[Unset, str]): Self link to the log entry Example: https://example.com/api/audit-
            logs/9913abd2-1a7c-42cb-a73e-e48a9e1bf4f2.
    """

    self_: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        self_ = self.self_

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if self_ is not UNSET:
            field_dict["self"] = self_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        self_ = d.pop("self", UNSET)

        audit_log_entry_links = cls(
            self_=self_,
        )

        audit_log_entry_links.additional_properties = d
        return audit_log_entry_links

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
