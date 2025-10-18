from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.audit_log_list_aggregations import AuditLogListAggregations
    from ..models.audit_log_list_hits import AuditLogListHits


T = TypeVar("T", bound="AuditLogList")


@_attrs_define
class AuditLogList:
    """
    Attributes:
        hits (Union[Unset, AuditLogListHits]):
        aggregations (Union[Unset, AuditLogListAggregations]): Aggregation results (if any)
    """

    hits: Union[Unset, "AuditLogListHits"] = UNSET
    aggregations: Union[Unset, "AuditLogListAggregations"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        hits: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.hits, Unset):
            hits = self.hits.to_dict()

        aggregations: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.aggregations, Unset):
            aggregations = self.aggregations.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if hits is not UNSET:
            field_dict["hits"] = hits
        if aggregations is not UNSET:
            field_dict["aggregations"] = aggregations

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.audit_log_list_aggregations import AuditLogListAggregations
        from ..models.audit_log_list_hits import AuditLogListHits

        d = dict(src_dict)
        _hits = d.pop("hits", UNSET)
        hits: Union[Unset, AuditLogListHits]
        if isinstance(_hits, Unset):
            hits = UNSET
        else:
            hits = AuditLogListHits.from_dict(_hits)

        _aggregations = d.pop("aggregations", UNSET)
        aggregations: Union[Unset, AuditLogListAggregations]
        if isinstance(_aggregations, Unset):
            aggregations = UNSET
        else:
            aggregations = AuditLogListAggregations.from_dict(_aggregations)

        audit_log_list = cls(
            hits=hits,
            aggregations=aggregations,
        )

        audit_log_list.additional_properties = d
        return audit_log_list

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
