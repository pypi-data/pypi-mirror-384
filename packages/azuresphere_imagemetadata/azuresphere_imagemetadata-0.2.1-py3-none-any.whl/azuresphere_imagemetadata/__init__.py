# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for license information.
# --------------------------------------------------------------------------------------------
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("azuresphere_imagemetadata")
    VERSION = __version__
except PackageNotFoundError:
    # package is not installed
    pass
