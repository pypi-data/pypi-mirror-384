# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
The required offset section (from what can be gleaned from code) shows the offset
 in flash where the image must be placed.
"""

from .metadata_id import MetadataSectionId
from .metadata import MetadataSection
import struct


class RequiredOffsetSection(MetadataSection):
    """
    The required offset section (from what can be gleaned from code) shows the offset
    in flash where the image must be placed.
    """

    offset: int
    # uint32_t offset

    def __init__(self, data=None):
        super().__init__("Required Offset", MetadataSectionId.RequiredFlashOffset, data)
        if data is not None:
            self.deserialize(data)
        else:
            self.offset = 0

    @staticmethod
    def size():
        """
        Returns the size of the required offset section in bytes.
        """
        return 4

    def deserialize(self, data):
        """
        Deserializes the required offset section from the given data.
        """
        self.offset = struct.unpack_from("<I", data, 0)[0]

    def serialize(self):
        """
        Serializes the required offset section to bytes.
        """
        return struct.pack("<I", self.offset)

    def __str__(self):
        out_lines = []
        out_lines.append(f"Offset: {self.offset:#x}")
        return "\n".join(out_lines)
