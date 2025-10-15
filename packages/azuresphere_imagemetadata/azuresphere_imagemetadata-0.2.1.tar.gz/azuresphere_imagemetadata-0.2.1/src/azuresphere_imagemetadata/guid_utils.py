# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Provides helper functions for working with Azure Sphere GUIDs.
Azure Sphere GUIDs have historically incorrectly ordered bytes.
"""

_RAW_GUID_LENGTH = 16
_HEX_GUID_LENGTH = 32


class Guid:
    """
    Represents a GUID that produces the same output as the C# Guid class for compatibility.

    To create a Guid instance you can either provide a byte array using the Guid ctor or a hex string
    using a static method `from_hex_string`.

    Using the `from_hex_string` method to create a Guid instance will convert the hex string
    into bytes and remaps the bytes such that the hex output via `str` or `hex` is the same as the input
    hex string.

    Using the Guid constructor with a byte array will perform no remapping.

    In either case, the raw bytes `bytes` will be in a different order to the output of `hex` or `str`.
    """

    @staticmethod
    def _raw_bytes_to_dotnet_guid(guid_bytes: bytes) -> bytearray:
        """
        Creates a Guid object from a stored guid.
        """
        guid = [0] * 16

        for i in range(0, 4):
            guid[i] = guid_bytes[3 - i]

        guid[4] = guid_bytes[5]
        guid[5] = guid_bytes[4]
        guid[6] = guid_bytes[7]
        guid[7] = guid_bytes[6]

        guid[8:] = guid_bytes[8:]

        return bytearray(guid)

    def _dotnet_guid_to_raw_bytes(guid_bytes: bytes) -> bytearray:
        """
        Correctly orders a guid stored in an image package e.g. image/component uids.
        """
        # reverse the "to_guid" operation so the raw bytes are stored in the correct order
        # to produce the same output
        guid = [0] * 16

        for i in range(0, 4):
            guid[i] = guid_bytes[3 - i]

        guid[4] = guid_bytes[5]
        guid[5] = guid_bytes[4]
        guid[6] = guid_bytes[7]
        guid[7] = guid_bytes[6]
        guid[8:] = guid_bytes[8:]

        return bytearray(guid)

    @staticmethod
    def from_hex_string(guid_string: str):
        """
        Creates a Guid object from a hex string.

        Accepts a hex string formatted as a GUID e.g. "01234567-1234-5678-1234-123456789012"
        or as a hex string without dashes e.g. "01234567123456781234123456789012".
        """
        format_removed = guid_string.replace("-", "")

        if not all(c in "0123456789abcdefABCDEF" for c in format_removed):
            raise ValueError("Invalid hex string. Contains non-hexadecimal characters.")

        if len(format_removed) != _HEX_GUID_LENGTH:
            raise ValueError(
                f"Invalid hex string. Expected 16 hex characters got {len(format_removed)}."
            )

        guid_bytes = bytearray.fromhex(format_removed)

        return Guid(Guid._dotnet_guid_to_raw_bytes(guid_bytes))

    def __init__(self, guid: bytes):
        """
        Default constructor assumes that the bytes provided are not to be remapped.
        """
        if len(guid) != _RAW_GUID_LENGTH:
            raise ValueError("Invalid GUID length. Expected 16 bytes.")
        self._guid = guid

    @property
    def bytes(self):
        """
        Returns the GUID as a byte array.
        """
        return self._guid

    @property
    def hex(self):
        """
        Returns the GUID as a hex string - no dashes.
        """
        return Guid._raw_bytes_to_dotnet_guid(self._guid).hex()

    def __str__(self):
        """
        Returns the GUID as a hex string with dashes.
        """
        return format_guid_as_string(self.hex)


def format_guid_as_string(guid) -> str:
    """
    Formats a GUID as a string observing the same format as dotnet code.
    """
    return f"{guid[0:8]}-{guid[8:12]}-{guid[12:16]}-{guid[16:20]}-{guid[20:32]}"


def to_guid(guid_bytes: bytes) -> str:
    """
    Correctly orders a guid stored in an image package e.g. image/component uids.
    """
    return Guid(guid_bytes).hex
