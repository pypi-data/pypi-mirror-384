import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.date_type import DateType


T = TypeVar("T", bound="Date")


@_attrs_define
class Date:
    """Date relevant to the resource.

    Attributes:
        date (datetime.date): A date or time interval according to Extended Date Time Format Level 0.
        type_ (DateType): The type of date.
        description (Union[Unset, str]):
    """

    date: datetime.date
    type_: "DateType"
    description: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        date = self.date.isoformat()

        type_ = self.type_.to_dict()

        description = self.description

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "date": date,
                "type": type_,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.date_type import DateType

        d = dict(src_dict)
        date = isoparse(d.pop("date")).date()

        type_ = DateType.from_dict(d.pop("type"))

        description = d.pop("description", UNSET)

        date = cls(
            date=date,
            type_=type_,
            description=description,
        )

        date.additional_properties = d
        return date

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
