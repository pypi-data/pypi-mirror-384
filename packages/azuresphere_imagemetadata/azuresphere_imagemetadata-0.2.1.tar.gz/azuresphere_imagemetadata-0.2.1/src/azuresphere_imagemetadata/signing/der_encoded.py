# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Takes a signature stored in the image and converts it to DER encoded format for use with pyca/cryptography.
C# code simply appends the R/S consecutively in byte format for the signature. This is not DER encoded.
"""

from ..exceptions import ImageMetadataConversionError
from cryptography.hazmat.primitives.asymmetric.utils import (
    encode_dss_signature,
    decode_dss_signature,
)

_DER_ENCODED_SIGNATURE_SIZE = 64


class DEREncodedSignature:
    @staticmethod
    def from_stored_signature(stored_signature: bytes) -> bytes:
        """
        Converts a signature appended to an Image to DER encoded format.
        The signature is generated from the data and metadata in the image.
        A stored signature is a 64 byte array, where the first 32 bytes are the R value and the last 32 bytes are the S value.
        """
        # C#/dotnet does not output a DER encoded signature, so we need to convert it.
        # der encoded signature is generally:
        # 0x30, payload length, 0x20, r length, r, 0x20, s length, s
        # for compatibility with dotnet, r length and s length must be 32 bytes long
        # if the first byte of r/s is >= 0x80, then 0 is added to the front of the r/s.
        # if the first byte of r/s is 0x00, then it is removed.
        # This is the only format supported.
        if len(stored_signature) != 64:
            raise ImageMetadataConversionError("Invalid stored signature length")

        r = stored_signature[:32]
        s = stored_signature[32:]

        r_int = int.from_bytes(r, byteorder="big", signed=False)
        s_int = int.from_bytes(s, byteorder="big", signed=False)

        return encode_dss_signature(r_int, s_int)

    @staticmethod
    def to_stored_signature(signature: bytes) -> bytes:
        """
        Extracts the R/S values from a DER encoded signature and returns them as a 64 byte array.
        The array will be appended to the Image as the signature.
        """
        r_int, s_int = decode_dss_signature(signature)

        r_bytes = int.to_bytes(r_int, length=32, byteorder="big", signed=False)
        s_bytes = int.to_bytes(s_int, length=32, byteorder="big", signed=False)

        # Ensure r and s are padded to 32 bytes if needed
        r_bytes = r_bytes.rjust(32, b"\x00")
        s_bytes = s_bytes.rjust(32, b"\x00")

        if len(r_bytes) > 32 or len(s_bytes) > 32:
            raise ImageMetadataConversionError(
                "Invalid generated DER encoded signature length"
            )

        return r_bytes + s_bytes

    @staticmethod
    def size():
        """
        Returns the size of the DER encoded signature.
        """
        return _DER_ENCODED_SIGNATURE_SIZE
