from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.additional_description_type import AdditionalDescriptionType
    from ..models.lang import Lang


T = TypeVar("T", bound="AdditionalDescription")


@_attrs_define
class AdditionalDescription:
    """Additional description in addition to the primary description (e.g. abstracts in other languages), methods or
    further notes.

        Attributes:
            description (str): Free text.
            type_ (AdditionalDescriptionType): The type of the description.
            lang (Union[Unset, Lang]): The language of the associated item.
    """

    description: str
    type_: "AdditionalDescriptionType"
    lang: Union[Unset, "Lang"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        description = self.description

        type_ = self.type_.to_dict()

        lang: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.lang, Unset):
            lang = self.lang.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "description": description,
                "type": type_,
            }
        )
        if lang is not UNSET:
            field_dict["lang"] = lang

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.additional_description_type import AdditionalDescriptionType
        from ..models.lang import Lang

        d = dict(src_dict)
        description = d.pop("description")

        type_ = AdditionalDescriptionType.from_dict(d.pop("type"))

        _lang = d.pop("lang", UNSET)
        lang: Union[Unset, Lang]
        if isinstance(_lang, Unset):
            lang = UNSET
        else:
            lang = Lang.from_dict(_lang)

        additional_description = cls(
            description=description,
            type_=type_,
            lang=lang,
        )

        additional_description.additional_properties = d
        return additional_description

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
