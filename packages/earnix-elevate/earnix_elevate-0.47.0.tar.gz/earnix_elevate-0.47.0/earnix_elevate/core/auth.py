from __future__ import annotations

import json
import threading
from functools import wraps
from http import HTTPStatus
from inspect import getmembers, ismethod
from typing import Any, Callable, Protocol

import jwt
import urllib3

from .const import (
    ACCEPT_JSON,
    AUTH_EXCHANGE_METHOD,
    AUTH_EXCHANGE_ROUTE,
    AUTH_HEADER_NAME,
    AUTH_HEADER_PREFIX,
    AUTH_RESPONSE_KEY,
    CONTENT_TYPE_JSON,
    JWT_DECODE_OPTIONS,
)
from .exceptions import ElevateAuthenticationException
from .utils import build_server_url, retry_on_exception


class AuthHeaderInjectable(Protocol):
    """
    Protocol for objects that can have authentication headers injected.

    This protocol defines the interface for API clients that support
    setting default headers and accessing authentication clients.
    """

    def set_default_header(self, header_name: str, header_value: str) -> None:
        """
        Set a default header for all API requests.

        :param header_name: The name of the header to set
        :type header_name: str
        :param header_value: The value of the header to set
        :type header_value: str
        """
        ...

    @property
    def auth(self) -> AuthClient:
        """
        Get the authentication client.

        :returns: The authentication client instance
        :rtype: AuthClient
        """
        ...


class AuthHeaderInjectableHolder(Protocol):
    """
    Protocol for objects that hold an API client with authentication header injection capability.

    This protocol defines the interface for service classes that contain
    an API client supporting authentication header injection.
    """

    @property
    def api_client(self) -> AuthHeaderInjectable:
        """
        Get the API client with authentication header injection capability.

        :returns: The API client instance
        :rtype: AuthHeaderInjectable
        """
        ...


class AuthClient:
    """
    Authentication client for the Earnix Elevate SDK.

    This class handles JWT token exchange, validation, and automatic renewal
    for API authentication. It automatically injects authentication headers
    into API requests and manages token lifecycle.

    Thread Safety:
    - The _http_client (urllib3.PoolManager) is thread-safe by design
    - Token refresh operations are protected by instance-level _token_refresh_lock
    - Multiple threads can safely use the same AuthClient instance
    - Each AuthClient instance has its own lock to prevent blocking between services

    :param holder: The service holder that contains the API client
    :type holder: AuthHeaderInjectableHolder
    :param server: The server name for authentication
    :type server: str
    :param client_id: The client ID for authentication
    :type client_id: str
    :param secret_key: The secret key for authentication
    :type secret_key: str
    """

    _http_client = urllib3.PoolManager()

    def __init__(
        self,
        holder: AuthHeaderInjectableHolder,
        server: str,
        client_id: str,
        secret_key: str,
    ) -> None:
        # Parameters are validated by BaseElevateService to avoid redundant validation
        self._url = build_server_url(server, AUTH_EXCHANGE_ROUTE)
        self._client_id = client_id
        self._secret_key = secret_key
        # Instance-level lock prevents race conditions during token refresh across threads
        self._token_refresh_lock = threading.Lock()

        self._set_new_token()
        AuthClient.register_auth_header_injector(holder)

    @property
    def _api_credentials_payload(self) -> dict:
        """
        Get the API credentials payload for token exchange.

        :returns: Dictionary containing client ID and secret for authentication
        :rtype: dict
        """
        return {"clientId": self._client_id, "secret": self._secret_key}

    @property
    def header(self) -> dict:
        """
        Get the authentication header for API requests.

        This property ensures the JWT token is valid and returns the
        authorization header with the Bearer token.

        :returns: Dictionary containing header name and value for authorization
        :rtype: dict
        """
        self._decode_jwt_with_regenerate()
        return {
            "header_name": AUTH_HEADER_NAME,
            "header_value": f"{AUTH_HEADER_PREFIX} {self._token}",
        }

    def _jwt_decode(self) -> None:
        """
        Decode and validate the current JWT token.

        :raises jwt.exceptions.ExpiredSignatureError: If the token has expired
        """
        jwt.decode(self._token, options=JWT_DECODE_OPTIONS)

    def _decode_jwt_with_regenerate(self) -> None:
        """
        Decode JWT token and regenerate if expired.

        This method attempts to decode the current token and automatically
        generates a new token if the current one has expired. Uses thread-safe
        token refresh to prevent race conditions.
        """
        try:
            self._jwt_decode()
        except jwt.exceptions.ExpiredSignatureError:
            # Use instance-level lock to ensure only one thread refreshes the token at a time
            with self._token_refresh_lock:
                # Double-check: another thread might have already refreshed the token
                try:
                    self._jwt_decode()
                    # Token is now valid, no refresh needed
                    return
                except jwt.exceptions.ExpiredSignatureError:
                    # Token is still expired, refresh it
                    self._set_new_token()

    @retry_on_exception(
        max_retries=3,
        exceptions=(urllib3.exceptions.HTTPError, ConnectionError, OSError),
        delay=1.0,
    )
    def _set_new_token(self) -> None:
        """
        Exchange credentials for a new JWT token.

        Makes a request to the authentication server to exchange client
        credentials for a new access token. Automatically retries on network
        failures to improve resilience.

        :raises ElevateAuthenticationException: If the credentials are invalid
        """
        headers = {"Content-Type": CONTENT_TYPE_JSON, "Accept": ACCEPT_JSON}

        resp = AuthClient._http_client.request(
            method=AUTH_EXCHANGE_METHOD,
            url=self._url,
            body=json.dumps(self._api_credentials_payload),
            headers=headers,
        )
        if resp.status != HTTPStatus.OK:
            raise ElevateAuthenticationException("Invalid credentials.")

        try:
            # Standardized response data handling
            response_text = self._extract_response_text(resp)
            response_data = json.loads(response_text)

            if AUTH_RESPONSE_KEY not in response_data:
                raise ElevateAuthenticationException(
                    f"Missing '{AUTH_RESPONSE_KEY}' in response"
                )

            self._token = response_data[AUTH_RESPONSE_KEY]
            if not self._token:
                raise ElevateAuthenticationException(
                    "Empty token received from authentication server"
                )

        except ElevateAuthenticationException:
            raise
        except (
            json.JSONDecodeError,
            UnicodeDecodeError,
            KeyError,
            AttributeError,
            TypeError,
        ) as e:
            error_msg = f"Invalid response from authentication server: {e}"
            raise ElevateAuthenticationException(error_msg) from e

    @staticmethod
    def _extract_response_text(resp: Any) -> str:
        """
        Extract text from HTTP response in a standardized way.

        :param resp: The HTTP response object
        :returns: Response text as string
        :raises ElevateAuthenticationException: If response data cannot be extracted
        """
        if not hasattr(resp, "data"):
            raise ElevateAuthenticationException(
                "Response object missing data attribute"
            )

        if resp.data is None:
            raise ElevateAuthenticationException(
                "Empty response from authentication server"
            )

        if isinstance(resp.data, bytes):
            try:
                return resp.data.decode("utf-8")
            except UnicodeDecodeError as e:
                raise ElevateAuthenticationException(
                    f"Invalid response encoding: {e}"
                ) from e
        elif isinstance(resp.data, str):
            return resp.data
        else:
            raise ElevateAuthenticationException(
                f"Unexpected response data type: {type(resp.data).__name__}. "
                f"Expected bytes or str."
            )

    @staticmethod
    def auth_header_injector(
        holder: AuthHeaderInjectableHolder, func: Callable
    ) -> Callable:
        """
        Decorator that injects authentication headers into API method calls.

        This decorator wraps API methods to automatically inject the current
        authentication header before making the API call.

        :param holder: The service holder containing the API client
        :type holder: AuthHeaderInjectableHolder
        :param func: The function to wrap with authentication injection
        :type func: Callable
        :returns: The wrapped function with authentication injection
        :rtype: Callable
        """

        @wraps(func)
        def injected_method(*args: Any, **kwargs: Any) -> Any:
            holder.api_client.set_default_header(**holder.api_client.auth.header)
            result = func(*args, **kwargs)
            return result

        return injected_method

    @classmethod
    def register_auth_header_injector(cls, holder: AuthHeaderInjectableHolder) -> None:
        """
        Register authentication header injection for all public methods of a holder.

        This method automatically wraps all public methods (those not starting with '_')
        of the provided holder with authentication header injection.

        :param holder: The service holder to register authentication injection for
        :type holder: AuthHeaderInjectableHolder
        """
        if holder is None:
            raise ValueError("Holder cannot be None")

        try:
            # Safely get members with additional error handling
            try:
                members = getmembers(holder, ismethod)
            except (TypeError, AttributeError) as e:
                raise ElevateAuthenticationException(
                    f"Cannot inspect holder object: {e}"
                ) from e

            for func_name, original_func in members:
                # Skip private methods and ensure we have a valid callable
                if (
                    not func_name.startswith("_")
                    and callable(original_func)
                    and hasattr(original_func, "__call__")
                ):
                    try:
                        decorated_func = cls.auth_header_injector(holder, original_func)
                        setattr(holder, func_name, decorated_func)
                    except (AttributeError, TypeError) as e:
                        # Log individual method failures but continue with others
                        raise ElevateAuthenticationException(
                            f"Failed to decorate method '{func_name}': {e}"
                        ) from e

        except ElevateAuthenticationException:
            # Re-raise our custom exceptions as-is
            raise
        except Exception as e:
            # Catch any other unexpected errors
            raise ElevateAuthenticationException(
                f"Unexpected error during auth header injector registration: {e}"
            ) from e
