# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
For sections that are not expected to be seen (i.e. legacy data structures before extensible metadata),
the not implemented section is used.
"""

from .metadata_id import MetadataSectionId
from .metadata import MetadataSection


class NotImplementedSection(MetadataSection):
    """
    NotImplementedSection is used for sections that are not expected to be seen.
    """

    def __init__(self, data):
        super().__init__("NotImplemented", MetadataSectionId.Undefined, data)
        self.data = data

    def __str__(self):
        return "NotImplementedSection\n\tdata: %s" % (self.data) + "\n"
