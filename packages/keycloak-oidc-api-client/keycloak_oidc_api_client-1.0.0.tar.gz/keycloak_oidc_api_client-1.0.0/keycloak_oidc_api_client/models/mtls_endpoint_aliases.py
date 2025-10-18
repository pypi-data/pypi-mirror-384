from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="MtlsEndpointAliases")


@_attrs_define
class MtlsEndpointAliases:
    """
    Attributes:
        token_endpoint (Union[Unset, str]):
        revocation_endpoint (Union[Unset, str]):
        introspection_endpoint (Union[Unset, str]):
        device_authorization_endpoint (Union[Unset, str]):
        registration_endpoint (Union[Unset, str]):
        userinfo_endpoint (Union[Unset, str]):
        pushed_authorization_request_endpoint (Union[Unset, str]):
        backchannel_authentication_endpoint (Union[Unset, str]):
    """

    token_endpoint: Union[Unset, str] = UNSET
    revocation_endpoint: Union[Unset, str] = UNSET
    introspection_endpoint: Union[Unset, str] = UNSET
    device_authorization_endpoint: Union[Unset, str] = UNSET
    registration_endpoint: Union[Unset, str] = UNSET
    userinfo_endpoint: Union[Unset, str] = UNSET
    pushed_authorization_request_endpoint: Union[Unset, str] = UNSET
    backchannel_authentication_endpoint: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        token_endpoint = self.token_endpoint

        revocation_endpoint = self.revocation_endpoint

        introspection_endpoint = self.introspection_endpoint

        device_authorization_endpoint = self.device_authorization_endpoint

        registration_endpoint = self.registration_endpoint

        userinfo_endpoint = self.userinfo_endpoint

        pushed_authorization_request_endpoint = self.pushed_authorization_request_endpoint

        backchannel_authentication_endpoint = self.backchannel_authentication_endpoint

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if token_endpoint is not UNSET:
            field_dict["token_endpoint"] = token_endpoint
        if revocation_endpoint is not UNSET:
            field_dict["revocation_endpoint"] = revocation_endpoint
        if introspection_endpoint is not UNSET:
            field_dict["introspection_endpoint"] = introspection_endpoint
        if device_authorization_endpoint is not UNSET:
            field_dict["device_authorization_endpoint"] = device_authorization_endpoint
        if registration_endpoint is not UNSET:
            field_dict["registration_endpoint"] = registration_endpoint
        if userinfo_endpoint is not UNSET:
            field_dict["userinfo_endpoint"] = userinfo_endpoint
        if pushed_authorization_request_endpoint is not UNSET:
            field_dict["pushed_authorization_request_endpoint"] = pushed_authorization_request_endpoint
        if backchannel_authentication_endpoint is not UNSET:
            field_dict["backchannel_authentication_endpoint"] = backchannel_authentication_endpoint

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        token_endpoint = d.pop("token_endpoint", UNSET)

        revocation_endpoint = d.pop("revocation_endpoint", UNSET)

        introspection_endpoint = d.pop("introspection_endpoint", UNSET)

        device_authorization_endpoint = d.pop("device_authorization_endpoint", UNSET)

        registration_endpoint = d.pop("registration_endpoint", UNSET)

        userinfo_endpoint = d.pop("userinfo_endpoint", UNSET)

        pushed_authorization_request_endpoint = d.pop("pushed_authorization_request_endpoint", UNSET)

        backchannel_authentication_endpoint = d.pop("backchannel_authentication_endpoint", UNSET)

        mtls_endpoint_aliases = cls(
            token_endpoint=token_endpoint,
            revocation_endpoint=revocation_endpoint,
            introspection_endpoint=introspection_endpoint,
            device_authorization_endpoint=device_authorization_endpoint,
            registration_endpoint=registration_endpoint,
            userinfo_endpoint=userinfo_endpoint,
            pushed_authorization_request_endpoint=pushed_authorization_request_endpoint,
            backchannel_authentication_endpoint=backchannel_authentication_endpoint,
        )

        mtls_endpoint_aliases.additional_properties = d
        return mtls_endpoint_aliases

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
