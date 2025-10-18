import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="Embargo")


@_attrs_define
class Embargo:
    """Only in the cases of `"record": "restricted"`` or `"files": "restricted"`` can an embargo be provided as input.
    However, once an embargo is lifted, the embargo section is kept for transparency.

    Denotes when an embargo must be lifted, at which point the record is made publicly accessible.

        Attributes:
            active (Union[Unset, bool]): Is the record under embargo or not.
            until (Union[Unset, datetime.date]): Required if `"active": "true"`.
            reason (Union[Unset, str]): Explanation for the embargo.
    """

    active: Union[Unset, bool] = UNSET
    until: Union[Unset, datetime.date] = UNSET
    reason: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        active = self.active

        until: Union[Unset, str] = UNSET
        if not isinstance(self.until, Unset):
            until = self.until.isoformat()

        reason = self.reason

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if active is not UNSET:
            field_dict["active"] = active
        if until is not UNSET:
            field_dict["until"] = until
        if reason is not UNSET:
            field_dict["reason"] = reason

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        active = d.pop("active", UNSET)

        _until = d.pop("until", UNSET)
        until: Union[Unset, datetime.date]
        if isinstance(_until, Unset):
            until = UNSET
        else:
            until = isoparse(_until).date()

        reason = d.pop("reason", UNSET)

        embargo = cls(
            active=active,
            until=until,
            reason=reason,
        )

        embargo.additional_properties = d
        return embargo

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
