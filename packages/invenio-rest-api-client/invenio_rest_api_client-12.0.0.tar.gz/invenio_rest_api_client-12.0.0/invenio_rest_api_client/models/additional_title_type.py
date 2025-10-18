from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.additional_title_type_id import AdditionalTitleTypeId

if TYPE_CHECKING:
    from ..models.additional_title_type_title import AdditionalTitleTypeTitle


T = TypeVar("T", bound="AdditionalTitleType")


@_attrs_define
class AdditionalTitleType:
    """The type of the title.

    Attributes:
        id (AdditionalTitleTypeId): Title type id from the controlled vocabulary.
        title (AdditionalTitleTypeTitle): The corresponding localized human readable label
    """

    id: AdditionalTitleTypeId
    title: "AdditionalTitleTypeTitle"
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
        from ..models.additional_title_type_title import AdditionalTitleTypeTitle

        d = dict(src_dict)
        id = AdditionalTitleTypeId(d.pop("id"))

        title = AdditionalTitleTypeTitle.from_dict(d.pop("title"))

        additional_title_type = cls(
            id=id,
            title=title,
        )

        additional_title_type.additional_properties = d
        return additional_title_type

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
