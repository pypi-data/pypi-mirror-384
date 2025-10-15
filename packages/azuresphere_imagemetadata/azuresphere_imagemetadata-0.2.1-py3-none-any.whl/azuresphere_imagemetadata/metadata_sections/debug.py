# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
The Debug Section provides additional useful metadata about the image.
This includes things like build time, and image name.
"""

from .metadata_id import MetadataSectionId
from .metadata import MetadataSection
import struct
from datetime import datetime, timezone


class DebugSection(MetadataSection):
    """
    The Debug Section provides additional useful metadata about the image:
    - The time the image was built.
    - The name of the image.
    """

    def __init__(self, data=None):
        super().__init__("Debug", MetadataSectionId.Debug, data)
        if data is not None:
            self.deserialize(data)
        else:
            self.debug_time = 0
            self.image_name_raw = bytes([0] * 32)
            self.image_name = ""

    @staticmethod
    def size():
        """
        The size of the Debug Section is 8 bytes for the time, and 32 bytes for the image name.
        """
        return 8 + 32

    def deserialize(self, data):
        """
        Deserialize the Debug Section from the provided data.
        """
        self.debug_time = struct.unpack_from("<Q", data, 0)[0]
        self.image_name_raw = struct.unpack_from("<32s", data, 8)[0]
        self.image_name = str(self.image_name_raw, encoding="utf-8")
        self.image_name = self.image_name.strip("\0")

    def serialize(self):
        """
        Serialize the Debug Section to a byte array.
        """
        return struct.pack("<Q32s", self.debug_time, self.image_name_raw)

    def __str__(self):
        utc_orig = datetime.fromtimestamp(self.debug_time, timezone.utc)
        LOCAL_TIMEZONE = datetime.now(timezone.utc).astimezone().tzinfo
        local = datetime.fromtimestamp(self.debug_time, LOCAL_TIMEZONE)

        out_lines = []
        out_lines.append(f"Name:              {self.image_name}")
        out_lines.append(f"Built On (UTC):    {utc_orig.strftime('%d/%m/%Y %H:%M:%S')}")
        out_lines.append(f"Built On (Local):  {local.strftime('%d/%m/%Y %H:%M:%S')}")

        return "\n".join(out_lines)
