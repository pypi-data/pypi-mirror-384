from abc import ABC
from os import getenv
from typing import Any, Dict, Optional

from .auth import AuthClient
from .const import USER_AGENT
from .exceptions import ElevateConfigurationException
from .utils import build_server_url, create_error_context, format_error_message
from .validation import validate_all_parameters


class BaseElevateClient(ABC):
    """
    Abstract base class for Elevate API clients.

    This class provides common functionality for all API clients in the SDK,
    including authentication management and configuration setup.

    :param server: The server name for the API endpoint
    :type server: str
    """

    _route: str
    _conf_class: Any

    def __init__(self, server: str, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the API client.

        :param server: The server name for the API endpoint
        :type server: str
        :param args: Additional positional arguments
        :param kwargs: Additional keyword arguments
        """
        self._auth: Optional[AuthClient] = None
        base_url = build_server_url(server, self._route)
        kwargs["configuration"] = self._conf_class(host=base_url)
        super().__init__(*args, **kwargs)
        self.user_agent = USER_AGENT

    @property
    def auth(self) -> Optional[AuthClient]:
        """
        Get the authentication client.

        :returns: The authentication client instance
        :rtype: Optional[AuthClient]
        """
        return self._auth

    # noinspection PyAttributeOutsideInit
    @auth.setter
    def auth(self, auth_client: AuthClient) -> None:
        """
        Set the authentication client.

        :param auth_client: The authentication client to use
        :type auth_client: AuthClient
        """
        self._auth = auth_client


class BaseElevateService(ABC):
    """
    Abstract base class for Elevate service classes.

    This class provides common functionality for all service classes in the SDK,
    including parameter validation, environment variable handling, and
    authentication setup.
    """

    _client_class: Any

    @staticmethod
    def _get_parameter_or_env(value: Optional[str], env_key: str) -> Optional[str]:
        """
        Get parameter value or fallback to environment variable.

        Empty strings are treated as invalid and will not fallback to environment variables.
        This ensures that explicitly provided empty strings are rejected during validation.

        :param value: The provided parameter value
        :type value: Optional[str]
        :param env_key: The environment variable key to check
        :type env_key: str
        :returns: The parameter value or environment variable value
        :rtype: Optional[str]
        """
        # Explicit empty strings should be rejected during validation, not silently replaced
        if value is not None and value != "":
            return value
        return getenv(env_key)

    @staticmethod
    def _build_configuration_error_message(
        error_str: str, param_values: Dict[str, Optional[str]]
    ) -> str:
        """
        Build a descriptive configuration error message using utilities from utils.py.

        :param error_str: The original error string
        :type error_str: str
        :param param_values: Dictionary mapping parameter names to their values
        :type param_values: Dict[str, Optional[str]]
        :returns: A descriptive error message
        :rtype: str
        """
        # Parameter configuration for error message generation
        param_configs = {
            "server": ("E2_SERVER", False),
            "client_id": ("E2_CLIENT_ID", False),
            "secret_key": ("E2_SECRET_KEY", True),
        }

        # Match error message to specific parameter for targeted error reporting
        error_param = next(
            (param for param in param_configs if param in error_str), None
        )

        if error_param:
            env_var, redact = param_configs[error_param]
            value = param_values.get(error_param)
            base_message = (
                f"Missing {env_var} environment variable or {error_param} parameter"
                if value is None
                else f"Invalid {error_param} parameter: {error_str}"
            )
            context = create_error_context(
                "parameter_validation",
                parameter=error_param,
                provided_value="<redacted>" if redact and value else value,
                env_var=env_var,
            )
        else:
            # Generic error case
            base_message = f"Configuration validation error: {error_str}"
            context = create_error_context(
                "parameter_validation",
                server=param_values.get("server"),
                client_id=param_values.get("client_id"),
                secret_key="<redacted>" if param_values.get("secret_key") else None,
            )

        # Use format_error_message from utils.py for consistent formatting
        return format_error_message(base_message, context, include_context=True)

    def __init__(
        self,
        server: Optional[str] = None,
        client_id: Optional[str] = None,
        secret_key: Optional[str] = None,
    ) -> None:
        """
        Initialize the Elevate service.

        :param server: The server name for the Elevate service API. If not provided, defaults to the `E2_SERVER` environment variable.
        :type server: str, optional
        :param client_id: The client ID for authentication. If not provided, defaults to the `E2_CLIENT_ID` environment variable.
        :type client_id: str, optional
        :param secret_key: The secret key for authentication. If not provided, defaults to the `E2_SECRET_KEY` environment variable.
        :type secret_key: str, optional
        :raises ElevateConfigurationException: If any required parameter is missing or invalid
        """
        # Get values from parameters or environment variables
        server_value = self._get_parameter_or_env(server, "E2_SERVER")
        client_id_value = self._get_parameter_or_env(client_id, "E2_CLIENT_ID")
        secret_key_value = self._get_parameter_or_env(secret_key, "E2_SECRET_KEY")

        # Centralized validation provides consistent error messages and behavior
        try:
            validated_server, validated_client_id, validated_secret_key = (
                validate_all_parameters(server_value, client_id_value, secret_key_value)
            )
        except ValueError as e:
            # Convert ValueError to more specific configuration exception
            param_values = {
                "server": server_value,
                "client_id": client_id_value,
                "secret_key": secret_key_value,
            }
            error_message = self._build_configuration_error_message(
                str(e), param_values
            )
            raise ElevateConfigurationException(error_message) from e

        self.api_client = self._client_class(validated_server)
        self.api_client.auth = AuthClient(
            self, validated_server, validated_client_id, validated_secret_key
        )
