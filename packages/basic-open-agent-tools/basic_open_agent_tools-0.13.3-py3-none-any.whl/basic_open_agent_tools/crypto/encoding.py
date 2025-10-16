"""Encoding and decoding utilities."""

import base64
import urllib.parse
from typing import Any, Callable, Union

try:
    from strands import tool as strands_tool
except ImportError:

    def strands_tool(func: Callable[..., Any]) -> Callable[..., Any]:  # type: ignore[no-redef]
        """Fallback decorator when strands is not available."""
        return func


from ..exceptions import BasicAgentToolsError


@strands_tool
def base64_encode(data: str) -> dict[str, Union[str, int]]:
    """
    Encode a string to Base64.

    Args:
        data: String to encode

    Returns:
        Dictionary with encoding results

    Raises:
        BasicAgentToolsError: If data is invalid
    """
    if not isinstance(data, str):
        raise BasicAgentToolsError("Data must be a string")

    print(f"[CRYPTO] Encoding {len(data)} chars to Base64")

    try:
        # Encode string to bytes, then to base64
        data_bytes = data.encode("utf-8")
        encoded_bytes = base64.b64encode(data_bytes)
        encoded_string = encoded_bytes.decode("ascii")

        print(
            f"[CRYPTO] Base64 encoding complete: {len(data)} chars -> {len(encoded_string)} chars"
        )

        return {
            "encoding": "base64",
            "original_data": data,
            "original_length": len(data),
            "encoded_data": encoded_string,
            "encoded_length": len(encoded_string),
        }

    except Exception as e:
        print(f"[CRYPTO] Base64 encoding failed: {e}")
        raise BasicAgentToolsError(f"Failed to encode data to Base64: {str(e)}")


@strands_tool
def base64_decode(encoded_data: str) -> dict[str, Union[str, int]]:
    """
    Decode a Base64 encoded string.

    Args:
        encoded_data: Base64 encoded string to decode

    Returns:
        Dictionary with decoding results

    Raises:
        BasicAgentToolsError: If encoded data is invalid
    """
    if not isinstance(encoded_data, str):
        raise BasicAgentToolsError("Encoded data must be a string")

    print(f"[CRYPTO] Decoding {len(encoded_data)} chars from Base64")

    if not encoded_data.strip():
        raise BasicAgentToolsError("Encoded data cannot be empty")

    try:
        # Decode from base64
        encoded_bytes = encoded_data.encode("ascii")
        decoded_bytes = base64.b64decode(encoded_bytes)
        decoded_string = decoded_bytes.decode("utf-8")

        print(
            f"[CRYPTO] Base64 decoding complete: {len(encoded_data)} chars -> {len(decoded_string)} chars"
        )

        return {
            "encoding": "base64",
            "encoded_data": encoded_data,
            "encoded_length": len(encoded_data),
            "decoded_data": decoded_string,
            "decoded_length": len(decoded_string),
        }

    except Exception as e:
        print(f"[CRYPTO] Base64 decoding failed: {e}")
        raise BasicAgentToolsError(f"Failed to decode Base64 data: {str(e)}")


@strands_tool
def url_encode(data: str) -> dict[str, Union[str, int]]:
    """
    URL encode a string (percent encoding).

    Args:
        data: String to URL encode

    Returns:
        Dictionary with encoding results

    Raises:
        BasicAgentToolsError: If data is invalid
    """
    if not isinstance(data, str):
        raise BasicAgentToolsError("Data must be a string")

    print(f"[CRYPTO] URL encoding {len(data)} chars")

    try:
        encoded_string = urllib.parse.quote(data, safe="")

        print(
            f"[CRYPTO] URL encoding complete: {len(data)} chars -> {len(encoded_string)} chars"
        )

        return {
            "encoding": "url",
            "original_data": data,
            "original_length": len(data),
            "encoded_data": encoded_string,
            "encoded_length": len(encoded_string),
        }

    except Exception as e:
        print(f"[CRYPTO] URL encoding failed: {e}")
        raise BasicAgentToolsError(f"Failed to URL encode data: {str(e)}")


@strands_tool
def url_decode(encoded_data: str) -> dict[str, Union[str, int]]:
    """
    URL decode a string (percent decoding).

    Args:
        encoded_data: URL encoded string to decode

    Returns:
        Dictionary with decoding results

    Raises:
        BasicAgentToolsError: If encoded data is invalid
    """
    if not isinstance(encoded_data, str):
        raise BasicAgentToolsError("Encoded data must be a string")

    print(f"[CRYPTO] URL decoding {len(encoded_data)} chars")

    try:
        decoded_string = urllib.parse.unquote(encoded_data)

        print(
            f"[CRYPTO] URL decoding complete: {len(encoded_data)} chars -> {len(decoded_string)} chars"
        )

        return {
            "encoding": "url",
            "encoded_data": encoded_data,
            "encoded_length": len(encoded_data),
            "decoded_data": decoded_string,
            "decoded_length": len(decoded_string),
        }

    except Exception as e:
        print(f"[CRYPTO] URL decoding failed: {e}")
        raise BasicAgentToolsError(f"Failed to URL decode data: {str(e)}")


@strands_tool
def hex_encode(data: str) -> dict[str, Union[str, int]]:
    """
    Encode a string to hexadecimal representation.

    Args:
        data: String to encode

    Returns:
        Dictionary with encoding results

    Raises:
        BasicAgentToolsError: If data is invalid
    """
    if not isinstance(data, str):
        raise BasicAgentToolsError("Data must be a string")

    print(f"[CRYPTO] Hex encoding {len(data)} chars")

    try:
        # Encode string to bytes, then to hex
        data_bytes = data.encode("utf-8")
        hex_string = data_bytes.hex()

        print(
            f"[CRYPTO] Hex encoding complete: {len(data)} chars -> {len(hex_string)} chars"
        )

        return {
            "encoding": "hex",
            "original_data": data,
            "original_length": len(data),
            "encoded_data": hex_string,
            "encoded_length": len(hex_string),
        }

    except Exception as e:
        print(f"[CRYPTO] Hex encoding failed: {e}")
        raise BasicAgentToolsError(f"Failed to encode data to hex: {str(e)}")


@strands_tool
def hex_decode(encoded_data: str) -> dict[str, Union[str, int]]:
    """
    Decode a hexadecimal encoded string.

    Args:
        encoded_data: Hex encoded string to decode

    Returns:
        Dictionary with decoding results

    Raises:
        BasicAgentToolsError: If encoded data is invalid
    """
    if not isinstance(encoded_data, str):
        raise BasicAgentToolsError("Encoded data must be a string")

    print(f"[CRYPTO] Hex decoding {len(encoded_data)} chars")

    if not encoded_data.strip():
        raise BasicAgentToolsError("Encoded data cannot be empty")

    encoded_data = encoded_data.strip()

    try:
        # Validate hex string
        if len(encoded_data) % 2 != 0:
            raise BasicAgentToolsError("Hex string must have even number of characters")

        # Decode from hex
        decoded_bytes = bytes.fromhex(encoded_data)
        decoded_string = decoded_bytes.decode("utf-8")

        print(
            f"[CRYPTO] Hex decoding complete: {len(encoded_data)} chars -> {len(decoded_string)} chars"
        )

        return {
            "encoding": "hex",
            "encoded_data": encoded_data,
            "encoded_length": len(encoded_data),
            "decoded_data": decoded_string,
            "decoded_length": len(decoded_string),
        }

    except UnicodeDecodeError:
        print("[CRYPTO] Hex decoding failed: Invalid UTF-8")
        raise BasicAgentToolsError("Decoded bytes do not represent valid UTF-8 text")
    except ValueError as e:
        print(f"[CRYPTO] Hex decoding failed: {e}")
        if "non-hexadecimal" in str(e).lower() or "invalid" in str(e).lower():
            raise BasicAgentToolsError("Invalid hexadecimal string")
        else:
            raise BasicAgentToolsError(f"Failed to decode hex data: {str(e)}")
    except Exception as e:
        print(f"[CRYPTO] Hex decoding failed: {e}")
        raise BasicAgentToolsError(f"Failed to decode hex data: {str(e)}")
