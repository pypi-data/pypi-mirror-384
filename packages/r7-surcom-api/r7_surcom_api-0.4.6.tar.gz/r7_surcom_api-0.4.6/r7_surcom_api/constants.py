"""
Constants used throughout the project
"""
import os

# --
# General
# --

LOGGER_NAME = "r7_surcom_api_logger"
ENV_LOG_LEVEL = "LOG_LEVEL"
# Pull out optional environment variables regarding timeouts
# Note these can get set in Fission environments via the configmap
# mappings defined in fission.environment.*.yaml (e.g. via 'ingest-configuration' configmap)
CONNECTION_TIMEOUT = int(os.environ.get("CONNECTOR_CONNECTION_TIMEOUT", "30"))
READ_TIMEOUT = int(os.environ.get("CONNECTOR_READ_TIMEOUT", "261"))

# used by HttpAdapter to set defaults when connectors make HTTP
# requests. Note, we use a tuple to declare distinct values for
# a connection timeout as well as a read timeout. The documentation
# for requests suggest making timeouts a multiple of 3.
REQUESTS_TIMEOUT = (CONNECTION_TIMEOUT, READ_TIMEOUT)  # seconds

# ------------------------ #

# --
# CLI
# --

# Map Connector Settings types to Python types
PARAM_TYPE_MAP = {
    "string": str,
    "boolean": bool,
    "integer": int,
    "number": float,
    "array": str,
    "object": dict,
    "json": dict,
}

# Default number of items to fetch when no specific value is provided
# NOTE: its 0 to indicate "all items"
MAX_ITEMS_DEFAULT = 0

# Prefix for environment variables that store Connector Settings
SETTING_ENV_VAR_PREFIX = "SURCOM_SETTING"

# Number of items per file with writing the Function result
UNLOAD_ITEMS_PER_FILE = 100

# ------------------------ #

# --
# Known Keys
# --

USER_LOG_ARG_NAME = '__user_log'
CONTEXT_ARG_NAME = '__context'
HIGH_WATER_MARK = 'high_water_mark'
IMPORT_CONFIGURATION_ITEMS = 'import_configuration_items'
MORE_FLAG_PROP = 'more_flag'
MORE_DATA_PROP = 'more_data'
ITEMS_PROP = 'items'
COMPLETED_PHASES_PROP = '_completed_phases'
SETTINGS_PARAM = "settings"

FUNCTION_KEYWORD_PARAMS = [
    USER_LOG_ARG_NAME,
    CONTEXT_ARG_NAME,
    HIGH_WATER_MARK,
    IMPORT_CONFIGURATION_ITEMS,
    MORE_FLAG_PROP,
    MORE_DATA_PROP,
    ITEMS_PROP,
    COMPLETED_PHASES_PROP
]

# ------------------------ #
