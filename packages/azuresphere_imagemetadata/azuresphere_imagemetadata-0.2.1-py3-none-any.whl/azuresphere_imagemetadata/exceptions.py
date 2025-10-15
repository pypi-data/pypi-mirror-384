# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for license information.
# --------------------------------------------------------------------------------------------


class ImageMetadataConversionError(Exception):
    """An error occuring during the conversion of image metadata."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ImageMetadataDeserializationError(ImageMetadataConversionError):
    """An error occuring during the deserialization of image metadata."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ImageMetadataSerializationError(ImageMetadataConversionError):
    """An error occuring during the serialization of image metadata."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
