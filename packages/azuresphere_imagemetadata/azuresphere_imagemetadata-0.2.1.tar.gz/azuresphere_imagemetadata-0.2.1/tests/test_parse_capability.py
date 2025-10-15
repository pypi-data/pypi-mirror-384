# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

CAPABILITY_PATH = os.path.join(
    ".", "tests", "test_files", "capabilities", "capability_e7a13771_1.bin"
)


def test_capability_parser_matches(test_runner, test_logger):
    logger = test_logger()
    logger.info("Beginning test_capability_parser_matches")
    test_runner.py_dotnet_diff_metadata(CAPABILITY_PATH)
    logger.info("Finishing test_capability_parser_matches")


def test_capability_content_decodes(test_logger):
    logger = test_logger()
    logger.info("Beginning test_capability_content_decodes")
    from azuresphere_imagemetadata import image_metadata

    with open(CAPABILITY_PATH, "rb") as f:
        capability_data = f.read()
        capability_metadata = image_metadata.ImageMetadata(capability_data)

        debug_section = capability_metadata.sections_by_name("Debug")[0]

        assert debug_section is not None

        assert debug_section.image_name == "fw_config"

        from azuresphere_imagemetadata.metadata_sections.internal.capabilities import (
            CapabilitiesSection,
        )

        capabilities_section = CapabilitiesSection(capability_metadata.image_data)
        assert len(capabilities_section.capabilities) > 0

        logger.info("Finishing test_capability_content_decodes")


def test_user_facing_translation(test_logger):
    """
    This test is to ensure that the user facing translation of capabilities is correct.

    If the mappings change, this test will need to be updated.
    """
    logger = test_logger()
    logger.info("Beginning test_user_facing_translation")

    from azuresphere_imagemetadata.metadata_sections.internal.capabilities import (
        Capability,
        UserFacingCapability,
    )

    std_capability_map = {
        Capability.NoCapability: "NoCapability",
        Capability.AllowTestKey: "AllowTestKey",
        Capability.EnablePlutonDebug: "EnablePlutonDebug",
        Capability.EnableHlosCoreDebug: "EnableHlosCoreDebug",
        Capability.EnableN9Debug: "EnableN9Debug",
        Capability.EnableHlosCoreConsole: "EnableHlosCoreConsole",
        Capability.EnableSltLoader: "EnableSltLoader",
        Capability.EnableSystemSoftwareDevelopment: "EnableSystemSoftwareDevelopment",
        Capability.EnableCustomerAppDevelopment: "EnableCustomerAppDevelopment",
        Capability.EnableRfTestMode: "EnableRfTestMode",
        Capability.UnlockGatewayD: "UnlockGatewayD",
    }

    user_facing_capability_map = {
        Capability.NoCapability: "NoCapability",
        Capability.AllowTestKey: "AllowTestKeySignedSoftware",
        Capability.EnablePlutonDebug: "EnablePlutonDebugging",
        Capability.EnableHlosCoreDebug: "EnableA7Debugging",
        Capability.EnableN9Debug: "EnableN9Debugging",
        5: "EnableA7GdbDebugging",
        6: "EnableIoM41Debugging",
        7: "EnableIoM42Debugging",
        Capability.EnableHlosCoreConsole: "EnableA7Console",
        Capability.EnableSltLoader: "EnableSltLoader",
        Capability.EnableSystemSoftwareDevelopment: "EnableSystemSoftwareDevelopment",
        Capability.EnableCustomerAppDevelopment: "EnableAppDevelopment",
        Capability.EnableRfTestMode: "EnableRfTestMode",
        Capability.UnlockGatewayD: "EnableFieldServicing",
    }

    for capability_value in range(0, Capability.UnlockGatewayD + 1):
        # test non-user facing capabilities
        cap = Capability(capability_value)
        if capability_value in std_capability_map:
            assert str(cap) == std_capability_map[capability_value]
        else:
            assert capability_value >= 5 and capability_value <= 7

        # test user facing capabilities
        user_facing_capability = UserFacingCapability(capability_value)
        assert (
            str(user_facing_capability) == user_facing_capability_map[capability_value]
        )

    logger.info("Finishing test_user_facing_translation")
