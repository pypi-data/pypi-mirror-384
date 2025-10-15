# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
A class that deserialises/parses image metadata given an Azure Sphere image.
"""

import struct

from .exceptions import ImageMetadataDeserializationError
from .metadata_sections.utils import class_from_section_id
from .metadata_sections.internal.onebl import OneBlInformationSection
from .metadata_headers.image_metadata import ImageMetadataHeader
from .metadata_headers.image_metadata_section import ImageMetadataSectionHeader
from typing import Optional
from .metadata_sections import (
    SignatureSection,
    IdentitySection,
    CompressionSection,
    TempImageMetadataSection,
    MetadataSectionId,
    DebugSection,
)


class ImageMetadata:
    """
    Image metadata contains a header, followed by a number of sections.
    """

    def __init__(self, data):
        self.sections = []
        self.section_headers = []
        self.header = None
        self.onebl = None
        self.end_of_metadata = 0
        self.start_of_metadata = 0
        self.signature_size = 0
        self.raw_data = bytes()
        if data is not None:
            self.deserialize(data)

    def deserialize(self, byte_data):
        """
        Image metadata is placed at the end of the file.

        :raises ImageMetadataDeserializationError: if the metadata is invalid
        """
        position = 0
        # The image signature is appended to the end of the metadata and is:
        # 64 bytes, if sha256 is used
        # 96 bytes, if sha384 is used
        possible_signature_sizes = [64, 96]
        for possible_signature_size in possible_signature_sizes:
            self.onebl = None  # reset onebl on loop as it can be set incorrectly
            minimum_valid_size = (
                possible_signature_size + 4 + ImageMetadataSectionHeader.size()
            )
            metadata_length_offset = possible_signature_size + 4
            onebl_metadata_length_offset = (
                possible_signature_size + 4 + OneBlInformationSection.size()
            )

            if len(byte_data) < minimum_valid_size:
                continue

            sig_area_size = possible_signature_size
            self.end_of_metadata = len(byte_data) - metadata_length_offset
            # length is stored in the four bytes before the signature
            target_length = struct.unpack_from("<I", byte_data, self.end_of_metadata)[0]

            if target_length <= 28:
                # This may be a 1BL only section
                if len(byte_data) < minimum_valid_size + OneBlInformationSection.size():
                    continue

                sig_area_size += OneBlInformationSection.size()

                position = (
                    len(byte_data)
                    - possible_signature_size
                    - OneBlInformationSection.size()
                )
                self.onebl = OneBlInformationSection(
                    byte_data[position : position + OneBlInformationSection.size()]
                )

                self.end_of_metadata = len(byte_data) - onebl_metadata_length_offset
                position = self.end_of_metadata
                target_length = struct.unpack_from("<I", byte_data, position)[0]

            if len(byte_data) < (sig_area_size + target_length):
                # Not enough space, fail
                continue

            if target_length < ImageMetadataHeader.size():
                # Length too small, fail
                continue

            header_position = len(byte_data) - sig_area_size - target_length
            self.start_of_metadata = header_position

            self.image_data = byte_data[0:header_position]

            header = ImageMetadataHeader(
                byte_data[
                    header_position : header_position + ImageMetadataHeader.size()
                ]
            )

            self.header = header

            if header.section_count == 0:
                continue

            section_addr = header_position + ImageMetadataHeader.size()

            for _ in range(0, header.section_count):
                if section_addr >= self.end_of_metadata:
                    continue

                section_header_data = byte_data[
                    section_addr : section_addr + ImageMetadataSectionHeader.size()
                ]
                section_header = ImageMetadataSectionHeader(section_header_data)

                self.section_headers += [section_header]

                if section_header.data_length == 0:
                    continue

                if (
                    section_addr
                    + ImageMetadataSectionHeader.size()
                    + section_header.data_length
                    > self.end_of_metadata
                ):
                    continue

                section_addr += ImageMetadataSectionHeader.size()

                self.sections += [
                    class_from_section_id(section_header.section_id)(
                        byte_data[
                            section_addr : section_addr + section_header.data_length
                        ]
                    )
                ]

                section_addr += section_header.data_length

            # Add the length of the length field itself (4 bytes)
            self.end_of_metadata += 4

            self.signature_size = possible_signature_size
            self.raw_data = byte_data[self.start_of_metadata : self.end_of_metadata]
            return
        raise ImageMetadataDeserializationError("Invalid metadata")

    def serialize(self):
        """
        Serialize the image metadata to a byte array.
        """
        header = ImageMetadataHeader()
        header.section_count = len(self.sections)

        out = header.serialize()

        for s in self.sections:
            sec_bytes = s.serialize()
            sec_header = ImageMetadataSectionHeader()
            sec_header.section_id = s.section_id
            sec_header.data_length = len(sec_bytes)
            out += sec_header.serialize()
            out += sec_bytes

        # Add the length of the metadata to the end
        # Include the length of the length field itself (4 bytes)
        out += struct.pack("<I", len(out) + 4)
        return out

    def add_section(self, section):
        """
        Add a section to the metadata.
        """
        self.sections += [section]

    def sections_by_name(self, name):
        """
        Returns a list of sections with the given name.
        """
        return [section for section in self.sections if section.name == name]

    def sections_by_id(self, section_id):
        """
        Returns a list of sections with the given id.
        """
        return [
            section for section in self.sections if section.section_id == section_id
        ]

    def remove_section(self, section):
        """
        Removes a section from the metadata.
        """
        self.sections = [s for s in self.sections if s != section]

    @property
    def signature(self) -> Optional[SignatureSection]:
        signature = self.sections_by_id(MetadataSectionId.Signature)
        if len(signature) > 1:
            raise ValueError("Multiple signature sections found")
        return signature[0] if len(signature) > 0 else None

    @property
    def identity(self) -> Optional[IdentitySection]:
        identity = self.sections_by_id(MetadataSectionId.Identity)
        if len(identity) > 1:
            raise ValueError("Multiple identity sections found")
        return identity[0] if len(identity) == 1 else None

    @property
    def compression_info(self) -> Optional[CompressionSection]:
        compression = self.sections_by_id(MetadataSectionId.Compression)
        if len(compression) > 1:
            raise ValueError("Multiple compression sections found")
        return compression[0] if len(compression) == 1 else None

    @property
    def tempinfo(self) -> Optional[TempImageMetadataSection]:
        tempinfo = self.sections_by_id(MetadataSectionId.TemporaryImage)
        if len(tempinfo) > 1:
            raise ValueError("Multiple tempinfo sections found")
        return tempinfo[0] if len(tempinfo) == 1 else None

    @property
    def debug(self) -> Optional[DebugSection]:
        debug = self.sections_by_id(MetadataSectionId.Debug)
        if len(debug) > 1:
            raise ValueError("Multiple debug sections found")
        return debug[0] if len(debug) == 1 else None

    def str_dotnet(self) -> str:
        """
        Returns a string representation of the metadata using the same formatting errors as
        the dotnet tool.
        """
        out_lines = []
        # to match dotnet output exactly, each section header has \r\n at the end of it
        # each content line has \r\r\n at the end of it.
        # This is likely a bug in the dotnet code where the lines were split assuming \n
        # as the line ending when infact the line ending was \r\n
        # We will match it for testing purposes.
        for section in self.sections:
            out_lines.append(f"  Section: {section.name}\r\n")

            # the formatting error was not globally applied to all sections,
            # so we need to special case this one
            if section.name == "Required Offset":
                for line in str(section).split("\n"):
                    if line.strip() == "":
                        continue
                    out_lines.append(f"    {line}\r\n")
            else:
                for line in str(section).split("\n"):
                    if line.strip() == "":
                        continue
                    out_lines.append(f"    {line}\r\r\n")

        if self.onebl is not None:
            out_lines.append("  Section: 1BL Information\r\n")
            for line in str(self.onebl).split("\n"):
                if line.strip() == "":
                    continue
                out_lines.append(f"    {line}\r\r\n")

        out_str = "".join(out_lines)
        return out_str + "\r\n"

    def __str__(self):
        """
        Returns a correctly formatted string representation of the metadata.
        """
        out_lines = []
        for section in self.sections:
            out_lines.append(f"  Section: {section.name}")

            for line in str(section).split("\n"):
                if line.strip() == "":
                    continue
                out_lines.append(f"    {line}")

        if self.onebl is not None:
            out_lines.append("  Section: 1BL Information")
            for line in str(self.onebl).split("\n"):
                if line.strip() == "":
                    continue
                out_lines.append(f"    {line}")

        return "\r\n".join(out_lines) + "\r\n"
