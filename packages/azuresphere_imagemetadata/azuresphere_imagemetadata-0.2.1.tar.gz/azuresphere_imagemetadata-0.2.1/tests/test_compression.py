import os
from azuresphere_imagemetadata.image import Image, CompressedImage
from azuresphere_imagemetadata.signing.app_development import AppDevelopmentSigner
from azuresphere_imagemetadata.metadata_sections.compression import CompressionType
from lzma import LZMACompressor, LZMADecompressor, FORMAT_ALONE
from pathlib import Path

COMPRESSED_SAMPLE_APP = os.path.join(
    ".", "tests", "test_files", "compressed", "io-hello-world-update.bin.lzma"
)


class LZMACompressorDecompressor:
    def compress(self, data: bytearray, compression_type: CompressionType) -> bytearray:
        assert compression_type.compression_type == CompressionType.Lzma, (
            "Only LZMA is supported"
        )
        lzma_compressor = LZMACompressor(format=FORMAT_ALONE)
        return lzma_compressor.compress(data) + lzma_compressor.flush()

    def decompress(
        self, data: bytearray, compression_type: CompressionType
    ) -> bytearray:
        assert compression_type.compression_type == CompressionType.Lzma, (
            "Only LZMA is supported"
        )
        lzma_decompressor = LZMADecompressor(format=FORMAT_ALONE)
        return lzma_decompressor.decompress(data)


def test_open_compressed_no_compressor(test_logger):
    logger = test_logger()
    logger.info("Beginning test_open_compressed_no_compressor")

    image = Image(Path(COMPRESSED_SAMPLE_APP).read_bytes())
    assert image.metadata.compression_info is not None
    assert image.is_compressed_image() is True, "Image should be compressed"
    assert image.metadata.compression_info.uncompressed_size != len(image.data), (
        "Uncompressed size should not match compressed size"
    )

    logger.info("Finishing test_open_compressed_no_compressor")


def test_open_compressed_with_compressor_check_compressed(test_logger):
    logger = test_logger()
    logger.info("Beginning test_open_compressed_with_compressor_check_compressed")

    image = CompressedImage(
        Path(COMPRESSED_SAMPLE_APP).read_bytes(),
        compressor=LZMACompressorDecompressor(),
    )
    assert image.is_compressed_image() is False, (
        "Inner image should not be compressed after decompressing"
    )
    assert image.outer.is_compressed_image() is True, "Outer image should be compressed"

    # the inner image is signed with the app dev cert, so we need to check that it is valid
    assert image.has_valid_signature() is True, "Inner image signature is not valid"
    # we cannot equivalently check the outer image signature because it is signed with the sys test, unavailable here
    # we check that the outer image is compressed and has a valid signature in test_compress_modified_image (after signing with app dev cert)

    logger.info("Finishing test_open_compressed_with_compressor_check_compressed")


def test_decompress_compress(test_logger, tmpdir):
    logger = test_logger()
    logger.info("Beginning test_decompress_compress")

    new_name = Path(tmpdir) / "recompressed_app.bin.lzma"

    image = CompressedImage(
        Path(COMPRESSED_SAMPLE_APP).read_bytes(),
        compressor=LZMACompressorDecompressor(),
    )

    uncompressed_size = image.outer.metadata.compression_info.uncompressed_size

    # serialize and reopen the image
    new_name.write_bytes(image.serialize())

    new_image = CompressedImage(
        new_name.read_bytes(), compressor=LZMACompressorDecompressor()
    )

    assert (
        len(new_image.data)
        + len(new_image.metadata.raw_data)
        + new_image.metadata.signature_size
        == uncompressed_size
    ), "Decompressed image size does not match original"
    assert new_image.has_valid_signature() is True, "Inner image signature is not valid"
    assert new_image.outer.has_valid_signature() is True, (
        "Outer image signature is not valid"
    )

    logger.info("Finishing test_decompress_compress")


def test_compress_modified_image(test_logger, tmpdir):
    logger = test_logger()
    logger.info("Beginning test_compress_image_serialize")

    MOCK_NEW_ID = "3b912ace-ecd2-49a5-ab84-9de7521106e9"

    image = Image(Path(COMPRESSED_SAMPLE_APP).read_bytes())

    image = CompressedImage(
        Path(COMPRESSED_SAMPLE_APP).read_bytes(),
        compressor=LZMACompressorDecompressor(),
    )
    assert image.outer.metadata.compression_info is not None
    assert (
        image.outer.metadata.compression_info.uncompressed_size
        == len(image.data)
        + len(image.metadata.raw_data)
        + image.metadata.signature_size
    )

    image.metadata.identity.image_uid = MOCK_NEW_ID
    image.metadata.identity.component_uid = MOCK_NEW_ID

    new_path = Path(tmpdir / "new_app.imgpkg")

    new_path.write_bytes(image.serialize())

    new_image = CompressedImage(
        new_path.read_bytes(), compressor=LZMACompressorDecompressor()
    )

    assert new_image.has_valid_signature() is True, "Inner image signature is not valid"
    # the new image should now be signed with the app dev cert, so we can check that it is valid
    assert new_image.outer.has_valid_signature() is True, (
        "Outer image signature is not valid"
    )

    assert new_image.metadata.identity.image_uid == MOCK_NEW_ID, (
        "Image UID does not match"
    )
    assert new_image.metadata.identity.component_uid == MOCK_NEW_ID, (
        "Component UID does not match"
    )
    assert new_image.outer.metadata.compression_info is not None, (
        "Compression info is None for outer image"
    )
    assert new_image.metadata.compression_info is None, (
        "Compression info is not None for inner image"
    )
    logger.info("Finishing test_compress_image_serialize")
