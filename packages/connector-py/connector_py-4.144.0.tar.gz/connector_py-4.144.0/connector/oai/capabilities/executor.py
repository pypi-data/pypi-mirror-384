import json
import re
from collections.abc import Callable, Mapping
from functools import cached_property
from inspect import isawaitable
from typing import Any, ClassVar, Generic, Literal, TypeVar, cast

from connector_sdk_types.generated import (
    AuthCredential,
    BasicCredential,
    CredentialConfig,
    ErrorResponse,
    JWTCredential,
    OAuth1Credential,
    OAuthClientCredential,
    OAuthCredential,
    ServiceAccountCredential,
    StandardCapabilityName,
    TokenCredential,
)
from connector_sdk_types.oai.capability import Request
from connector_sdk_types.oai.modules.oauth_module_types import (
    AuthSetting,
    EmptySettings,
    OAuthConfig,
)
from pydantic import BaseModel, ValidationError

from connector.oai.capability import (
    CapabilityCallableProto,
    Response,
    capability_requires_authentication,
)
from connector.observability.instrument import Instrument
from connector.utils.validation_utils import get_missing_field_titles

from .errors import (
    CapabilityExecutionError,
    CapabilityRequestAuthenticationError,
    CapabilityRequestSettingsError,
    CapabilityRequestValidationError,
    CapabilityResponseError,
)

REQUEST = TypeVar("REQUEST", bound=Request)
SETTINGS = TypeVar("SETTINGS", bound=BaseModel)


CredentialAttrName = Literal[
    "oauth", "oauth_client_credentials", "oauth1", "basic", "token", "jwt", "service_account"
]
"""A literal of the attribute names for supported auth credential types."""


AuthSettingCredentialMap = Mapping[AuthSetting | None, CredentialAttrName]
"""A mapping from supported credential types to the name of the attribute storing that credential.

Note that `None` should not map to a value, but is added to the type to allow for simplified `get()` operations.
"""


def pascalcase_to_snakecase(value: str) -> str:
    """
    Convert a PascalCase or camelCase string to snake_case.
    """
    # Insert underscore before capital letters and lowercase the string
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", value)
    snake = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
    return snake


class CapabilityExecutor(Generic[REQUEST, SETTINGS]):
    """Executes an integration capability."""

    CREDENTIAL_TYPE_TO_ATTR_NAME: ClassVar[AuthSettingCredentialMap] = {
        OAuthCredential: "oauth",
        OAuthClientCredential: "oauth_client_credentials",
        OAuth1Credential: "oauth1",
        BasicCredential: "basic",
        TokenCredential: "token",
        JWTCredential: "jwt",
        ServiceAccountCredential: "service_account",
    }
    """An exhaustive mapping from supported credential types to the name
    of the attribute storing that credential.
    """

    def __init__(
        self,
        *,
        app_id: str,
        capability_name: str,
        capability: CapabilityCallableProto[REQUEST],
        credentials_by_id: dict[str, CredentialConfig | OAuthConfig],
        settings_model: type[SETTINGS],
        auth_setting: AuthSetting | None,
        exception_handle: Callable[[Exception], ErrorResponse],
        request_validate_json: Callable[[Any], REQUEST],
        instrument: Instrument,
    ) -> None:
        self._app_id = app_id
        self._name = capability_name
        self._capability = capability
        self._credentials_by_id = credentials_by_id
        self._settings_model = settings_model
        self._auth_setting = auth_setting
        self._exception_handle = exception_handle
        self._request_validate_json = request_validate_json
        self._instrument = instrument

    @cached_property
    def _requires_authentication(self) -> bool:
        """Determines if this capability requires authentication."""

        # WARN: AUTHENTICATION IS NOT ENABLED FOR THE APP INFO CAPABILITY!
        # Since this is not migrated yet, we just flat out skip is_app_info_call
        # In the future we can re-instate the is_required() checks inside this
        # validation and make this work for is_app_info_call automatically (its
        # not required for is_app_info_call)
        if self._name == StandardCapabilityName.APP_INFO:
            return False

        return capability_requires_authentication(self._capability)

    @cached_property
    def _requires_settings_validation(self) -> bool:
        """Determines if this capability requires settings validation."""

        # WARN: SETTINGS VALIDATION IS NOT ENABLED FOR THE APP INFO CAPABILITY!
        # Since this is not migrated yet, we just flat out skip is_app_info_call
        # In the future we can re-instate the is_required() checks inside this
        # validation and make this work for is_app_info_call automatically (its
        # not required for is_app_info_call)
        if self._name == StandardCapabilityName.APP_INFO:
            return False

        return self._settings_model != EmptySettings

    # TODO: Capture observability stats on errors.
    async def execute(self, serialized_request: str) -> str:
        """
        Executes the capability for the provided request.

        Raises:
            CapabilityError: If the capability could not be executed sucessfully.
        """
        with self._instrument.parse_request.timer():
            request = self._parse_request(serialized_request)

        with self._instrument.validate_settings.timer():
            if self._requires_settings_validation:
                self._validate_settings(request.settings)

        try:
            with self._instrument.execute.timer():
                response = await self._execute(request)
        except Exception as exc:
            self._instrument.execution.failure.exception.node(
                pascalcase_to_snakecase(exc.__class__.__name__)
            ).incr()
            handled_exception_response = self._exception_handle(exc)
            raise CapabilityExecutionError(error_response=handled_exception_response) from exc

        if not isinstance(response, BaseModel):
            self._instrument.execution.failure.response.invalid_type.incr()
            raise CapabilityResponseError(self._app_id)

        self._instrument.execution.success.incr()
        with self._instrument.response.serialization.timer():
            return response.model_dump_json()

    async def _execute(self, request: REQUEST) -> Response:
        """A light-weight wrapper for capability execution."""
        result = self._capability(request)
        if isawaitable(result):
            return await result

        return cast(Response, result)

    def _validate_settings(self, request_settings: Any) -> None:
        """Validates the request settings based on the integrations requirements."""

        if request_settings is None:
            self._instrument.settings.failure.missing.incr()
            raise CapabilityRequestSettingsError(
                self._app_id,
                message=(
                    f"No settings passed on request: {self._app_id} "
                    f"requires {self._settings_model.__name__}"
                ),
            )

        try:
            self._settings_model.model_validate(request_settings)
        except ValidationError as exc:
            self._instrument.settings.failure.invalid.incr()
            message = "Invalid settings passed on request."

            # Check if the validation error is due to missing required fields
            missing_titles, _ = get_missing_field_titles(exc, self._settings_model)
            if missing_titles:
                missing = ", ".join(missing_titles)
                message = f"{message} Missing required settings: {missing}"

            raise CapabilityRequestSettingsError(self._app_id, message=message) from exc

        self._instrument.settings.success.incr()

    def _parse_request(self, serialized_request: str) -> REQUEST:
        """Parses a json-compatible string into an instance of this capabilities
        request type.

        Raises:
            CapabilityRequestDecodeError: If the capability request cannot be decoded.
        """
        try:
            request = self._request_validate_json(serialized_request)
        except ValidationError as exc:
            self._instrument.request.failure.invalid.incr()
            raise CapabilityRequestValidationError(
                self._app_id,
                message=f"Invalid request - {repr(exc.errors())}",
            ) from exc

        if self._requires_authentication:
            self._authenticate_request(serialized_request)

        self._instrument.request.success.incr()
        return request

    def _authenticate_request(self, serialized_request: str) -> None:
        """Authenticates a capability request.

        Raises:
            CapabilityRequestDecodeError: If the capability request cannot be decoded.
            CapabilityAuthenticationError: If the request could not be authenticated.
        """

        # PERF: (Austin Ward | 10-01-25)
        # Since the `Request` type expects each capability request to have
        # an `auth` and `credentials` field, it's unlikely we need to perform
        # this duplicate deserialization (first on the model, then into
        # json-compatible python). However, for backwards compatibility, we'll
        # continue performing authentication against the json object.
        # The only way this would not be backwards compatible is if the
        # serialized request contains credentials and auth data, but the fields
        # do not exist in the model. However, if that was the case, then the
        # request would not require authentication, based on the logic in
        # `capability_requires_authentication`.
        try:
            deserialized_request = json.loads(serialized_request)
        except json.JSONDecodeError as exc:
            self._instrument.authenticate.failure.unloadable.incr()
            raise CapabilityRequestValidationError(self._app_id) from exc

        if not isinstance(deserialized_request, dict):
            self._instrument.authenticate.failure.non_object.incr()
            raise CapabilityRequestValidationError(self._app_id)

        request_credentials = deserialized_request.get("credentials")
        request_auth = deserialized_request.get("auth")

        # If the request includes both credentials and auth fields, it's
        # considered invalid.
        if request_credentials is not None and request_auth is not None:
            self._instrument.authenticate.failure.both_creds_and_auth.incr()
            raise CapabilityRequestAuthenticationError(
                self._app_id,
                message=(
                    "Cannot pass credentials and auth in the same request, "
                    "if you've meant to make this connector multi-auth "
                    "compatible, please remove the auth field."
                ),
            )

        if request_credentials is not None:
            self._validate_request_credentials(request_credentials)
            return

        if request_auth is not None:
            self._validate_request_auth(request_auth)
            return

        # If the request includes neither credentials or auth fields, it's
        # considered invalid.
        raise CapabilityRequestAuthenticationError(self._app_id)

    def _validate_request_credentials(self, request_credentials: Any) -> Any:
        """Authenticates the request credentials."""

        if len(request_credentials) == 0:
            self._instrument.credentials.failure.missing.incr()
            raise CapabilityRequestAuthenticationError(
                self._app_id, message="Missing credentials in request"
            )

        for index, serialized_credential in enumerate(request_credentials):
            self._validate_request_credential(index, serialized_credential)

        self._instrument.credentials.success.incr()

    def _validate_request_credential(
        self,
        credential_index: int,
        serialized_credential: Any,
    ) -> None:
        """Parses a serialized credential into an auth credential, validating
        against the expected credential identifiers.

        Raises:
            CapabilityAuthenticationError: If the credential is invalid.
        """
        try:
            credential = AuthCredential.model_validate(serialized_credential)
        except ValidationError as exc:
            self._instrument.credentials.failure.malformed.incr()
            raise CapabilityRequestAuthenticationError(
                self._app_id,
                message="Malformed credentials in request",
            ) from exc

        if not credential.id:
            self._instrument.credentials.failure.missing_id.incr()
            raise CapabilityRequestAuthenticationError(
                self._app_id,
                message=f"Missing ID in credential at index {credential_index}",
            )

        # All request credentials must exist on the connector.
        connector_credential = self._credentials_by_id.get(credential.id)
        if connector_credential is None:
            self._instrument.credentials.failure.invalid_id.incr()
            raise CapabilityRequestAuthenticationError(
                self._app_id,
                message=f"Credential with id '{credential.id}' not expected",
            )

        # If the connector requires the credential, but the credential is not
        # supplied, the request is invalid. In this scenario, the connector
        # credential type is an attribute on the credential which is required.
        # Optional credentials may provide extra capability functionality, so
        # we don't validate them if partial data can be retrieved.
        if (
            not connector_credential.optional
            and getattr(credential, connector_credential.type) is None
        ):
            self._instrument.credentials.failure.node(f"missing_{connector_credential.type}").incr()
            raise CapabilityRequestAuthenticationError(
                self._app_id,
                message=f"Missing '{connector_credential.type}' credential in request",
            )

    def _validate_request_auth(self, request_auth: Any) -> None:
        """Authenticates the request auth."""
        # PERF: As I understand it, this credential validation should
        # occur on the request model itself. If this is true, then this
        # extra validation is unecessary. We can add instrumentation to
        # validate this.
        try:
            auth_credential = AuthCredential.model_validate(request_auth)
        except ValidationError as exc:
            self._instrument.auth.failure.malformed.incr()
            raise CapabilityRequestAuthenticationError(
                self._app_id,
                message="Malformed credentials in request",
            ) from exc

        credential_attr_name = self.CREDENTIAL_TYPE_TO_ATTR_NAME.get(
            self._auth_setting,
        )
        if credential_attr_name and not getattr(auth_credential, credential_attr_name):
            self._instrument.auth.failure.missing.incr()
            raise CapabilityRequestAuthenticationError(
                self._app_id,
                message=f"Missing '{credential_attr_name}' auth in request",
            )

        self._instrument.auth.success.incr()
