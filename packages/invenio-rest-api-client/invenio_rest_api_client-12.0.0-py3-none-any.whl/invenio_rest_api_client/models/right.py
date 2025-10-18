from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.right_description import RightDescription
    from ..models.right_title import RightTitle


T = TypeVar("T", bound="Right")


@_attrs_define
class Right:
    """Right management statement for the resource.

    Attributes:
        id (Union[Unset, str]): Identifier value.
        title (Union[Unset, RightTitle]): Localized human readable title.
        description (Union[Unset, RightDescription]): Localized license description text
        links (Union[Unset, str]): Link to full license.
    """

    id: Union[Unset, str] = UNSET
    title: Union[Unset, "RightTitle"] = UNSET
    description: Union[Unset, "RightDescription"] = UNSET
    links: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        title: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.title, Unset):
            title = self.title.to_dict()

        description: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.description, Unset):
            description = self.description.to_dict()

        links = self.links

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if title is not UNSET:
            field_dict["title"] = title
        if description is not UNSET:
            field_dict["description"] = description
        if links is not UNSET:
            field_dict["links"] = links

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.right_description import RightDescription
        from ..models.right_title import RightTitle

        d = dict(src_dict)
        id = d.pop("id", UNSET)

        _title = d.pop("title", UNSET)
        title: Union[Unset, RightTitle]
        if isinstance(_title, Unset):
            title = UNSET
        else:
            title = RightTitle.from_dict(_title)

        _description = d.pop("description", UNSET)
        description: Union[Unset, RightDescription]
        if isinstance(_description, Unset):
            description = UNSET
        else:
            description = RightDescription.from_dict(_description)

        links = d.pop("links", UNSET)

        right = cls(
            id=id,
            title=title,
            description=description,
            links=links,
        )

        right.additional_properties = d
        return right

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
