from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.mtls_endpoint_aliases import MtlsEndpointAliases


T = TypeVar("T", bound="WellKnown")


@_attrs_define
class WellKnown:
    """
    Attributes:
        issuer (Union[Unset, str]):
        authorization_endpoint (Union[Unset, str]):
        token_endpoint (Union[Unset, str]):
        introspection_endpoint (Union[Unset, str]):
        userinfo_endpoint (Union[Unset, str]):
        end_session_endpoint (Union[Unset, str]):
        frontchannel_logout_session_supported (Union[Unset, bool]):
        frontchannel_logout_supported (Union[Unset, bool]):
        jwks_uri (Union[Unset, str]):
        check_session_iframe (Union[Unset, str]):
        grant_types_supported (Union[Unset, list[str]]):
        acr_values_supported (Union[Unset, list[str]]):
        response_types_supported (Union[Unset, list[str]]):
        subject_types_supported (Union[Unset, list[str]]):
        id_token_signing_alg_values_supported (Union[Unset, list[str]]):
        id_token_encryption_alg_values_supported (Union[Unset, list[str]]):
        id_token_encryption_enc_values_supported (Union[Unset, list[str]]):
        userinfo_signing_alg_values_supported (Union[Unset, list[str]]):
        userinfo_encryption_alg_values_supported (Union[Unset, list[str]]):
        userinfo_encryption_enc_values_supported (Union[Unset, list[str]]):
        request_object_signing_alg_values_supported (Union[Unset, list[str]]):
        request_object_encryption_alg_values_supported (Union[Unset, list[str]]):
        request_object_encryption_enc_values_supported (Union[Unset, list[str]]):
        response_modes_supported (Union[Unset, list[str]]):
        registration_endpoint (Union[Unset, str]):
        token_endpoint_auth_methods_supported (Union[Unset, list[str]]):
        token_endpoint_auth_signing_alg_values_supported (Union[Unset, list[str]]):
        introspection_endpoint_auth_methods_supported (Union[Unset, list[str]]):
        introspection_endpoint_auth_signing_alg_values_supported (Union[Unset, list[str]]):
        authorization_signing_alg_values_supported (Union[Unset, list[str]]):
        authorization_encryption_alg_values_supported (Union[Unset, list[str]]):
        authorization_encryption_enc_values_supported (Union[Unset, list[str]]):
        claims_supported (Union[Unset, list[str]]):
        claim_types_supported (Union[Unset, list[str]]):
        claims_parameter_supported (Union[Unset, bool]):
        scopes_supported (Union[Unset, list[str]]):
        request_parameter_supported (Union[Unset, bool]):
        request_uri_parameter_supported (Union[Unset, bool]):
        require_request_uri_registration (Union[Unset, bool]):
        code_challenge_methods_supported (Union[Unset, list[str]]):
        tls_client_certificate_bound_access_tokens (Union[Unset, bool]):
        revocation_endpoint (Union[Unset, str]):
        revocation_endpoint_auth_methods_supported (Union[Unset, list[str]]):
        revocation_endpoint_auth_signing_alg_values_supported (Union[Unset, list[str]]):
        backchannel_logout_supported (Union[Unset, bool]):
        backchannel_logout_session_supported (Union[Unset, bool]):
        device_authorization_endpoint (Union[Unset, str]):
        backchannel_token_delivery_modes_supported (Union[Unset, list[str]]):
        backchannel_authentication_endpoint (Union[Unset, str]):
        backchannel_authentication_request_signing_alg_values_supported (Union[Unset, list[str]]):
        require_pushed_authorization_requests (Union[Unset, bool]):
        pushed_authorization_request_endpoint (Union[Unset, str]):
        mtls_endpoint_aliases (Union[Unset, MtlsEndpointAliases]):
        authorization_response_iss_parameter_supported (Union[Unset, bool]):
    """

    issuer: Union[Unset, str] = UNSET
    authorization_endpoint: Union[Unset, str] = UNSET
    token_endpoint: Union[Unset, str] = UNSET
    introspection_endpoint: Union[Unset, str] = UNSET
    userinfo_endpoint: Union[Unset, str] = UNSET
    end_session_endpoint: Union[Unset, str] = UNSET
    frontchannel_logout_session_supported: Union[Unset, bool] = UNSET
    frontchannel_logout_supported: Union[Unset, bool] = UNSET
    jwks_uri: Union[Unset, str] = UNSET
    check_session_iframe: Union[Unset, str] = UNSET
    grant_types_supported: Union[Unset, list[str]] = UNSET
    acr_values_supported: Union[Unset, list[str]] = UNSET
    response_types_supported: Union[Unset, list[str]] = UNSET
    subject_types_supported: Union[Unset, list[str]] = UNSET
    id_token_signing_alg_values_supported: Union[Unset, list[str]] = UNSET
    id_token_encryption_alg_values_supported: Union[Unset, list[str]] = UNSET
    id_token_encryption_enc_values_supported: Union[Unset, list[str]] = UNSET
    userinfo_signing_alg_values_supported: Union[Unset, list[str]] = UNSET
    userinfo_encryption_alg_values_supported: Union[Unset, list[str]] = UNSET
    userinfo_encryption_enc_values_supported: Union[Unset, list[str]] = UNSET
    request_object_signing_alg_values_supported: Union[Unset, list[str]] = UNSET
    request_object_encryption_alg_values_supported: Union[Unset, list[str]] = UNSET
    request_object_encryption_enc_values_supported: Union[Unset, list[str]] = UNSET
    response_modes_supported: Union[Unset, list[str]] = UNSET
    registration_endpoint: Union[Unset, str] = UNSET
    token_endpoint_auth_methods_supported: Union[Unset, list[str]] = UNSET
    token_endpoint_auth_signing_alg_values_supported: Union[Unset, list[str]] = UNSET
    introspection_endpoint_auth_methods_supported: Union[Unset, list[str]] = UNSET
    introspection_endpoint_auth_signing_alg_values_supported: Union[Unset, list[str]] = UNSET
    authorization_signing_alg_values_supported: Union[Unset, list[str]] = UNSET
    authorization_encryption_alg_values_supported: Union[Unset, list[str]] = UNSET
    authorization_encryption_enc_values_supported: Union[Unset, list[str]] = UNSET
    claims_supported: Union[Unset, list[str]] = UNSET
    claim_types_supported: Union[Unset, list[str]] = UNSET
    claims_parameter_supported: Union[Unset, bool] = UNSET
    scopes_supported: Union[Unset, list[str]] = UNSET
    request_parameter_supported: Union[Unset, bool] = UNSET
    request_uri_parameter_supported: Union[Unset, bool] = UNSET
    require_request_uri_registration: Union[Unset, bool] = UNSET
    code_challenge_methods_supported: Union[Unset, list[str]] = UNSET
    tls_client_certificate_bound_access_tokens: Union[Unset, bool] = UNSET
    revocation_endpoint: Union[Unset, str] = UNSET
    revocation_endpoint_auth_methods_supported: Union[Unset, list[str]] = UNSET
    revocation_endpoint_auth_signing_alg_values_supported: Union[Unset, list[str]] = UNSET
    backchannel_logout_supported: Union[Unset, bool] = UNSET
    backchannel_logout_session_supported: Union[Unset, bool] = UNSET
    device_authorization_endpoint: Union[Unset, str] = UNSET
    backchannel_token_delivery_modes_supported: Union[Unset, list[str]] = UNSET
    backchannel_authentication_endpoint: Union[Unset, str] = UNSET
    backchannel_authentication_request_signing_alg_values_supported: Union[Unset, list[str]] = UNSET
    require_pushed_authorization_requests: Union[Unset, bool] = UNSET
    pushed_authorization_request_endpoint: Union[Unset, str] = UNSET
    mtls_endpoint_aliases: Union[Unset, "MtlsEndpointAliases"] = UNSET
    authorization_response_iss_parameter_supported: Union[Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        issuer = self.issuer

        authorization_endpoint = self.authorization_endpoint

        token_endpoint = self.token_endpoint

        introspection_endpoint = self.introspection_endpoint

        userinfo_endpoint = self.userinfo_endpoint

        end_session_endpoint = self.end_session_endpoint

        frontchannel_logout_session_supported = self.frontchannel_logout_session_supported

        frontchannel_logout_supported = self.frontchannel_logout_supported

        jwks_uri = self.jwks_uri

        check_session_iframe = self.check_session_iframe

        grant_types_supported: Union[Unset, list[str]] = UNSET
        if not isinstance(self.grant_types_supported, Unset):
            grant_types_supported = self.grant_types_supported

        acr_values_supported: Union[Unset, list[str]] = UNSET
        if not isinstance(self.acr_values_supported, Unset):
            acr_values_supported = self.acr_values_supported

        response_types_supported: Union[Unset, list[str]] = UNSET
        if not isinstance(self.response_types_supported, Unset):
            response_types_supported = self.response_types_supported

        subject_types_supported: Union[Unset, list[str]] = UNSET
        if not isinstance(self.subject_types_supported, Unset):
            subject_types_supported = self.subject_types_supported

        id_token_signing_alg_values_supported: Union[Unset, list[str]] = UNSET
        if not isinstance(self.id_token_signing_alg_values_supported, Unset):
            id_token_signing_alg_values_supported = self.id_token_signing_alg_values_supported

        id_token_encryption_alg_values_supported: Union[Unset, list[str]] = UNSET
        if not isinstance(self.id_token_encryption_alg_values_supported, Unset):
            id_token_encryption_alg_values_supported = self.id_token_encryption_alg_values_supported

        id_token_encryption_enc_values_supported: Union[Unset, list[str]] = UNSET
        if not isinstance(self.id_token_encryption_enc_values_supported, Unset):
            id_token_encryption_enc_values_supported = self.id_token_encryption_enc_values_supported

        userinfo_signing_alg_values_supported: Union[Unset, list[str]] = UNSET
        if not isinstance(self.userinfo_signing_alg_values_supported, Unset):
            userinfo_signing_alg_values_supported = self.userinfo_signing_alg_values_supported

        userinfo_encryption_alg_values_supported: Union[Unset, list[str]] = UNSET
        if not isinstance(self.userinfo_encryption_alg_values_supported, Unset):
            userinfo_encryption_alg_values_supported = self.userinfo_encryption_alg_values_supported

        userinfo_encryption_enc_values_supported: Union[Unset, list[str]] = UNSET
        if not isinstance(self.userinfo_encryption_enc_values_supported, Unset):
            userinfo_encryption_enc_values_supported = self.userinfo_encryption_enc_values_supported

        request_object_signing_alg_values_supported: Union[Unset, list[str]] = UNSET
        if not isinstance(self.request_object_signing_alg_values_supported, Unset):
            request_object_signing_alg_values_supported = self.request_object_signing_alg_values_supported

        request_object_encryption_alg_values_supported: Union[Unset, list[str]] = UNSET
        if not isinstance(self.request_object_encryption_alg_values_supported, Unset):
            request_object_encryption_alg_values_supported = self.request_object_encryption_alg_values_supported

        request_object_encryption_enc_values_supported: Union[Unset, list[str]] = UNSET
        if not isinstance(self.request_object_encryption_enc_values_supported, Unset):
            request_object_encryption_enc_values_supported = self.request_object_encryption_enc_values_supported

        response_modes_supported: Union[Unset, list[str]] = UNSET
        if not isinstance(self.response_modes_supported, Unset):
            response_modes_supported = self.response_modes_supported

        registration_endpoint = self.registration_endpoint

        token_endpoint_auth_methods_supported: Union[Unset, list[str]] = UNSET
        if not isinstance(self.token_endpoint_auth_methods_supported, Unset):
            token_endpoint_auth_methods_supported = self.token_endpoint_auth_methods_supported

        token_endpoint_auth_signing_alg_values_supported: Union[Unset, list[str]] = UNSET
        if not isinstance(self.token_endpoint_auth_signing_alg_values_supported, Unset):
            token_endpoint_auth_signing_alg_values_supported = self.token_endpoint_auth_signing_alg_values_supported

        introspection_endpoint_auth_methods_supported: Union[Unset, list[str]] = UNSET
        if not isinstance(self.introspection_endpoint_auth_methods_supported, Unset):
            introspection_endpoint_auth_methods_supported = self.introspection_endpoint_auth_methods_supported

        introspection_endpoint_auth_signing_alg_values_supported: Union[Unset, list[str]] = UNSET
        if not isinstance(self.introspection_endpoint_auth_signing_alg_values_supported, Unset):
            introspection_endpoint_auth_signing_alg_values_supported = (
                self.introspection_endpoint_auth_signing_alg_values_supported
            )

        authorization_signing_alg_values_supported: Union[Unset, list[str]] = UNSET
        if not isinstance(self.authorization_signing_alg_values_supported, Unset):
            authorization_signing_alg_values_supported = self.authorization_signing_alg_values_supported

        authorization_encryption_alg_values_supported: Union[Unset, list[str]] = UNSET
        if not isinstance(self.authorization_encryption_alg_values_supported, Unset):
            authorization_encryption_alg_values_supported = self.authorization_encryption_alg_values_supported

        authorization_encryption_enc_values_supported: Union[Unset, list[str]] = UNSET
        if not isinstance(self.authorization_encryption_enc_values_supported, Unset):
            authorization_encryption_enc_values_supported = self.authorization_encryption_enc_values_supported

        claims_supported: Union[Unset, list[str]] = UNSET
        if not isinstance(self.claims_supported, Unset):
            claims_supported = self.claims_supported

        claim_types_supported: Union[Unset, list[str]] = UNSET
        if not isinstance(self.claim_types_supported, Unset):
            claim_types_supported = self.claim_types_supported

        claims_parameter_supported = self.claims_parameter_supported

        scopes_supported: Union[Unset, list[str]] = UNSET
        if not isinstance(self.scopes_supported, Unset):
            scopes_supported = self.scopes_supported

        request_parameter_supported = self.request_parameter_supported

        request_uri_parameter_supported = self.request_uri_parameter_supported

        require_request_uri_registration = self.require_request_uri_registration

        code_challenge_methods_supported: Union[Unset, list[str]] = UNSET
        if not isinstance(self.code_challenge_methods_supported, Unset):
            code_challenge_methods_supported = self.code_challenge_methods_supported

        tls_client_certificate_bound_access_tokens = self.tls_client_certificate_bound_access_tokens

        revocation_endpoint = self.revocation_endpoint

        revocation_endpoint_auth_methods_supported: Union[Unset, list[str]] = UNSET
        if not isinstance(self.revocation_endpoint_auth_methods_supported, Unset):
            revocation_endpoint_auth_methods_supported = self.revocation_endpoint_auth_methods_supported

        revocation_endpoint_auth_signing_alg_values_supported: Union[Unset, list[str]] = UNSET
        if not isinstance(self.revocation_endpoint_auth_signing_alg_values_supported, Unset):
            revocation_endpoint_auth_signing_alg_values_supported = (
                self.revocation_endpoint_auth_signing_alg_values_supported
            )

        backchannel_logout_supported = self.backchannel_logout_supported

        backchannel_logout_session_supported = self.backchannel_logout_session_supported

        device_authorization_endpoint = self.device_authorization_endpoint

        backchannel_token_delivery_modes_supported: Union[Unset, list[str]] = UNSET
        if not isinstance(self.backchannel_token_delivery_modes_supported, Unset):
            backchannel_token_delivery_modes_supported = self.backchannel_token_delivery_modes_supported

        backchannel_authentication_endpoint = self.backchannel_authentication_endpoint

        backchannel_authentication_request_signing_alg_values_supported: Union[Unset, list[str]] = UNSET
        if not isinstance(self.backchannel_authentication_request_signing_alg_values_supported, Unset):
            backchannel_authentication_request_signing_alg_values_supported = (
                self.backchannel_authentication_request_signing_alg_values_supported
            )

        require_pushed_authorization_requests = self.require_pushed_authorization_requests

        pushed_authorization_request_endpoint = self.pushed_authorization_request_endpoint

        mtls_endpoint_aliases: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.mtls_endpoint_aliases, Unset):
            mtls_endpoint_aliases = self.mtls_endpoint_aliases.to_dict()

        authorization_response_iss_parameter_supported = self.authorization_response_iss_parameter_supported

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if issuer is not UNSET:
            field_dict["issuer"] = issuer
        if authorization_endpoint is not UNSET:
            field_dict["authorization_endpoint"] = authorization_endpoint
        if token_endpoint is not UNSET:
            field_dict["token_endpoint"] = token_endpoint
        if introspection_endpoint is not UNSET:
            field_dict["introspection_endpoint"] = introspection_endpoint
        if userinfo_endpoint is not UNSET:
            field_dict["userinfo_endpoint"] = userinfo_endpoint
        if end_session_endpoint is not UNSET:
            field_dict["end_session_endpoint"] = end_session_endpoint
        if frontchannel_logout_session_supported is not UNSET:
            field_dict["frontchannel_logout_session_supported"] = frontchannel_logout_session_supported
        if frontchannel_logout_supported is not UNSET:
            field_dict["frontchannel_logout_supported"] = frontchannel_logout_supported
        if jwks_uri is not UNSET:
            field_dict["jwks_uri"] = jwks_uri
        if check_session_iframe is not UNSET:
            field_dict["check_session_iframe"] = check_session_iframe
        if grant_types_supported is not UNSET:
            field_dict["grant_types_supported"] = grant_types_supported
        if acr_values_supported is not UNSET:
            field_dict["acr_values_supported"] = acr_values_supported
        if response_types_supported is not UNSET:
            field_dict["response_types_supported"] = response_types_supported
        if subject_types_supported is not UNSET:
            field_dict["subject_types_supported"] = subject_types_supported
        if id_token_signing_alg_values_supported is not UNSET:
            field_dict["id_token_signing_alg_values_supported"] = id_token_signing_alg_values_supported
        if id_token_encryption_alg_values_supported is not UNSET:
            field_dict["id_token_encryption_alg_values_supported"] = id_token_encryption_alg_values_supported
        if id_token_encryption_enc_values_supported is not UNSET:
            field_dict["id_token_encryption_enc_values_supported"] = id_token_encryption_enc_values_supported
        if userinfo_signing_alg_values_supported is not UNSET:
            field_dict["userinfo_signing_alg_values_supported"] = userinfo_signing_alg_values_supported
        if userinfo_encryption_alg_values_supported is not UNSET:
            field_dict["userinfo_encryption_alg_values_supported"] = userinfo_encryption_alg_values_supported
        if userinfo_encryption_enc_values_supported is not UNSET:
            field_dict["userinfo_encryption_enc_values_supported"] = userinfo_encryption_enc_values_supported
        if request_object_signing_alg_values_supported is not UNSET:
            field_dict["request_object_signing_alg_values_supported"] = request_object_signing_alg_values_supported
        if request_object_encryption_alg_values_supported is not UNSET:
            field_dict["request_object_encryption_alg_values_supported"] = (
                request_object_encryption_alg_values_supported
            )
        if request_object_encryption_enc_values_supported is not UNSET:
            field_dict["request_object_encryption_enc_values_supported"] = (
                request_object_encryption_enc_values_supported
            )
        if response_modes_supported is not UNSET:
            field_dict["response_modes_supported"] = response_modes_supported
        if registration_endpoint is not UNSET:
            field_dict["registration_endpoint"] = registration_endpoint
        if token_endpoint_auth_methods_supported is not UNSET:
            field_dict["token_endpoint_auth_methods_supported"] = token_endpoint_auth_methods_supported
        if token_endpoint_auth_signing_alg_values_supported is not UNSET:
            field_dict["token_endpoint_auth_signing_alg_values_supported"] = (
                token_endpoint_auth_signing_alg_values_supported
            )
        if introspection_endpoint_auth_methods_supported is not UNSET:
            field_dict["introspection_endpoint_auth_methods_supported"] = introspection_endpoint_auth_methods_supported
        if introspection_endpoint_auth_signing_alg_values_supported is not UNSET:
            field_dict["introspection_endpoint_auth_signing_alg_values_supported"] = (
                introspection_endpoint_auth_signing_alg_values_supported
            )
        if authorization_signing_alg_values_supported is not UNSET:
            field_dict["authorization_signing_alg_values_supported"] = authorization_signing_alg_values_supported
        if authorization_encryption_alg_values_supported is not UNSET:
            field_dict["authorization_encryption_alg_values_supported"] = authorization_encryption_alg_values_supported
        if authorization_encryption_enc_values_supported is not UNSET:
            field_dict["authorization_encryption_enc_values_supported"] = authorization_encryption_enc_values_supported
        if claims_supported is not UNSET:
            field_dict["claims_supported"] = claims_supported
        if claim_types_supported is not UNSET:
            field_dict["claim_types_supported"] = claim_types_supported
        if claims_parameter_supported is not UNSET:
            field_dict["claims_parameter_supported"] = claims_parameter_supported
        if scopes_supported is not UNSET:
            field_dict["scopes_supported"] = scopes_supported
        if request_parameter_supported is not UNSET:
            field_dict["request_parameter_supported"] = request_parameter_supported
        if request_uri_parameter_supported is not UNSET:
            field_dict["request_uri_parameter_supported"] = request_uri_parameter_supported
        if require_request_uri_registration is not UNSET:
            field_dict["require_request_uri_registration"] = require_request_uri_registration
        if code_challenge_methods_supported is not UNSET:
            field_dict["code_challenge_methods_supported"] = code_challenge_methods_supported
        if tls_client_certificate_bound_access_tokens is not UNSET:
            field_dict["tls_client_certificate_bound_access_tokens"] = tls_client_certificate_bound_access_tokens
        if revocation_endpoint is not UNSET:
            field_dict["revocation_endpoint"] = revocation_endpoint
        if revocation_endpoint_auth_methods_supported is not UNSET:
            field_dict["revocation_endpoint_auth_methods_supported"] = revocation_endpoint_auth_methods_supported
        if revocation_endpoint_auth_signing_alg_values_supported is not UNSET:
            field_dict["revocation_endpoint_auth_signing_alg_values_supported"] = (
                revocation_endpoint_auth_signing_alg_values_supported
            )
        if backchannel_logout_supported is not UNSET:
            field_dict["backchannel_logout_supported"] = backchannel_logout_supported
        if backchannel_logout_session_supported is not UNSET:
            field_dict["backchannel_logout_session_supported"] = backchannel_logout_session_supported
        if device_authorization_endpoint is not UNSET:
            field_dict["device_authorization_endpoint"] = device_authorization_endpoint
        if backchannel_token_delivery_modes_supported is not UNSET:
            field_dict["backchannel_token_delivery_modes_supported"] = backchannel_token_delivery_modes_supported
        if backchannel_authentication_endpoint is not UNSET:
            field_dict["backchannel_authentication_endpoint"] = backchannel_authentication_endpoint
        if backchannel_authentication_request_signing_alg_values_supported is not UNSET:
            field_dict["backchannel_authentication_request_signing_alg_values_supported"] = (
                backchannel_authentication_request_signing_alg_values_supported
            )
        if require_pushed_authorization_requests is not UNSET:
            field_dict["require_pushed_authorization_requests"] = require_pushed_authorization_requests
        if pushed_authorization_request_endpoint is not UNSET:
            field_dict["pushed_authorization_request_endpoint"] = pushed_authorization_request_endpoint
        if mtls_endpoint_aliases is not UNSET:
            field_dict["mtls_endpoint_aliases"] = mtls_endpoint_aliases
        if authorization_response_iss_parameter_supported is not UNSET:
            field_dict["authorization_response_iss_parameter_supported"] = (
                authorization_response_iss_parameter_supported
            )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.mtls_endpoint_aliases import MtlsEndpointAliases

        d = dict(src_dict)
        issuer = d.pop("issuer", UNSET)

        authorization_endpoint = d.pop("authorization_endpoint", UNSET)

        token_endpoint = d.pop("token_endpoint", UNSET)

        introspection_endpoint = d.pop("introspection_endpoint", UNSET)

        userinfo_endpoint = d.pop("userinfo_endpoint", UNSET)

        end_session_endpoint = d.pop("end_session_endpoint", UNSET)

        frontchannel_logout_session_supported = d.pop("frontchannel_logout_session_supported", UNSET)

        frontchannel_logout_supported = d.pop("frontchannel_logout_supported", UNSET)

        jwks_uri = d.pop("jwks_uri", UNSET)

        check_session_iframe = d.pop("check_session_iframe", UNSET)

        grant_types_supported = cast(list[str], d.pop("grant_types_supported", UNSET))

        acr_values_supported = cast(list[str], d.pop("acr_values_supported", UNSET))

        response_types_supported = cast(list[str], d.pop("response_types_supported", UNSET))

        subject_types_supported = cast(list[str], d.pop("subject_types_supported", UNSET))

        id_token_signing_alg_values_supported = cast(list[str], d.pop("id_token_signing_alg_values_supported", UNSET))

        id_token_encryption_alg_values_supported = cast(
            list[str], d.pop("id_token_encryption_alg_values_supported", UNSET)
        )

        id_token_encryption_enc_values_supported = cast(
            list[str], d.pop("id_token_encryption_enc_values_supported", UNSET)
        )

        userinfo_signing_alg_values_supported = cast(list[str], d.pop("userinfo_signing_alg_values_supported", UNSET))

        userinfo_encryption_alg_values_supported = cast(
            list[str], d.pop("userinfo_encryption_alg_values_supported", UNSET)
        )

        userinfo_encryption_enc_values_supported = cast(
            list[str], d.pop("userinfo_encryption_enc_values_supported", UNSET)
        )

        request_object_signing_alg_values_supported = cast(
            list[str], d.pop("request_object_signing_alg_values_supported", UNSET)
        )

        request_object_encryption_alg_values_supported = cast(
            list[str], d.pop("request_object_encryption_alg_values_supported", UNSET)
        )

        request_object_encryption_enc_values_supported = cast(
            list[str], d.pop("request_object_encryption_enc_values_supported", UNSET)
        )

        response_modes_supported = cast(list[str], d.pop("response_modes_supported", UNSET))

        registration_endpoint = d.pop("registration_endpoint", UNSET)

        token_endpoint_auth_methods_supported = cast(list[str], d.pop("token_endpoint_auth_methods_supported", UNSET))

        token_endpoint_auth_signing_alg_values_supported = cast(
            list[str], d.pop("token_endpoint_auth_signing_alg_values_supported", UNSET)
        )

        introspection_endpoint_auth_methods_supported = cast(
            list[str], d.pop("introspection_endpoint_auth_methods_supported", UNSET)
        )

        introspection_endpoint_auth_signing_alg_values_supported = cast(
            list[str], d.pop("introspection_endpoint_auth_signing_alg_values_supported", UNSET)
        )

        authorization_signing_alg_values_supported = cast(
            list[str], d.pop("authorization_signing_alg_values_supported", UNSET)
        )

        authorization_encryption_alg_values_supported = cast(
            list[str], d.pop("authorization_encryption_alg_values_supported", UNSET)
        )

        authorization_encryption_enc_values_supported = cast(
            list[str], d.pop("authorization_encryption_enc_values_supported", UNSET)
        )

        claims_supported = cast(list[str], d.pop("claims_supported", UNSET))

        claim_types_supported = cast(list[str], d.pop("claim_types_supported", UNSET))

        claims_parameter_supported = d.pop("claims_parameter_supported", UNSET)

        scopes_supported = cast(list[str], d.pop("scopes_supported", UNSET))

        request_parameter_supported = d.pop("request_parameter_supported", UNSET)

        request_uri_parameter_supported = d.pop("request_uri_parameter_supported", UNSET)

        require_request_uri_registration = d.pop("require_request_uri_registration", UNSET)

        code_challenge_methods_supported = cast(list[str], d.pop("code_challenge_methods_supported", UNSET))

        tls_client_certificate_bound_access_tokens = d.pop("tls_client_certificate_bound_access_tokens", UNSET)

        revocation_endpoint = d.pop("revocation_endpoint", UNSET)

        revocation_endpoint_auth_methods_supported = cast(
            list[str], d.pop("revocation_endpoint_auth_methods_supported", UNSET)
        )

        revocation_endpoint_auth_signing_alg_values_supported = cast(
            list[str], d.pop("revocation_endpoint_auth_signing_alg_values_supported", UNSET)
        )

        backchannel_logout_supported = d.pop("backchannel_logout_supported", UNSET)

        backchannel_logout_session_supported = d.pop("backchannel_logout_session_supported", UNSET)

        device_authorization_endpoint = d.pop("device_authorization_endpoint", UNSET)

        backchannel_token_delivery_modes_supported = cast(
            list[str], d.pop("backchannel_token_delivery_modes_supported", UNSET)
        )

        backchannel_authentication_endpoint = d.pop("backchannel_authentication_endpoint", UNSET)

        backchannel_authentication_request_signing_alg_values_supported = cast(
            list[str], d.pop("backchannel_authentication_request_signing_alg_values_supported", UNSET)
        )

        require_pushed_authorization_requests = d.pop("require_pushed_authorization_requests", UNSET)

        pushed_authorization_request_endpoint = d.pop("pushed_authorization_request_endpoint", UNSET)

        _mtls_endpoint_aliases = d.pop("mtls_endpoint_aliases", UNSET)
        mtls_endpoint_aliases: Union[Unset, MtlsEndpointAliases]
        if isinstance(_mtls_endpoint_aliases, Unset):
            mtls_endpoint_aliases = UNSET
        else:
            mtls_endpoint_aliases = MtlsEndpointAliases.from_dict(_mtls_endpoint_aliases)

        authorization_response_iss_parameter_supported = d.pop("authorization_response_iss_parameter_supported", UNSET)

        well_known = cls(
            issuer=issuer,
            authorization_endpoint=authorization_endpoint,
            token_endpoint=token_endpoint,
            introspection_endpoint=introspection_endpoint,
            userinfo_endpoint=userinfo_endpoint,
            end_session_endpoint=end_session_endpoint,
            frontchannel_logout_session_supported=frontchannel_logout_session_supported,
            frontchannel_logout_supported=frontchannel_logout_supported,
            jwks_uri=jwks_uri,
            check_session_iframe=check_session_iframe,
            grant_types_supported=grant_types_supported,
            acr_values_supported=acr_values_supported,
            response_types_supported=response_types_supported,
            subject_types_supported=subject_types_supported,
            id_token_signing_alg_values_supported=id_token_signing_alg_values_supported,
            id_token_encryption_alg_values_supported=id_token_encryption_alg_values_supported,
            id_token_encryption_enc_values_supported=id_token_encryption_enc_values_supported,
            userinfo_signing_alg_values_supported=userinfo_signing_alg_values_supported,
            userinfo_encryption_alg_values_supported=userinfo_encryption_alg_values_supported,
            userinfo_encryption_enc_values_supported=userinfo_encryption_enc_values_supported,
            request_object_signing_alg_values_supported=request_object_signing_alg_values_supported,
            request_object_encryption_alg_values_supported=request_object_encryption_alg_values_supported,
            request_object_encryption_enc_values_supported=request_object_encryption_enc_values_supported,
            response_modes_supported=response_modes_supported,
            registration_endpoint=registration_endpoint,
            token_endpoint_auth_methods_supported=token_endpoint_auth_methods_supported,
            token_endpoint_auth_signing_alg_values_supported=token_endpoint_auth_signing_alg_values_supported,
            introspection_endpoint_auth_methods_supported=introspection_endpoint_auth_methods_supported,
            introspection_endpoint_auth_signing_alg_values_supported=introspection_endpoint_auth_signing_alg_values_supported,
            authorization_signing_alg_values_supported=authorization_signing_alg_values_supported,
            authorization_encryption_alg_values_supported=authorization_encryption_alg_values_supported,
            authorization_encryption_enc_values_supported=authorization_encryption_enc_values_supported,
            claims_supported=claims_supported,
            claim_types_supported=claim_types_supported,
            claims_parameter_supported=claims_parameter_supported,
            scopes_supported=scopes_supported,
            request_parameter_supported=request_parameter_supported,
            request_uri_parameter_supported=request_uri_parameter_supported,
            require_request_uri_registration=require_request_uri_registration,
            code_challenge_methods_supported=code_challenge_methods_supported,
            tls_client_certificate_bound_access_tokens=tls_client_certificate_bound_access_tokens,
            revocation_endpoint=revocation_endpoint,
            revocation_endpoint_auth_methods_supported=revocation_endpoint_auth_methods_supported,
            revocation_endpoint_auth_signing_alg_values_supported=revocation_endpoint_auth_signing_alg_values_supported,
            backchannel_logout_supported=backchannel_logout_supported,
            backchannel_logout_session_supported=backchannel_logout_session_supported,
            device_authorization_endpoint=device_authorization_endpoint,
            backchannel_token_delivery_modes_supported=backchannel_token_delivery_modes_supported,
            backchannel_authentication_endpoint=backchannel_authentication_endpoint,
            backchannel_authentication_request_signing_alg_values_supported=backchannel_authentication_request_signing_alg_values_supported,
            require_pushed_authorization_requests=require_pushed_authorization_requests,
            pushed_authorization_request_endpoint=pushed_authorization_request_endpoint,
            mtls_endpoint_aliases=mtls_endpoint_aliases,
            authorization_response_iss_parameter_supported=authorization_response_iss_parameter_supported,
        )

        well_known.additional_properties = d
        return well_known

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
