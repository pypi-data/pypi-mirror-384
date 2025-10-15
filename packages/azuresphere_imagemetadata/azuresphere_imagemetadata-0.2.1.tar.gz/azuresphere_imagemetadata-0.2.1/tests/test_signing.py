# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from azuresphere_imagemetadata.image import Image
from azuresphere_imagemetadata.metadata_sections.metadata_id import MetadataSectionId
from azuresphere_imagemetadata.metadata_sections import SignatureSection
from azuresphere_imagemetadata.signing.der_encoded import DEREncodedSignature
from azuresphere_imagemetadata.signing.signer import SigningType
from azuresphere_imagemetadata.signing.app_development import AppDevelopmentSigner
from hashlib import sha256
from pathlib import Path
import pytest

from contextlib import ExitStack as does_not_raise

IMAGEPACKAGE_PATH = Path.cwd() / "tests" / "test_files" / "applications" / "HelloWorld_HighLevelApp.imagepackage"


def test_der_encoding_signature(test_logger):
    logger = test_logger()
    logger.info("Beginning test_der_encoding_signature")
    image = Image(IMAGEPACKAGE_PATH.read_bytes())
    signature = image.signature

    der_encoded = DEREncodedSignature.from_stored_signature(signature)
    assert (
        der_encoded.hex()
        == "3045022034927c117b091bee37409056f2751ebe355fa0d4487ae38ffa6539f5b6be40d5022100f3ad9cfd1f44ad5c1a9efbaf79e06b17d051470acd3d21d5d8f7eeda7a1c814c"
    )

    decoded = DEREncodedSignature.to_stored_signature(der_encoded)
    assert decoded == signature
    logger.info("Finishing test_der_encoding_signature")


def test_signing_thumbprint_matches(test_logger):
    logger = test_logger()
    logger.info("Beginning test_signing_thumbprint_matches")

    image = Image(IMAGEPACKAGE_PATH.read_bytes())

    assert image.metadata.signature is not None

    app_development_signer = AppDevelopmentSigner()

    assert (
        image.metadata.signature.signing_cert_thumbprint.hex()
        == app_development_signer.thumbprint()
    )

    logger.info("Finishing test_signing_thumbprint_matches")


def test_package_signature_verifiable(test_logger):
    logger = test_logger()
    logger.info("Beginning test_package_signature_verifiable")

    image = Image(IMAGEPACKAGE_PATH.read_bytes())

    assert image.metadata.signature is not None

    assert image.has_valid_signature()

    logger.info("Finishing test_package_signature_verifiable")


def test_new_package_signature_verifiable(test_logger, tmp_path):
    logger = test_logger()
    logger.info("Beginning test_new_package_signature_verifiable")
    new_file_loc = tmp_path / "im.out"

    image = Image(IMAGEPACKAGE_PATH.read_bytes())

    # checks that "rewriting" the file results in a valid image
    image = Image(image.serialize())
    assert image.has_valid_signature()

    logger.info("Finishing test_new_package_signature_verifiable")

def test_new_package_has_matching_signature_metadata(test_logger):
    logger = test_logger()
    logger.info("Beginning test_new_package_has_signature_metadata")

    image = Image(IMAGEPACKAGE_PATH.read_bytes())

    orig_sig_sec = image.metadata.signature
    orig_der_sig = image.signature
    assert orig_sig_sec is not None
    assert orig_der_sig is not None
    assert len(orig_der_sig) in [64, 96]


    image = Image(image.serialize())
    new_sig_sec = image.metadata.signature
    new_der_sig = image.signature

    assert new_der_sig != orig_der_sig
    assert new_sig_sec.signing_cert_thumbprint == orig_sig_sec.signing_cert_thumbprint

    assert image.has_valid_signature()
    logger.info("Finishing test_new_package_has_signature_metadata")

@pytest.mark.parametrize("known_signers, result",
    [
        ([AppDevelopmentSigner()], (AppDevelopmentSigner(), SigningType.ECDsa256)),
        ([], (None, None))
    ],
    ids= [
        "valid_signer",
        "no_signer"
    ]
)
def test_signer_resolves(test_logger, known_signers, result):
    logger = test_logger()
    logger.info("Beginning test_signer_resolves")

    image = Image(IMAGEPACKAGE_PATH.read_bytes())

    signer, signing_type = image.resolve_signer_and_type(known_signers=known_signers)
    expected_signer, expected_signing_type = result
    assert type(signer) == type(expected_signer)
    assert signing_type == expected_signing_type


@pytest.mark.parametrize("metadata_bytes, expectation",
    [
        (IMAGEPACKAGE_PATH.read_bytes(), does_not_raise()),
        (Image(IMAGEPACKAGE_PATH.read_bytes()).serialize(), does_not_raise()),
        (IMAGEPACKAGE_PATH.read_bytes()[:-DEREncodedSignature.size()] + bytearray(64), pytest.raises(Exception, match="Image signature is not valid")),
        (Image(IMAGEPACKAGE_PATH.read_bytes()).serialize(include_signature=False), pytest.raises(Exception, match="No metadata found in image."))
    ],
    ids= [
        "original_file",
        "new_signature",
        "invalid_signature",
        "no_signature"
    ]
)
def test_dotnet_can_parse_signed_images(test_logger, dotnet_runner, tmp_path, metadata_bytes, expectation):
    logger = test_logger()
    logger.info("Beginning test_signer_resolves")

    runner = dotnet_runner()

    written_img = tmp_path / "img.out"

    written_img.write_bytes(metadata_bytes)

    with expectation:
        logger.info(runner.run("metadata_with_signature", str(written_img)))