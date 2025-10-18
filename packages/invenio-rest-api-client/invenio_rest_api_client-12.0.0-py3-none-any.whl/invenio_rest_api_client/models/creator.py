from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.affiliation import Affiliation
    from ..models.person_or_org import PersonOrOrg
    from ..models.role import Role


T = TypeVar("T", bound="Creator")


@_attrs_define
class Creator:
    """
    Attributes:
        person_or_org (PersonOrOrg): The person or organization.
        role (Union[Unset, Role]): The role of the person or organisation selected from a customizable controlled
            vocabulary.
        affiliations (Union[Unset, list['Affiliation']]): Affilations if `person_or_org.type` is personal.
    """

    person_or_org: "PersonOrOrg"
    role: Union[Unset, "Role"] = UNSET
    affiliations: Union[Unset, list["Affiliation"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        person_or_org = self.person_or_org.to_dict()

        role: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.role, Unset):
            role = self.role.to_dict()

        affiliations: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.affiliations, Unset):
            affiliations = []
            for affiliations_item_data in self.affiliations:
                affiliations_item = affiliations_item_data.to_dict()
                affiliations.append(affiliations_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "person_or_org": person_or_org,
            }
        )
        if role is not UNSET:
            field_dict["role"] = role
        if affiliations is not UNSET:
            field_dict["affiliations"] = affiliations

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.affiliation import Affiliation
        from ..models.person_or_org import PersonOrOrg
        from ..models.role import Role

        d = dict(src_dict)
        person_or_org = PersonOrOrg.from_dict(d.pop("person_or_org"))

        _role = d.pop("role", UNSET)
        role: Union[Unset, Role]
        if isinstance(_role, Unset):
            role = UNSET
        else:
            role = Role.from_dict(_role)

        affiliations = []
        _affiliations = d.pop("affiliations", UNSET)
        for affiliations_item_data in _affiliations or []:
            affiliations_item = Affiliation.from_dict(affiliations_item_data)

            affiliations.append(affiliations_item)

        creator = cls(
            person_or_org=person_or_org,
            role=role,
            affiliations=affiliations,
        )

        creator.additional_properties = d
        return creator

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
