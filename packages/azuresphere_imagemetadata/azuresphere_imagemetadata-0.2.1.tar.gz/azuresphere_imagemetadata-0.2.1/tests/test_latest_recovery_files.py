# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from shutil import rmtree
from requests import get
from zipfile import ZipFile
from azuresphere_imagemetadata.image import ImageMetadata
from azuresphere_imagemetadata.image_manifest import ImageManifest


_RECOVERY_IMAGES_URL = "https://prod.releases.sphere.azure.net/recovery/mt3620an.zip"
DOWNLOAD_PATH = os.path.join(".", "tests", "test_files", "recovery_images")


def clean_recovery_files_location(dest_path: str):
    if os.path.exists(dest_path):
        rmtree(dest_path)

    os.makedirs(dest_path)


def download_latest_recovery_files(dest_path: str):
    clean_recovery_files_location(dest_path)
    response = get(_RECOVERY_IMAGES_URL, stream=True)
    if response.status_code == 200:
        zip_file_path = os.path.join(dest_path, "latest_recovery_images.zip")
        with open(zip_file_path, "w+b") as f:
            f.write(response.raw.read())
        with ZipFile(zip_file_path) as zf:
            zf.extractall(dest_path)
        os.remove(zip_file_path)


def in_exclusions(diff_output):

    exclusions = [
        # dotnet output does not take into account daylight savings time, so timestamps will be off by an hour at certain times of the year.
        "Built On (Local)",
    ]

    for exclusion in exclusions:
        for line in diff_output:
            if exclusion in line:
                return True

    return False


def test_latest_recovery_files(test_runner, test_logger):
    logger = test_logger()
    logger.info("Beginning test_recovery_files")

    exclusions = [
        # dotnet output does not take into account daylight savings time, so timestamps will be off by an hour at certain times of the year.
        "Built On (Local)",
    ]

    download_latest_recovery_files(DOWNLOAD_PATH)

    for file in os.listdir(DOWNLOAD_PATH):

        full_path = os.path.join(DOWNLOAD_PATH, file)

        if not os.path.isfile(full_path):
            continue

        test_runner.py_dotnet_diff_metadata(full_path, exclusions)

    logger.info("Finishing test_recovery_files")


def test_latest_recovery_manifest(test_logger):
    logger = test_logger()
    logger.info("Beginning test_recovery_manifest")

    download_latest_recovery_files(DOWNLOAD_PATH)

    with open(os.path.join(DOWNLOAD_PATH, "recovery.imagemanifest"), "rb") as f:
        byte_data = f.read()
        metadata = ImageMetadata(byte_data)

        # simply checks if the manifest can be parsed
        # more comprehensive tests are in test_knownset_recovery_files.py
        ImageManifest.from_image_metadata(metadata)

    logger.info("Finishing test_recovery_manifest")
