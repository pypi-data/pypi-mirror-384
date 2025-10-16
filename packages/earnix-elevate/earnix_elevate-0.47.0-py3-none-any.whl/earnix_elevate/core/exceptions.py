"""
Custom exceptions for the Earnix Elevate SDK.

This module provides specific exception types for different error categories,
improving error handling and debugging compared to generic exceptions.
"""


class ElevateConfigurationException(Exception):
    """
    Exception raised for configuration and validation errors.

    This exception is raised when there are issues with SDK configuration,
    such as missing or invalid parameters, environment variables, or
    configuration values.
    """

    pass


class ElevateAuthenticationException(Exception):
    """
    Exception raised for authentication-related errors.

    This exception is raised when there are issues with authentication,
    such as invalid credentials, expired tokens, or authentication
    server errors.
    """

    pass
