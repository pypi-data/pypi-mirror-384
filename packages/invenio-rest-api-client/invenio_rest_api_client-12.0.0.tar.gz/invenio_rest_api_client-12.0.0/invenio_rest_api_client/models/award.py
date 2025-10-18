from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.award_identifier import AwardIdentifier
    from ..models.award_title import AwardTitle


T = TypeVar("T", bound="Award")


@_attrs_define
class Award:
    """The award (grant) sponsored by the funder.

    Attributes:
        id (Union[Unset, str]): The award id from the controlled vocabulary.
        title (Union[Unset, AwardTitle]): The localized title of the award.
        number (Union[Unset, str]): The code assigned by the funder to a sponsored award (grant).
        identifiers (Union[Unset, list['AwardIdentifier']]): Identifiers for the award.
    """

    id: Union[Unset, str] = UNSET
    title: Union[Unset, "AwardTitle"] = UNSET
    number: Union[Unset, str] = UNSET
    identifiers: Union[Unset, list["AwardIdentifier"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        title: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.title, Unset):
            title = self.title.to_dict()

        number = self.number

        identifiers: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.identifiers, Unset):
            identifiers = []
            for identifiers_item_data in self.identifiers:
                identifiers_item = identifiers_item_data.to_dict()
                identifiers.append(identifiers_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if title is not UNSET:
            field_dict["title"] = title
        if number is not UNSET:
            field_dict["number"] = number
        if identifiers is not UNSET:
            field_dict["identifiers"] = identifiers

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.award_identifier import AwardIdentifier
        from ..models.award_title import AwardTitle

        d = dict(src_dict)
        id = d.pop("id", UNSET)

        _title = d.pop("title", UNSET)
        title: Union[Unset, AwardTitle]
        if isinstance(_title, Unset):
            title = UNSET
        else:
            title = AwardTitle.from_dict(_title)

        number = d.pop("number", UNSET)

        identifiers = []
        _identifiers = d.pop("identifiers", UNSET)
        for identifiers_item_data in _identifiers or []:
            identifiers_item = AwardIdentifier.from_dict(identifiers_item_data)

            identifiers.append(identifiers_item)

        award = cls(
            id=id,
            title=title,
            number=number,
            identifiers=identifiers,
        )

        award.additional_properties = d
        return award

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
