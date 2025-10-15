"""
Methods in here are for use in any Connector

Usage:
    from r7_surcom_api import utils
    ...
    verify = utils.str_to_bool('False')

"""


def str_to_bool(value, default: bool = False) -> bool:
    """
    Convert value to either a ``True`` or ``False`` boolean.
    If the value is "empty", return the default.

    Returns ``False`` if ``value`` is anything
    other than: ``'1', 'true', 'yes' or 'on'``

    :param value: the value to convert
    :type value: str
    :return: ``True`` or ``False``
    :rtype: bool
    """
    value = str(value).lower().strip()
    if value in ('1', 'true', 't', 'yes', 'y', 'on'):
        return True
    if value in ('0', 'false', 'f', 'no', 'n', 'off'):
        return False
    return default
