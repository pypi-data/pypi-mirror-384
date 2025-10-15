
# Copyright (C) 2023-2025 Cognizant Digital Business, Evolutionary AI.
# All Rights Reserved.
# Issued under the Academic Public License.
#
# You can be released from the terms, and requirements of the Academic Public
# License by purchasing a commercial license.
# Purchase of a commercial license is mandatory for any use of the
# neuro-san SDK Software in commercial settings.
#
# END COPYRIGHT

from leaf_common.config.config_filter_chain import ConfigFilterChain

from neuro_san.internals.graph.persistence.manifest_dict_config_filter import ManifestDictConfigFilter
from neuro_san.internals.graph.persistence.manifest_key_config_filter import ManifestKeyConfigFilter
from neuro_san.internals.graph.persistence.served_manifest_config_filter import ServedManifestConfigFilter


class ManifestFilterChain(ConfigFilterChain):
    """
    ConfigFilterChain for manifest files
    """

    def __init__(self, manifest_file: str):
        """
        Constructor

        :param manifest_file: The name of the manifest file we are processing for logging purposes
        """
        super().__init__()

        # Order matters
        self.register(ManifestKeyConfigFilter(manifest_file))
        self.register(ManifestDictConfigFilter(manifest_file))
        self.register(ServedManifestConfigFilter(manifest_file))
