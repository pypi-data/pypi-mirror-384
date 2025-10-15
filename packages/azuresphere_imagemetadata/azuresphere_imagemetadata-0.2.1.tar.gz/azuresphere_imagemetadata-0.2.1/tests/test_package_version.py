# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for license information.
# --------------------------------------------------------------------------------------------

import azuresphere_imagemetadata


def test_built_package_toml_versions_match():
    version = azuresphere_imagemetadata.__version__
    with open("pyproject.toml", "r") as f:
        toml = f.read()
        assert f'version = "{version}"' in toml
