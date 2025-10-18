from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.relation_type_id import RelationTypeId

if TYPE_CHECKING:
    from ..models.relation_type_title import RelationTypeTitle


T = TypeVar("T", bound="RelationType")


@_attrs_define
class RelationType:
    """The relation of the record to this related resource.

    Attributes:
        id (RelationTypeId): Relation type id from the controlled vocabulary
        title (RelationTypeTitle): The corresponding localized human readable label
    """

    id: RelationTypeId
    title: "RelationTypeTitle"
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
        from ..models.relation_type_title import RelationTypeTitle

        d = dict(src_dict)
        id = RelationTypeId(d.pop("id"))

        title = RelationTypeTitle.from_dict(d.pop("title"))

        relation_type = cls(
            id=id,
            title=title,
        )

        relation_type.additional_properties = d
        return relation_type

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
