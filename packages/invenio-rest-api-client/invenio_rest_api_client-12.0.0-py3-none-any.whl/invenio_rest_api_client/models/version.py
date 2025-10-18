from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="Version")


@_attrs_define
class Version:
    """
    Attributes:
        index (Union[Unset, int]):
        is_latest (Union[Unset, bool]):
        is_latest_draft (Union[Unset, bool]):
    """

    index: Union[Unset, int] = UNSET
    is_latest: Union[Unset, bool] = UNSET
    is_latest_draft: Union[Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        index = self.index

        is_latest = self.is_latest

        is_latest_draft = self.is_latest_draft

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if index is not UNSET:
            field_dict["index"] = index
        if is_latest is not UNSET:
            field_dict["is_latest"] = is_latest
        if is_latest_draft is not UNSET:
            field_dict["is_latest_draft"] = is_latest_draft

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        index = d.pop("index", UNSET)

        is_latest = d.pop("is_latest", UNSET)

        is_latest_draft = d.pop("is_latest_draft", UNSET)

        version = cls(
            index=index,
            is_latest=is_latest,
            is_latest_draft=is_latest_draft,
        )

        version.additional_properties = d
        return version

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
