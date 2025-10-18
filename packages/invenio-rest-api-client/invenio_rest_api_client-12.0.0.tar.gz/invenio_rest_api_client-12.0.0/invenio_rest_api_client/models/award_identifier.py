from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="AwardIdentifier")


@_attrs_define
class AwardIdentifier:
    """Identifier for the award.

    Attributes:
        scheme (str): The identifier scheme.
        identifier (str): Actual value of the identifier.
    """

    scheme: str
    identifier: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        scheme = self.scheme

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
        scheme = d.pop("scheme")

        identifier = d.pop("identifier")

        award_identifier = cls(
            scheme=scheme,
            identifier=identifier,
        )

        award_identifier.additional_properties = d
        return award_identifier

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
