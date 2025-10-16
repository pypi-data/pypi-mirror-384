import json as _json
import typing as _typing

import crypticorn.auth as _crypticorn_auth
import fastapi as _fastapi
import fastapi.security as _fastapi_security
import typing_extensions as _typing_extensions

from .types import BaseUrl

_AUTHENTICATE_HEADER = "WWW-Authenticate"
_AUTHENTICATE_SCOPES_HEADER = "WWW-Authenticate-Scopes"
_BEARER_AUTH_SCHEME = "Bearer"
_APIKEY_AUTH_SCHEME = "X-API-Key"
_BASIC_AUTH_SCHEME = "Basic"

# Auth Schemes
_http_bearer = _fastapi_security.HTTPBearer(
    bearerFormat="JWT",
    auto_error=False,
    description="The JWT to use for authentication.",
)

_apikey_header = _fastapi_security.APIKeyHeader(
    name=_APIKEY_AUTH_SCHEME,
    auto_error=False,
    description="The API key to use for authentication.",
)

_http_basic = _fastapi_security.HTTPBasic(
    scheme_name=_BASIC_AUTH_SCHEME,
    auto_error=False,
    description="The username and password to use for authentication.",
)


# Auth Handler
class AuthHandler:
    """
    Middleware for verifying API requests. Verifies the validity of the authentication token, scopes, etc.

    :param base_url: The base URL of the API.
    :param api_version: The version of the API.
    """

    def __init__(
        self,
        base_url: BaseUrl = BaseUrl.PROD,
    ):
        self.url = f"{base_url}/v1/auth"
        self.client = _crypticorn_auth.AuthClient(
            _crypticorn_auth.Configuration(host=self.url), is_sync=False
        )

    async def _verify_api_key(self, api_key: str) -> _crypticorn_auth.Verify200Response:
        """
        Verifies the API key.
        """
        self.client.config.access_token = None  # ensure no Authorization header
        self.client.config.api_key = {"APIKeyHeader": api_key}
        return await self.client.login.verify()  # type: ignore[misc]

    async def _verify_bearer(
        self, bearer: _fastapi_security.HTTPAuthorizationCredentials
    ) -> _crypticorn_auth.Verify200Response:
        """
        Verifies the bearer token.
        """
        self.client.config.api_key = {}  # ensure no X-API-Key header
        self.client.config.access_token = bearer.credentials
        return await self.client.login.verify()  # type: ignore[misc]

    async def _verify_basic(
        self, basic: _fastapi_security.HTTPBasicCredentials
    ) -> _crypticorn_auth.Verify200Response:
        """
        Verifies the basic authentication credentials.
        """
        return await self.client.login.verify_basic_auth(basic.username, basic.password)  # type: ignore[misc]

    async def _validate_scopes(
        self, api_scopes: list[str], user_scopes: list[str]
    ) -> None:
        """
        Checks if the required scopes are a subset of the user scopes.
        """
        if not set(api_scopes).issubset(user_scopes):
            raise _fastapi.HTTPException(
                status_code=403,
                detail="Insufficient scopes to access this resource (required: "
                + ", ".join(api_scopes)
                + ", allowed: "
                + ", ".join(user_scopes)
                + ")",
                headers={
                    _AUTHENTICATE_HEADER: f"{_BEARER_AUTH_SCHEME}, {_APIKEY_AUTH_SCHEME}"
                },
            )

    async def _extract_message(
        self, e: _crypticorn_auth.client.exceptions.ApiException
    ) -> str:
        """
        Tries to extract the message from the body of the exception.
        """
        try:
            load = _json.loads(
                _typing.cast(_typing.Union[str, bytes, bytearray], e.body)
            )
        except (_json.JSONDecodeError, TypeError):
            return _typing.cast(str, e.body)
        else:
            common_keys = ["message"]
            for key in common_keys:
                if key in load:
                    return load[key]
            return load

    async def _handle_exception(self, e: Exception) -> _fastapi.HTTPException:
        """
        Handles exceptions and returns a HTTPException with the appropriate status code and detail.
        """
        if isinstance(e, _crypticorn_auth.client.exceptions.ApiException):
            # handle the TRPC Zod errors from auth-service
            # Unfortunately, we cannot share the error messages defined in python/crypticorn/common/errors.py with the typescript client
            message = await self._extract_message(e)
            if message == "Invalid API key":
                return _fastapi.HTTPException(
                    status_code=401,
                    detail="Invalid API key",
                    headers={_AUTHENTICATE_HEADER: _APIKEY_AUTH_SCHEME},
                )
            elif message == "API key expired":
                return _fastapi.HTTPException(
                    status_code=401,
                    detail="API key expired",
                    headers={_AUTHENTICATE_HEADER: _APIKEY_AUTH_SCHEME},
                )
            elif message == "jwt expired":
                return _fastapi.HTTPException(
                    status_code=401,
                    detail="JWT token expired",
                    headers={_AUTHENTICATE_HEADER: _BEARER_AUTH_SCHEME},
                )
            elif message == "Invalid basic authentication credentials":
                return _fastapi.HTTPException(
                    status_code=401,
                    detail="Invalid basic authentication credentials",
                    headers={_AUTHENTICATE_HEADER: _BASIC_AUTH_SCHEME},
                )
            else:
                return _fastapi.HTTPException(
                    status_code=401,
                    detail="Invalid bearer token",
                    headers={_AUTHENTICATE_HEADER: _BEARER_AUTH_SCHEME},
                )

        elif isinstance(e, _fastapi.HTTPException):
            return e
        else:
            return _fastapi.HTTPException(
                status_code=500,
                detail=str(e),
            )

    async def api_key_auth(
        self,
        api_key: _typing_extensions.Annotated[
            _typing.Union[str, None], _fastapi.Depends(_apikey_header)
        ] = None,
        sec: _fastapi_security.SecurityScopes = _fastapi_security.SecurityScopes(),
    ) -> _crypticorn_auth.Verify200Response:
        """
        Verifies the API key and checks the scopes.
        Use this function if you only want to allow access via the API key.
        This function is used for HTTP connections.
        """
        try:
            return await self.full_auth(
                bearer=None, api_key=api_key, basic=None, sec=sec
            )
        except _fastapi.HTTPException as e:
            # Re-raise with appropriate headers
            headers = dict(e.headers) if e.headers else {}
            headers.update({_AUTHENTICATE_HEADER: _APIKEY_AUTH_SCHEME})
            raise _fastapi.HTTPException(
                status_code=e.status_code, detail=e.detail, headers=headers
            )

    async def bearer_auth(
        self,
        bearer: _typing_extensions.Annotated[
            _typing.Union[_fastapi_security.HTTPAuthorizationCredentials, None],
            _fastapi.Depends(_http_bearer),
        ] = None,
        sec: _fastapi_security.SecurityScopes = _fastapi_security.SecurityScopes(),
    ) -> _crypticorn_auth.Verify200Response:
        """
        Verifies the bearer token and checks the scopes.
        Use this function if you only want to allow access via the bearer token.
        This function is used for HTTP connections.
        """
        try:
            return await self.full_auth(
                bearer=bearer, api_key=None, basic=None, sec=sec
            )
        except _fastapi.HTTPException as e:
            # Re-raise with appropriate headers
            headers = dict(e.headers) if e.headers else {}
            headers.update({_AUTHENTICATE_HEADER: _BEARER_AUTH_SCHEME})
            raise _fastapi.HTTPException(
                status_code=e.status_code, detail=e.detail, headers=headers
            )

    async def basic_auth(
        self,
        credentials: _typing_extensions.Annotated[
            _typing.Union[_fastapi_security.HTTPBasicCredentials, None],
            _fastapi.Depends(_http_basic),
        ],
        sec: _fastapi_security.SecurityScopes = _fastapi_security.SecurityScopes(),
    ) -> _crypticorn_auth.Verify200Response:
        """
        Verifies the basic authentication credentials. This authentication method should just be used in cases where JWT and API key authentication are not desired or not possible.
        """
        try:
            return await self.full_auth(
                basic=credentials, bearer=None, api_key=None, sec=sec
            )
        except _fastapi.HTTPException as e:
            # Re-raise with appropriate headers
            headers = dict(e.headers) if e.headers else {}
            headers.update({_AUTHENTICATE_HEADER: _BASIC_AUTH_SCHEME})
            raise _fastapi.HTTPException(
                status_code=e.status_code, detail=e.detail, headers=headers
            )

    async def combined_auth(
        self,
        bearer: _typing_extensions.Annotated[
            _typing.Union[_fastapi_security.HTTPAuthorizationCredentials, None],
            _fastapi.Depends(_http_bearer),
        ] = None,
        api_key: _typing_extensions.Annotated[
            _typing.Union[str, None], _fastapi.Depends(_apikey_header)
        ] = None,
        sec: _fastapi_security.SecurityScopes = _fastapi_security.SecurityScopes(),
    ) -> _crypticorn_auth.Verify200Response:
        """
        Verifies the bearer token and/or API key and checks the scopes.
        Returns early on the first successful verification and raises the first error after all tokens are tried.
        Use this function if you want to allow access via either the bearer token or the API key.
        This function is used for HTTP connections.
        """
        try:
            return await self.full_auth(
                basic=None, bearer=bearer, api_key=api_key, sec=sec
            )
        except _fastapi.HTTPException as e:
            # Re-raise with appropriate headers
            headers = dict(e.headers) if e.headers else {}
            headers.update(
                {_AUTHENTICATE_HEADER: f"{_BEARER_AUTH_SCHEME}, {_APIKEY_AUTH_SCHEME}"}
            )
            raise _fastapi.HTTPException(
                status_code=e.status_code, detail=e.detail, headers=headers
            )

    async def full_auth(
        self,
        basic: _typing_extensions.Annotated[
            _typing.Union[_fastapi_security.HTTPBasicCredentials, None],
            _fastapi.Depends(_http_basic),
        ] = None,
        bearer: _typing_extensions.Annotated[
            _typing.Union[_fastapi_security.HTTPAuthorizationCredentials, None],
            _fastapi.Depends(_http_bearer),
        ] = None,
        api_key: _typing_extensions.Annotated[
            _typing.Union[str, None], _fastapi.Depends(_apikey_header)
        ] = None,
        sec: _fastapi_security.SecurityScopes = _fastapi_security.SecurityScopes(),
    ) -> _crypticorn_auth.Verify200Response:
        """
        IMPORTANT: combined_auth is sufficient for most use cases.

        This function adds basic auth to the mix, which is needed for external services like prometheus, but is not recommended for internal use.
        Verifies the bearer token, API key and basic authentication credentials and checks the scopes.
        Returns early on the first successful verification and raises the first error after all tokens are tried.
        Use this function if you want to allow access via either the bearer token, the API key or the basic authentication credentials.
        This function is used for HTTP connections.
        """
        tokens = [bearer, api_key, basic]
        first_error = None
        for token in tokens:
            try:
                if token is None:
                    continue
                res = None
                if isinstance(token, str):
                    res = await self._verify_api_key(token)
                elif isinstance(token, _fastapi_security.HTTPAuthorizationCredentials):
                    res = await self._verify_bearer(token)
                elif isinstance(token, _fastapi_security.HTTPBasicCredentials):
                    res = await self._verify_basic(token)
                if res is None:
                    continue
                if sec:
                    await self._validate_scopes(sec.scopes, res.scopes or [])
                return res

            except Exception as e:
                # Store the first error, but continue trying other tokens
                if first_error is None:
                    first_error = await self._handle_exception(e)
                continue

        # If we get here, either no credentials were provided or all failed
        if first_error:
            raise first_error
        else:
            headers = {
                _AUTHENTICATE_HEADER: f"{_BEARER_AUTH_SCHEME}, {_APIKEY_AUTH_SCHEME}, {_BASIC_AUTH_SCHEME}",
            }
            if len(sec.scopes) > 0:
                headers[_AUTHENTICATE_SCOPES_HEADER] = sec.scope_str
            raise _fastapi.HTTPException(
                status_code=401,
                detail="No credentials provided. Check the WWW-Authenticate header for the available authentication methods.",
                headers=headers,
            )

    async def ws_api_key_auth(
        self,
        api_key: _typing_extensions.Annotated[
            _typing.Union[str, None], _fastapi.Query()
        ] = None,
        sec: _fastapi_security.SecurityScopes = _fastapi_security.SecurityScopes(),
    ) -> _crypticorn_auth.Verify200Response:
        """
        Verifies the API key and checks the scopes.
        Use this function if you only want to allow access via the API key.
        This function is used for WebSocket connections.
        """
        return await self.api_key_auth(api_key=api_key, sec=sec)

    async def ws_bearer_auth(
        self,
        bearer: _typing_extensions.Annotated[
            _typing.Union[str, None], _fastapi.Query()
        ] = None,
        sec: _fastapi_security.SecurityScopes = _fastapi_security.SecurityScopes(),
    ) -> _crypticorn_auth.Verify200Response:
        """
        Verifies the bearer token and checks the scopes.
        Use this function if you only want to allow access via the bearer token.
        This function is used for WebSocket connections.
        """
        credentials = (
            _fastapi_security.HTTPAuthorizationCredentials(
                scheme="Bearer", credentials=bearer
            )
            if bearer
            else None
        )
        return await self.bearer_auth(bearer=credentials, sec=sec)

    async def ws_combined_auth(
        self,
        bearer: _typing_extensions.Annotated[
            _typing.Union[str, None], _fastapi.Query()
        ] = None,
        api_key: _typing_extensions.Annotated[
            _typing.Union[str, None], _fastapi.Query()
        ] = None,
        sec: _fastapi_security.SecurityScopes = _fastapi_security.SecurityScopes(),
    ) -> _crypticorn_auth.Verify200Response:
        """
        Verifies the bearer token and/or API key and checks the scopes.
        Use this function if you want to allow access via either the bearer token or the API key.
        This function is used for WebSocket connections.
        """
        credentials = (
            _fastapi_security.HTTPAuthorizationCredentials(
                scheme="Bearer", credentials=bearer
            )
            if bearer
            else None
        )
        return await self.combined_auth(bearer=credentials, api_key=api_key, sec=sec)
