# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for license information.
# --------------------------------------------------------------------------------------------

import struct
from ..metadata_sections.utils import name_from_section_id


class ImageMetadataSectionHeader:
    """
    section metadata header describes the upcoming section.
    uint16_t section_id
    uint16 length
    bytes[length]
    """

    def __init__(self, data=None):
        if data is not None:
            self.deserialize(data)
        else:
            self.section_id = 0
            self.data_length = 0

    @staticmethod
    def size() -> int:
        """
        size of the section header (4 bytes).
        """
        return 4

    def deserialize(self, data: bytearray):
        """
        deserialize the section header from bytes.
        """
        self.section_id = struct.unpack_from("<H", data, 0)[0]
        self.data_length = struct.unpack_from("<H", data, 2)[0]

    def serialize(self) -> bytearray:
        """
        serialize the section header into bytes.
        """
        return struct.pack("<HH", self.section_id, self.data_length)

    def __str__(self) -> str:
        return (
            "ImageMetadataSectionHeader\n\t"
            + f"section_id: {self.section_id:x}"
            + f"({name_from_section_id(self.section_id)})\n\t"
            + f"data_length: {self.data_length}"
        )
