from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="PID")


@_attrs_define
class PID:
    """An external persistent identifier object.

    Attributes:
        identifier (Union[Unset, Any]): An identifier.
        provider (Union[Unset, str]): The provider of the persistent identifier.
        client (Union[Unset, str]): Client identifier for the specific PID.
    """

    identifier: Union[Unset, Any] = UNSET
    provider: Union[Unset, str] = UNSET
    client: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        identifier = self.identifier

        provider = self.provider

        client = self.client

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if identifier is not UNSET:
            field_dict["identifier"] = identifier
        if provider is not UNSET:
            field_dict["provider"] = provider
        if client is not UNSET:
            field_dict["client"] = client

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        identifier = d.pop("identifier", UNSET)

        provider = d.pop("provider", UNSET)

        client = d.pop("client", UNSET)

        pid = cls(
            identifier=identifier,
            provider=provider,
            client=client,
        )

        return pid
