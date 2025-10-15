import json
import typing as t

import httpx
from connector.oai.errors import HTTPHandler
from connector.oai.integration import DescriptionData, Integration
from connector_sdk_types.generated import (
    BasicCredential,
    Error,
    ErrorCode,
    ErrorResponse,
    ListAccountsRequest,
    ListAccountsResponse,
    StandardCapabilityName,
)

Case = tuple[
    Integration,
    StandardCapabilityName,
    str,
    dict[str, t.Any],
]


def case_http_status_error() -> Case:
    """Test if HTTPStatusError can be handled with HTTPHandler.

    We register capability that is mocked to raise ``HTTPStatusError``.
    Since the integration has ``HTTPHandler`` registered for handling
    such error, we should end up with ``ErrorResponse`` that contains
    the details about HTTP error.
    """
    app_id = "test"
    integration = Integration(
        app_id=app_id,
        version="0.1.0",
        auth=BasicCredential,
        exception_handlers=[
            (httpx.HTTPStatusError, HTTPHandler, None),
        ],
        description_data=DescriptionData(user_friendly_name="hi, testing", categories=[]),
    )
    # will be mocked with actual response just to avoid making request
    requested_url = "https://httpstat.us/401"
    response_status_code = httpx.codes.UNAUTHORIZED

    capability_name = StandardCapabilityName.LIST_ACCOUNTS

    @integration.register_capability(capability_name)
    async def list_accounts(args: ListAccountsRequest) -> ListAccountsResponse:
        def request_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                text="401 Unauthorized",
                status_code=response_status_code,
            )

        with httpx.Client(transport=httpx.MockTransport(request_handler)) as client:
            _response_text = client.get(requested_url).raise_for_status().text

        # this should never happen
        return ListAccountsResponse(
            response=[],
            raw_data=None,
        )

    request_data = json.dumps(
        {
            "auth": {"basic": {"username": "user", "password": "pass"}},
            "request": {},
        }
    )
    expected_response = ErrorResponse(
        is_error=True,
        error=Error(
            message="[401][https://httpstat.us/401] 401 Unauthorized",
            error_code=ErrorCode.UNAUTHORIZED,
            app_id=app_id,
            status_code=response_status_code,
            raised_by="HTTPStatusError",
            raised_in=f"{__name__}:{capability_name.value}",
        ),
    )
    return (
        integration,
        StandardCapabilityName.LIST_ACCOUNTS,
        request_data,
        expected_response.model_dump(),
    )


def case_http_status_error_400() -> Case:
    """Test if HTTPStatusError with 400 status can be handled with HTTPHandler."""
    app_id = "test"
    integration = Integration(
        app_id=app_id,
        version="0.1.0",
        auth=BasicCredential,
        exception_handlers=[
            (httpx.HTTPStatusError, HTTPHandler, None),
        ],
        description_data=DescriptionData(user_friendly_name="hi, testing", categories=[]),
    )
    requested_url = "https://httpstat.us/400"
    response_status_code = httpx.codes.BAD_REQUEST

    capability_name = StandardCapabilityName.LIST_ACCOUNTS

    @integration.register_capability(capability_name)
    async def list_accounts(args: ListAccountsRequest) -> ListAccountsResponse:
        def request_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                text="400 Bad Request",
                status_code=response_status_code,
            )

        with httpx.Client(transport=httpx.MockTransport(request_handler)) as client:
            _response_text = client.get(requested_url).raise_for_status().text

        return ListAccountsResponse(
            response=[],
            raw_data=None,
        )

    request_data = json.dumps(
        {
            "auth": {"basic": {"username": "user", "password": "pass"}},
            "request": {},
        }
    )
    expected_response = ErrorResponse(
        is_error=True,
        error=Error(
            message="[400][https://httpstat.us/400] 400 Bad Request",
            error_code=ErrorCode.BAD_REQUEST,
            app_id=app_id,
            status_code=response_status_code,
            raised_by="HTTPStatusError",
            raised_in=f"{__name__}:{capability_name.value}",
        ),
    )
    return (
        integration,
        StandardCapabilityName.LIST_ACCOUNTS,
        request_data,
        expected_response.model_dump(),
    )


def case_http_status_error_403() -> Case:
    """Test if HTTPStatusError with 403 status can be handled with HTTPHandler."""
    app_id = "test"
    integration = Integration(
        app_id=app_id,
        version="0.1.0",
        auth=BasicCredential,
        exception_handlers=[
            (httpx.HTTPStatusError, HTTPHandler, None),
        ],
        description_data=DescriptionData(user_friendly_name="hi, testing", categories=[]),
    )
    requested_url = "https://httpstat.us/403"
    response_status_code = httpx.codes.FORBIDDEN

    capability_name = StandardCapabilityName.LIST_ACCOUNTS

    @integration.register_capability(capability_name)
    async def list_accounts(args: ListAccountsRequest) -> ListAccountsResponse:
        def request_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                text="403 Forbidden",
                status_code=response_status_code,
            )

        with httpx.Client(transport=httpx.MockTransport(request_handler)) as client:
            _response_text = client.get(requested_url).raise_for_status().text

        return ListAccountsResponse(
            response=[],
            raw_data=None,
        )

    request_data = json.dumps(
        {
            "auth": {"basic": {"username": "user", "password": "pass"}},
            "request": {},
        }
    )
    expected_response = ErrorResponse(
        is_error=True,
        error=Error(
            message="[403][https://httpstat.us/403] 403 Forbidden",
            error_code=ErrorCode.PERMISSION_DENIED,
            app_id=app_id,
            status_code=response_status_code,
            raised_by="HTTPStatusError",
            raised_in=f"{__name__}:{capability_name.value}",
        ),
    )
    return (
        integration,
        StandardCapabilityName.LIST_ACCOUNTS,
        request_data,
        expected_response.model_dump(),
    )


def case_http_status_error_404() -> Case:
    """Test if HTTPStatusError with 404 status can be handled with HTTPHandler."""
    app_id = "test"
    integration = Integration(
        app_id=app_id,
        version="0.1.0",
        auth=BasicCredential,
        exception_handlers=[
            (httpx.HTTPStatusError, HTTPHandler, None),
        ],
        description_data=DescriptionData(user_friendly_name="hi, testing", categories=[]),
    )
    requested_url = "https://httpstat.us/404"
    response_status_code = httpx.codes.NOT_FOUND

    capability_name = StandardCapabilityName.LIST_ACCOUNTS

    @integration.register_capability(capability_name)
    async def list_accounts(args: ListAccountsRequest) -> ListAccountsResponse:
        def request_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                text="404 Not Found",
                status_code=response_status_code,
            )

        with httpx.Client(transport=httpx.MockTransport(request_handler)) as client:
            _response_text = client.get(requested_url).raise_for_status().text

        return ListAccountsResponse(
            response=[],
            raw_data=None,
        )

    request_data = json.dumps(
        {
            "auth": {"basic": {"username": "user", "password": "pass"}},
            "request": {},
        }
    )
    expected_response = ErrorResponse(
        is_error=True,
        error=Error(
            message="[404][https://httpstat.us/404] 404 Not Found",
            error_code=ErrorCode.NOT_FOUND,
            app_id=app_id,
            status_code=response_status_code,
            raised_by="HTTPStatusError",
            raised_in=f"{__name__}:{capability_name.value}",
        ),
    )
    return (
        integration,
        StandardCapabilityName.LIST_ACCOUNTS,
        request_data,
        expected_response.model_dump(),
    )


def case_http_status_error_429() -> Case:
    """Test if HTTPStatusError with 429 status can be handled with HTTPHandler."""
    app_id = "test"
    integration = Integration(
        app_id=app_id,
        version="0.1.0",
        auth=BasicCredential,
        exception_handlers=[
            (httpx.HTTPStatusError, HTTPHandler, None),
        ],
        description_data=DescriptionData(user_friendly_name="hi, testing", categories=[]),
    )
    requested_url = "https://httpstat.us/429"
    response_status_code = httpx.codes.TOO_MANY_REQUESTS

    capability_name = StandardCapabilityName.LIST_ACCOUNTS

    @integration.register_capability(capability_name)
    async def list_accounts(args: ListAccountsRequest) -> ListAccountsResponse:
        def request_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                text="429 Too Many Requests",
                status_code=response_status_code,
            )

        with httpx.Client(transport=httpx.MockTransport(request_handler)) as client:
            _response_text = client.get(requested_url).raise_for_status().text

        return ListAccountsResponse(
            response=[],
            raw_data=None,
        )

    request_data = json.dumps(
        {
            "auth": {"basic": {"username": "user", "password": "pass"}},
            "request": {},
        }
    )
    expected_response = ErrorResponse(
        is_error=True,
        error=Error(
            message="[429][https://httpstat.us/429] 429 Too Many Requests",
            error_code=ErrorCode.RATE_LIMIT,
            app_id=app_id,
            status_code=response_status_code,
            raised_by="HTTPStatusError",
            raised_in=f"{__name__}:{capability_name.value}",
        ),
    )
    return (
        integration,
        StandardCapabilityName.LIST_ACCOUNTS,
        request_data,
        expected_response.model_dump(),
    )


def case_http_status_error_502() -> Case:
    """Test if HTTPStatusError with 502 status can be handled with HTTPHandler."""
    app_id = "test"
    integration = Integration(
        app_id=app_id,
        version="0.1.0",
        auth=BasicCredential,
        exception_handlers=[
            (httpx.HTTPStatusError, HTTPHandler, None),
        ],
        description_data=DescriptionData(user_friendly_name="hi, testing", categories=[]),
    )
    requested_url = "https://httpstat.us/502"
    response_status_code = httpx.codes.BAD_GATEWAY

    capability_name = StandardCapabilityName.LIST_ACCOUNTS

    @integration.register_capability(capability_name)
    async def list_accounts(args: ListAccountsRequest) -> ListAccountsResponse:
        def request_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                text="502 Bad Gateway",
                status_code=response_status_code,
            )

        with httpx.Client(transport=httpx.MockTransport(request_handler)) as client:
            _response_text = client.get(requested_url).raise_for_status().text

        return ListAccountsResponse(
            response=[],
            raw_data=None,
        )

    request_data = json.dumps(
        {
            "auth": {"basic": {"username": "user", "password": "pass"}},
            "request": {},
        }
    )
    expected_response = ErrorResponse(
        is_error=True,
        error=Error(
            message="[502][https://httpstat.us/502] 502 Bad Gateway",
            error_code=ErrorCode.BAD_GATEWAY,
            app_id=app_id,
            status_code=response_status_code,
            raised_by="HTTPStatusError",
            raised_in=f"{__name__}:{capability_name.value}",
        ),
    )
    return (
        integration,
        StandardCapabilityName.LIST_ACCOUNTS,
        request_data,
        expected_response.model_dump(),
    )


def case_http_status_error_500() -> Case:
    """Test if HTTPStatusError with 500 status can be handled with HTTPHandler (fallback to API_ERROR)."""
    app_id = "test"
    integration = Integration(
        app_id=app_id,
        version="0.1.0",
        auth=BasicCredential,
        exception_handlers=[
            (httpx.HTTPStatusError, HTTPHandler, None),
        ],
        description_data=DescriptionData(user_friendly_name="hi, testing", categories=[]),
    )
    requested_url = "https://httpstat.us/500"
    response_status_code = httpx.codes.INTERNAL_SERVER_ERROR

    capability_name = StandardCapabilityName.LIST_ACCOUNTS

    @integration.register_capability(capability_name)
    async def list_accounts(args: ListAccountsRequest) -> ListAccountsResponse:
        def request_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                text="500 Internal Server Error",
                status_code=response_status_code,
            )

        with httpx.Client(transport=httpx.MockTransport(request_handler)) as client:
            _response_text = client.get(requested_url).raise_for_status().text

        return ListAccountsResponse(
            response=[],
            raw_data=None,
        )

    request_data = json.dumps(
        {
            "auth": {"basic": {"username": "user", "password": "pass"}},
            "request": {},
        }
    )
    expected_response = ErrorResponse(
        is_error=True,
        error=Error(
            message="[500][https://httpstat.us/500] 500 Internal Server Error",
            error_code=ErrorCode.API_ERROR,
            app_id=app_id,
            status_code=response_status_code,
            raised_by="HTTPStatusError",
            raised_in=f"{__name__}:{capability_name.value}",
        ),
    )
    return (
        integration,
        StandardCapabilityName.LIST_ACCOUNTS,
        request_data,
        expected_response.model_dump(),
    )
