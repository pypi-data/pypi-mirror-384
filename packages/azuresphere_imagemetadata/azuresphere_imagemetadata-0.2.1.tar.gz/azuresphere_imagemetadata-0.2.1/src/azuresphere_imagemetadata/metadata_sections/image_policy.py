# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
The image policy section indicates whether the image can be invalidated or sideloaded from normal world (OS).
"""

from .metadata_id import MetadataSectionId
from .metadata import MetadataSection
import struct
from typing import List


class ImagePolicyFlags:
    """
    Image policy flags enum.
    """

    # uint32_t flags
    NoFlags = 0
    InvalidateFromNormalWorld = 0x1 << 0
    SideloadFromNormalWorld = 0x1 << 1

    flags: int

    def __init__(self, data=None):
        if data is not None:
            self.deserialize(data)
        else:
            self.flags = self.NoFlags

    def get_flags_name(self) -> List[str]:
        """
        Converts the flags to a string array.
        """
        flags = []
        if self.flags & ImagePolicyFlags.InvalidateFromNormalWorld:
            flags += ["InvalidateFromNormalWorld"]
        if self.flags & ImagePolicyFlags.SideloadFromNormalWorld:
            flags += ["SideloadFromNormalWorld"]
        return flags

    @staticmethod
    def size():
        """
        Returns the size of the flags field in bytes.
        """
        return 4

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

    def __str__(self):
        return "ImagePolicyFlags\n\tflags: %d" % (self.flags) + "\n"


class ImagePolicySection(MetadataSection):
    """
    The image policy section, if present, indicates whether the image can be invalidated or sideloaded from normal world (OS).
    """

    def __init__(self, data=None):
        super().__init__("Image Policy", MetadataSectionId.ImagePolicy, data)

        if data is not None:
            self.deserialize(data)
        else:
            self.flags = ImagePolicyFlags(None)

    @staticmethod
    def size():
        """
        Returns the size of the image policy section in bytes.
        """
        return ImagePolicyFlags.size()

    def deserialize(self, data):
        """
        Deserializes the image policy section from the given data.
        """
        self.flags = ImagePolicyFlags(data)

    def serialize(self):
        """
        Serializes the image policy section to bytes.
        """
        return self.flags.serialize()

    def __str__(self):
        invalid_from_nw = "InvalidateFromNormalWorld" in self.flags.get_flags_name()
        sideload_from_nw = "SideloadFromNormalWorld" in self.flags.get_flags_name()

        out_lines = []
        out_lines.append(f"Allow invalidation from Normal World: {invalid_from_nw}")
        out_lines.append(f"Allow sideloading from Normal World: {sideload_from_nw}")

        return "\n".join(out_lines)
