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

from json import JSONEncoder
from typing import Any, Callable

from .utility import base64_to_hash, base64_to_int, hash_to_base64, hash_to_hex, hex_to_hash, hex_to_int, int_to_base64, \
    int_to_hex


class _JSONStringEncoder(JSONEncoder):
    """
    String encoder for JSON export.
    """

    def __init__(self, hash_to: Callable[[bytes], str], padded_int_to: Callable[[int], str], unpadded_int_to: Callable[[int], str], unpadded_int_keys: list[str], *args, **kwargs):
        """
        Constructor.

        :param hash_to:
        Hash to string function.

        :param padded_int_to:
        Padded integer to string function.

        :param unpadded_int_to:
        Unpadded integer to string function.

        :param unpadded_int_keys:
        Integer keys not to be padded.

        :param args:
        Additional arguments.

        :param kwargs:
        Additional arguments.
        """
        super().__init__(*args, **kwargs)

        self._hash_to = hash_to
        self._padded_int_to = padded_int_to
        self._unpadded_int_to = unpadded_int_to
        self._unpadded_int_keys = unpadded_int_keys

    def __map(self, key: str, value: Any) -> Any:
        """
        String encoder implementation for JSON export.

        :param value:
        Value.

        :return:
        String if value is hash or integer, original value otherwise.
        """
        result: Any

        if isinstance(value, dict):
            # Map nested object.
            result = dict((k, self.__map(k, v)) for (k, v) in value.items())
        elif isinstance(value, bytes):
            result = self._hash_to(value)
        elif isinstance(value, int):
            result = self._padded_int_to(value) if key not in self._unpadded_int_keys else self._unpadded_int_to(value)
        elif isinstance(value, list):
            result = [self.__map(key, element) for element in value]
        else:
            result = value

        return result

    def iterencode(self, o: Any, _one_shot = False) -> Any:
        """
        Encode the given object.

        :param o:
        Object to encode.

        :param _one_shot:
        Additional argument.

        :return:
        Encoded object.
        """

        return super().iterencode(self.__map("", o), _one_shot)


class JSONHexEncoder(_JSONStringEncoder):
    """
    Hexadecimal encoder for JSON export.
    """

    @staticmethod
    def __int_to_padded_hex(value: int):
        """
        Convert integer value to padded hexadecimal string.

        :param value:
        Integer value.

        :return:
        Padded hexadecimal string.
        """

        return int_to_hex(value, True)

    @staticmethod
    def __int_to_unpadded_hex(value: int):
        """
        Convert integer value to unpadded hexadecimal string.

        :param value:
        Integer value.

        :return:
        Unpadded hexadecimal string.
        """

        return int_to_hex(value, False)

    def __init__(self, unpadded_int_keys: list[str], *args, **kwargs):
        """
        Constructor.

        :param unpadded_int_keys:
        Integer keys not to be padded.

        :param args:
        Additional arguments.

        :param kwargs:
        Additional arguments.
        """

        super().__init__(hash_to_hex, JSONHexEncoder.__int_to_padded_hex, JSONHexEncoder.__int_to_unpadded_hex, unpadded_int_keys, *args, **kwargs)


class JSONBase64Encoder(_JSONStringEncoder):
    """
    Base64 encoder for JSON export.
    """

    @staticmethod
    def __padded_int_to_base64(value: int):
        """
        Convert integer value to padded base64 string.

        :param value:
        Integer value.

        :return:
        Padded base64 string.
        """

        return int_to_base64(value, True)

    @staticmethod
    def __unpadded_int_to_base64(value: int):
        """
        Convert integer value to unpadded base64 string.

        :param value:
        Integer value.

        :return:
        Unpadded base64 string.
        """

        return int_to_base64(value, False)

    def __init__(self, unpadded_int_keys: list[str], *args, **kwargs):
        """
        Constructor.

        :param unpadded_int_keys:
        Integer keys not to be padded.

        :param args:
        Additional arguments.

        :param kwargs:
        Additional arguments.
        """

        super().__init__(hash_to_base64, JSONBase64Encoder.__padded_int_to_base64, JSONBase64Encoder.__unpadded_int_to_base64, unpadded_int_keys, *args, **kwargs)


class _JSONStringDecoder:
    """
    String decoder for JSON import.
    """

    def __init__(self, to_hash: Callable[[str], bytes], padded_to_int: Callable[[str], int], to_unpadded_int: Callable[[str], int], hash_keys: list[str], padded_int_keys: list[str], unpadded_int_keys: list[str]):
        """
        Constructor.

        :param to_hash:
        String to hash function.

        :param padded_to_int:
        Padded string to integer function.

        :param to_unpadded_int:
        Unpadded string to integer function.

        :param hash_keys:
        Hash keys.

        :param padded_int_keys:
        Integer keys expected to be padded.

        :param unpadded_int_keys:
        Integer keys expected not to be padded.
        """

        self._to_hash = to_hash
        self._to_padded_int = padded_to_int
        self._to_unpadded_int = to_unpadded_int
        self._hash_keys = hash_keys
        self._padded_int_keys = padded_int_keys
        self._unpadded_int_keys = unpadded_int_keys

    def __map(self, key: str, value: Any) -> Any:
        """
        String decoder implementation for JSON import.

        :param key:
        Key.

        :param value:
        Value.

        :return:
        Hash if key is present in hash keys, integer if key is present in integer keys, original value otherwise.
        """

        result: Any

        if isinstance(value, dict):
            # Nested objects will have been processed already.
            result = dict((k, self.__map(k, v)) for (k, v) in value.items()) if key == "" else value
        else:
            if key in self._hash_keys:
                to = self._to_hash
            elif key in self._padded_int_keys:
                to = self._to_padded_int
            elif key in self._unpadded_int_keys:
                to = self._to_unpadded_int
            else:
                to = None

            if to is not None:
                if isinstance(value, str):
                    result = to(value)
                elif isinstance(value, list):
                    result = []

                    for element in value:
                        if not isinstance(element, str):
                            raise ValueError(f"Value for key {key} is not a string or array of strings")

                        result.append(to(element))
                else:
                    raise ValueError(f"Value for key {key} is not a string or array of strings")
            else:
                result = value

        return result

    def decode(self, o: Any) -> Any:
        return self.__map("", o)


class JSONHexDecoder(_JSONStringDecoder):
    """
    Hexadecimal decoder for JSON import.
    """

    @staticmethod
    def __padded_hex_to_int(s: str):
        """
        Convert padded hexadecimal string to integer value.

        :param s:
        Padded hexadecimal string.

        :return:
        Integer value.
        """

        return hex_to_int(s, True)

    @staticmethod
    def __unpadded_hex_to_int(s: str):
        """
        Convert integer value to unpadded hexadecimal string.

        :param s:
        Unpadded hexadecimal string.

        :return:
        Integer value.
        """

        return hex_to_int(s, False)

    def __init__(self, hash_keys: list[str], padded_int_keys: list[str], unpadded_int_keys: list[str]):
        """
        Constructor.

        :param hash_keys:
        Hash keys.

        :param padded_int_keys:
        Integer keys expected to be padded.

        :param unpadded_int_keys:
        Integer keys expected not to be padded.
        """

        super().__init__(hex_to_hash, JSONHexDecoder.__padded_hex_to_int, JSONHexDecoder.__unpadded_hex_to_int, hash_keys, padded_int_keys, unpadded_int_keys)


class JSONBase64Decoder(_JSONStringDecoder):
    """
    Base64 decoder for JSON import.
    """

    @staticmethod
    def __padded_base64_to_int(s: str):
        """
        Convert padded base64 string to integer value.

        :param s:
        Padded base64 string.

        :return:
        Integer value.
        """

        return base64_to_int(s, True)

    @staticmethod
    def __unpadded_base64_to_int(s: str):
        """
        Convert integer value to unpadded base64 string.

        :param s:
        Unpadded base64 string.

        :return:
        Integer value.
        """

        return base64_to_int(s, False)

    def __init__(self, hash_keys: list[str], padded_int_keys: list[str], unpadded_int_keys: list[str]):
        """
        Constructor.

        :param hash_keys:
        Hash keys.

        :param padded_int_keys:
        Integer keys expected to be padded.

        :param unpadded_int_keys:
        Integer keys expected not to be padded.
        """

        super().__init__(base64_to_hash, JSONBase64Decoder.__padded_base64_to_int, JSONBase64Decoder.__unpadded_base64_to_int, hash_keys, padded_int_keys, unpadded_int_keys)
