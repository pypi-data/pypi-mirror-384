from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.award import Award
    from ..models.funder import Funder


T = TypeVar("T", bound="Funding")


@_attrs_define
class Funding:
    """Information about financial support (funding) for the resource being registered.

    Attributes:
        funder (Funder): The organisation of the funding provider.
        award (Union[Unset, Award]): The award (grant) sponsored by the funder.
    """

    funder: "Funder"
    award: Union[Unset, "Award"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        funder = self.funder.to_dict()

        award: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.award, Unset):
            award = self.award.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "funder": funder,
            }
        )
        if award is not UNSET:
            field_dict["award"] = award

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.award import Award
        from ..models.funder import Funder

        d = dict(src_dict)
        funder = Funder.from_dict(d.pop("funder"))

        _award = d.pop("award", UNSET)
        award: Union[Unset, Award]
        if isinstance(_award, Unset):
            award = UNSET
        else:
            award = Award.from_dict(_award)

        funding = cls(
            funder=funder,
            award=award,
        )

        funding.additional_properties = d
        return funding

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
