# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
This enum lists all of the possible metadata section IDs.

This enum is used by the MetadataSection class to identify the type of metadata section that is being parsed.
It is also reflectively used when parsing an image to determine which metadata sections are present in the image
and the class that should be invoked on the data.
"""


class MetadataSectionId:
    # /// <summary>
    # /// None / not defined
    # /// </summary>
    Undefined = 0

    # /// <summary>
    # /// 'AD' - Legacy ABI depends info (Processed it as 'unkknown')
    # /// </summary>
    LegacyABIDepends = 0x4441

    # /// <summary>
    # /// 'AP' - Legacy ABI provides info (Processed it as 'unkknown')
    # /// </summary>
    LegacyABIProvides = 0x5041

    # /// <summary>
    # /// 'ND' - ABI depends info
    # /// </summary>
    ABIDepends = 0x444E

    # /// <summary>
    # /// 'NP' - ABI provides info
    # /// </summary>
    ABIProvides = 0x504E

    # /// <summary>
    # /// 'CM' - Compression info
    # /// </summary>
    Compression = 0x4D43

    # /// <summary>
    # /// 'DB' - Debug info
    # /// </summary>
    Debug = 0x4244

    # /// <summary>
    # /// 'LG' - legacy footer format
    # /// </summary>
    Legacy = 0x474C

    # /// <summary>
    # /// 'ID' - Identity info
    # /// </summary>
    Identity = 0x4449

    # /// <summary>
    # /// 'RV' - Revocation info
    # /// </summary>
    Revocation = 0x5652

    # /// <summary>
    # /// 'SG' - signature info
    # /// </summary>
    Signature = 0x4753

    # /// <summary>
    # /// 'TP' Temporary image info
    # /// </summary>
    TemporaryImage = 0x5054

    # /// <summary>
    # /// 'RO' Required offset info
    # /// </summary>
    RequiredFlashOffset = 0x4F52

    # /// <summary>
    # /// 'IP' Image policy info
    # /// </summary>
    ImagePolicy = 0x5049
