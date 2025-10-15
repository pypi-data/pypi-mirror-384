# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Documents the binary format of Capabilities.

A capability is not an image metadata section, but rather the content.
Image metadata is appended to the end of a capability file.
"""

from ..metadata import MetadataSection
from ...exceptions import ImageMetadataDeserializationError
import struct
from typing import List


class Capability:
    """
    Represents a capability and holds the possible numeric values of a capability.

    When cast to a string, this class returns non-user facing names for capabilities.
    """

    # /// <summary>
    # /// default case with no capability.
    # /// NoCapability indicates  no further capability is following.
    # /// </summary>
    NoCapability = 0x0

    # /// <summary>
    # /// allow test key in secure boot for development purpose.
    # /// </summary>
    AllowTestKey = 0x1

    # /// <summary>
    # /// enable Pluton M4 debug.
    # /// </summary>
    EnablePlutonDebug = 0x2

    # /// <summary>
    # /// enable Hlos Core debug.
    # /// </summary>
    EnableHlosCoreDebug = 0x3

    # /// <summary>
    # /// enable N9 debug.
    # /// </summary>
    EnableN9Debug = 0x4

    # /// <summary>
    # /// enable Hlos Core console.
    # /// </summary>
    EnableHlosCoreConsole = 0x8

    # /// <summary>
    # /// Enable SLT Loader from 1BL
    # /// </summary>
    EnableSltLoader = 0x9

    # /// <summary>
    # /// enable System Software Development.
    # /// </summary>
    EnableSystemSoftwareDevelopment = 0xA

    # /// <summary>
    # /// enable Customer App Development.
    # /// </summary>
    EnableCustomerAppDevelopment = 0xB

    # /// <summary>
    # /// Enable entering low-level RF Test Mode.
    # /// </summary>
    EnableRfTestMode = 0xC

    # /// <summary>
    # /// Unlock GatewayD host communication
    # /// </summary>
    UnlockGatewayD = 0xD

    @staticmethod
    def customer_capabilities() -> List[int]:
        """
        Returns a list of customer capabilities.
        """
        return [
            Capability.EnableCustomerAppDevelopment,
            Capability.EnableRfTestMode,
            Capability.UnlockGatewayD,
        ]

    @staticmethod
    def internal_capabilities() -> List[int]:
        """
        Returns a list of internal capabilities.
        """
        return [
            Capability.AllowTestKey,
            Capability.EnablePlutonDebug,
            Capability.EnableHlosCoreDebug,
            Capability.EnableN9Debug,
            Capability.EnableHlosCoreConsole,
            Capability.EnableSltLoader,
            Capability.EnableSystemSoftwareDevelopment,
        ]

    def __init__(self, capability: bytearray):
        self.capability = capability

    def __str__(self):
        return Capability.capability_to_name(self.capability)

    @staticmethod
    def capability_to_name(capability) -> str:
        capability_map = {
            Capability.NoCapability: "NoCapability",
            Capability.AllowTestKey: "AllowTestKey",
            Capability.EnablePlutonDebug: "EnablePlutonDebug",
            Capability.EnableHlosCoreDebug: "EnableHlosCoreDebug",
            Capability.EnableN9Debug: "EnableN9Debug",
            Capability.EnableHlosCoreConsole: "EnableHlosCoreConsole",
            Capability.EnableSltLoader: "EnableSltLoader",
            Capability.EnableSystemSoftwareDevelopment: "EnableSystemSoftwareDevelopment",
            Capability.EnableCustomerAppDevelopment: "EnableCustomerAppDevelopment",
            Capability.EnableRfTestMode: "EnableRfTestMode",
            Capability.UnlockGatewayD: "UnlockGatewayD",
        }
        return capability_map.get(capability, "UnknownCapability")


class UserFacingCapability(Capability):
    """
    Represents a capability and holds the possible numeric values of a capability.

    When cast to a string, this class returns user facing names for capabilities.
    """

    def __str__(self):
        return UserFacingCapability.capability_to_name(self.capability)

    # override the function used to generate the string representation of the capability.
    @staticmethod
    def capability_to_name(capability) -> str:
        capability_map = {
            Capability.NoCapability: "NoCapability",
            Capability.AllowTestKey: "AllowTestKeySignedSoftware",
            Capability.EnablePlutonDebug: "EnablePlutonDebugging",
            Capability.EnableHlosCoreDebug: "EnableA7Debugging",
            Capability.EnableN9Debug: "EnableN9Debugging",
            # 5 - 7 are no longer used in the current implementation
            5: "EnableA7GdbDebugging",
            6: "EnableIoM41Debugging",
            7: "EnableIoM42Debugging",
            Capability.EnableHlosCoreConsole: "EnableA7Console",
            Capability.EnableSltLoader: "EnableSltLoader",
            Capability.EnableSystemSoftwareDevelopment: "EnableSystemSoftwareDevelopment",
            Capability.EnableCustomerAppDevelopment: "EnableAppDevelopment",
            Capability.EnableRfTestMode: "EnableRfTestMode",
            Capability.UnlockGatewayD: "EnableFieldServicing",
        }
        return capability_map.get(capability, "UnknownCapability")


class CapabilitiesSection(MetadataSection):
    """
    A capability file contains:
    # uint32_t magic 0x5CFD5CFD
    # uint32_t version
    # uint32_t data_length
    # bytes[64] device_id
    # bytes[64] capabilities
    """

    def __init__(self, data):
        super().__init__("Capabilities", None, data)
        if data is not None:
            self.deserialize(data)
        else:
            self.magic_value = 0
            self.version = 0
            self.data_length = 0
            self.device_id = [0] * 64
            self.capabilities_raw = [0] * 64

    @staticmethod
    def size():
        """
        Returns the size of the capabilities section in bytes.
        """
        return 136

    @property
    def capabilities(self):
        """
        Returns a list of capabilities.
        """
        return [capability for capability in self.capabilities_raw if capability != 0]

    @capabilities.setter
    def capabilities(self, value: bytearray):
        """
        Sets the capabilities using the provided bytearray.
        Each index in the bytearray represents a capability.
        """
        for idx, v in enumerate(value):
            self.capabilities_raw[idx] = v

    def deserialize(self, data: bytearray):
        """
        Given a bytearray, deserialize the data into properties
        """
        self.magic_value = struct.unpack_from("<I", data, 0)[0]
        self.version = struct.unpack_from("<I", data, 4)[0]
        self.data_length = struct.unpack_from("<I", data, 8)[0]
        self.device_id_raw = bytearray(data[12:76])
        self.device_id = self.device_id_raw.hex()
        self.capabilities_raw = data[76:140]

        if self.magic_value != 0x5CFD5CFD:
            raise ImageMetadataDeserializationError(
                "CapabilityStructure magic is not correct"
            )

    def serialize(self) -> bytes:
        """
        Serializes the data into a bytearray.
        """
        data = bytearray(self.size())
        struct.pack_into("<I", data, 0, self.magic_value)
        struct.pack_into("<I", data, 4, self.version)
        struct.pack_into("<I", data, 8, self.data_length)
        data[12:76] = self.device_id_raw
        data[76:140] = self.capabilities_raw
        return data

    def __str__(self):
        out_lines = []
        out_lines.append("Capability Data:")
        out_lines.append(f"\tMagic: {self.magic_value}")
        out_lines.append(f"\tMetadata Version: {self.version}")
        out_lines.append(f"\tLength: {self.data_length}")
        out_lines.append(f"\tDevice ID: {self.device_id}")
        out_lines.append("\tCapabilities:")
        for capability in self.capabilities:
            cap = Capability(capability)
            out_lines.append(f"\t\t{cap}")
        return "\n".join(out_lines)
