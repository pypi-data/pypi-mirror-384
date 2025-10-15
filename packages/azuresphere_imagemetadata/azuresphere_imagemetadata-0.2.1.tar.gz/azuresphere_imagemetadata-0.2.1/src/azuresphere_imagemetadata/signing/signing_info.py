# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
This class returns the hash algorithm and signature size for the given SoC.

This should be considered deprecated given that there are no plans to support hashes other than
sha256, and boards other than the mt3620...
"""

from hashlib import sha256, sha384
from ..metadata_sections.signature import SigningType


class SocType:
    """
    SoC type enum
    """

    mt3620 = 0
    conundrum = 0x1
    conundrumv8 = 0x2
    conundrumr5 = 0x3
    rpi4 = 0x4
    imx7ulp = 0x5
    imx8ulp = 0x6


class SigningInfo:
    """
    A signing factory for the different SoCs that returns the correct
    signature algorithm and metadata.

    The signature is appended to the metadata section at the end of the file.
    Signing is performed over the metadata and image data combined (i.e. from byte 0:end).
    """

    def _signing_info_type(self):
        """
        Returns the signing type for the given SoC
        """
        if self.soc == SocType.mt3620:
            return SigningType.ECDsa256

        if self.soc == SocType.conundrum:
            return SigningType.ECDsa384

        if self.soc == SocType.conundrumv8:
            return SigningType.ECDsa384

        if self.soc == SocType.conundrumr5:
            return SigningType.ECDsa384

        if self.soc == SocType.rpi4:
            return SigningType.ECDsa256

        if self.soc == SocType.imx7ulp:
            return SigningType.ECDsa256

        if self.soc == SocType.imx8ulp:
            return SigningType.ECDsa384

        return SigningType.Invalid

    def __init__(self, soc_type=SocType.mt3620):
        self.soc = soc_type
        self.type = self._signing_info_type()

    def get_signature_size(self):
        """
        Returns the size of the signature in bytes.
        """
        if self.type == SigningType.ECDsa256:
            return 64

        if self.type == SigningType.ECDsa384:
            return 96

        return 64

    def get_hash_algorithm(self):
        """
        Returns the hash algorithm for the given SoC.
        """
        if self.type == SigningType.ECDsa256:
            return sha256

        if self.type == SigningType.ECDsa384:
            return sha384

        raise ValueError("Invalid signing type")
