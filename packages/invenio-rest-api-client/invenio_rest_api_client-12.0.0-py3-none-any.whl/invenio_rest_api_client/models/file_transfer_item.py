from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.file_transfer import FileTransfer


T = TypeVar("T", bound="FileTransferItem")


@_attrs_define
class FileTransferItem:
    """A file object.

    Attributes:
        key (str): Key (filename) of the file
        size (Union[Unset, int]): Size of the file in bytes.
        checksum (Union[Unset, str]): Checksum of the file.
        transfer (Union[Unset, FileTransfer]):
    """

    key: str
    size: Union[Unset, int] = UNSET
    checksum: Union[Unset, str] = UNSET
    transfer: Union[Unset, "FileTransfer"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        key = self.key

        size = self.size

        checksum = self.checksum

        transfer: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.transfer, Unset):
            transfer = self.transfer.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "key": key,
            }
        )
        if size is not UNSET:
            field_dict["size"] = size
        if checksum is not UNSET:
            field_dict["checksum"] = checksum
        if transfer is not UNSET:
            field_dict["transfer"] = transfer

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.file_transfer import FileTransfer

        d = dict(src_dict)
        key = d.pop("key")

        size = d.pop("size", UNSET)

        checksum = d.pop("checksum", UNSET)

        _transfer = d.pop("transfer", UNSET)
        transfer: Union[Unset, FileTransfer]
        if isinstance(_transfer, Unset):
            transfer = UNSET
        else:
            transfer = FileTransfer.from_dict(_transfer)

        file_transfer_item = cls(
            key=key,
            size=size,
            checksum=checksum,
            transfer=transfer,
        )

        file_transfer_item.additional_properties = d
        return file_transfer_item

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
