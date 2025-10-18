from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.feature_identifier import FeatureIdentifier
    from ..models.geo_json_line_string import GeoJSONLineString
    from ..models.geo_json_multi_line_string import GeoJSONMultiLineString
    from ..models.geo_json_multi_point import GeoJSONMultiPoint
    from ..models.geo_json_multi_polygon import GeoJSONMultiPolygon
    from ..models.geo_json_point import GeoJSONPoint
    from ..models.geo_json_polygon import GeoJSONPolygon


T = TypeVar("T", bound="Feature")


@_attrs_define
class Feature:
    """A GeoJSON feature object.

    Attributes:
        geometry (Union['GeoJSONLineString', 'GeoJSONMultiLineString', 'GeoJSONMultiPoint', 'GeoJSONMultiPolygon',
            'GeoJSONPoint', 'GeoJSONPolygon', Unset]):
        identifiers (Union[Unset, list['FeatureIdentifier']]): A list of geographic location identifiers.
        place (Union[Unset, str]): Free text, used to describe a geographical location.
        description (Union[Unset, str]): Free text, used for any extra information related to the location.
    """

    geometry: Union[
        "GeoJSONLineString",
        "GeoJSONMultiLineString",
        "GeoJSONMultiPoint",
        "GeoJSONMultiPolygon",
        "GeoJSONPoint",
        "GeoJSONPolygon",
        Unset,
    ] = UNSET
    identifiers: Union[Unset, list["FeatureIdentifier"]] = UNSET
    place: Union[Unset, str] = UNSET
    description: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.geo_json_line_string import GeoJSONLineString
        from ..models.geo_json_multi_line_string import GeoJSONMultiLineString
        from ..models.geo_json_multi_point import GeoJSONMultiPoint
        from ..models.geo_json_point import GeoJSONPoint
        from ..models.geo_json_polygon import GeoJSONPolygon

        geometry: Union[Unset, dict[str, Any]]
        if isinstance(self.geometry, Unset):
            geometry = UNSET
        elif isinstance(self.geometry, GeoJSONPoint):
            geometry = self.geometry.to_dict()
        elif isinstance(self.geometry, GeoJSONLineString):
            geometry = self.geometry.to_dict()
        elif isinstance(self.geometry, GeoJSONPolygon):
            geometry = self.geometry.to_dict()
        elif isinstance(self.geometry, GeoJSONMultiPoint):
            geometry = self.geometry.to_dict()
        elif isinstance(self.geometry, GeoJSONMultiLineString):
            geometry = self.geometry.to_dict()
        else:
            geometry = self.geometry.to_dict()

        identifiers: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.identifiers, Unset):
            identifiers = []
            for identifiers_item_data in self.identifiers:
                identifiers_item = identifiers_item_data.to_dict()
                identifiers.append(identifiers_item)

        place = self.place

        description = self.description

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if geometry is not UNSET:
            field_dict["geometry"] = geometry
        if identifiers is not UNSET:
            field_dict["identifiers"] = identifiers
        if place is not UNSET:
            field_dict["place"] = place
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.feature_identifier import FeatureIdentifier
        from ..models.geo_json_line_string import GeoJSONLineString
        from ..models.geo_json_multi_line_string import GeoJSONMultiLineString
        from ..models.geo_json_multi_point import GeoJSONMultiPoint
        from ..models.geo_json_multi_polygon import GeoJSONMultiPolygon
        from ..models.geo_json_point import GeoJSONPoint
        from ..models.geo_json_polygon import GeoJSONPolygon

        d = dict(src_dict)

        def _parse_geometry(
            data: object,
        ) -> Union[
            "GeoJSONLineString",
            "GeoJSONMultiLineString",
            "GeoJSONMultiPoint",
            "GeoJSONMultiPolygon",
            "GeoJSONPoint",
            "GeoJSONPolygon",
            Unset,
        ]:
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_geometry_geo_json_point = GeoJSONPoint.from_dict(data)

                return componentsschemas_geometry_geo_json_point
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_geometry_geo_json_line_string = GeoJSONLineString.from_dict(data)

                return componentsschemas_geometry_geo_json_line_string
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_geometry_geo_json_polygon = GeoJSONPolygon.from_dict(data)

                return componentsschemas_geometry_geo_json_polygon
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_geometry_geo_json_multi_point = GeoJSONMultiPoint.from_dict(data)

                return componentsschemas_geometry_geo_json_multi_point
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_geometry_geo_json_multi_line_string = GeoJSONMultiLineString.from_dict(data)

                return componentsschemas_geometry_geo_json_multi_line_string
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            componentsschemas_geometry_geo_json_multi_polygon = GeoJSONMultiPolygon.from_dict(data)

            return componentsschemas_geometry_geo_json_multi_polygon

        geometry = _parse_geometry(d.pop("geometry", UNSET))

        identifiers = []
        _identifiers = d.pop("identifiers", UNSET)
        for identifiers_item_data in _identifiers or []:
            identifiers_item = FeatureIdentifier.from_dict(identifiers_item_data)

            identifiers.append(identifiers_item)

        place = d.pop("place", UNSET)

        description = d.pop("description", UNSET)

        feature = cls(
            geometry=geometry,
            identifiers=identifiers,
            place=place,
            description=description,
        )

        feature.additional_properties = d
        return feature

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
