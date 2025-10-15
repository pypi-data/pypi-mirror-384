# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for license information.
# --------------------------------------------------------------------------------------------

from .exceptions import (
    ImageMetadataDeserializationError,
    ImageMetadataSerializationError,
)
from .image_metadata import ImageMetadata
from .metadata_sections.identity import ImageType
from .metadata_sections import SignatureSection
from .signing.app_development import AppDevelopmentSigner
from .signing.der_encoded import DEREncodedSignature
from .signing.signer import SigningType, Signer
from hashlib import sha256, sha384
from typing import Optional, List, Tuple
from .metadata_sections.compression import CompressionType
from copy import copy, deepcopy

_KNOWN_SIGNERS = [AppDevelopmentSigner()]


class ImageCompressorDecompressor:
    def __init__():
        pass

    def compress(
        self,
        data: bytearray,
        # default to invalid compression type
        compression_type: CompressionType = CompressionType(None),
    ) -> bytearray:
        raise NotImplementedError(
            "Compress is not implemented in this class. Please subclass and implement compress/decompress"
        )

    def decompress(
        self,
        data: bytearray,
        # default to invalid compression type
        compression_type: CompressionType = CompressionType(None),
    ) -> bytearray:
        raise NotImplementedError(
            "Decompress is not implemented in this class. Please subclass and implement compress/decompress"
        )


class Image:
    def __init__(
        self,
        data: Optional[bytearray] = None,
    ):
        """
        Creates an Image object from the data (if provided).
        @param data: The image data to be deserialized. If None, the object will be created with no data.
        @param compressor: The optional compressor to be used for compressing/decompressing the image data.
                           If compressor is provided, the image will be automatically compressed/decompressed
                           during serialization and deserialization.
        """
        self.signature = None
        self.data = data
        self.metadata = ImageMetadata(None)

        if data is not None:
            self.deserialize(data)

    def _verify_signature(
        self, with_signer: Signer, signing_type: SigningType = SigningType.ECDsa256
    ) -> bool:
        der_encoded = DEREncodedSignature.from_stored_signature(self.signature)

        return with_signer.verify(
            der_encoded,
            (
                # use raw data to check signature as it contains the unmodified image metadata
                sha256(self.data + self.metadata.raw_data).digest()
                if signing_type == SigningType.ECDsa256
                else sha384(self.data + self.metadata.raw_data).digest()
            ),
            signing_type=signing_type,
        )

    def is_compressed_image(self) -> bool:
        """
        Returns True if the image is compressed, False otherwise.
        """
        return self.metadata.compression_info is not None

    def has_valid_signature(self, known_signers: List[Signer] = _KNOWN_SIGNERS) -> bool:
        """
        Iterates over the provided list of signers `known_signers` until the signature is correctly verified.

        @returns True if the signature belongs to any of the `known_signers`
        """
        # no signature
        if len(self.signature) == 0:
            return False

        # exhaustive list of signing types
        signing_types = [SigningType.ECDsa256, SigningType.ECDsa384]

        result = False
        for signer in known_signers:
            for signing_type in signing_types:
                result = self._verify_signature(signer, signing_type=signing_type)
                if result:
                    return True

        return result

    def resolve_signer_and_type(
        self, known_signers: List[Signer] = _KNOWN_SIGNERS
    ) -> Tuple[Optional[Signer], Optional[SigningType]]:
        """
        Iterates over the provided list of signers `known_signers` until the signature is correctly verified.

        @returns If matched, returns the matching signer and signing type. Otherwise returns the tuple: None,None
        """
        signature = self.metadata.signature
        INVALID_SIG_RESULT = None, None

        if signature is None:
            return INVALID_SIG_RESULT

        sign_type = signature.signing_type.signing_type

        if sign_type == SigningType.Invalid:
            return INVALID_SIG_RESULT

        for signer in known_signers:
            result = self._verify_signature(signer, signing_type=sign_type)

            if result:
                return signer, sign_type

        return INVALID_SIG_RESULT

    def as_bytes(
        self,
        signer=AppDevelopmentSigner(),
        include_signature=False,
        fixed_size=None,
        signing_type: SigningType = SigningType.ECDsa256,
    ):
        """
        Serializes the current image and metadata to a byte array.

        If `include_signature` is True, the returned bytes will have a signature appended and the SignatureSection within the metadata
        will be rewritten per the provided `signer` and `signing_type`.

        If `include_signature` is False, the current metadata and image data will be returned without a signature. This output cannot be
        parsed again by this library as metadata is only valid with a signature.
        """
        new_metadata = deepcopy(self.metadata)

        if include_signature:
            new_metadata.remove_section(new_metadata.signature)

            # add a new signature metadata section from the provided signer
            new_sig_metadata = SignatureSection()
            new_sig_type = SigningType(None)

            new_sig_metadata.signing_cert_thumbprint = bytes.fromhex(
                signer.thumbprint(signing_type=signing_type)
            )

            new_sig_type.signing_type = signing_type
            new_sig_metadata.signing_type = new_sig_type

            new_metadata.add_section(new_sig_metadata)

        new_data = copy(self.data)

        # Pad the data to a multiple of 4 bytes
        if len(new_data) % 4 != 0:
            new_data += b"\0" * (4 - len(new_data) % 4)

        # 1BL special case when metadata does not specify fixed size, leave space for info structure
        # This will be the case of older 1BLs that did not have fixed size in their metadata
        if (
            fixed_size is None
            and new_metadata.identity is not None
            and new_metadata.identity.image_type == ImageType.OneBL
        ):
            fixed_size = 16 * 1024

        metadata_bytes = new_metadata.serialize()

        total_size = len(new_data) + len(metadata_bytes)

        # add the default signature size
        # note: as far can be determined, the only signature size in use is 64 bytes
        total_size += DEREncodedSignature.size() if include_signature else 0

        # if fixed_size is provided, then the file size must match the provided size.
        # the total file size is: data + padding + metadata + signature
        # if the fixed size is smaller than the total size, then an exception is thrown
        padding = b""
        if fixed_size is not None:
            if fixed_size < total_size:
                raise ImageMetadataSerializationError(
                    "Fixed size is smaller than the current file size. Will not shrink file content."
                )
            else:
                padding += b"\0" * (fixed_size - total_size)

        if include_signature:
            self.signature = DEREncodedSignature.to_stored_signature(
                # sign the uncompressed data
                signer.sign_data(
                    new_data + padding + metadata_bytes, signing_type=signing_type
                )
            )
        else:
            self.signature = b""

        return new_data + padding + metadata_bytes + self.signature

    def deserialize(self, data):
        self.metadata = ImageMetadata(data)
        self.signature = data[-self.metadata.signature_size :]
        self.data = data[: self.metadata.start_of_metadata]

    def serialize(
        self,
        signer=AppDevelopmentSigner(),
        include_signature=True,
        fixed_size=None,
        signing_type: SigningType = SigningType.ECDsa256,
    ):
        return self.as_bytes(
            signer, include_signature, fixed_size, signing_type=signing_type
        )


class CompressedImage:
    """
    A compressed image is an image that has been compressed using a compressor.
    It is a subclass of the Image class and provides additional functionality for compressing and decompressing the image data.
    """

    def __init__(self, data: bytearray, compressor: ImageCompressorDecompressor):
        self.compressor = compressor
        self._outer = Image(data)

        if self._outer.metadata.compression_info is None:
            raise ValueError("Image does not have a compression section!")

        self._inner = Image(self._decompress(self._outer.data))

    @property
    def outer(self) -> Image:
        """
        Returns the outer Image, which wraps a compressed image.

        @note there should be no need to interface with the outer image directly, unless trying to validate the outer image signature.
        """
        return self._outer

    @property
    def metadata(self) -> ImageMetadata:
        """
        Returns the metadata of the inner Image.
        """
        return self._inner.metadata

    @property
    def data(self) -> bytearray:
        """
        Returns the data of the inner Image.
        """
        return self._inner.data

    @property
    def signature(self) -> bytearray:
        """
        Returns the signature of the inner Image.
        """
        return self._inner.signature

    def is_compressed_image(self) -> bool:
        """
        Returns True if the Inner image is compressed, False otherwise.
        """
        return self._inner.is_compressed_image()

    def has_valid_signature(self, known_signers: List[Signer] = _KNOWN_SIGNERS) -> bool:
        """
        Iterates over the provided list of signers `known_signers` until the signature for the CompressedImage is correctly verified.

        @note this will not validate the outer image signature, only the "inner" compressed signature.
              The outer image can be accessed via the `outer` property.

        @returns True if the signature belongs to any of the `known_signers`
        """
        return self._inner.has_valid_signature(known_signers=known_signers)

    def resolve_signer_and_type(
        self, known_signers: List[Signer] = _KNOWN_SIGNERS
    ) -> Tuple[Optional[Signer], Optional[SigningType]]:
        """
        Iterates over the provided list of signers `known_signers` until the signature is correctly verified.

        @note this will not resolve the outer image signer and signing type, only the "inner" compressed signer and type.
              The outer image can be accessed via the `outer` property.

        @returns If matched, returns the matching signer and signing type. Otherwise returns the tuple: None,None
        """
        return self._inner.resolve_signer_and_type(known_signers=known_signers)

    def serialize(
        self,
        signer=AppDevelopmentSigner(),
        include_signature=True,
        fixed_size=None,
        signing_type: SigningType = SigningType.ECDsa256,
    ):
        # base new compression info off of previous settings
        comp_info = self._outer.metadata.compression_info

        from copy import deepcopy

        self._outer.metadata = deepcopy(self._inner.metadata)

        inner_signer, inner_signing_type = self._inner.resolve_signer_and_type(
            known_signers=_KNOWN_SIGNERS + [signer]
        )

        # if the inner image signer is not known, then use the provided signer
        if inner_signer is None:
            inner_signer = signer
            inner_signing_type = signing_type

        new_data = self._inner.serialize(
            inner_signer,
            include_signature,
            signing_type=(
                inner_signing_type
                if inner_signing_type is not None
                else SigningType.ECDsa256
            ),
        )
        comp_info.uncompressed_size = len(new_data)

        self._outer.metadata.add_section(comp_info)

        self._outer.data = self._compress(new_data)

        return self._outer.serialize(
            signer, include_signature, fixed_size, signing_type=signing_type
        )

    def _decompress(self, data):
        if self._outer.metadata.identity is None:
            raise ValueError("Provided image does not have an identity section!")

        if self._outer.metadata.compression_info.uncompressed_size <= 0:
            raise ValueError(
                f"Image has invalid uncompressed size: {self._outer.metadata.compression_info.uncompressed_size}"
            )

        decompressed = self.compressor.decompress(
            data, self._outer.metadata.compression_info.compression_type
        )

        if len(decompressed) != self._outer.metadata.compression_info.uncompressed_size:
            raise ValueError(
                f"Decompressed data size does not match uncompressed size: {len(decompressed)} != {self._outer.metadata.compression_info.uncompressed_size}"
            )

        return decompressed

    def _compress(self, data):
        if self._outer.metadata.compression_info is None:
            raise ValueError(
                "Provided image does not have a compression section, cannot compress!"
            )

        if self._outer.metadata.identity is None:
            raise ValueError("Provided image does not have an identity section!")

        if self._outer.metadata.compression_info.uncompressed_size <= 0:
            raise ValueError(
                f"Image has invalid uncompressed size: {self._outer.metadata.compression_info.uncompressed_size}"
            )

        if self._outer.metadata.compression_info.uncompressed_size != len(data):
            raise ValueError(
                f"Image compression info does not match data length: {self._outer.metadata.compression_info.uncompressed_size} != {len(data)}"
            )

        return self.compressor.compress(
            data, self._outer.metadata.compression_info.compression_type
        )
