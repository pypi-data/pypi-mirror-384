"""
Copyright © 2025 Legendary Requirements

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import base64
import hashlib
import math
import re
from io import BufferedIOBase

HASH_BYTE_LENGTH = 32
"""
Hash is a 32-byte array.
"""

HASH_BIT_LENGTH = 8 * HASH_BYTE_LENGTH
"""
Hash is a 256-bit array.
"""

HASH_HEX_LENGTH = 2 * HASH_BYTE_LENGTH
"""
Hash is a 64-character hexadecimal string.
"""

HASH_BASE64_LENGTH = math.floor((HASH_BYTE_LENGTH * 4 / 3 + 3) / 4) * 4
"""
Hash is a 44-character base64 string.
"""

NULL_HASH = bytes(HASH_BYTE_LENGTH)
"""
The hash of null is all zeros.
"""

OUTER_BIT = 1 << HASH_BIT_LENGTH
"""
Outer bit representing 2^HASH_BIT_LENGTH.
"""

# Bits go from highest to lowest, with final bit of zero.
BITS = [1 << i for i in range(HASH_BIT_LENGTH - 1, -1, -1)] + [0]
"""
Single bits for constructing SMT.
"""

def is_valid_hash(hash: bytes) -> bool:
    """
    Determine if hash is valid.

    :param hash:
    Hash.

    :return:
    True if hash has exactly the required number of bytes.
    """

    return len(hash) == HASH_BYTE_LENGTH

def validate_hash(hash: bytes):
    """
    Validate a hash and raise ~ValueError~ if invalid.
    
    :param hash:
    Hash.
    """

    if not is_valid_hash(hash):
        raise ValueError("Invalid hash")

def bytes_to_int(bytes: bytes) -> int:
    """
    Convert bytes to integer value.

    :param bytes:
    Bytes.

    :return:
    Integer value.
    """

    return int.from_bytes(bytes, byteorder = "big")

def hash_to_int(hash: bytes) -> int:
    """
    Convert hash to integer value.

    :param hash:
    Hash.

    :return:
    Integer value.
    """

    validate_hash(hash)

    return bytes_to_int(hash)

def int_to_hash(value: int) -> bytes:
    """
    Convert integer value to hash.

    :param value:
    Integer value.

    :return:
    Hash.
    """
    return int.to_bytes(value, HASH_BYTE_LENGTH, byteorder = "big")

def hash_to_hex(hash: bytes) -> str:
    """
    Convert hash to hexadecimal string.

    :param hash:
    Hash.

    :return:
    Hexadecimal string.
    """

    validate_hash(hash)

    return hash.hex()

def int_to_hex(value: int, padded: bool) -> str:
    """
    Convert integer value to hexadecimal string.

    :param value:
    Integer value.

    :param padded:
    If true, string is padded to HASH_HEX_LENGTH characters.

    :return:
    Hexadecimal string.
    """

    s = hex(value)[2:]

    return s.rjust(HASH_HEX_LENGTH, "0") if padded else s

def _validate_hex(s: str, validate_hash_length: bool) -> None:
    """
    Validate a hexadecimal string.

    :param s:
    String.

    :param validate_hash_length:
    If true, validate that length is that of a hash hex string.
    """

    s_length = len(s)

    if s_length < (HASH_HEX_LENGTH if validate_hash_length else 1) or s_length > HASH_HEX_LENGTH or not re.match("^([0-9A-Fa-f])+$", s):
        raise ValueError("Invalid hexadecimal string")

def hex_to_hash(s: str) -> bytes:
    """
    Convert hexadecimal string to hash.

    :param s:
    Hexadecimal string.

    :return:
    Hash.
    """

    _validate_hex(s, True)

    return bytes.fromhex(s)

def hex_to_int(s: str, padded: bool) -> int:
    """
    Convert hexadecimal string to integer.

    :param s:
    Hexadecimal string.

    :param padded:
    If true, string is expected to be padded to HASH_HEX_LENGTH characters.

    :return:
    Integer value.
    """

    _validate_hex(s, padded)

    return int(s, 16)

def bytes_to_base64(bytes: bytes) -> str:
    """
    Convert bytes to base64 string.

    :param bytes:
    Bytes.

    :return:
    Base64 string.
    """

    return base64.b64encode(bytes).decode("ascii")

def hash_to_base64(hash: bytes) -> str:
    """
    Convert hash to base64 string.

    :param hash:
    Hash.

    :return:
    Base64 string.
    """

    validate_hash(hash)

    return bytes_to_base64(hash)

def int_to_base64(value: int, padded: bool) -> str:
    """
    Convert integer value to base64 string.

    :param value:
    Integer value.

    :param padded:
    If true, string is padded to HASH_BASE64_LENGTH characters.

    :return:
    Base64 string.
    """

    bytes = int_to_hash(value)

    if not padded:
        non_zero_index = 0

        while non_zero_index < HASH_BYTE_LENGTH and bytes[non_zero_index] == 0:
            non_zero_index += 1

        if non_zero_index != HASH_BYTE_LENGTH:
            bytes = bytes[non_zero_index:]
        else:
            bytes = b"\x00"

    return bytes_to_base64(bytes)

def _validate_base64(s: str, validate_hash_length: bool) -> None:
    """
    Validate a base64 string.

    :param s:
    String.

    :param validate_hash_length:
    If true, validate that length is that of a hash base64 string.
    """

    s_length = len(s)

    if s_length < (HASH_BASE64_LENGTH if validate_hash_length else 4) or s_length > HASH_BASE64_LENGTH or not re.match("^[-A-Za-z0-9+/]*={0,3}$", s):
        raise ValueError("Invalid base64 string")

def base64_to_bytes(s: str, validate_hash_length: bool) -> bytes:
    """
    Convert base64 string to hash.

    :param s:
    Base64 string.

    :param validate_hash_length:
    If true, validate that length is that of a hash base64 string.

    :return:
    Hash.
    """

    _validate_base64(s, validate_hash_length)

    return base64.b64decode(s)

def base64_to_hash(s: str) -> bytes:
    """
    Convert base64 string to hash.

    :param s:
    Base64 string.

    :return:
    Hash.
    """

    return base64_to_bytes(s, True)

def base64_to_int(s: str, padded: bool) -> int:
    """
    Convert base64 string to integer.

    :param s:
    Base64 string.

    :param padded:
    If true, string is expected to be padded to HASH_HEX_LENGTH characters.

    :return:
    Integer value.
    """

    return bytes_to_int(base64_to_bytes(s, padded))

def block_hash(*blocks: bytes) -> bytes:
    """
    Calculate a block hash for a variable number of blocks.

    :param blocks:
    Blocks.

    :return:
    SHA-256 hash of all blocks as a contiguous block.
    """

    sha256 = hashlib.sha256()

    for block in blocks:
        sha256.update(block)

    return sha256.digest()

def hashes_equal(hash1: bytes, hash2: bytes) -> bool:
    """
    Determine if two hashes are equal.

    :param hash1:
    Hash 1.

    :param hash2:
    Hash 2.

    :return:
    True if hash1 and hash2 are the correct length and have matching contents.
    """

    return is_valid_hash(hash1) & is_valid_hash(hash2) & (hash1 == hash2)


class IOBytesIterator:
    """
    I/O bytes iterator.
    """

    def __init__(self, io: BufferedIOBase):
        """
        Constructor.

        :param io:
        Buffered I/O object.
        """
        self._io = io

    def __iter__(self):
        return self

    def __next__(self) -> int:
        """
        Get the next byte.

        :return:
        Next byte.
        """

        data = self._io.read(1)

        if len(data) == 0:
            raise StopIteration

        return data[0]
