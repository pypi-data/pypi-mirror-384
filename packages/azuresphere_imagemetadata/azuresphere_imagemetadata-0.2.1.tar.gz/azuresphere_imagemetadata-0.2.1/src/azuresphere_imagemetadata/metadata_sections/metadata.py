# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
MetadataSection is the super class for all metadata sections.
It contains common properties (name, section_id, raw_data).
"""
from .metadata_id import MetadataSectionId


class MetadataSection:
    """
    MetadataSection is the super class for all metadata sections.
    """

    name: str
    section_id: MetadataSectionId
    raw_data: bytearray

    def __init__(self, name: str, section_id: MetadataSectionId, data: bytearray):
        self.name = name
        self.section_id = section_id
        # preserve a copy of the original data buf.
        self.raw_data = data

    def serialize(self) -> bytes:
        """
        Serializes the section into a bytearray.
        """
        raise NotImplementedError

    def deserialize(self, data: bytes):
        """
        deserializes the section into a bytearray.
        """
        raise NotImplementedError
