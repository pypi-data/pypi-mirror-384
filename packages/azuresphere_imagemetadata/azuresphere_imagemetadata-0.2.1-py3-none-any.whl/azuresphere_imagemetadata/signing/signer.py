# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Previously called "AppTestKeyResolver" in C# code, this class is used to sign applications for development.
"""

from hashlib import sha256, sha384
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.primitives.asymmetric import ec, utils
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.exceptions import InvalidSignature
from dataclasses import dataclass
from typing import Optional
from ..metadata_sections.signature import SigningType


@dataclass
class SigningMap:
    ctp: Optional[x509.Certificate] = None
    ecdsa_256: Optional[pkcs12.PKCS12KeyAndCertificates] = None
    ecdsa_384: Optional[pkcs12.PKCS12KeyAndCertificates] = None


class Signer:
    """
    Uses the certificates in the ./certificates folder to sign applications for development.
    """

    def __init__(self, map: SigningMap):
        self.signing_map = map

    def _retrieve_signing_cert(
        self, signing_type: SigningType
    ) -> pkcs12.PKCS12KeyAndCertificates:
        cert = None
        if signing_type == SigningType.ECDsa256:
            cert = self.signing_map.ecdsa_256
        elif signing_type == SigningType.ECDsa384:
            cert = self.signing_map.ecdsa_384

        return cert

    def thumbprint(self, signing_type: SigningType = SigningType.ECDsa256) -> str:
        """
        returns the thumbprint for the given signing type.
        """
        signing_cert = self._retrieve_signing_cert(signing_type)

        if signing_cert is None:
            raise ValueError("Signing certificate not found")

        return signing_cert.cert.certificate.fingerprint(hashes.SHA1()).hex()

    def sign_data(
        self, data: bytes, signing_type: SigningType = SigningType.ECDsa256
    ) -> bytes:
        """
        signs the provided data using the app development certificate
        use the "new"? certificate by default.

        returns the DER encoded signature.
        """
        signing_cert = self._retrieve_signing_cert(signing_type)

        if signing_cert is None:
            raise ValueError("Signing certificate not found for signing type")

        return signing_cert.key.sign(
            (
                sha256(data).digest()
                if signing_type == SigningType.ECDsa256
                else sha384(data).digest()
            ),
            ec.ECDSA(
                utils.Prehashed(
                    hashes.SHA256()
                    if signing_type == SigningType.ECDsa256
                    else hashes.SHA384()
                )
            ),
        )

    def verify(
        self,
        stored_signature: bytes,
        computed_hash: bytes,
        signing_type: SigningType = SigningType.ECDsa256,
    ) -> bool:
        """
        verifies the provided hash using the app development certificates.
        """

        signing_cert = self._retrieve_signing_cert(signing_type)

        if signing_cert is None:
            return False

        cert = signing_cert.cert.certificate

        try:
            cert.public_key().verify(
                stored_signature,
                computed_hash,
                ec.ECDSA(
                    utils.Prehashed(
                        hashes.SHA256()
                        if signing_type == SigningType.ECDsa256
                        else hashes.SHA384()
                    )
                ),
            )
            return True
        except InvalidSignature as e:
            # if here, the signature failed to validate - continue to try ctp
            pass

        ctp_cert = self.signing_map.ctp

        if ctp_cert is None:
            return False

        try:
            ctp_cert.public_key().verify(
                stored_signature,
                computed_hash,
                ec.ECDSA(utils.Prehashed(hashes.SHA256())),
            )
            return True
        except (InvalidSignature, ValueError) as e:
            # if here, all expected signatures failed to validate - return false
            return False
