import base64
import json
import logging
from urllib.parse import unquote

logger = logging.getLogger(__name__)
import base64
from urllib.parse import unquote

def decode_str(encoded: str) -> str:
    """
    Decodes a base64 + URL-encoded string into plain text.

    Args:
        encoded (str): The encoded input string.

    Returns:
        str: Decoded plain text string.
    """
    try:
        # First base64 decode, then URL-decode the resulting string
        decoded_bytes = base64.b64decode(encoded)
        decoded_text = decoded_bytes.decode("utf-8")
        return unquote(decoded_text)
    except Exception as e:
        raise ValueError(f"❌ [DECODE_STR] Invalid encoded string: {e}")


def decode_dict(encoded: str) -> dict | None:
    """
    Decodes a base64 + URL-encoded string and parses it into a dictionary.

    Args:
        encoded (str): The encoded input string.

    Returns:
        dict | None: Parsed dictionary if valid JSON, otherwise None.
    """
    try:
        decoded = decode_str(encoded)
        return json.loads(decoded)
    except Exception:
        return None