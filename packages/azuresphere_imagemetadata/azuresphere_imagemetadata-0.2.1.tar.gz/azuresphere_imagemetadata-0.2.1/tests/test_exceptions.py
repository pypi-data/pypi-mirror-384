"""Test that the custom exceptions are raised as expected."""
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for license information.
# --------------------------------------------------------------------------------------------

from unittest.mock import MagicMock
import pytest
from pytest_mock import MockFixture

from contextlib import nullcontext as does_not_raise
from azuresphere_imagemetadata.exceptions import (
    ImageMetadataConversionError,
    ImageMetadataDeserializationError,
    ImageMetadataConversionError
)

from azuresphere_imagemetadata.metadata_headers.image_metadata import ImageMetadataHeader
from azuresphere_imagemetadata.metadata_sections.internal.capabilities import CapabilitiesSection
from azuresphere_imagemetadata.metadata_sections.utils import (
    class_from_section_id,
    MetadataSectionId
)
from azuresphere_imagemetadata.image_metadata import ImageMetadata
from azuresphere_imagemetadata.image import Image


@pytest.fixture
def mocked_struct_unpack_magic_value(request: pytest.FixtureRequest):
    """Fixture to return an unpacked value  from struct.unpack_from.
    The expected parameter is the magic value to be returned.
    """
    magic = request.param
    return [magic]


def test__exception_raises__image_metadata_deserialize():
    """Test that the exceptions are appropriately raised when the image metadata is invalid."""

    with pytest.raises(ImageMetadataDeserializationError):
        ImageMetadata(b"invalid-bytes")

@pytest.mark.parametrize(
    "expectation, valid_signature, image_metadata_side_effect",
    [
        (pytest.raises(ImageMetadataDeserializationError, match="Invalid metadata"), False, [None,ImageMetadataDeserializationError("Invalid metadata")]),
        (does_not_raise(), True, None),
    ],
    ids = [
        "invalid-metadata",
        "good-metadata"
    ]
)
def test__exception_raises__image_deserialize(mocker: MockFixture, valid_signature, image_metadata_side_effect, expectation):
    """Test that the exceptions are appropriately raised when the image is invalid.
    """
    input_data = b"ImageMETADATAsignature"

    # Mock the image metadata object
    metadata = MagicMock(
        start_of_metadata = 5,
        end_of_metadata = 13,
        signature_size = len("signature") if valid_signature else 1
    )
    mocker.patch("azuresphere_imagemetadata.image.ImageMetadata",
        return_value=metadata,
        side_effect = image_metadata_side_effect
    )

    with expectation:
        Image(input_data)

@pytest.mark.parametrize(
    "expectation, section_id",
    [
        (does_not_raise(), MetadataSectionId.Undefined),
        (does_not_raise(), MetadataSectionId.Revocation),
        (pytest.raises(ImageMetadataConversionError), None),

    ],
    ids = [
        "undefined",
        "revocation", # represents any valid section id
        "unknown"
    ]
)
def test__exception_raises__class_from_section_id(expectation, section_id):
    """Test that the class_from_section_id function returns the correct class based on the section id."""
    with expectation:
        class_from_section_id(section_id)

@pytest.mark.parametrize(
    "expectation, magic_value",
    [
        (pytest.raises(ImageMetadataDeserializationError), 0x0),
        (does_not_raise(), ImageMetadataHeader.CorrectMagicValue),
    ],
    ids = [
        "raises",
        "does_not_raise"
    ]
)
def test__exception_raises__imagemetadata_header_deserialize(mocker: MockFixture, expectation, magic_value):

    mocker.patch("azuresphere_imagemetadata.metadata_headers.image_metadata.struct.unpack_from",
        return_value = [magic_value]
    )

    with expectation:
        ImageMetadataHeader(b"INPUT_DATA")

@pytest.mark.parametrize(
    "expectation, magic_value",
    [
        (pytest.raises(ImageMetadataDeserializationError), 0x0),
        (does_not_raise(), 0x5CFD5CFD),
    ],
    ids = [ "raises", "does_not_raise"]
)
def test__exception_raises__capabilities_section_deserialize(mocker: MockFixture, expectation, magic_value):

    mocker.patch("azuresphere_imagemetadata.metadata_sections.internal.capabilities.struct.unpack_from", return_value = [magic_value])

    input_data = "__".join(["LONG_STRING_INPUT_DATA" for _ in range(10)])
    with expectation:
        CapabilitiesSection(input_data.encode())
