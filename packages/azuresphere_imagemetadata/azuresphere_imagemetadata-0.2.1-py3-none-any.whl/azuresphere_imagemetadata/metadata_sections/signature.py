# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
The signature section contains the certificate hash and signing type used to sign the image.
"""

from .metadata_id import MetadataSectionId
from .metadata import MetadataSection
import struct


class SigningType:
    """
    Signing type enum.
    """

    Invalid = 0
    ECDsa256 = 1
    ECDsa384 = 2

    def __init__(self, data: bytes):
        if data is not None:
            self.deserialize(data)
        else:
            self.signing_type = 0

    def deserialize(self, data: bytes):
        """
        Deserializes the signing type from the given data.
        """
        self.signing_type = struct.unpack_from("<I", data, 0)[0]

    def serialize(self):
        """
        Serializes the signing type to bytes.
        """
        return struct.pack("<I", self.signing_type)

    def get_name(self):
        """
        Get the name of the signing type.
        """
        if self.signing_type == SigningType.Invalid:
            return "Invalid"
        elif self.signing_type == SigningType.ECDsa256:
            return "ECDsa256"
        elif self.signing_type == SigningType.ECDsa384:
            return "ECDsa384"
        else:
            raise ValueError("Unknown signing type")


class SignatureSection(MetadataSection):
    """
    The signature section contains the certificate hash and signing type used to sign the image.
    # byte[20] SigningCertThumbprint
    # uint32 signing type
    """

    def __init__(self, data=None):
        super().__init__("Signature", MetadataSectionId.Signature, data)
        if data is not None:
            self.deserialize(data)
        else:
            self.signing_cert_thumbprint = b""
            self.signing_type = SigningType(None)

    @staticmethod
    def size():
        """
        Returns the size of the signature section in bytes.
        """
        return 24

    def deserialize(self, data):
        """
        Deserializes the signature section from the given data.
        """
        self.signing_cert_thumbprint = struct.unpack_from("<20s", data, 0)[0]
        self.signing_type = SigningType(data[20:])

    def serialize(self):
        return (
            struct.pack("<20s", self.signing_cert_thumbprint)
            + self.signing_type.serialize()
        )

    def __str__(self):
        cert = self.signing_cert_thumbprint
        out_lines = []
        out_lines.append(f"Signing Type:      {self.signing_type.get_name()}")
        out_lines.append(f"Cert:              {cert.hex()}")
        out_lines.append(f"Cert Thumbprint:   {cert.hex()}")
        return "\n".join(out_lines)
