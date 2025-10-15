# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
The temporary image section describes a development image to be sideloaded to the device.
"""

from .metadata_id import MetadataSectionId
from .metadata import MetadataSection
import struct


class TempImageMetadataFlags:
    """
    Temporary image metadata flags.
    """

    RemoveAtBoot = 0x1
    UnderDevelopment = 0x2

    def __init__(self, data=None):
        if data is not None:
            self.deserialize(data)
        else:
            self.flags = 0

    def deserialize(self, data):
        """
        Deserializes the flags from the given data.
        """
        self.flags = struct.unpack_from("<I", data, 0)[0]

    def serialize(self):
        """
        Serializes the flags to bytes.
        """
        return struct.pack("<I", self.flags)

    def get_flag_names(self):
        """
        Converts the flags to a string array.
        """
        names = []
        if self.flags & TempImageMetadataFlags.RemoveAtBoot:
            names += ["RemoveAtBoot"]
        elif self.flags & TempImageMetadataFlags.UnderDevelopment:
            names += ["UnderDevelopment"]
        return names

    def __str__(self):
        return ", ".join(self.get_flag_names())


class TempImageMetadataSection(MetadataSection):
    """
    The temporary image section describes the properties a development image to be sideloaded to the device.
    """

    # TempImageMetadata
    # uint32_t flags

    def __init__(self, data=None):
        super().__init__("Temporary Image", MetadataSectionId.TemporaryImage, data)
        if data is not None:
            self.deserialize(data)
        else:
            self.flags = TempImageMetadataFlags(None)

    @staticmethod
    def size():
        """
        Returns the size of the temporary image section in bytes.
        """
        return 4

    def deserialize(self, data):
        """
        Deserializes the temporary image section from the given data.
        """
        self.flags = TempImageMetadataFlags(data)

    def serialize(self):
        """
        Serializes the temporary image section to bytes.
        """
        return self.flags.serialize()

    def __str__(self):
        remove_at_boot = "RemoveAtBoot" in self.flags.get_flag_names()
        under_development = "UnderDevelopment" in self.flags.get_flag_names()

        out_lines = []
        out_lines.append(f"Remove image at boot: {remove_at_boot}")
        out_lines.append(f"Under development: {under_development}")
        return "\n".join(out_lines)
