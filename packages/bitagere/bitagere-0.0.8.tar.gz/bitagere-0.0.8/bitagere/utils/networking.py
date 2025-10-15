import netaddr


class IPConversionError(ValueError):
    """Custom exception for IP conversion issues."""

    pass


class InvalidIPAddressFormat(ValueError):
    """Custom exception for invalid IP address format."""

    pass


def int_to_ip(int_val: int) -> str:
    """
    Maps an integer to a unique IP string (IPv4 or IPv6).

    Args:
        int_val: The integer representation of an IP.

    Returns:
        The string representation of the IP.

    Raises:
        IPConversionError: If the integer value is not a valid IP representation.
    """
    try:
        return str(netaddr.IPAddress(int_val))
    except netaddr.core.AddrFormatError as e:
        raise IPConversionError(
            f"Failed to convert integer {int_val} to IP: {e}"
        ) from e
    except Exception as e:  # Catch any other netaddr related error during conversion
        raise IPConversionError(
            f"An unexpected error occurred converting integer {int_val} to IP: {e}"
        ) from e


def ip_to_int(str_val: str) -> int:
    """
    Maps an IP string (IPv4 or IPv6) to its unique integer representation.

    Args:
        str_val: The string representation of an IP.

    Returns:
        The integer representation of the IP.

    Raises:
        IPConversionError: If the string value is not a valid IP.
    """
    try:
        return int(netaddr.IPAddress(str_val))
    except netaddr.core.AddrFormatError as e:
        raise IPConversionError(
            f"Failed to convert IP string '{str_val}' to integer: {e}"
        ) from e
    except Exception as e:  # Catch any other netaddr related error during conversion
        raise IPConversionError(
            f"An unexpected error occurred converting IP string '{str_val}' to integer: {e}"
        ) from e


def get_ip_version(str_val: str) -> int:
    """
    Returns the IP version (4 or 6) for a given IP string.

    Args:
        str_val: The string representation of an IP.

    Returns:
        The IP version (4 for IPv4, 6 for IPv6).

    Raises:
        IPConversionError: If the string value is not a valid IP.
    """
    try:
        return int(netaddr.IPAddress(str_val).version)
    except netaddr.core.AddrFormatError as e:
        raise IPConversionError(
            f"Failed to determine IP version for '{str_val}': {e}"
        ) from e
    except Exception as e:  # Catch any other netaddr related error
        raise IPConversionError(
            f"An unexpected error occurred determining IP version for '{str_val}': {e}"
        ) from e
