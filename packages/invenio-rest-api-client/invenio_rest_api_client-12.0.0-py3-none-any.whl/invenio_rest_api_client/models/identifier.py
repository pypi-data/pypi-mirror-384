from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.person_or_org_identifier_scheme import PersonOrOrgIdentifierScheme

T = TypeVar("T", bound="Identifier")


@_attrs_define
class Identifier:
    """Person or organisation identifier.

    Attributes:
        scheme (PersonOrOrgIdentifierScheme): The identifier scheme.

            Note that the identifiers' schemes are passed lowercased e.g. ORCID is `orcid`.
        identifier (str): Actual value of the identifier.
    """

    scheme: PersonOrOrgIdentifierScheme
    identifier: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        scheme = self.scheme.value

        identifier = self.identifier

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "scheme": scheme,
                "identifier": identifier,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        scheme = PersonOrOrgIdentifierScheme(d.pop("scheme"))

        identifier = d.pop("identifier")

        identifier = cls(
            scheme=scheme,
            identifier=identifier,
        )

        identifier.additional_properties = d
        return identifier

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
