from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.additional_title_type import AdditionalTitleType
    from ..models.lang import Lang


T = TypeVar("T", bound="AdditionalTitle")


@_attrs_define
class AdditionalTitle:
    """Additional name or title by which a resource is known.

    Attributes:
        title (str): The additional title.
        type_ (AdditionalTitleType): The type of the title.
        lang (Union[Unset, Lang]): The language of the associated item.
    """

    title: str
    type_: "AdditionalTitleType"
    lang: Union[Unset, "Lang"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        title = self.title

        type_ = self.type_.to_dict()

        lang: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.lang, Unset):
            lang = self.lang.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "title": title,
                "type": type_,
            }
        )
        if lang is not UNSET:
            field_dict["lang"] = lang

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.additional_title_type import AdditionalTitleType
        from ..models.lang import Lang

        d = dict(src_dict)
        title = d.pop("title")

        type_ = AdditionalTitleType.from_dict(d.pop("type"))

        _lang = d.pop("lang", UNSET)
        lang: Union[Unset, Lang]
        if isinstance(_lang, Unset):
            lang = UNSET
        else:
            lang = Lang.from_dict(_lang)

        additional_title = cls(
            title=title,
            type_=type_,
            lang=lang,
        )

        additional_title.additional_properties = d
        return additional_title

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
