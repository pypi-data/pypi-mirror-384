# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

IMAGEPACKAGE_PATH = os.path.join(
    ".", "tests", "test_files", "applications", "HelloWorld_HighLevelApp.imagepackage"
)


def test_application_parser(test_runner, test_logger):
    logger = test_logger()
    logger.info("Beginning test_application_parser")
    test_runner.py_dotnet_diff_metadata(IMAGEPACKAGE_PATH)
    logger.info("Finishing test_application_parser")
