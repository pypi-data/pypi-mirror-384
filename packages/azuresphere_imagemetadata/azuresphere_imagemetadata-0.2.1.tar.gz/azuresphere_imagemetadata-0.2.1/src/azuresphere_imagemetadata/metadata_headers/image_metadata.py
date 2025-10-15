# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Contains definition for the different headers used in image metadata.
"""

from ..exceptions import ImageMetadataDeserializationError
import struct


class ImageMetadataHeader:
    """
    image metadata header
    describes the layout of the image metadata (i.e. number of sections).

    contains:
    uint32_t magic 0x4d345834
    uint32_t section_count
    """

    CorrectMagicValue = 0x4D345834

    def __init__(self, data=None):
        if data is not None:
            self.deserialize(data)
        else:
            self.magic_value = self.CorrectMagicValue
            self.section_count = 0

    @staticmethod
    def size() -> int:
        """
        size of the header (8 bytes).
        """
        return 8

    def deserialize(self, data: bytearray):
        """
        deserialize the header and check magic values match.
        """
        self.magic_value = struct.unpack_from("<I", data, 0)[0]
        self.section_count = struct.unpack_from("<I", data, 4)[0]

        if self.magic_value != ImageMetadataHeader.CorrectMagicValue:
            raise ImageMetadataDeserializationError(
                "ImageMetadataHeader: Invalid magic value"
            )

    def serialize(self) -> bytearray:
        """
        serialize the header.
        """
        return struct.pack("<II", self.magic_value, self.section_count)

    def __str__(self):
        return (
            "ImageMetadataHeader\n\tmagic_value: "
            + str(self.magic_value)
            + "\n\tsection_count: "
            + str(self.section_count)
            + "\n"
        )
