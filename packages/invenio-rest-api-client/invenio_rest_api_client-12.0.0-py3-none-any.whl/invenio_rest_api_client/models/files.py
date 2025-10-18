from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="Files")


@_attrs_define
class Files:
    """Files options for the record.

    More informations can be found on InvenioRDM Official page:
    https://inveniordm.docs.cern.ch/reference/rest_api_drafts_records/#files-options

        Attributes:
            enabled (Union[Unset, bool]): Should (and can) files be attached to this record or not.
            default_preview (Union[Unset, str]): Filename of file to be previewed by default.
            order (Union[Unset, list[str]]): Array of filename strings in display order.
    """

    enabled: Union[Unset, bool] = UNSET
    default_preview: Union[Unset, str] = UNSET
    order: Union[Unset, list[str]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        enabled = self.enabled

        default_preview = self.default_preview

        order: Union[Unset, list[str]] = UNSET
        if not isinstance(self.order, Unset):
            order = self.order

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if enabled is not UNSET:
            field_dict["enabled"] = enabled
        if default_preview is not UNSET:
            field_dict["default_preview"] = default_preview
        if order is not UNSET:
            field_dict["order"] = order

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        enabled = d.pop("enabled", UNSET)

        default_preview = d.pop("default_preview", UNSET)

        order = cast(list[str], d.pop("order", UNSET))

        files = cls(
            enabled=enabled,
            default_preview=default_preview,
            order=order,
        )

        files.additional_properties = d
        return files

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
