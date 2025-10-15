# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Documents the expected structure of the OneBlInformation section.
Like capability files, this is not a metadata section, but rather the content.
"""

from ..metadata import MetadataSection
import struct


class OneBlInformationSection(MetadataSection):
    """
    Documents the binary format of OneBlInformation:
        uint32_t Information1
        uint32_t Information2
        uint32_t Information3
        uint32_t ChipId
        uint32_t Major
        uint32_t Minor
        uint32_t Patch
        uint32_t SecurityVersionNumber
    """

    def __init__(self, data):
        super().__init__("OneBlInformation", None, data)
        if data is not None:
            self.deserialize(data)
        else:
            self.information1 = 0
            self.information2 = 0
            self.information3 = 0
            self.chip_id = 0
            self.major = 0
            self.minor = 0
            self.patch = 0
            self.security_version_number = 0

    @staticmethod
    def size():
        """
        Returns the size of the section in bytes.
        """
        return 32

    def deserialize(self, data):
        """
        Deserializes the section from binary data.
        """
        self.raw_bytes = data
        self.information1 = struct.unpack_from("<I", data, 0)[0]
        self.information2 = struct.unpack_from("<I", data, 4)[0]
        self.information3 = struct.unpack_from("<I", data, 8)[0]
        self.chip_id = struct.unpack_from("<I", data, 12)[0]
        self.major = struct.unpack_from("<I", data, 16)[0]
        self.minor = struct.unpack_from("<I", data, 20)[0]
        self.patch = struct.unpack_from("<I", data, 24)[0]
        self.security_version_number = struct.unpack_from("<I", data, 28)[0]

    def serialize(self):
        """
        Serializes the section to binary data.
        """
        return struct.pack(
            "<IIIIIIII",
            self.information1,
            self.information2,
            self.information3,
            self.chip_id,
            self.major,
            self.minor,
            self.patch,
            self.security_version_number,
        )

    def __str__(self):
        out_lines = []
        out_lines.append(f"Security Version:  {self.security_version_number}")
        return "\n".join(out_lines)
