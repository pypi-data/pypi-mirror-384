from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.access import Access
    from ..models.custom_fields import CustomFields
    from ..models.files import Files
    from ..models.metadata import Metadata


T = TypeVar("T", bound="UpdateDraftRecord")


@_attrs_define
class UpdateDraftRecord:
    """
    Attributes:
        access (Union[Unset, Access]): Denotes record-specific read (visibility) options.

            More informations can be found on InvenioRDM Official page:
            https://inveniordm.docs.cern.ch/reference/metadata/#access
        files (Union[Unset, Files]): Files options for the record.

            More informations can be found on InvenioRDM Official page:
            https://inveniordm.docs.cern.ch/reference/rest_api_drafts_records/#files-options
        metadata (Union[Unset, Metadata]): Metadata schema of bibliographic records in InvenioRDM.

            More informations can be found on InvenioRDM Official page:
            https://inveniordm.docs.cern.ch/reference/metadata/#metadata
        custom_fields (Union[Unset, CustomFields]): Custom fields metadata for the record. (v10 and newer).

            More informations can be found on InvenioRDM Official page:
            https://inveniordm.docs.cern.ch/operate/customize/metadata/custom_fields/records/#declaring-custom-fields
    """

    access: Union[Unset, "Access"] = UNSET
    files: Union[Unset, "Files"] = UNSET
    metadata: Union[Unset, "Metadata"] = UNSET
    custom_fields: Union[Unset, "CustomFields"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        access: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.access, Unset):
            access = self.access.to_dict()

        files: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.files, Unset):
            files = self.files.to_dict()

        metadata: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        custom_fields: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.custom_fields, Unset):
            custom_fields = self.custom_fields.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if access is not UNSET:
            field_dict["access"] = access
        if files is not UNSET:
            field_dict["files"] = files
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if custom_fields is not UNSET:
            field_dict["custom_fields"] = custom_fields

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.access import Access
        from ..models.custom_fields import CustomFields
        from ..models.files import Files
        from ..models.metadata import Metadata

        d = dict(src_dict)
        _access = d.pop("access", UNSET)
        access: Union[Unset, Access]
        if isinstance(_access, Unset):
            access = UNSET
        else:
            access = Access.from_dict(_access)

        _files = d.pop("files", UNSET)
        files: Union[Unset, Files]
        if isinstance(_files, Unset):
            files = UNSET
        else:
            files = Files.from_dict(_files)

        _metadata = d.pop("metadata", UNSET)
        metadata: Union[Unset, Metadata]
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = Metadata.from_dict(_metadata)

        _custom_fields = d.pop("custom_fields", UNSET)
        custom_fields: Union[Unset, CustomFields]
        if isinstance(_custom_fields, Unset):
            custom_fields = UNSET
        else:
            custom_fields = CustomFields.from_dict(_custom_fields)

        update_draft_record = cls(
            access=access,
            files=files,
            metadata=metadata,
            custom_fields=custom_fields,
        )

        update_draft_record.additional_properties = d
        return update_draft_record

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
