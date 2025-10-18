import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.additional_description import AdditionalDescription
    from ..models.additional_title import AdditionalTitle
    from ..models.alternate_identifier import AlternateIdentifier
    from ..models.creator import Creator
    from ..models.date import Date
    from ..models.funding import Funding
    from ..models.lang import Lang
    from ..models.location import Location
    from ..models.reference import Reference
    from ..models.related_identifier import RelatedIdentifier
    from ..models.resource_type import ResourceType
    from ..models.right import Right
    from ..models.subject import Subject


T = TypeVar("T", bound="Metadata")


@_attrs_define
class Metadata:
    """Metadata schema of bibliographic records in InvenioRDM.

    More informations can be found on InvenioRDM Official page:
    https://inveniordm.docs.cern.ch/reference/metadata/#metadata

        Attributes:
            resource_type (ResourceType): The type of the resource described by the record.
            title (str): A primary name or primary title by which a resource is known.
            publication_date (datetime.date): The date when the resource was or will be made publicly available.
            creators (list['Creator']): The creators field registers those persons or organisations that should be credited
                for the resource described by the record.
            publisher (str): The name of the entity that holds, archives, publishes, prints, distributes, releases, issues,
                or produces the resource.
            additional_titles (Union[Unset, list['AdditionalTitle']]): Additional names or titles by which a resource is
                known
            description (Union[Unset, str]): The description of a record.
            additional_descriptions (Union[Unset, list['AdditionalDescription']]): Additional descriptions in addition to
                the primary description (e.g. abstracts in other languages), methods or further notes.
            rights (Union[Unset, list['Right']]): Rights management statement for the resource.
            copyright_ (Union[Unset, str]): The copyright field allows authors or depositors to specify a copyright
                statement for the record.
            contributors (Union[Unset, Any]): The organisations or persons responsible for collecting, managing,
                distributing, or otherwise contributing to the development of the resource.
            subjects (Union[Unset, list['Subject']]): Subject, keyword, classification code, or key phrase describing the
                resource.
            languages (Union[Unset, list['Lang']]): The languages of the resource.
            dates (Union[Unset, list['Date']]): Different dates relevant to the resource.
            version (Union[Unset, str]): The version number of the resource.
            identifiers (Union[Unset, list['AlternateIdentifier']]): Persistent identifiers for the resource other than the
                ones registered as system-managed internal or external persistent identifiers.
            related_identifiers (Union[Unset, list['RelatedIdentifier']]): Identifiers of related resources.
            sizes (Union[Unset, list[str]]): Size (e.g. bytes, pages, inches, etc.) or duration (extent), e.g. hours,
                minutes, days, etc., of a resource.
            formats (Union[Unset, list[str]]): Technical format of the resource.
            locations (Union[Unset, list['Location']]): Spatial region or named place where the data was gathered or about
                which the data is focused.
            funding (Union[Unset, list['Funding']]): Information about financial support (funding) for the resource being
                registered.
            references (Union[Unset, list['Reference']]): A list of reference strings.
    """

    resource_type: "ResourceType"
    title: str
    publication_date: datetime.date
    creators: list["Creator"]
    publisher: str
    additional_titles: Union[Unset, list["AdditionalTitle"]] = UNSET
    description: Union[Unset, str] = UNSET
    additional_descriptions: Union[Unset, list["AdditionalDescription"]] = UNSET
    rights: Union[Unset, list["Right"]] = UNSET
    copyright_: Union[Unset, str] = UNSET
    contributors: Union[Unset, Any] = UNSET
    subjects: Union[Unset, list["Subject"]] = UNSET
    languages: Union[Unset, list["Lang"]] = UNSET
    dates: Union[Unset, list["Date"]] = UNSET
    version: Union[Unset, str] = UNSET
    identifiers: Union[Unset, list["AlternateIdentifier"]] = UNSET
    related_identifiers: Union[Unset, list["RelatedIdentifier"]] = UNSET
    sizes: Union[Unset, list[str]] = UNSET
    formats: Union[Unset, list[str]] = UNSET
    locations: Union[Unset, list["Location"]] = UNSET
    funding: Union[Unset, list["Funding"]] = UNSET
    references: Union[Unset, list["Reference"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        resource_type = self.resource_type.to_dict()

        title = self.title

        publication_date = self.publication_date.isoformat()

        creators = []
        for creators_item_data in self.creators:
            creators_item = creators_item_data.to_dict()
            creators.append(creators_item)

        publisher = self.publisher

        additional_titles: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.additional_titles, Unset):
            additional_titles = []
            for additional_titles_item_data in self.additional_titles:
                additional_titles_item = additional_titles_item_data.to_dict()
                additional_titles.append(additional_titles_item)

        description = self.description

        additional_descriptions: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.additional_descriptions, Unset):
            additional_descriptions = []
            for additional_descriptions_item_data in self.additional_descriptions:
                additional_descriptions_item = additional_descriptions_item_data.to_dict()
                additional_descriptions.append(additional_descriptions_item)

        rights: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.rights, Unset):
            rights = []
            for rights_item_data in self.rights:
                rights_item = rights_item_data.to_dict()
                rights.append(rights_item)

        copyright_ = self.copyright_

        contributors = self.contributors

        subjects: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.subjects, Unset):
            subjects = []
            for subjects_item_data in self.subjects:
                subjects_item = subjects_item_data.to_dict()
                subjects.append(subjects_item)

        languages: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.languages, Unset):
            languages = []
            for languages_item_data in self.languages:
                languages_item = languages_item_data.to_dict()
                languages.append(languages_item)

        dates: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.dates, Unset):
            dates = []
            for dates_item_data in self.dates:
                dates_item = dates_item_data.to_dict()
                dates.append(dates_item)

        version = self.version

        identifiers: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.identifiers, Unset):
            identifiers = []
            for identifiers_item_data in self.identifiers:
                identifiers_item = identifiers_item_data.to_dict()
                identifiers.append(identifiers_item)

        related_identifiers: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.related_identifiers, Unset):
            related_identifiers = []
            for related_identifiers_item_data in self.related_identifiers:
                related_identifiers_item = related_identifiers_item_data.to_dict()
                related_identifiers.append(related_identifiers_item)

        sizes: Union[Unset, list[str]] = UNSET
        if not isinstance(self.sizes, Unset):
            sizes = self.sizes

        formats: Union[Unset, list[str]] = UNSET
        if not isinstance(self.formats, Unset):
            formats = self.formats

        locations: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.locations, Unset):
            locations = []
            for locations_item_data in self.locations:
                locations_item = locations_item_data.to_dict()
                locations.append(locations_item)

        funding: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.funding, Unset):
            funding = []
            for funding_item_data in self.funding:
                funding_item = funding_item_data.to_dict()
                funding.append(funding_item)

        references: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.references, Unset):
            references = []
            for references_item_data in self.references:
                references_item = references_item_data.to_dict()
                references.append(references_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "resource_type": resource_type,
                "title": title,
                "publication_date": publication_date,
                "creators": creators,
                "publisher": publisher,
            }
        )
        if additional_titles is not UNSET:
            field_dict["additional_titles"] = additional_titles
        if description is not UNSET:
            field_dict["description"] = description
        if additional_descriptions is not UNSET:
            field_dict["additional_descriptions"] = additional_descriptions
        if rights is not UNSET:
            field_dict["rights"] = rights
        if copyright_ is not UNSET:
            field_dict["copyright"] = copyright_
        if contributors is not UNSET:
            field_dict["contributors"] = contributors
        if subjects is not UNSET:
            field_dict["subjects"] = subjects
        if languages is not UNSET:
            field_dict["languages"] = languages
        if dates is not UNSET:
            field_dict["dates"] = dates
        if version is not UNSET:
            field_dict["version"] = version
        if identifiers is not UNSET:
            field_dict["identifiers"] = identifiers
        if related_identifiers is not UNSET:
            field_dict["related_identifiers"] = related_identifiers
        if sizes is not UNSET:
            field_dict["sizes"] = sizes
        if formats is not UNSET:
            field_dict["formats"] = formats
        if locations is not UNSET:
            field_dict["locations"] = locations
        if funding is not UNSET:
            field_dict["funding"] = funding
        if references is not UNSET:
            field_dict["references"] = references

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.additional_description import AdditionalDescription
        from ..models.additional_title import AdditionalTitle
        from ..models.alternate_identifier import AlternateIdentifier
        from ..models.creator import Creator
        from ..models.date import Date
        from ..models.funding import Funding
        from ..models.lang import Lang
        from ..models.location import Location
        from ..models.reference import Reference
        from ..models.related_identifier import RelatedIdentifier
        from ..models.resource_type import ResourceType
        from ..models.right import Right
        from ..models.subject import Subject

        d = dict(src_dict)
        resource_type = ResourceType.from_dict(d.pop("resource_type"))

        title = d.pop("title")

        publication_date = isoparse(d.pop("publication_date")).date()

        creators = []
        _creators = d.pop("creators")
        for creators_item_data in _creators:
            creators_item = Creator.from_dict(creators_item_data)

            creators.append(creators_item)

        publisher = d.pop("publisher")

        additional_titles = []
        _additional_titles = d.pop("additional_titles", UNSET)
        for additional_titles_item_data in _additional_titles or []:
            additional_titles_item = AdditionalTitle.from_dict(additional_titles_item_data)

            additional_titles.append(additional_titles_item)

        description = d.pop("description", UNSET)

        additional_descriptions = []
        _additional_descriptions = d.pop("additional_descriptions", UNSET)
        for additional_descriptions_item_data in _additional_descriptions or []:
            additional_descriptions_item = AdditionalDescription.from_dict(additional_descriptions_item_data)

            additional_descriptions.append(additional_descriptions_item)

        rights = []
        _rights = d.pop("rights", UNSET)
        for rights_item_data in _rights or []:
            rights_item = Right.from_dict(rights_item_data)

            rights.append(rights_item)

        copyright_ = d.pop("copyright", UNSET)

        contributors = d.pop("contributors", UNSET)

        subjects = []
        _subjects = d.pop("subjects", UNSET)
        for subjects_item_data in _subjects or []:
            subjects_item = Subject.from_dict(subjects_item_data)

            subjects.append(subjects_item)

        languages = []
        _languages = d.pop("languages", UNSET)
        for languages_item_data in _languages or []:
            languages_item = Lang.from_dict(languages_item_data)

            languages.append(languages_item)

        dates = []
        _dates = d.pop("dates", UNSET)
        for dates_item_data in _dates or []:
            dates_item = Date.from_dict(dates_item_data)

            dates.append(dates_item)

        version = d.pop("version", UNSET)

        identifiers = []
        _identifiers = d.pop("identifiers", UNSET)
        for identifiers_item_data in _identifiers or []:
            identifiers_item = AlternateIdentifier.from_dict(identifiers_item_data)

            identifiers.append(identifiers_item)

        related_identifiers = []
        _related_identifiers = d.pop("related_identifiers", UNSET)
        for related_identifiers_item_data in _related_identifiers or []:
            related_identifiers_item = RelatedIdentifier.from_dict(related_identifiers_item_data)

            related_identifiers.append(related_identifiers_item)

        sizes = cast(list[str], d.pop("sizes", UNSET))

        formats = cast(list[str], d.pop("formats", UNSET))

        locations = []
        _locations = d.pop("locations", UNSET)
        for locations_item_data in _locations or []:
            locations_item = Location.from_dict(locations_item_data)

            locations.append(locations_item)

        funding = []
        _funding = d.pop("funding", UNSET)
        for funding_item_data in _funding or []:
            funding_item = Funding.from_dict(funding_item_data)

            funding.append(funding_item)

        references = []
        _references = d.pop("references", UNSET)
        for references_item_data in _references or []:
            references_item = Reference.from_dict(references_item_data)

            references.append(references_item)

        metadata = cls(
            resource_type=resource_type,
            title=title,
            publication_date=publication_date,
            creators=creators,
            publisher=publisher,
            additional_titles=additional_titles,
            description=description,
            additional_descriptions=additional_descriptions,
            rights=rights,
            copyright_=copyright_,
            contributors=contributors,
            subjects=subjects,
            languages=languages,
            dates=dates,
            version=version,
            identifiers=identifiers,
            related_identifiers=related_identifiers,
            sizes=sizes,
            formats=formats,
            locations=locations,
            funding=funding,
            references=references,
        )

        metadata.additional_properties = d
        return metadata

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
