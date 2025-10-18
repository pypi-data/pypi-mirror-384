from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.audit_log_entry import AuditLogEntry


T = TypeVar("T", bound="AuditLogListHits")


@_attrs_define
class AuditLogListHits:
    """
    Attributes:
        total (Union[Unset, int]): Total number of log entries
        hits (Union[Unset, list['AuditLogEntry']]):
    """

    total: Union[Unset, int] = UNSET
    hits: Union[Unset, list["AuditLogEntry"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        total = self.total

        hits: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.hits, Unset):
            hits = []
            for hits_item_data in self.hits:
                hits_item = hits_item_data.to_dict()
                hits.append(hits_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if total is not UNSET:
            field_dict["total"] = total
        if hits is not UNSET:
            field_dict["hits"] = hits

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.audit_log_entry import AuditLogEntry

        d = dict(src_dict)
        total = d.pop("total", UNSET)

        hits = []
        _hits = d.pop("hits", UNSET)
        for hits_item_data in _hits or []:
            hits_item = AuditLogEntry.from_dict(hits_item_data)

            hits.append(hits_item)

        audit_log_list_hits = cls(
            total=total,
            hits=hits,
        )

        audit_log_list_hits.additional_properties = d
        return audit_log_list_hits

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
