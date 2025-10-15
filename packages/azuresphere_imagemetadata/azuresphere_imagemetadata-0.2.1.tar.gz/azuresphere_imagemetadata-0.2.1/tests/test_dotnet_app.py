# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for license information.
# --------------------------------------------------------------------------------------------

import pytest


def test_incorrect_path_fails(test_runner, test_logger):
    logger = test_logger()
    logger.info("Beginning test_incorrect_path_fails")

    with pytest.raises(Exception):
        test_runner.py_dotnet_diff_metadata("incorrect_path")

    logger.info("Finishing test_incorrect_path_fails")
