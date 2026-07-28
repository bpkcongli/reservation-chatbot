"""Small dependency-free ULID generator for conversation and message IDs."""

import secrets
from datetime import datetime

CROCKFORD_BASE32 = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
ULID_LENGTH = 26


def generate_ulid(now: datetime) -> str:
    """Generate a valid 26-character ULID from a clock value and secure randomness."""

    timestamp_ms = int(now.timestamp() * 1000)
    if not 0 <= timestamp_ms < 2**48:
        raise ValueError("ULID timestamp is outside the supported 48-bit range.")
    payload = timestamp_ms.to_bytes(6, byteorder="big") + secrets.token_bytes(10)
    value = int.from_bytes(payload, byteorder="big")
    encoded = ["0"] * ULID_LENGTH
    for index in range(ULID_LENGTH - 1, -1, -1):
        encoded[index] = CROCKFORD_BASE32[value & 31]
        value >>= 5
    return "".join(encoded)
