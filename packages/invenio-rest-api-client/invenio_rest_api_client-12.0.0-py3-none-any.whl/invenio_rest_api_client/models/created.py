import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.access import Access
    from ..models.created_links import CreatedLinks
    from ..models.created_metadata import CreatedMetadata
    from ..models.created_parent import CreatedParent
    from ..models.files import Files
    from ..models.pi_ds import PIDs
    from ..models.version import Version


T = TypeVar("T", bound="Created")


@_attrs_define
class Created:
    """
    Attributes:
        access (Union[Unset, Access]): Denotes record-specific read (visibility) options.

            More informations can be found on InvenioRDM Official page:
            https://inveniordm.docs.cern.ch/reference/metadata/#access
        created (Union[Unset, datetime.datetime]):
        expires_at (Union[Unset, datetime.datetime]):
        files (Union[Unset, Files]): Files options for the record.

            More informations can be found on InvenioRDM Official page:
            https://inveniordm.docs.cern.ch/reference/rest_api_drafts_records/#files-options
        id (Union[Unset, str]):
        is_published (Union[Unset, bool]):
        links (Union[Unset, CreatedLinks]):
        metadata (Union[Unset, CreatedMetadata]):
        parent (Union[Unset, CreatedParent]):
        pids (Union[Unset, PIDs]):
        revision_id (Union[Unset, int]):
        updated (Union[Unset, datetime.datetime]):
        versions (Union[Unset, Version]):
    """

    access: Union[Unset, "Access"] = UNSET
    created: Union[Unset, datetime.datetime] = UNSET
    expires_at: Union[Unset, datetime.datetime] = UNSET
    files: Union[Unset, "Files"] = UNSET
    id: Union[Unset, str] = UNSET
    is_published: Union[Unset, bool] = UNSET
    links: Union[Unset, "CreatedLinks"] = UNSET
    metadata: Union[Unset, "CreatedMetadata"] = UNSET
    parent: Union[Unset, "CreatedParent"] = UNSET
    pids: Union[Unset, "PIDs"] = UNSET
    revision_id: Union[Unset, int] = UNSET
    updated: Union[Unset, datetime.datetime] = UNSET
    versions: Union[Unset, "Version"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        access: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.access, Unset):
            access = self.access.to_dict()

        created: Union[Unset, str] = UNSET
        if not isinstance(self.created, Unset):
            created = self.created.isoformat()

        expires_at: Union[Unset, str] = UNSET
        if not isinstance(self.expires_at, Unset):
            expires_at = self.expires_at.isoformat()

        files: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.files, Unset):
            files = self.files.to_dict()

        id = self.id

        is_published = self.is_published

        links: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.links, Unset):
            links = self.links.to_dict()

        metadata: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        parent: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.parent, Unset):
            parent = self.parent.to_dict()

        pids: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.pids, Unset):
            pids = self.pids.to_dict()

        revision_id = self.revision_id

        updated: Union[Unset, str] = UNSET
        if not isinstance(self.updated, Unset):
            updated = self.updated.isoformat()

        versions: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.versions, Unset):
            versions = self.versions.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if access is not UNSET:
            field_dict["access"] = access
        if created is not UNSET:
            field_dict["created"] = created
        if expires_at is not UNSET:
            field_dict["expires_at"] = expires_at
        if files is not UNSET:
            field_dict["files"] = files
        if id is not UNSET:
            field_dict["id"] = id
        if is_published is not UNSET:
            field_dict["is_published"] = is_published
        if links is not UNSET:
            field_dict["links"] = links
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if parent is not UNSET:
            field_dict["parent"] = parent
        if pids is not UNSET:
            field_dict["pids"] = pids
        if revision_id is not UNSET:
            field_dict["revision_id"] = revision_id
        if updated is not UNSET:
            field_dict["updated"] = updated
        if versions is not UNSET:
            field_dict["versions"] = versions

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.access import Access
        from ..models.created_links import CreatedLinks
        from ..models.created_metadata import CreatedMetadata
        from ..models.created_parent import CreatedParent
        from ..models.files import Files
        from ..models.pi_ds import PIDs
        from ..models.version import Version

        d = dict(src_dict)
        _access = d.pop("access", UNSET)
        access: Union[Unset, Access]
        if isinstance(_access, Unset):
            access = UNSET
        else:
            access = Access.from_dict(_access)

        _created = d.pop("created", UNSET)
        created: Union[Unset, datetime.datetime]
        if isinstance(_created, Unset):
            created = UNSET
        else:
            created = isoparse(_created)

        _expires_at = d.pop("expires_at", UNSET)
        expires_at: Union[Unset, datetime.datetime]
        if isinstance(_expires_at, Unset):
            expires_at = UNSET
        else:
            expires_at = isoparse(_expires_at)

        _files = d.pop("files", UNSET)
        files: Union[Unset, Files]
        if isinstance(_files, Unset):
            files = UNSET
        else:
            files = Files.from_dict(_files)

        id = d.pop("id", UNSET)

        is_published = d.pop("is_published", UNSET)

        _links = d.pop("links", UNSET)
        links: Union[Unset, CreatedLinks]
        if isinstance(_links, Unset):
            links = UNSET
        else:
            links = CreatedLinks.from_dict(_links)

        _metadata = d.pop("metadata", UNSET)
        metadata: Union[Unset, CreatedMetadata]
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = CreatedMetadata.from_dict(_metadata)

        _parent = d.pop("parent", UNSET)
        parent: Union[Unset, CreatedParent]
        if isinstance(_parent, Unset):
            parent = UNSET
        else:
            parent = CreatedParent.from_dict(_parent)

        _pids = d.pop("pids", UNSET)
        pids: Union[Unset, PIDs]
        if isinstance(_pids, Unset):
            pids = UNSET
        else:
            pids = PIDs.from_dict(_pids)

        revision_id = d.pop("revision_id", UNSET)

        _updated = d.pop("updated", UNSET)
        updated: Union[Unset, datetime.datetime]
        if isinstance(_updated, Unset):
            updated = UNSET
        else:
            updated = isoparse(_updated)

        _versions = d.pop("versions", UNSET)
        versions: Union[Unset, Version]
        if isinstance(_versions, Unset):
            versions = UNSET
        else:
            versions = Version.from_dict(_versions)

        created = cls(
            access=access,
            created=created,
            expires_at=expires_at,
            files=files,
            id=id,
            is_published=is_published,
            links=links,
            metadata=metadata,
            parent=parent,
            pids=pids,
            revision_id=revision_id,
            updated=updated,
            versions=versions,
        )

        created.additional_properties = d
        return created

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
