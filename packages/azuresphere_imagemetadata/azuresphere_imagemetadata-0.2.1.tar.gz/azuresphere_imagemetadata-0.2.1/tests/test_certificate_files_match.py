# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for license information.
# --------------------------------------------------------------------------------------------

import filecmp
import os


def test_certificate_file_contents(test_logger):
    logger = test_logger()
    logger.info("Beginning test_certificate_file_contents")

    pfx_path = os.path.join(
        ".", "src", "azuresphere_imagemetadata", "certificates", "app_test_sign.pfx"
    )
    pfx_dotnet_path = os.path.join(".", "exp23-tools", "keys", "app_test_sign.pfx")
    assert filecmp.cmp(pfx_path, pfx_dotnet_path, shallow=False)

    cert_path = os.path.join(
        ".", "src", "azuresphere_imagemetadata", "certificates", "tp_app_test_sign.cer"
    )
    cert_dotnet_path = os.path.join(".", "exp23-tools", "keys", "tp_app_test_sign.cer")
    assert filecmp.cmp(cert_path, cert_dotnet_path, shallow=False)

    logger.info("Finishing test_certificate_file_contents")
