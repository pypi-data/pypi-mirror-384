from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="RequestToken")


@_attrs_define
class RequestToken:
    """
    Attributes:
        client_id (str):
        grant_type (str):
        device_code (Union[Unset, str]):
        client_secret (Union[Unset, str]):
        refresh_token (Union[Unset, str]):
    """

    client_id: str
    grant_type: str
    device_code: Union[Unset, str] = UNSET
    client_secret: Union[Unset, str] = UNSET
    refresh_token: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        client_id = self.client_id

        grant_type = self.grant_type

        device_code = self.device_code

        client_secret = self.client_secret

        refresh_token = self.refresh_token

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "client_id": client_id,
                "grant_type": grant_type,
            }
        )
        if device_code is not UNSET:
            field_dict["device_code"] = device_code
        if client_secret is not UNSET:
            field_dict["client_secret"] = client_secret
        if refresh_token is not UNSET:
            field_dict["refresh_token"] = refresh_token

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        client_id = d.pop("client_id")

        grant_type = d.pop("grant_type")

        device_code = d.pop("device_code", UNSET)

        client_secret = d.pop("client_secret", UNSET)

        refresh_token = d.pop("refresh_token", UNSET)

        request_token = cls(
            client_id=client_id,
            grant_type=grant_type,
            device_code=device_code,
            client_secret=client_secret,
            refresh_token=refresh_token,
        )

        request_token.additional_properties = d
        return request_token

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
