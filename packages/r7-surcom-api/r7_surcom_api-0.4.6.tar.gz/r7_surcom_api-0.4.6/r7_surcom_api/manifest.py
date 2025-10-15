"""
accessor for the connector manifest
"""

import inspect
import os

from r7_surcom_api import helpers, ref_utils

# TODO: write test for this module


class Manifest:
    """
    Access helper for the connector manifest
    """

    def __init__(self, filepath: str = None):
        # The manifest file should be in the 'filepath' directory, or its parent

        if not filepath:
            # Try to use the location of the caller
            filepath = inspect.stack()[1][1]

        filepath = helpers.find_manifest_file(filepath)
        manifest = helpers.load_yaml(filepath)
        self.path = os.path.basename(filepath)

        # The manifest can use '$ref' references (like OpenAPI/JSONschema)
        # to include common parameters *defined within the same manifest*.
        # Let's resolve those first.
        self.manifest = ref_utils.resolve_internal_refs("<manifest>", manifest)

    @property
    def id(self):
        """
        The connector's id
        """
        return self.get("id")

    @property
    def name(self):
        """
        The connector's names
        """
        return self.get("name")

    @property
    def version(self):
        """
        The connector's version
        """
        return self.get("version")

    @property
    def namespace(self):
        """
        The connector's namespace is everything before the last dot in the id
        """
        return self.get("id").rsplit(".", maxsplit=1)[0]

    def get(self, key):
        """
        Get a value
        """
        return self.manifest.get(key)

    def secrets(self):
        """
        Get secrets declared in the manifest
        """
        yield from list(self.manifest.get("secrets") or {})

    def settings(self):
        """
        Get secrets declared in the manifest
        """
        yield from list(self.manifest.get("settings") or {})

    def functions(self):
        """
        Get functions declared in the manifest
        """
        yield from list(self.manifest.get("functions") or {})

    def get_setting(self, name) -> dict:
        """
        Get a setting by its name. If not found return an
        empty dict
        """
        settings = self.manifest.get("settings", [])

        if not settings:
            return {}

        for s in settings:
            if s.get("name") == name:
                return s

        return {}
