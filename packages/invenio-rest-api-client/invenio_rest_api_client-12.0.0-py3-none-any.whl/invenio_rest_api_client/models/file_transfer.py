from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.file_transfer_type import FileTransferType
from ..types import UNSET, Unset

T = TypeVar("T", bound="FileTransfer")


@_attrs_define
class FileTransfer:
    """
    Attributes:
        type_ (Union[Unset, FileTransferType]): The actual technology that is used to store a file
        url (Union[Unset, str]): URL to fetch the file from
    """

    type_: Union[Unset, FileTransferType] = UNSET
    url: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_: Union[Unset, str] = UNSET
        if not isinstance(self.type_, Unset):
            type_ = self.type_.value

        url = self.url

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if type_ is not UNSET:
            field_dict["type"] = type_
        if url is not UNSET:
            field_dict["url"] = url

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _type_ = d.pop("type", UNSET)
        type_: Union[Unset, FileTransferType]
        if isinstance(_type_, Unset):
            type_ = UNSET
        else:
            type_ = FileTransferType(_type_)

        url = d.pop("url", UNSET)

        file_transfer = cls(
            type_=type_,
            url=url,
        )

        file_transfer.additional_properties = d
        return file_transfer

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
