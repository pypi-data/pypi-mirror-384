from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.identifier_scheme import IdentifierScheme
from ..types import UNSET, Unset

T = TypeVar("T", bound="Reference")


@_attrs_define
class Reference:
    """Reference string.

    Attributes:
        reference (str): The full reference string.
        scheme (Union[Unset, IdentifierScheme]): The scheme of the identifier
        identifier (Union[Unset, str]): The identifier if known.
    """

    reference: str
    scheme: Union[Unset, IdentifierScheme] = UNSET
    identifier: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        reference = self.reference

        scheme: Union[Unset, str] = UNSET
        if not isinstance(self.scheme, Unset):
            scheme = self.scheme.value

        identifier = self.identifier

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "reference": reference,
            }
        )
        if scheme is not UNSET:
            field_dict["scheme"] = scheme
        if identifier is not UNSET:
            field_dict["identifier"] = identifier

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        reference = d.pop("reference")

        _scheme = d.pop("scheme", UNSET)
        scheme: Union[Unset, IdentifierScheme]
        if isinstance(_scheme, Unset):
            scheme = UNSET
        else:
            scheme = IdentifierScheme(_scheme)

        identifier = d.pop("identifier", UNSET)

        reference = cls(
            reference=reference,
            scheme=scheme,
            identifier=identifier,
        )

        reference.additional_properties = d
        return reference

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
