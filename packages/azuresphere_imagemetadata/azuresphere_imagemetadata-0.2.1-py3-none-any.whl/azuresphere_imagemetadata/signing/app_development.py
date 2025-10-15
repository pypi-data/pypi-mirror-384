# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Previously called "AppTestKeyResolver" in C# code, this class is used to sign applications for development.
"""

from cryptography import x509
from cryptography.hazmat.primitives.serialization import pkcs12
from pathlib import Path
import os
from .signer import Signer, SigningMap

PARENT_DIR = Path(__file__).parent.parent


class AppDevelopmentSigner(Signer):
    """
    Uses the certificates in the ./certificates folder to sign applications for development.
    """

    def __init__(self):
        # current working theory is that tp_app_test_sign is for older image packages.
        with open(
            os.path.join(PARENT_DIR, "certificates", "tp_app_test_sign.cer"), "rb"
        ) as f:
            ctp_signing_cert = x509.load_pem_x509_certificate(f.read())

        # app_test_sign.pfx is for newer image packages and should be used by default.
        # code should be able to read signatures signed by either key,
        # but should only sign using app_test_sign.pfx
        with open(
            os.path.join(PARENT_DIR, "certificates", "app_test_sign.pfx"), "rb"
        ) as f:
            test_signing_cert = pkcs12.load_pkcs12(f.read(), None)

        signing_map = SigningMap(ctp=ctp_signing_cert, ecdsa_256=test_signing_cert)

        super().__init__(signing_map)
