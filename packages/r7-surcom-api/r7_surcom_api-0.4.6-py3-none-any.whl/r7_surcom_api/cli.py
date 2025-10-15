import argparse
import json
import logging
import os
import sys
from functools import partial

from r7_surcom_api.functions import PythonFunction
from r7_surcom_api.manifest import Manifest
from r7_surcom_api import constants, helpers, utils

# Try get the log level from env variable, default to INFO
log_level = os.getenv(constants.ENV_LOG_LEVEL, "INFO").upper()

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=getattr(logging, log_level))
LOG = logging.getLogger(constants.LOGGER_NAME)


def _write_output_files(items: dict, outdir: str):
    """
    Write 'items' to 'outdir', in files named for each type in the items
    """
    # TODO: add test
    # Check that we can write the output directory (will raise if there's a file not a directory)
    os.makedirs(outdir, exist_ok=True)

    # Scan all the items for type names, then we'll write a file for each type
    typenames = set(map(lambda item: item["type"], items))

    for typename in sorted(typenames):
        # Unload each type to file(s)
        def _this_type(typeid, item):
            return item["type"] == typeid

        page = 0
        for group in helpers.grouper(
            filter(partial(_this_type, typename), items),
            blocksize=constants.UNLOAD_ITEMS_PER_FILE,
        ):
            if page == 0:
                filename = f"{typename}.json"
            else:
                filename = f"{typename}.{page:04}.json"
            page = page + 1

            LOG.info("Writing '%s'", filename)

            # Write in 'sample-data format' (not wrapped in items[]/type+content)
            dump = [item["content"] for item in list(filter(None, group))]

            with open(os.path.join(outdir, filename), "w", encoding="utf-8") as handle:
                json.dump(dump, handle, indent=2)


def _invoke_function(
    fn: PythonFunction,
    args: argparse.Namespace,
    **kwargs
):

    collected_items = []
    i = 1

    if fn.is_test:
        result = fn.userfunc(kwargs.get("user_log"), **kwargs.get("settings"))

        if result.get("status") == "success":
            LOG.info("Test function executed successfully")
        else:
            LOG.error("Test function failed")

        if result.get("message"):
            LOG.info("Message: %s", result.get("message"))

        return

    else:
        for item in fn.userfunc(**kwargs):

            if isinstance(item, dict):
                collected_items.append(item)

            if args.max_items and i >= args.max_items:
                # Stop after the specified number of items
                LOG.info("Reached the max items limit of %d, stopping", args.max_items)
                break

            i += 1

        if collected_items:
            # Write the output to files in the output directory
            _write_output_files(collected_items, outdir=args.results_dir)


def surcom_function_cli(
    path_functions_module: str = None
):
    """
    To use: create a file __main__.py in your package, with:
    ```
        from r7_surcom_api import surcom_function_cli
        if __name__ == "__main__":
            surcom_function_cli()
    ```
    """
    if not path_functions_module:
        path_functions_module = os.path.dirname(sys.modules["__main__"].__file__)

    path_connector = os.path.dirname(path_functions_module)
    manifest_yaml = Manifest(path_connector)

    fns = {}

    for f in manifest_yaml.functions():
        fn = PythonFunction(f, path_functions_module)
        fns.update({fn.id_wo_ns: fn})

    parser = argparse.ArgumentParser(
        description=f"Run a specified function in {manifest_yaml.name}"
    )

    parser.add_argument(
        "fn",
        type=str,
        help="The name of the function to execute",
        choices=[fn.id_wo_ns for _, fn in fns.items()]
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    parser.add_argument(
        "--results-dir",
        type=str,
        default="/app/output",
        help="Directory to write the contents of the types to"
    )

    parser.add_argument(
        "--max-items",
        type=int,
        default=constants.MAX_ITEMS_DEFAULT,
        help="The max number of items to get. Specify 0 to get all items. Defaults to 0"
    )

    # 1. We add an argparse argument for each setting in the manifest
    for s in manifest_yaml.settings():
        s_flag = s.get("name")
        s_type = constants.PARAM_TYPE_MAP.get(s.get("type"))
        s_help = s.get("description") or s.get("title")
        s_default = os.getenv(f"{constants.SETTING_ENV_VAR_PREFIX}_{s_flag.upper()}", s.get("default"))
        s_choices = s.get("enum")

        # NOTE: If the type is a bool, we treat as a string and
        # convert it to a boolean later on down the line
        if s_type is bool:
            s_type = str

        parser.add_argument(
            f"--{s_flag}",
            type=s_type,
            help=s_help,
            default=s_default,
            choices=s_choices
        )

    # 2. Then we parse the args
    args = parser.parse_args()

    if args.verbose:
        LOG.setLevel(logging.DEBUG)

    settings_dict = {}

    # 3. For each setting, we get its value from args
    for s in manifest_yaml.settings():
        arg_value = getattr(args, s.get("name"))

        if s.get("type") == "boolean":
            # Convert boolean strings to actual booleans
            arg_value = utils.str_to_bool(arg_value, default=s.get("default"))

        # If its an array...
        if s.get("type") == "array":

            if not arg_value:
                continue

            # We split the value on a comma and trim whitespaces only if it
            # is a string. If we use the `default` the value will already be a list
            if isinstance(arg_value, str):
                arg_value = [item.strip() for item in arg_value.split(",")]

            s_items = s.get("items", {})

            if s_items.get("type") == "string":
                settings_dict[s.get("name")] = arg_value

            elif s_items.get("type") == "integer":
                settings_dict[s.get("name")] = [int(item) for item in arg_value]

            elif s_items.get("type") == "number":
                settings_dict[s.get("name")] = [float(item) for item in arg_value]
            else:
                raise ValueError(f"Unsupported array item type: {s_items.get('type')}")

            continue

        settings_dict[s.get("name")] = arg_value

    for s_name, s in settings_dict.items():

        manifest_setting = manifest_yaml.get_setting(s_name)

        if settings_dict.get(s_name) is None and manifest_setting.get("nullable") is False:
            raise ValueError(f"Setting '{s_name}' is required but not provided")

    fn: PythonFunction = fns.get(args.fn)

    kwargs = {
        "user_log": LOG,
        "settings": settings_dict
    }

    _invoke_function(fn, args, **kwargs)
