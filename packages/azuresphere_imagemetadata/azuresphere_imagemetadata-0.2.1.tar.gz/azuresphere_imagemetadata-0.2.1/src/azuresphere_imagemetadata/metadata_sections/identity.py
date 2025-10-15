# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
The identity section contains information about the image, such as the image type, version, and size.
All images must have an identity metadata section.
"""

from .metadata_id import MetadataSectionId
from .metadata import MetadataSection
from ..guid_utils import Guid
import struct
import uuid


class ImageType:
    """
    Image type enum.
    """

    # /// <summary>
    # /// Invalid.
    # /// </summary>
    Invalid = 0

    # /// <summary>
    # /// Better known as 1BL; code executed by the ROM on Pluton.
    # /// </summary>
    OneBL = 1

    # /// <summary>
    # /// Pluton runtime.
    # /// </summary>
    PlutonRuntime = 2

    # /// <summary>
    # /// Vendor-specific WiFi firmware.
    # /// </summary>
    WifiFirmware = 3

    # /// <summary>
    # /// Secure World runtime, a.k.a. security monitor.
    # /// </summary>
    SecurityMonitor = 4

    # /// <summary>
    # /// Normal World loader.
    # /// </summary>
    NormalWorldLoader = 5

    # /// <summary>
    # /// Device Tree, used by Normal World OS.
    # /// </summary>
    NormalWorldDTB = 6

    # /// <summary>
    # /// Normal World OS kernel.
    # /// </summary>
    NormalWorldKernel = 7

    # /// <summary>
    # /// Normal World root file system.
    # /// </summary>
    RootFs = 8

    # /// <summary>
    # /// Normal World, services written and managed by Microsoft.
    # /// </summary>
    Services = 9

    # /// <summary>
    # /// Normal World, user-mode apps.
    # /// </summary>
    Applications = 10

    # /// <summary>
    # /// Configuration data for firmware (Pluton, HlosCore).
    # /// </summary>
    FirmwareConfig = 13

    # /// <summary>
    # /// Boot Manifest (secure flash storage)
    # /// </summary>
    BootManifest = 16

    # /// <summary>
    # /// Normal World File System
    # /// </summary>
    NormalWorldFileSystem = 17

    # ///<summary>
    # /// The TrustedKeystore image
    # ///</summary>
    TrustedKeystore = 19

    # ///<summary>
    # /// An image containing policies for the device.
    # ///</summary>
    Policy = 20

    # /// <summary>
    # /// An image containing board configuration for each customer system.
    # /// </summary>
    CustomerBoardConfig = 21

    # /// <summary>
    # /// An image containing the certificates needed by the OTA update process.
    # /// </summary>
    UpdateCertStore = 22

    # /// <summary>
    # /// A manifest describing the update of our trusted keys and certificate stores.
    # /// </summary>
    BaseSystemUpdateManifest = 23

    # /// <summary>
    # /// A manifest describing the update of our system software.
    # /// </summary>
    FirmwareUpdateManifest = 24

    # /// <summary>
    # /// A manifest describing the update of 3rd-party images.
    # /// </summary>
    CustomerUpdateManifest = 25

    # /// <summary>
    # /// A manifest describing system software for recovery.
    # /// </summary>
    RecoveryManifest = 26

    # /// <summary>
    # /// A manifest set that contains 1 or more manifests and flags concerning those manifests.
    # /// </summary>
    ManifestSet = 27

    # /// <summary>
    # /// Sentinel value indicating an unspecified image type.
    # /// </summary>
    Other = 28

    @staticmethod
    def get_name(image_type) -> str:
        """
        Returns the name of the provided image type.
        """
        if image_type == ImageType.Invalid:
            return "Invalid"
        elif image_type == ImageType.OneBL:
            return "OneBL"
        elif image_type == ImageType.PlutonRuntime:
            return "PlutonRuntime"
        elif image_type == ImageType.WifiFirmware:
            return "WifiFirmware"
        elif image_type == ImageType.SecurityMonitor:
            return "SecurityMonitor"
        elif image_type == ImageType.NormalWorldLoader:
            return "NormalWorldLoader"
        elif image_type == ImageType.NormalWorldDTB:
            return "NormalWorldDTB"
        elif image_type == ImageType.NormalWorldKernel:
            return "NormalWorldKernel"
        elif image_type == ImageType.RootFs:
            return "RootFs"
        elif image_type == ImageType.Services:
            return "Services"
        elif image_type == ImageType.Applications:
            return "Applications"
        elif image_type == ImageType.FirmwareConfig:
            return "FirmwareConfig"
        elif image_type == ImageType.BootManifest:
            return "BootManifest"
        elif image_type == ImageType.NormalWorldFileSystem:
            return "NormalWorldFileSystem"
        elif image_type == ImageType.TrustedKeystore:
            return "TrustedKeystore"
        elif image_type == ImageType.Policy:
            return "Policy"
        elif image_type == ImageType.CustomerBoardConfig:
            return "CustomerBoardConfig"
        elif image_type == ImageType.UpdateCertStore:
            return "UpdateCertStore"
        elif image_type == ImageType.BaseSystemUpdateManifest:
            return "BaseSystemUpdateManifest"
        elif image_type == ImageType.FirmwareUpdateManifest:
            return "FirmwareUpdateManifest"
        elif image_type == ImageType.CustomerUpdateManifest:
            return "CustomerUpdateManifest"
        elif image_type == ImageType.RecoveryManifest:
            return "RecoveryManifest"
        elif image_type == ImageType.ManifestSet:
            return "ManifestSet"
        elif image_type == ImageType.Other:
            return "Other"
        else:
            return "Unknown"


class IdentitySection(MetadataSection):
    """
    Identity section of the metadata.
    Contains information about the image included the image type, uuid and component id.
    """

    # identity
    # ushort image_tyoe
    # ushort reserved
    # byte[16] uuid
    # byte[16] component_id

    def __init__(self, data=None):
        super().__init__("Identity", MetadataSectionId.Identity, data)
        if data is not None:
            self.deserialize(data)
        else:
            self.image_type = ImageType.Invalid
            self.reserved = 0
            self.image_uid_raw = bytes([0] * 16)
            self.component_uid_raw = bytes([0] * 16)

    @staticmethod
    def size():
        """
        Returns the size of the identity section in bytes.
        """
        return 36

    @property
    def image_uid(self):
        """
        Returns the image uuid as a string.
        """
        return str(Guid(self.image_uid_raw))

    @image_uid.setter
    def image_uid(self, value: str):
        """
        Sets the image uuid from a hex string.
        """
        self.image_uid_raw = Guid.from_hex_string(value).bytes

    @property
    def component_uid(self):
        """
        Returns the component uuid as a string.
        """
        return str(Guid(self.component_uid_raw))

    @component_uid.setter
    def component_uid(self, value: str):
        """
        Sets the component uuid from a string.
        """
        self.component_uid_raw = Guid.from_hex_string(value).bytes

    def deserialize(self, data):
        """
        Deserializes the identity section from the provided data.
        """
        self.image_type = struct.unpack_from("<H", data, 0)[0]
        self.reserved = struct.unpack_from("<H", data, 2)[0]
        self.component_uid_raw = struct.unpack_from("<16s", data, 4)[0]
        self.image_uid_raw = struct.unpack_from("<16s", data, 20)[0]

    def serialize(self):
        """
        Serializes the identity section into bytes.
        """
        data = bytearray(IdentitySection.size())
        struct.pack_into("<H", data, 0, self.image_type)
        struct.pack_into("<H", data, 2, self.reserved)
        struct.pack_into("<16s", data, 4, self.component_uid_raw)
        struct.pack_into("<16s", data, 20, self.image_uid_raw)
        return data

    def __str__(self):
        out_lines = []
        out_lines.append(f"Image Type:        {ImageType.get_name(self.image_type)}")
        out_lines.append(f"Component UID:     {self.component_uid}")
        out_lines.append(f"Image UID:         {self.image_uid}")
        return "\n".join(out_lines)
