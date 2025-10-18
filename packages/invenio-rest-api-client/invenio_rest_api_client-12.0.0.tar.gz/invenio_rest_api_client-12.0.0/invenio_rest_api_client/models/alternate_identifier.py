from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.identifier_scheme import IdentifierScheme

T = TypeVar("T", bound="AlternateIdentifier")


@_attrs_define
class AlternateIdentifier:
    """Persistent identifier for the resource other than the ones registered as system-managed internal or external
    persistent identifiers.

        Attributes:
            identifier (str): identifier value
            scheme (IdentifierScheme): The scheme of the identifier
    """

    identifier: str
    scheme: IdentifierScheme
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        identifier = self.identifier

        scheme = self.scheme.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "identifier": identifier,
                "scheme": scheme,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        identifier = d.pop("identifier")

        scheme = IdentifierScheme(d.pop("scheme"))

        alternate_identifier = cls(
            identifier=identifier,
            scheme=scheme,
        )

        alternate_identifier.additional_properties = d
        return alternate_identifier

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
