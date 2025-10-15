"""
This module contains utility functions for the r7_surcom_api package.
"""

import logging
import os
from collections import defaultdict
from itertools import zip_longest

import yaml

from r7_surcom_api import constants

LOG = logging.getLogger(constants.LOGGER_NAME)


def grouper(
    iterable,
    blocksize,
    fillvalue=None
):
    """
    Collect data into fixed-length chunks or blocks.

    :param iterable: An iterable to be grouped into chunks.
    :param blocksize: The number of elements in each chunk.
    :param fillvalue: The value to fill in if the iterable is not evenly divisible by blocksize.

    :return: An iterator that yields tuples containing the grouped elements.
    """
    # TODO: write test
    # Caller should use 'list(filter(None, group))' to strip empty elements from the last chunk.
    if not blocksize:
        return [(iterable)]
    if iterable is None:
        return []
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    # https://docs.python.org/3/library/itertools.html#itertools-recipes
    args = [iter(iterable)] * blocksize
    return zip_longest(*args, fillvalue=fillvalue)


def dict_merge(target: dict, source: dict, merge_arrays: bool = False) -> dict:
    """
    Merge 'source' into 'target', optionally merging array content.

    :param target: The target dictionary to merge into
    :param source: The source dictionary to merge from
    :param merge_arrays: If True, arrays will be merged; if False, arrays will be replaced
    :return: The merged dictionary
    """
    for key, val in source.items():
        if isinstance(target.get(key), dict):
            if isinstance(val, dict):
                dict_merge(target[key], val)
            else:
                # v is not a dictionary, overwrites the target
                target[key] = val
        elif isinstance(target.get(key), list) and merge_arrays:
            if isinstance(val, list):
                target[key].extend(val)
            else:
                # v is not a list, overwrites the target
                target[key] = val
        else:
            # target[k] didn't exist, or is not a dictionary
            target[key] = val
    return target


def dict_is_subset(superset: dict, subset: dict):
    """
    Does the 'superset' dict include all of the 'subset' dict?
    """
    for name, value in subset.items():
        if name not in superset:
            return False

        test = superset[name]
        if isinstance(value, list):
            try:
                if not set(value) <= set(test):
                    return False
            except TypeError:
                # Incomparable, e.g. lists of dicts, let's declare it's ok
                pass
        elif isinstance(value, dict) and isinstance(test, dict):
            if not dict_is_subset(test, value):
                return False
        else:
            if value != test:
                return False
    return True


def find_manifest_file(
    filepath: str
) -> str:
    """
    Find the manifest file in the given filepath or its parent directories.
    The manifest file is expected to be named 'manifest.yaml'.
    If the file is not found, a ValueError is raised with a message indicating the filepath.

    :param filepath: The starting directory to search for the manifest file.
    :type filepath: str
    :return: The path to the manifest file if found.
    :rtype: str
    """
    # TODO: add test
    def _find_up(filepath, filename):
        path = os.path.join(filepath, filename)
        if os.path.isfile(path):
            return path
        if os.path.ismount(filepath):
            return None
        return _find_up(os.path.dirname(filepath), filename)

    msg = f"The manifest file was not found at '{filepath}'."
    filepath = _find_up(filepath, "manifest.yaml")
    if filepath:
        return filepath
    raise ValueError(msg)


def load_yaml(
    filepath: str
) -> dict:
    """
    Load a YAML file and return its content as a dictionary.

    This function checks to see if the `ruamel.yaml` library is installed in the environment.
    If it is, it uses `ruamel.yaml` to load the YAML file to preserve backwards compatibility.

    If its not installed, PyYAML is used as a fallback.

    :param filepath: The path to the YAML file to be loaded.
    :type filepath: str
    :return: A dictionary containing the content of the YAML file.
    :rtype: dict
    """
    # TODO: add test
    # TODO: add test
    ruamel_yaml_is_installed = False
    rtn_value = {}

    try:
        from ruamel.yaml import YAML, representer
        ruamel_yaml_is_installed = True
        LOG.warning("'ruamel.yaml' is installed in this environment so we will use it to "
                    "preserve backwards compatibility. Preferably, use PyYAML instead.")

    except ImportError:
        LOG.debug("'ruamel.yaml' is not installed, loading '%s' with PyYAML.", filepath)

    if ruamel_yaml_is_installed:

        yml = YAML()
        yml.default_flow_style = False
        yml.representer.add_representer(
            defaultdict, representer.Representer.represent_dict
        )

        with open(filepath, "r", encoding="utf-8-sig") as fp:
            rtn_value = yml.load(fp)

    else:
        with open(filepath, "r", encoding="utf-8-sig") as fp:
            rtn_value = yaml.safe_load(fp)

    return rtn_value
