import inspect
import json
import os
import subprocess
from typing import List

from solidipes.mounters.cloud import optional_parameter

################################################################
from solidipes.utils import solidipes_logging as logging

################################################################
print = logging.invalidPrint
logger = logging.getLogger()
################################################################


class RcloneUtils:
    """Wrapper to all Rclone features."""

    credential_names = ["pass", "bearer_token"]

    def __init__(self, **kwargs) -> None:
        super().__init__()

        import shutil

        path = shutil.which("rclone")
        if not path:
            raise FileNotFoundError("cannot find rclone")
        logger.info(f"reading config: {self.rclone_config_fname()}")

    @optional_parameter
    def remote() -> str:
        "Remote name to use/save in the rclone config"
        pass

    def save_rclone_config(self) -> None:
        if not hasattr(self, "_remote"):
            raise RuntimeError("remote keyword must be used")

        import configparser

        config = configparser.ConfigParser()
        try:
            config.read(self.rclone_config_fname())
        except Exception:
            pass

        config[self.remote] = {}
        for k, v in self.make_rclone_config().items():
            config[self.remote][k] = v
        with open(self.rclone_config_fname(), "w") as f:
            config.write(f)

    def make_rclone_config(self):
        config = {}

        import configparser

        _config = configparser.ConfigParser()
        _config.read(self.rclone_config_fname())
        if hasattr(self, "_remote") and self._remote in _config:
            return _config[self.remote]

        config["type"] = self._protocol

        # check dynamically built methods for parameter values if applicable
        for name, method in inspect.getmembers(self):
            # Build a rclone configuration file
            option_shift = {"password": "pass", "twofa": "2fa"}
            option_name = name
            if option_name in option_shift:
                option_name = option_shift[name]

            if option_name not in self.option_properties:
                continue

            logger.debug(f"option_name {option_name}")
            logger.debug(f"method name:  {name}")
            value = getattr(self, name)
            logger.debug(f"value:  {value}")
            properties = self.option_properties[option_name]
            logger.debug(f"properties:  {properties}")

            if value is None or value == "":
                if properties["obscured"]:
                    raise RuntimeError(f"option: '{name}' is mandatory here")
                continue

            # Only use rclone-related options with an actual value
            if properties["obscured"]:
                value = self.rclone_obscure(value)
            config[option_name] = value
        return config

    def make_rclone_options(self):
        config = self.make_rclone_config()
        if hasattr(self, "option_properties"):
            option_properties = self.option_properties
        elif "type" in config:
            self._protocol = config["type"]
            _class = rclone_classes_per_parser_key["rclone-" + self._protocol]
            option_properties = _class.option_properties
        rclone_options = []

        # check dynamically built methods for parameter values if applicable
        for option_name, value in config.items():
            # Only use rclone-related options with an actual value
            if option_name not in option_properties:
                continue
            option_prefix = "-" + option_properties[option_name]["prefix"]
            rclone_options += [f"-{option_prefix}-{option_name}={value}"]
        return rclone_options

    def create_command(self, rclone_cmd, headless=False) -> List[str]:
        rclone_options = self.make_rclone_options()
        logger.debug(self.make_rclone_config())
        rclone_args = [
            f":{self._protocol}:",
            "-vv",
        ]

        command = (
            [
                "rclone",
                rclone_cmd,
            ]
            + rclone_args
            + rclone_options
        )
        return command

    @classmethod
    def rclone_config_fname(cls) -> str:
        out, err = cls.run_and_check_return("rclone config file".split(), fail_message="config failed")
        path = out.split("\n")[1]
        logger.debug(path)
        return path

    def check_connection(self):
        return self.lsd("--max-depth 0")

    def ls(self, options="", **kwargs) -> None:
        command = self.create_command("ls", **kwargs)
        command += options.split()
        logger.debug(" ".join(command))
        return self.run_and_check_return(command, fail_message="ls failed", **kwargs)

    def lsd(self, options="", **kwargs) -> None:
        command = self.create_command("lsd", **kwargs)
        command += options.split()
        logger.debug(" ".join(command))
        return self.run_and_check_return(command, fail_message="ls failed", **kwargs)

    def about(self, options="", **kwargs) -> None:
        command = self.create_command("about", **kwargs)
        command += options.split()
        logger.debug(" ".join(command))
        return self.run_and_check_return(command, fail_message="about failed", **kwargs)

    def sync(self, src, dst, options="", **kwargs) -> None:
        self.save_rclone_config()
        command = ["rclone", "sync", src, dst]
        command += options.split()
        logger.info(" ".join(command))
        return self.run_and_check_return(command, fail_message="about failed", **kwargs)

    def mount(self, **kwargs) -> None:
        """Mount Rclone remote volume"""

        # check if can connect
        self.check_connection()

        # Create directory if it does not exist
        if not os.path.exists(self.path):
            os.makedirs(self.path)

        command = self.create_command("mount", headless=False)
        command += [self.path, "--allow-non-empty", "--daemon", "-vv"]
        logger.debug(" ".join(command))

        self.run_and_check_return(command, fail_message="Mounting failed", **kwargs)

    def rclone_obscure(self, string):
        """
        Call rclone to encrypt a string
        (use for options where IsPassword is true)
        """
        stdout, stderr = self.run_and_check_return(["rclone", "obscure", string], fail_message="Obscure failed")
        return stdout


################################################################
# Dynamically creates the classes for mounting with rclone
# ################################################################
def create_dynamic_function(name, docstring, is_required=True):
    """
    Factory function to:
    - create a function with the given name.
     - set its docstring
     - decorate it as a solidipes parameter or optional_parameter
    """

    def dynamic_func() -> str:
        """Template function, will receive its actual docstring later"""
        return ""

    dynamic_func.__name__ = name
    dynamic_func.__doc__ = docstring

    from solidipes.utils.utils import optional_parameter, parameter

    # Apply the appropriate decorator
    if is_required:
        return parameter(dynamic_func)
    else:
        return optional_parameter(dynamic_func)


################################################################


def rclone_config_schema():
    """
    Call rclone to retrieve the JSON description of all available protocols,
    and their associated options
    """
    try:
        proc = subprocess.Popen(
            ["rclone", "config", "providers"],
            stdout=subprocess.PIPE,
        )
    except FileNotFoundError:
        message = "rclone not found - is it installed in your path ?"
        message += "\nrclone mount commands are not available"
        logger.error(message)
        return []
    except subprocess.CalledProcessError:
        message = "Error executing rclone"
        logger.error(message)
        return []

    std_output = proc.stdout.read()
    schema = json.loads(std_output)
    return schema


################################################################
rclone_classes = {}
rclone_classes_per_parser_key = {}


################################################################
def build_rclone_classes():
    import textwrap

    for protocol_object in rclone_config_schema():
        protocol_name = protocol_object["Name"].replace(" ", "_")
        protocol_prefix = protocol_object["Prefix"]
        if protocol_name == "alias":
            continue

        class_name = protocol_name.capitalize() + "RcloneUtils"
        docstring = f"{protocol_name} filesystem (rclone)"

        _class = type(
            class_name,
            (RcloneUtils,),
            {
                "parser_key": f"rclone-{protocol_name}",
                "_protocol": protocol_prefix,
                "__doc__": docstring,
            },
        )
        rclone_classes[class_name] = _class
        option_properties = {}
        registered_options = set()
        credential_names = ["access_key_id", "secret_access_key"]

        # Loop over potential parameters, starting with all mandatory ones
        for required in [True, False]:
            for option in protocol_object["Options"]:
                prefix = "" if option["NoPrefix"] else protocol_object["Prefix"]
                if option["Required"] == required:
                    option_shift = {"pass": "password", "2fa": "twofa"}
                    option_name = option["Name"]
                    if option_name in registered_options:
                        continue
                    registered_options.add(option_name)
                    if option_name in option_shift:
                        option_name = option_shift[option_name]

                    option_help = option["Help"].replace("\\", "\\\\")
                    option_help = textwrap.fill(option_help, width=79)
                    func = create_dynamic_function(option_name, option_help, required)
                    setattr(_class, option_name, func)
                    option_properties[option["Name"]] = {"prefix": prefix, "obscured": option["IsPassword"]}
                    setattr(_class, "option_properties", option_properties)
                    if option["IsPassword"]:
                        credential_names.append(option_name)
        _class.credential_names = credential_names
        rclone_classes_per_parser_key[_class.parser_key] = _class


################################################################

build_rclone_classes()


################################################################
def declare_subclasses(parent_class, prefix):
    subclasses = {}
    for class_name, _class in rclone_classes.items():
        new_class_name = class_name.replace("Utils", prefix)
        # logger.info(f"declare {new_class_name}")

        daughter_class = type(
            new_class_name,
            (parent_class, _class),
            {
                "parser_key": _class.parser_key,
                "_protocol": _class._protocol,
                "__doc__": prefix + ": " + _class.__doc__,
            },
        )
        subclasses[new_class_name] = daughter_class

    return subclasses


################################################################
