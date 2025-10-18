from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.related_identifier_resource_type_id import RelatedIdentifierResourceTypeId

if TYPE_CHECKING:
    from ..models.related_identifier_resource_type_title import RelatedIdentifierResourceTypeTitle


T = TypeVar("T", bound="RelatedIdentifierResourceType")


@_attrs_define
class RelatedIdentifierResourceType:
    """The resource type of the related resource

    Attributes:
        id (RelatedIdentifierResourceTypeId): Date type id from the controlled vocabulary.
        title (RelatedIdentifierResourceTypeTitle): The corresponding localized human readable label
    """

    id: RelatedIdentifierResourceTypeId
    title: "RelatedIdentifierResourceTypeTitle"
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
        from ..models.related_identifier_resource_type_title import RelatedIdentifierResourceTypeTitle

        d = dict(src_dict)
        id = RelatedIdentifierResourceTypeId(d.pop("id"))

        title = RelatedIdentifierResourceTypeTitle.from_dict(d.pop("title"))

        related_identifier_resource_type = cls(
            id=id,
            title=title,
        )

        related_identifier_resource_type.additional_properties = d
        return related_identifier_resource_type

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
