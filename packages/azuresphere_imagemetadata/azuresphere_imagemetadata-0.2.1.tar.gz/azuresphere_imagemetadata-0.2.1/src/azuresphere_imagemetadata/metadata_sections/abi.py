# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
The ABI depends/provides list software dependencies/requirements of a given image.
"""

from .metadata_id import MetadataSectionId
from .metadata import MetadataSection
import struct
from typing import List


class ABIDependsType:
    """
    The type of dependency.
    """

    NoDependency = 0
    SecureWorldRuntime = 1
    OSRuntime = 2
    ApplicationRuntime = 3


class ABIIdentity:
    """
    ABI Identity wraps the AbiDependsType.
    It provides deserialisation and stringification.
    """

    # uint32_t version
    # uint32_t type

    def __init__(self, data):
        self.deserialize(data)

    @staticmethod
    def size():
        """
        The size of the ABI Identity in bytes.
        """
        return 8

    def deserialize(self, data):
        """
        Deserialise the ABI Identity member properties from the given data.
        """
        self.raw_bytes = data
        self.version = struct.unpack_from("<I", data, 0)[0]
        self.type = struct.unpack_from("<I", data, 4)[0]

    def serialize(self):
        return struct.pack("<II", self.version, self.type)

    def get_type_name(self):
        """
        Get the stringified name of the ABI Identity type.
        """
        if self.type == ABIDependsType.NoDependency:
            return "NoDependency"
        elif self.type == ABIDependsType.SecureWorldRuntime:
            return "SecureWorldRuntime"
        elif self.type == ABIDependsType.OSRuntime:
            return "OSRuntime"
        elif self.type == ABIDependsType.ApplicationRuntime:
            return "ApplicationRuntime"
        else:
            raise TypeError("Unknown AbiDependsIdentity type: %d" % (self.type))

    def __str__(self):
        return f"{self.get_type_name()}@{self.version}"


class ABISection(MetadataSection):
    """
    The superclass of ABIProvides/ABIDepends.
    It provides functionality common to both.
    """

    versions: List[ABIIdentity]
    version_count: int

    def __init__(self, name, section_id, data):
        super().__init__(name, section_id, data)
        if data is not None:
            self.deserialize(data)
        else:
            self.version_count = 0
            self.versions = []

    @staticmethod
    def size():
        """
        The size of the ABI section in bytes.
        """
        return 4

    def deserialize(self, data):
        """
        Deserialise the ABI section member properties from the given data.
        """
        self.version_count = struct.unpack_from("<I", data, 0)[0]
        self.versions = []
        offset = 4
        for _ in range(self.version_count):
            self.versions += [ABIIdentity(data[offset : offset + ABIIdentity.size()])]
            offset += ABIIdentity.size()

    def serialize(self):
        """
        Serialise the ABI section member properties.
        """
        out = struct.pack("<I", len(self.versions))
        for v in self.versions:
            out += v.serialize()
        return out

    def _to_string(self, prefix):
        """
        Helper function to stringify the ABI section.
        """
        out_lines = []
        for v in self.versions:
            out_lines.append(f"{prefix}{v}")
        return "\n".join(out_lines)


class ABIProvidesSection(ABISection):
    """
    The ABI Provides section lists any binary dependencies that the image
    provides.
    """

    def __init__(self, data=None):
        super().__init__("ABI Provides", MetadataSectionId.ABIProvides, data)

    def __str__(self):
        return self._to_string("Provides:          ")


class ABIDependsSection(ABISection):
    """
    The ABI Depends section lists any binary dependencies that the image
    requires.
    """

    def __init__(self, data=None):
        super().__init__("ABI Depends", MetadataSectionId.ABIDepends, data)

    def __str__(self):
        return self._to_string("Depends:           ")
