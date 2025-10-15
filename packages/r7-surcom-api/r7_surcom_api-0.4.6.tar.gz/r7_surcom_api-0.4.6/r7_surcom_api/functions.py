"""
Invoking Python functions.
Also includes some validity checking.
"""
import importlib
import inspect
import logging
import os
import sys
from logging import ERROR, NOTSET, WARNING
from typing import List

from r7_surcom_api import constants, helpers

logger = logging.getLogger(constants.LOGGER_NAME)

# TODO: we need to add a test for this module

STANDARD_PARAMS = {
    "more_flag": {"offload": "never", "schema": {"type": "boolean"}},
    "more_data": {
        "offload": "always",
        "schema": {
            "type": "object",
        },
    },
    "items": {
        "offload": "always",
        "schema": {"type": "array", "items": {"type": "object"}},
    },
}


class PythonFunction:
    """
    A Python function declared in the connector manifest, and implemented in the current scope.
    """

    def __init__(self, functiondef: dict, modulepath: str) -> None:
        # 'func' is the function definition from the connector manifest.
        self.func = functiondef
        self.func_id = self.func["id"]

        # Get the id w/o namespace
        # (e.g. 'mock.myconnector.my_function' -> 'my_function')
        self.id_wo_ns = self.func_id.split(".")[-1]

        # 'modulepath' is the file or directory containing the module to load
        self.modulepath = modulepath

        # Find the python callable
        self.userfunc = self._callable()

        # Inspect the python userfunc
        self.python_args = inspect.getfullargspec(self.userfunc)

        self.error_level = NOTSET

    def __str__(self):
        return self.func_id

    def __repr__(self):
        return self.__str__()

    @property
    def is_hidden(self):
        """Is the function hidden?"""
        return self.func.get("hidden", False)

    @property
    def is_test(self):
        """Is this the 'test connection' function?"""
        return self.func_id.split(".")[-1] == "test"

    @property
    def returns_items(self) -> bool:
        """
        Does the function definition have 'items' in its return schema?
        """
        for ret in self.func.get("returns", []):
            ret_id = ret["name"]
            if ret_id == "items":
                return True
        return False

    @property
    def python_arguments(self) -> List[str]:
        """
        Get the names of the python function arguments
        """
        return self.python_args.args

    @property
    def manifest_arguments(self) -> List[str]:
        """
        Get the names of the function's declared arguments
        """
        return [param.get("name") for param in self.func.get("parameters", {})]

    def check(self) -> str:
        """
        Check that the Python and manifest align, and that conventions are being followed.
        Return the highest info level (ERROR or WARNING or NOTSET)
        """
        self.error_level = NOTSET

        def _log(lev, err):
            logger.log(lev, err)
            self.error_level = max(self.error_level, lev)

        for param in self.func.get("parameters", []):
            # If the manifest is missing a name for any parameter, that's bad
            if "name" not in param:
                _log(ERROR, f"Function '{self.func_id}' has a parameter with no name.")
            # If it's one of the "standard parameters", check the definition
            req = STANDARD_PARAMS.get(param["name"])
            if req and not helpers.dict_is_subset(param, req):
                _log(
                    ERROR,
                    f"Function '{self.func_id}': parameter '{param['name']}' should include: {req}.",
                )

        # Check the return values
        for ret in self.func.get("returns", []):
            if "name" not in ret:
                _log(
                    ERROR,
                    f"Function '{self.func_id}' has a return property with no name.",
                )
            # If it's one of the "standard parameters", check the definition
            req = STANDARD_PARAMS.get(ret["name"])
            if req and not helpers.dict_is_subset(ret, req):
                _log(
                    ERROR,
                    f"Function '{self.func_id}': return '{ret['name']}' should include: {req}.",
                )

        # Do the parameters match up with the manifest?
        # (If the python function takes a '**kwargs' parameter, it'll accept anything, no need to check)
        if not self.python_args.varkw:

            # Check the parameters defined by the manifest
            for param in self.manifest_arguments:
                if param.startswith("_"):
                    _log(
                        ERROR,
                        f"Function '{self.func_id}': parameter '{param}' should not start with underscore.",
                    )
                if param not in self.python_arguments:
                    _log(
                        ERROR,
                        f"Function '{self.func_id}': parameter '{param}' is not declared in the Python function.",
                    )

            # Check the parameters defined by the function
            for param in self.python_args.args:
                if not param.startswith("_"):
                    if param not in self.manifest_arguments:
                        _log(
                            WARNING,
                            f"Function '{self.func_id}': parameter '{param}' is not declared in the manifest.",
                        )

        # If the manifest is missing a response, or the response is not an object, that's bad
        returns_def = self.func.get("returns", {})
        if not returns_def:
            _log(ERROR, f"Function '{self.func_id}' is missing 'returns'.")
        # Unfortunately the definition of 'returns' is not very solid.  Need more investigation.
        # if self.is_test:
        #     if "status" not in returns_def[0]["schema"].get("properties", {}):
        #         return f"Test function '{self.func_id}' should return an object with 'status' and 'message'."

        # OK
        return self.error_level

    def _callable(self):
        """
        Find the callable entrypoint 'handler' in the module at 'filepath'
        """
        filepath = self.modulepath

        # 'entrypoint' is the name of the python entrypoint for the function to call
        handler = self.func["entrypoint"]

        # handler looks like `path.to.module.function`
        parts = handler.rsplit(".", 1)
        if len(handler) == 0:
            # default to main.main if entrypoint wasn't provided
            modulename = "main"
            funcname = "main"
        elif len(parts) == 1:
            modulename = "main"
            funcname = parts[0]
        else:
            modulename = parts[0]
            funcname = parts[1]

        # check whether the destination is a directory or a file
        if os.path.isdir(filepath):
            # add package directory path into module search path
            sys.path.append(filepath)

            if __package__:
                mod = importlib.import_module(modulename, __package__)
            else:
                mod = importlib.import_module(modulename)

        else:
            # load source from destination python file
            mod = importlib.machinery.SourceFileLoader("mod", filepath).load_module(
                modulename
            )

        # load user function from module
        userfunc = getattr(mod, funcname)
        return userfunc
