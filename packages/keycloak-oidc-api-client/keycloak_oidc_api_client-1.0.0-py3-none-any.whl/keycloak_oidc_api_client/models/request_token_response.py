from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="RequestTokenResponse")


@_attrs_define
class RequestTokenResponse:
    """
    Attributes:
        access_token (str):
        refresh_token (str):
        expires_in (Union[Unset, int]):
        refresh_expires_in (Union[Unset, int]):
        token_type (Union[Unset, str]):
        id_token (Union[Unset, str]):
        not_before_policy (Union[Unset, int]):
        session_state (Union[Unset, str]):
        scope (Union[Unset, str]):
    """

    access_token: str
    refresh_token: str
    expires_in: Union[Unset, int] = UNSET
    refresh_expires_in: Union[Unset, int] = UNSET
    token_type: Union[Unset, str] = UNSET
    id_token: Union[Unset, str] = UNSET
    not_before_policy: Union[Unset, int] = UNSET
    session_state: Union[Unset, str] = UNSET
    scope: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        access_token = self.access_token

        refresh_token = self.refresh_token

        expires_in = self.expires_in

        refresh_expires_in = self.refresh_expires_in

        token_type = self.token_type

        id_token = self.id_token

        not_before_policy = self.not_before_policy

        session_state = self.session_state

        scope = self.scope

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "access_token": access_token,
                "refresh_token": refresh_token,
            }
        )
        if expires_in is not UNSET:
            field_dict["expires_in"] = expires_in
        if refresh_expires_in is not UNSET:
            field_dict["refresh_expires_in"] = refresh_expires_in
        if token_type is not UNSET:
            field_dict["token_type"] = token_type
        if id_token is not UNSET:
            field_dict["id_token"] = id_token
        if not_before_policy is not UNSET:
            field_dict["not-before-policy"] = not_before_policy
        if session_state is not UNSET:
            field_dict["session_state"] = session_state
        if scope is not UNSET:
            field_dict["scope"] = scope

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        access_token = d.pop("access_token")

        refresh_token = d.pop("refresh_token")

        expires_in = d.pop("expires_in", UNSET)

        refresh_expires_in = d.pop("refresh_expires_in", UNSET)

        token_type = d.pop("token_type", UNSET)

        id_token = d.pop("id_token", UNSET)

        not_before_policy = d.pop("not-before-policy", UNSET)

        session_state = d.pop("session_state", UNSET)

        scope = d.pop("scope", UNSET)

        request_token_response = cls(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            refresh_expires_in=refresh_expires_in,
            token_type=token_type,
            id_token=id_token,
            not_before_policy=not_before_policy,
            session_state=session_state,
            scope=scope,
        )

        request_token_response.additional_properties = d
        return request_token_response

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
