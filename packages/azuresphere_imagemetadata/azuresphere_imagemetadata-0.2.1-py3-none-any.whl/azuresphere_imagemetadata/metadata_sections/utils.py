# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
metadata utility functions to retrieve a name from a section id and to retrieve a class from a section id.
"""

from ..exceptions import ImageMetadataConversionError
from .metadata_id import MetadataSectionId
from .metadata import MetadataSection
from .abi import ABIDependsSection, ABIProvidesSection
from .compression import CompressionSection
from .debug import DebugSection
from .identity import IdentitySection
from .image_policy import ImagePolicySection
from .required_offset import RequiredOffsetSection
from .revocation import RevocationSection
from .signature import SignatureSection
from .temporary_image import TempImageMetadataSection
from .not_implemented import NotImplementedSection


def name_from_section_id(section_id: MetadataSectionId) -> str:
    """
    Returns the name of the section from the section id.
    """
    if section_id == MetadataSectionId.Undefined:
        return "Undefined"
    elif section_id == MetadataSectionId.LegacyABIDepends:
        return "LegacyABIDepends"
    elif section_id == MetadataSectionId.LegacyABIProvides:
        return "LegacyABIProvides"
    elif section_id == MetadataSectionId.ABIDepends:
        return "ABIDepends"
    elif section_id == MetadataSectionId.ABIProvides:
        return "ABIProvides"
    elif section_id == MetadataSectionId.Compression:
        return "Compression"
    elif section_id == MetadataSectionId.Debug:
        return "Debug"
    elif section_id == MetadataSectionId.Legacy:
        return "Legacy"
    elif section_id == MetadataSectionId.Identity:
        return "Identity"
    elif section_id == MetadataSectionId.Revocation:
        return "Revocation"
    elif section_id == MetadataSectionId.Signature:
        return "Signature"
    elif section_id == MetadataSectionId.TemporaryImage:
        return "TemporaryImage"
    elif section_id == MetadataSectionId.RequiredFlashOffset:
        return "RequiredFlashOffset"
    elif section_id == MetadataSectionId.ImagePolicy:
        return "ImagePolicy"
    else:
        return "Unknown"


def class_from_section_id(section_id: MetadataSectionId) -> MetadataSection:
    """
    Metadata section factory that returns the class of the section from the section id.
    """
    if section_id == MetadataSectionId.Undefined:
        return NotImplementedSection
    elif section_id == MetadataSectionId.LegacyABIDepends:
        return NotImplementedSection
    elif section_id == MetadataSectionId.LegacyABIProvides:
        return NotImplementedSection
    elif section_id == MetadataSectionId.ABIDepends:
        return ABIDependsSection
    elif section_id == MetadataSectionId.ABIProvides:
        return ABIProvidesSection
    elif section_id == MetadataSectionId.Compression:
        return CompressionSection
    elif section_id == MetadataSectionId.Debug:
        return DebugSection
    elif section_id == MetadataSectionId.Legacy:
        return NotImplementedSection
    elif section_id == MetadataSectionId.Identity:
        return IdentitySection
    elif section_id == MetadataSectionId.Revocation:
        return RevocationSection
    elif section_id == MetadataSectionId.Signature:
        return SignatureSection
    elif section_id == MetadataSectionId.TemporaryImage:
        return TempImageMetadataSection
    elif section_id == MetadataSectionId.RequiredFlashOffset:
        return RequiredOffsetSection
    elif section_id == MetadataSectionId.ImagePolicy:
        return ImagePolicySection
    else:
        raise ImageMetadataConversionError("Unknown section id: " + str(section_id))
