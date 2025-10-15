# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from shutil import rmtree
import pytest


def clean_recovery_files_location(dest_path: str):
    if os.path.exists(dest_path):
        rmtree(dest_path)

    os.makedirs(dest_path)


def find_recovery_folders(path: str):
    return [
        os.path.join(path, f)
        for f in os.listdir(path)
        if os.path.isdir(os.path.join(path, f))
    ]


def test_recovery_files(test_runner, test_logger, recovery_images_path):
    # Test to see if all provided recovery files can be parsed
    if not recovery_images_path:
        pytest.skip("No recovery images path specified")

    logger = test_logger()
    logger.info("Beginning test_recovery_files")

    exclusions = [
        # dotnet output does not take into account daylight savings time, so timestamps will be off by an hour at certain times of the year.
        "Built On (Local)",
    ]

    for recovery_folder in find_recovery_folders(recovery_images_path):
        logger.info(f"Processing {recovery_folder}")
        for file in os.listdir(recovery_folder):
            full_path = os.path.join(recovery_folder, file)

            if not os.path.isfile(full_path):
                continue

            test_runner.py_dotnet_diff_metadata(full_path, exclusions)

    logger.info("Finishing test_recovery_files")


def test_recovery_manifest_parsing(test_runner, test_logger, recovery_images_path):
    # Test to see if all provided recovery manifest files can be parsed
    if not recovery_images_path:
        pytest.skip("No recovery images path specified")

    logger = test_logger()
    logger.info("Beginning test_recovery_manifest_parsing")

    for recovery_folder in find_recovery_folders(recovery_images_path):
        test_runner.py_dotnet_diff_manifest(
            os.path.join(recovery_folder, "recovery.imagemanifest")
        )

    logger.info("Finishing test_recovery_manifest_parsing")
