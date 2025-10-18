from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.identifier_scheme import IdentifierScheme
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.related_identifier_resource_type import RelatedIdentifierResourceType
    from ..models.relation_type import RelationType


T = TypeVar("T", bound="RelatedIdentifier")


@_attrs_define
class RelatedIdentifier:
    """Identifier of related resources.

    Attributes:
        identifier (str): A global unique persistent identifier for a related resource.
        scheme (IdentifierScheme): The scheme of the identifier
        relation_type (RelationType): The relation of the record to this related resource.
        resource_type (Union[Unset, RelatedIdentifierResourceType]): The resource type of the related resource
    """

    identifier: str
    scheme: IdentifierScheme
    relation_type: "RelationType"
    resource_type: Union[Unset, "RelatedIdentifierResourceType"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        identifier = self.identifier

        scheme = self.scheme.value

        relation_type = self.relation_type.to_dict()

        resource_type: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.resource_type, Unset):
            resource_type = self.resource_type.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "identifier": identifier,
                "scheme": scheme,
                "relation_type": relation_type,
            }
        )
        if resource_type is not UNSET:
            field_dict["resource_type"] = resource_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.related_identifier_resource_type import RelatedIdentifierResourceType
        from ..models.relation_type import RelationType

        d = dict(src_dict)
        identifier = d.pop("identifier")

        scheme = IdentifierScheme(d.pop("scheme"))

        relation_type = RelationType.from_dict(d.pop("relation_type"))

        _resource_type = d.pop("resource_type", UNSET)
        resource_type: Union[Unset, RelatedIdentifierResourceType]
        if isinstance(_resource_type, Unset):
            resource_type = UNSET
        else:
            resource_type = RelatedIdentifierResourceType.from_dict(_resource_type)

        related_identifier = cls(
            identifier=identifier,
            scheme=scheme,
            relation_type=relation_type,
            resource_type=resource_type,
        )

        related_identifier.additional_properties = d
        return related_identifier

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
