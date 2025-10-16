"""
Validation utilities for the Earnix Elevate SDK.

This module provides centralized validation functions to ensure consistent
parameter validation across the SDK.
"""

from typing import Optional, Tuple

from .const import (
    DANGEROUS_PATTERNS,
    DNS_FQDN_MAX_LENGTH,
    DNS_LABEL_MAX_LENGTH,
    DOMAIN_SUFFIX,
)


def validate_and_strip(value: Optional[str], field_name: str) -> str:
    """
    Validates and strips a string value.

    This function handles None values, strips whitespace, and ensures the
    resulting value is not empty. It provides consistent error messages
    for validation failures. Empty strings are explicitly rejected.

    :param value: The string value to validate (can be None)
    :type value: Optional[str]
    :param field_name: The field name for error messages
    :type field_name: str
    :returns: The stripped string value
    :rtype: str
    :raises ValueError: If value is None, not a string, empty, or whitespace-only
    """
    if value is None:
        raise ValueError(f"{field_name} cannot be None")

    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string, got {type(value).__name__}")

    stripped_value = value.strip()
    if not stripped_value:
        raise ValueError(f"{field_name} cannot be empty or whitespace-only")

    return stripped_value


def _check_dangerous_patterns(server_name: str) -> Tuple[bool, str]:
    """
    Check for dangerous patterns that could lead to security issues.

    :param server_name: The server name to validate
    :type server_name: str
    :returns: Tuple of (is_valid, error_message)
    :rtype: Tuple[bool, str]
    """
    for pattern, description in DANGEROUS_PATTERNS:
        if pattern in server_name:
            return False, f"Server name contains invalid {description}: '{pattern}'"
    return True, ""


def _check_allowed_characters(server_name: str) -> Tuple[bool, str]:
    """
    Check that server name contains only allowed ASCII characters.

    :param server_name: The server name to validate
    :type server_name: str
    :returns: Tuple of (is_valid, error_message)
    :rtype: Tuple[bool, str]
    """
    for char in server_name:
        if not (
            ("a" <= char <= "z")
            or ("A" <= char <= "Z")
            or ("0" <= char <= "9")
            or char == "-"
            or char == "."
        ):
            return (
                False,
                f"Server name contains invalid character: '{char}'. Only alphanumeric characters, hyphens, and dots are allowed",
            )
    return True, ""


def _check_dns_compliance(server_name: str) -> Tuple[bool, str]:
    """
    Check DNS compliance rules for server name.

    :param server_name: The server name to validate
    :type server_name: str
    :returns: Tuple of (is_valid, error_message)
    :rtype: Tuple[bool, str]
    """
    # DNS labels cannot start or end with hyphens per RFC standards
    if server_name.startswith("-") or server_name.endswith("-"):
        return False, "Server name cannot start/end with hyphen"

    # Empty DNS labels cause resolution failures and security issues
    if server_name.startswith(".") or server_name.endswith(".") or ".." in server_name:
        return False, "Server name cannot contain empty labels"

    return True, ""


def _check_length_limits(server_name: str) -> Tuple[bool, str]:
    """
    Check length limits for server name and its labels.

    :param server_name: The server name to validate
    :type server_name: str
    :returns: Tuple of (is_valid, error_message)
    :rtype: Tuple[bool, str]
    """
    # RFC 1035 limits prevent DNS server rejection and URL construction failures
    final_fqdn_length = len(server_name) + len(DOMAIN_SUFFIX)
    if final_fqdn_length > DNS_FQDN_MAX_LENGTH:
        return (
            False,
            f"Server name too long. Final FQDN would exceed {DNS_FQDN_MAX_LENGTH} characters",
        )

    # Individual DNS labels have strict length limits per RFC 1035
    for label in server_name.split("."):
        if len(label) > DNS_LABEL_MAX_LENGTH:
            return (
                False,
                f"Server name label '{label}' too long (max {DNS_LABEL_MAX_LENGTH} characters)",
            )
        if len(label) == 0:
            return False, "Server name cannot contain empty labels (consecutive dots)"

    return True, ""


def _validate_server_name_internal(server_name: str) -> Tuple[bool, str]:
    """
    Internal validation function that returns validation result and error message.

    This function performs all server name validation checks in a logical order,
    from basic requirements to more specific DNS and security validations.

    :param server_name: The server name to validate
    :type server_name: str
    :returns: Tuple of (is_valid, error_message)
    :rtype: Tuple[bool, str]
    """
    if not server_name:
        return False, "Server name cannot be empty"

    # Run validation checks in order
    validation_checks = [
        _check_dangerous_patterns,
        _check_allowed_characters,
        _check_dns_compliance,
        _check_length_limits,
    ]

    for check in validation_checks:
        is_valid, error_message = check(server_name)
        if not is_valid:
            return False, error_message

    return True, ""


def is_valid_server_name(server_name: str) -> bool:
    """
    Validates server name for DNS compliance and security.

    This function prevents injection attacks and ensures DNS compliance
    by rejecting problematic characters and enforcing DNS rules.
    The server name will be used to construct a FQDN like
    "https://{server_name}.e2.earnix.com", so it must be DNS compliant.

    :param server_name: The server name to validate
    :type server_name: str
    :returns: True if the server name is valid, False otherwise
    :rtype: bool
    """
    is_valid, _ = _validate_server_name_internal(server_name)
    return is_valid


def validate_server_name(server_name: str) -> str:
    """
    Validates server name with DNS compliance checks.

    This function combines basic validation with DNS compliance validation
    to ensure the server name is safe and valid for URL construction.

    :param server_name: The server name to validate
    :type server_name: str
    :returns: The validated server name
    :rtype: str
    :raises ValueError: If server name is invalid or not DNS compliant
    """
    is_valid, error_message = _validate_server_name_internal(server_name)
    if not is_valid:
        raise ValueError(error_message)
    return server_name


def validate_all_parameters(
    server: Optional[str], client_id: Optional[str], secret_key: Optional[str]
) -> Tuple[str, str, str]:
    """
    Validates all three required parameters together.

    This function ensures all parameters are valid and returns them as
    stripped strings. The server parameter also undergoes DNS compliance
    validation to ensure it's safe for URL construction.

    :param server: The server parameter
    :type server: Optional[str]
    :param client_id: The client ID parameter
    :type client_id: Optional[str]
    :param secret_key: The secret key parameter
    :type secret_key: Optional[str]
    :returns: Tuple of (server, client_id, secret_key) as stripped strings
    :rtype: Tuple[str, str, str]
    :raises ValueError: If any parameter is None, empty, whitespace-only, or server is not DNS compliant
    """
    validated_server = validate_and_strip(server, "server")
    validated_server = validate_server_name(validated_server)
    validated_client_id = validate_and_strip(client_id, "client_id")
    validated_secret_key = validate_and_strip(secret_key, "secret_key")

    return validated_server, validated_client_id, validated_secret_key
