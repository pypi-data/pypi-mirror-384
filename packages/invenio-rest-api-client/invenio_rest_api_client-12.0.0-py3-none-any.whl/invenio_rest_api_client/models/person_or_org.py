from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.person_or_org_type import PersonOrOrgType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.identifier import Identifier


T = TypeVar("T", bound="PersonOrOrg")


@_attrs_define
class PersonOrOrg:
    """The person or organization.

    Attributes:
        type_ (PersonOrOrgType): The type of name.
        given_name (Union[Unset, str]): Given name(s).
        family_name (Union[Unset, str]): Family name.
        name (Union[Unset, str]): The full name of the organisation.

            For a person, this field is generated from `given_name` and `family_name`.
        identifiers (Union[Unset, list['Identifier']]): Person or organisation identifiers.
    """

    type_: PersonOrOrgType
    given_name: Union[Unset, str] = UNSET
    family_name: Union[Unset, str] = UNSET
    name: Union[Unset, str] = UNSET
    identifiers: Union[Unset, list["Identifier"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        given_name = self.given_name

        family_name = self.family_name

        name = self.name

        identifiers: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.identifiers, Unset):
            identifiers = []
            for identifiers_item_data in self.identifiers:
                identifiers_item = identifiers_item_data.to_dict()
                identifiers.append(identifiers_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
            }
        )
        if given_name is not UNSET:
            field_dict["given_name"] = given_name
        if family_name is not UNSET:
            field_dict["family_name"] = family_name
        if name is not UNSET:
            field_dict["name"] = name
        if identifiers is not UNSET:
            field_dict["identifiers"] = identifiers

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.identifier import Identifier

        d = dict(src_dict)
        type_ = PersonOrOrgType(d.pop("type"))

        given_name = d.pop("given_name", UNSET)

        family_name = d.pop("family_name", UNSET)

        name = d.pop("name", UNSET)

        identifiers = []
        _identifiers = d.pop("identifiers", UNSET)
        for identifiers_item_data in _identifiers or []:
            identifiers_item = Identifier.from_dict(identifiers_item_data)

            identifiers.append(identifiers_item)

        person_or_org = cls(
            type_=type_,
            given_name=given_name,
            family_name=family_name,
            name=name,
            identifiers=identifiers,
        )

        person_or_org.additional_properties = d
        return person_or_org

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
