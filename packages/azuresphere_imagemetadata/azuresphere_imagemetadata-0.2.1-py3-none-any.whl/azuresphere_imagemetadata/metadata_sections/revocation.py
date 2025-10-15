# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
The revocation section, iff present, an image can be revoked using fused based revocation.
This revocation check is similar to the ROM revocation of 1BLs and involves checking a security version
number against a 32 bit SW fuse.  If bit N is set to 1 then security version N is not trusted.
In general this version would only be increased when we need to do revocation and is otherwise static
 from build to build.
"""

from .metadata_id import MetadataSectionId
from .metadata import MetadataSection
import struct


class RevocationSection(MetadataSection):
    """
    The class that represent the revocation section.
    """

    name = "Revocation"
    section_id = MetadataSectionId.Revocation

    # uint32_t version
    def __init__(self, data=None):
        super().__init__("Revocation", MetadataSectionId.Revocation, data)
        if data is not None:
            self.deserialize(data)
        else:
            self.version = 0

    @staticmethod
    def size():
        """
        Returns the size of the revocation section in bytes.
        """
        return 4

    def deserialize(self, data):
        """
        Deserializes the revocation section from the given data.
        """
        self.version = struct.unpack_from("<I", data, 0)[0]

    def serialize(self):
        """
        Serializes the revocation section to bytes.
        """
        return struct.pack("<I", self.version)

    def __str__(self):
        out_lines = []
        out_lines.append(f"Security Version:  {self.version}")
        return "\n".join(out_lines)
