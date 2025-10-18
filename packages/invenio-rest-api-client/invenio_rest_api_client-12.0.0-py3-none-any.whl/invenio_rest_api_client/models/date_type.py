from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.date_type_id import DateTypeId

if TYPE_CHECKING:
    from ..models.date_type_title import DateTypeTitle


T = TypeVar("T", bound="DateType")


@_attrs_define
class DateType:
    """The type of date.

    Attributes:
        id (DateTypeId): Date type id from the controlled vocabulary
        title (DateTypeTitle): The corresponding localized human readable label
    """

    id: DateTypeId
    title: "DateTypeTitle"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id.value

        title = self.title.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "title": title,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.date_type_title import DateTypeTitle

        d = dict(src_dict)
        id = DateTypeId(d.pop("id"))

        title = DateTypeTitle.from_dict(d.pop("title"))

        date_type = cls(
            id=id,
            title=title,
        )

        date_type.additional_properties = d
        return date_type

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
