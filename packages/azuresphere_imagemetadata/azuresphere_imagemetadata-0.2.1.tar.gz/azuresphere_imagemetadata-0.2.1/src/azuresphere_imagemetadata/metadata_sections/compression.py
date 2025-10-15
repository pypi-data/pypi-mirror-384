# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Compression section, if present, shows what compression algorithm was used to compress the image.
It also gives the uncompressed size of the image.
"""

from .metadata_id import MetadataSectionId
from .metadata import MetadataSection
import struct


class CompressionType:
    """
    Compression type enum.
    """

    Invalid = 0
    Lzma = 1

    compression_type: int

    def __init__(self, data):
        if data is not None:
            self.deserialize(data)
        else:
            self.compression_type = 0

    @staticmethod
    def size():
        """
        Returns the size of the compression type in bytes.
        """
        return 4

    def get_compression_type_name(self):
        """
        Converts the compression type to a string
        """
        if self.compression_type == CompressionType.Lzma:
            return "Lzma"

        raise ValueError(
            "CompressionSection: Invalid compression type %d" % (self.compression_type)
        )

    def deserialize(self, data):
        """
        Deserializes the compression type from the given data.
        """
        self.compression_type = struct.unpack_from("<I", data, 0)[0]

    def serialize(self):
        return struct.pack("<I", self.compression_type)

    def __str__(self):
        return str(self.compression_type)


class CompressionSection(MetadataSection):
    """
    The compression section, if present, shows what compression algorithm was used to compress the image.
    """

    # uint32_t uncompressed_size
    # uint32_t compression_type

    uncompressed_size: int
    compression_type: CompressionType

    def __init__(self, data=None):
        super().__init__("Compression", MetadataSectionId.Compression, data)

        if data is not None:
            self.deserialize(data)
        else:
            self.uncompressed_size = 0
            self.compression_type = CompressionType(None)

    @staticmethod
    def size():
        """
        Returns the size of the compression section in bytes.
        Uncompressed member size + compression type size.
        """
        return CompressionType.size() + 4

    def deserialize(self, data):
        """
        Deserializes the compression section from the given data.
        """
        self.uncompressed_size = struct.unpack_from("<I", data, 0)[0]
        self.compression_type = CompressionType(data[4:])

    def serialize(self):
        return (
            struct.pack("<I", self.uncompressed_size)
            + self.compression_type.serialize()
        )

    def __str__(self):
        out_lines = []
        out_lines.append(f"Type:              {self.compression_type}")
        out_lines.append(f"Uncompressed size: {self.uncompressed_size:,} bytes")
        return "\n".join(out_lines)
