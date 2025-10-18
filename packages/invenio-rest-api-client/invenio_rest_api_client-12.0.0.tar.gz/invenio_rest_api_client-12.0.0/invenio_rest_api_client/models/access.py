from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.access_files import AccessFiles
from ..models.access_record import AccessRecord
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.embargo import Embargo


T = TypeVar("T", bound="Access")


@_attrs_define
class Access:
    """Denotes record-specific read (visibility) options.

    More informations can be found on InvenioRDM Official page:
    https://inveniordm.docs.cern.ch/reference/metadata/#access

        Attributes:
            record (AccessRecord): Read access to the record.

                `public` means anyone can see the record/files, `restricted` means only the owner(s) or specific users can see
                the record/files.
            files (AccessFiles): Read access to the record's files.

                `public` means anyone can see the record/files, `restricted` means only the owner(s) or specific users can see
                the record/files.
            embargo (Union[Unset, Embargo]): Only in the cases of `"record": "restricted"`` or `"files": "restricted"`` can
                an embargo be provided as input.
                However, once an embargo is lifted, the embargo section is kept for transparency.

                Denotes when an embargo must be lifted, at which point the record is made publicly accessible.
    """

    record: AccessRecord
    files: AccessFiles
    embargo: Union[Unset, "Embargo"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        record = self.record.value

        files = self.files.value

        embargo: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.embargo, Unset):
            embargo = self.embargo.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "record": record,
                "files": files,
            }
        )
        if embargo is not UNSET:
            field_dict["embargo"] = embargo

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.embargo import Embargo

        d = dict(src_dict)
        record = AccessRecord(d.pop("record"))

        files = AccessFiles(d.pop("files"))

        _embargo = d.pop("embargo", UNSET)
        embargo: Union[Unset, Embargo]
        if isinstance(_embargo, Unset):
            embargo = UNSET
        else:
            embargo = Embargo.from_dict(_embargo)

        access = cls(
            record=record,
            files=files,
            embargo=embargo,
        )

        access.additional_properties = d
        return access

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
