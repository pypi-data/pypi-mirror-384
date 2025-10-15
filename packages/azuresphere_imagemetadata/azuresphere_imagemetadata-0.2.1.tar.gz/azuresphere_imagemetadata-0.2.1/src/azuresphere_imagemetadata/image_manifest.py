# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for license information.
# --------------------------------------------------------------------------------------------

import struct
from datetime import datetime, timezone
from .metadata_sections.abi import ABIIdentity
from .image_metadata import ImageMetadata
from .guid_utils import to_guid, format_guid_as_string
from .metadata_sections.identity import ImageType


class PartitionType:
    Invalid = 0
    Firmware = 1
    Backups = 2
    Applications = 4
    LogStorage = 5
    NWConfig = 6
    BootloaderOne = 7
    BootloaderOneBackup = 8
    LocatorTable = 9
    LocatorTableBackup = 10
    BlockHashes = 11
    BlockHashesBackup = 12
    BootManifest = 13
    BootManifestBackup = 14
    TelemetryStorage = 15
    LastValidPhysicalPartition = 15
    MaxPhysicalLayout = 16383
    # All layouts above 2^14 - 1 are virtual layouts that do not describe physical flash data, but
    # rather describe flash policy.
    EC_RuntimeProtectedRange = 16384
    MaxVirtualLayout = 65535

    @staticmethod
    def get_name(value):
        if value == PartitionType.Invalid:
            return "invalid"
        if value == PartitionType.Firmware:
            return "firmware"
        if value == PartitionType.Backups:
            return "backups"
        if value == PartitionType.Applications:
            return "applications"
        if value == PartitionType.LogStorage:
            return "log_storage"
        if value == PartitionType.NWConfig:
            return "nw_config"
        if value == PartitionType.BootloaderOne:
            return "bootloader_one"
        if value == PartitionType.BootloaderOneBackup:
            return "bootloader_one_backup"
        if value == PartitionType.LocatorTable:
            return "locator_table"
        if value == PartitionType.LocatorTableBackup:
            return "locator_table_backup"
        if value == PartitionType.BlockHashes:
            return "block_hashes"
        if value == PartitionType.BlockHashesBackup:
            return "block_hashes_backup"
        if value == PartitionType.BootManifest:
            return "boot_manifest"
        if value == PartitionType.BootManifestBackup:
            return "boot_manifest_backup"
        if value == PartitionType.TelemetryStorage:
            return "telemetry_storage"
        raise ValueError("Unknown partition type: " + str(value))


class ManifestHeader:
    """
    Manifest header
    Only V3 is supported. Earlier versions will raise an exception.
    """

    VERSION1 = 1
    VERSION2 = 2
    VERSION3 = 3
    MAX_COUNT_ABI_IDENTITIES = 2

    def __init__(self, data):
        if data is None:
            self.version = ManifestHeader.VERSION3
            self.image_count = 0
            self.manifest_header_size = 0
            self.manifest_entry_size = 0
            self.build_date = 0
            self.manifest_version = 0
        else:
            self.deserialize(data)

    @staticmethod
    def size():
        """
        Returns the size of the ManifestHeader in bytes.
        """
        return 16

    def deserialize(self, data):
        """
        Deserializes the ManifestHeader from the provided data.
        """
        self.version = struct.unpack("<H", data[0:2])[0]

        if self.version != ManifestHeader.VERSION3:
            raise ValueError("Unsupported manifest version: " + str(self.version))

        self.image_count = struct.unpack("<H", data[2:4])[0]
        self.manifest_header_size = struct.unpack("<H", data[4:6])[0]
        self.manifest_entry_size = struct.unpack("<H", data[6:8])[0]
        self.build_date = struct.unpack("<Q", data[8:16])[0]

    def __str__(self):
        LOCAL_TIMEZONE = datetime.now(timezone.utc).astimezone().tzinfo
        local = datetime.fromtimestamp(self.build_date, LOCAL_TIMEZONE)
        return f"ManifestHeader: version={self.version}, image_count={self.image_count}, manifest_header_size={self.manifest_header_size}, manifest_entry_size={self.manifest_entry_size}, build_date={local.strftime('%d/%m/%Y %H:%M:%S')}"


class ManifestEntry:
    """Manifest entry"""

    UID_SIZE = 16

    def __init__(self, data):
        self.image_uid_raw = None
        self.component_uid_raw = None
        self.image_type = 0
        self.partition_type = 0
        self.image_file_size = 0
        self.uncompressed_image_size = 0
        self.provides = []
        self.depends = []
        if data is not None:
            self.deserialize(data)

    @property
    def image_uid(self):
        """
        Returns the image uuid as a string.
        """
        return format_guid_as_string(to_guid(self.image_uid_raw))

    @property
    def component_uid(self):
        """
        Returns the component uuid as a string.
        """
        return format_guid_as_string(to_guid(self.component_uid_raw))

    def deserialize(self, data):
        """
        Deserializes the ManifestEntry from the provided data.
        """
        offset = 0
        self.image_uid_raw = data[offset : offset + ManifestEntry.UID_SIZE]
        offset += ManifestEntry.UID_SIZE
        self.component_uid_raw = data[offset : offset + ManifestEntry.UID_SIZE]
        offset += ManifestEntry.UID_SIZE
        self.image_type = struct.unpack("<H", data[offset : offset + 2])[0]
        offset += 2
        self.partition_type = struct.unpack("<H", data[offset : offset + 2])[0]
        offset += 2
        self.image_file_size = struct.unpack("<I", data[offset : offset + 4])[0]
        offset += 4
        self.uncompressed_image_size = struct.unpack("<I", data[offset : offset + 4])[0]
        offset += 4

        for _ in range(0, ManifestHeader.MAX_COUNT_ABI_IDENTITIES):
            self.provides += [ABIIdentity(data[offset : offset + ABIIdentity.size()])]
            offset += ABIIdentity.size()

        for _ in range(0, ManifestHeader.MAX_COUNT_ABI_IDENTITIES):
            self.depends += [ABIIdentity(data[offset : offset + ABIIdentity.size()])]
            offset += ABIIdentity.size()

    def __str__(self):
        provides_string = ", ".join([str(p) for p in self.provides])
        depends_string = ", ".join([str(d) for d in self.depends])
        return f"ManifestEntry: image_uid={self.image_uid}, component_uid={self.component_uid}, image_type={ImageType.get_name(self.image_type)}, partition_type={self.partition_type}, image_file_size={self.image_file_size}, uncompressed_image_size={self.uncompressed_image_size}, provides=[{provides_string}], depends=[{depends_string}]"


class ImageManifest:
    """
    An ImageManifest lists the images and any dependencies for a recovery folder.

    The manifest is structured as follows:
    - ManifestHeader
    - ManifestEntry (repeated header.image_count times)
    """

    def __init__(self, data):
        self.header = None
        self.entries = []
        if data is not None:
            self.deserialize(data)

    def deserialize(self, data):
        """
        Deserializes the ImageManifest from the provided data.
        """
        offset = 0
        self.header = ManifestHeader(data[offset : offset + ManifestHeader.size()])
        offset += ManifestHeader.size()
        for _ in range(0, self.header.image_count):
            entry = ManifestEntry(
                data[offset : offset + self.header.manifest_entry_size]
            )
            self.entries.append(entry)
            offset += self.header.manifest_entry_size

    def __str__(self):
        out_lines = []
        out_lines.append(str(self.header))
        for e in self.entries:
            out_lines.append(str(e))
        return "\n".join(out_lines)

    @staticmethod
    def from_image_metadata(image_metadata: ImageMetadata):
        return ImageManifest(image_metadata.image_data)

    def str_dotnet(self) -> str:
        """
        Returns a string representation of the manifest using the same formatting as dotnet.
        """
        out_lines = []
        out_lines.append(f"Version: {self.header.version}")
        out_lines.append(
            f"ImageCount: {self.header.image_count}, Number Entries: {len(self.entries)}"
        )

        for entry in self.entries:
            out_lines.append(
                f"Image type: {ImageType.get_name(entry.image_type)} ({entry.image_type}), Partition: {PartitionType.get_name(entry.partition_type)}, component uid: {entry.component_uid}, image uid: {entry.image_uid}, size: {entry.image_file_size}, uncompressed size: {entry.uncompressed_image_size}"
            )

        return "\n".join(out_lines) + "\n"
