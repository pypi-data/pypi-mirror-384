import argparse
import getpass
import logging
import os
import pprint
import sys
import time
from dataclasses import dataclass

import save_and_restore_api
from save_and_restore_api import SaveRestoreAPI

version = save_and_restore_api.__version__

logger = logging.getLogger("save-and-restore-api")

EXIT_CODE_SUCCESS = 0
EXIT_CODE_CLI_PARAMETER_ERROR = 1
EXIT_CODE_OPERATION_FAILED = 2


@dataclass
class Settings:
    """
    Data structure for storing command line parameters.
    """

    command: str = None
    operation: str = None
    base_url: str = None
    create_folders: bool = False
    user_name: str = None
    user_password: str = None
    config_name: str = None
    file_name: str = None
    file_format: str = None
    timeout: float = 5


def setup_loggers(*, log_level, name="save-and-restore-api"):
    """
    Configure loggers.

    Parameters
    ----------
    name: str
        Module name (typically ``__name__``)
    log_level
        Logging level (e.g. ``logging.INFO``, ``"INFO"`` or ``20``)
    """
    log_stream_handler = logging.StreamHandler(sys.stdout)
    log_stream_handler.setLevel(log_level)
    if (
        (log_level == logging.DEBUG)
        or (log_level == "DEBUG")
        or (isinstance(log_level, int) and (log_level <= 10))
    ):
        log_stream_format = "[%(levelname)1.1s %(asctime)s.%(msecs)03d %(name)s %(module)s:%(lineno)d] %(message)s"
    else:
        log_stream_format = "[%(levelname)1.1s %(asctime)s %(name)s] %(message)s"

    log_stream_handler.setFormatter(logging.Formatter(fmt=log_stream_format))
    logging.getLogger(name).handlers.clear()
    logging.getLogger(name).addHandler(log_stream_handler)
    logging.getLogger(name).setLevel(log_level)
    logging.getLogger(name).propagate = False


def parse_args(settings):
    """
    Perform full parsing of the command line arguments. Results are saved in the ``settings`` object.

    Parameters
    ----------
    settings: Settings
        Settings object where command line parameters are saved.

    Returns
    -------
    None
    """

    def formatter(prog):
        # Set maximum width such that printed help mostly fits in the RTD theme code block (documentation).
        return argparse.RawDescriptionHelpFormatter(prog, max_help_position=20, width=90)

    parser = argparse.ArgumentParser(
        description="save-and-restore: CLI tool for operations on Save-and-Restore nodes.\n"
        f"save-and-restore-api version {version}\n\n"
        "The following operations are currently supported:\n"
        "    LOGIN: check user login credentials.\n"
        "    CONFIG GET: read an existing config node.\n"
        "    CONFIG ADD: create a new config node. The config node is created based\n"
        "        on the list of PVs loaded from file. The file name and format are specified\n"
        "        using the '--file-name' ('-f') and '--file-format' parameters.\n"
        "    CONFIG UPDATE: update an existing config node.\n"
        "\n"
        "Host URL specified as the '--base-url' parameter. User authenticates by the user name\n"
        "(--user-name) and the password. The user name and the password can be passed using\n"
        "the environment variables (see below) or entered interactively.\n"
        "\n"
        "Supported environment variables:\n"
        "    SAVE_AND_RESTORE_API_BASE_URL: host URL (see '--base-url' parameter);\n"
        "    SAVE_AND_RESTORE_API_USER_NAME: user name (see '--user-name' parameter);\n"
        "    SAVE_AND_RESTORE_API_USER_PASSWORD: user password (use with caution).\n"
        "CLI parameters override the respective environment variables.\n"
        "\n"
        "\n"
        "Exit codes:\n"
        "    0: operation successful;\n"
        "    1: error in command line parameters;\n"
        "    2: operation failed.\n"
        "\n"
        "Examples:\n"
        "\n"
        "  Check login credentials. User password is requested interactively. Alternatively,\n"
        "  the password can be passed using environment variable `SAVE_AND_RESTORE_API_USER_PASSWORD`\n"
        "\n"
        "  save-and-restore --base-url http://localhost:8080/save-restore --user-name=user LOGIN\n"
        "\n"
        "  Read the configuration node named 'eiger_config'. Print the full configuration data\n"
        "  (the list of PVs):\n"
        "\n"
        "  save-and-restore --base-url http://localhost:8080/save-restore \\\n"
        "    CONFIG GET --config-name /detectors/imaging/eiger_config --show-data=ON\n"
        "\n"
        "  Create a new configuration node named 'eiger_config'. Load the list of PVs from\n"
        "  file ``eiger_pvs.sav``. Automatically create any missing parent folders in the path:\n"
        "\n"
        "  save-and-restore --base-url=http://localhost:8080/save-restore --user-name=user \\\n"
        "    --create-folders=ON CONFIG ADD --config-name=/detectors/imaging/eiger_config \\\n"
        "    --file-name=eiger_pvs.sav --file-format=autosave\n"
        "\n"
        "  Update the existing configuration node named 'eiger_config'. Load the list of PVs\n"
        "  from the file ``eiger_pvs.sav``:\n"
        "\n"
        "  save-and-restore --base-url http://localhost:8080/save-restore --user-name=user \\\n"
        "    CONFIG UPDATE --config-name /detectors/imaging/eiger_config \\\n"
        "    --file-name eiger_pvs.sav --file-format autosave\n"
        "\n"
        "  Add new or update the existing configuration node named 'eiger_config'. Load the list of PVs\n"
        "  from the file ``eiger_pvs.sav``:\n"
        "\n"
        "  save-and-restore --base-url http://localhost:8080/save-restore --user-name=user \\\n"
        "    CONFIG ADD-OR-UPDATE --config-name /detectors/imaging/eiger_config \\\n"
        "    --file-name eiger_pvs.sav --file-format autosave\n",
        formatter_class=formatter,
    )

    parser.add_argument(
        "--base-url",
        dest="base_url",
        type=str,
        default=None,
        help="Base URL for communication with the host, e.g. http://localhost:8080/save-restore.",
    )

    parser.add_argument(
        "--user-name",
        dest="user_name",
        type=str,
        default=None,
        help=(
            "User name for authentication with save-and-restore service. If the operation requires "
            "authentication and the user name is not specified, the user is prompted for the name. "
            "The user is also prompted for the password."
        ),
    )

    parser.add_argument(
        "--create-folders",
        dest="create_folders",
        type=str,
        choices=["ON", "OFF"],
        default="OFF",
        help=(
            "Create missing folders if required to complete the operation. The operation fails "
            "if the parameter is OFF and the required folders are missing. Default: '%(default)s'."
        ),
    )

    parser.add_argument(
        "--verbose",
        dest="verbose",
        action="store_true",
        help="Enable print of the debug output, including tracebacks.",
    )

    subparser_command = parser.add_subparsers(dest="command", help="Select the operation type.")

    parser_config = subparser_command.add_parser(
        "LOGIN",
        help="Check user login credentials.",
        formatter_class=formatter,
    )

    parser_config = subparser_command.add_parser(
        "CONFIG",
        help="Operations on configuration nodes.",
        formatter_class=formatter,
    )

    subparser_config_operation = parser_config.add_subparsers(dest="operation", help="Select the operation.")
    parser_config_get = subparser_config_operation.add_parser(
        "GET",
        help="Read configuration node. The command may be used to check if a config node exists.",
        formatter_class=formatter,
    )

    parser_config_get.add_argument(
        "--config-name",
        dest="config_name",
        type=str,
        default=None,
        help="Configuration name including folders, e.g. /detectors/imaging/eiger_config",
    )

    parser_config_get.add_argument(
        "--show-data",
        dest="show_data",
        type=str,
        choices=["ON", "OFF"],
        default="OFF",
        help="Print the loaded config data. The config node information is always printed. "
        "Default: '%(default)s'.",
    )

    # subparser_config_operation = parser_config.add_subparsers(dest="operation", help="Select the operation.")
    parser_config_add = subparser_config_operation.add_parser(
        "ADD",
        help="Add (create) a new configuration node.",
        formatter_class=formatter,
    )

    parser_config_add.add_argument(
        "--config-name",
        dest="config_name",
        type=str,
        default=None,
        help="Configuration name including folders, e.g. /detectors/imaging/eiger_config",
    )

    parser_config_add.add_argument(
        "--file-name",
        "-f",
        dest="file_name",
        type=str,
        default=None,
        help="Name of the file used as a source of PV names.",
    )

    parser_config_add.add_argument(
        "--file-format",
        dest="file_format",
        type=str,
        choices=["autosave"],
        default="autosave",
        help="Format of the file specified by '--file-name'. Default: '%(default)s'",
    )

    parser_config_add.add_argument(
        "--show-data",
        dest="show_data",
        type=str,
        choices=["ON", "OFF"],
        default="OFF",
        help="Print the loaded config data. The config node information is always printed. "
        "Default: '%(default)s'.",
    )

    parser_config_update = subparser_config_operation.add_parser(
        "UPDATE", help="Update an existing configuration node."
    )

    parser_config_update.add_argument(
        "--config-name",
        dest="config_name",
        type=str,
        default=None,
        help="Configuration name including folders, e.g. /detectors/imaging/eiger_config",
    )

    parser_config_update.add_argument(
        "--file-name",
        "-f",
        dest="file_name",
        type=str,
        default=None,
        help="Name of the file used as a source of PV names.",
    )

    parser_config_update.add_argument(
        "--file-format",
        dest="file_format",
        type=str,
        choices=["autosave"],
        default="autosave",
        help="Format of the file specified by '--file-name'. Default: '%(default)s'",
    )

    parser_config_update.add_argument(
        "--show-data",
        dest="show_data",
        type=str,
        choices=["ON", "OFF"],
        default="OFF",
        help="Print the loaded config data. The config node information is always printed. "
        "Default: '%(default)s'.",
    )

    parser_config_add_or_update = subparser_config_operation.add_parser(
        "ADD-OR-UPDATE", help="Add a new or update the existing configuration node."
    )

    parser_config_add_or_update.add_argument(
        "--config-name",
        dest="config_name",
        type=str,
        default=None,
        help="Configuration name including folders, e.g. /detectors/imaging/eiger_config",
    )

    parser_config_add_or_update.add_argument(
        "--file-name",
        "-f",
        dest="file_name",
        type=str,
        default=None,
        help="Name of the file used as a source of PV names.",
    )

    parser_config_add_or_update.add_argument(
        "--file-format",
        dest="file_format",
        type=str,
        choices=["autosave"],
        default="autosave",
        help="Format of the file specified by '--file-name'. Default: '%(default)s'",
    )

    parser_config_add_or_update.add_argument(
        "--show-data",
        dest="show_data",
        type=str,
        choices=["ON", "OFF"],
        default="OFF",
        help="Print the loaded config data. The config node information is always printed. "
        "Default: '%(default)s'.",
    )

    class ExitOnError(Exception):
        pass

    try:
        args = parser.parse_args()

        settings.base_url = args.base_url or os.environ.get("SAVE_AND_RESTORE_API_BASE_URL", None)
        settings.create_folders = args.create_folders == "ON"
        settings.user_name = args.user_name or os.environ.get("SAVE_AND_RESTORE_API_USER_NAME", None)
        settings.user_password = os.environ.get("SAVE_AND_RESTORE_API_USER_PASSWORD", None)
        settings.verbose_output = args.verbose

        if not settings.base_url:
            logger.error("Required '--base-url' ('-u') parameter is not specified")
            parser.print_help()
            raise ExitOnError()

        success = False
        if args.command == "CONFIG":
            settings.command = args.command
            if args.operation == "GET":
                settings.operation = args.operation
                settings.config_name = args.config_name
                settings.show_data = args.show_data == "ON"
                success = True
                if not settings.config_name:
                    logger.error("Required '--config-name' parameter is not specified")
                    success = False
                if not success:
                    parser_config_get.print_help()
                    raise ExitOnError()

            elif args.operation in ("ADD", "UPDATE", "ADD-OR-UPDATE"):
                settings.operation = args.operation
                settings.config_name = args.config_name
                settings.file_name = args.file_name
                settings.file_format = args.file_format
                settings.show_data = args.show_data == "ON"
                success = True
                if not settings.config_name:
                    logger.error("Required '--config-name' parameter is not specified")
                    success = False
                if not settings.file_name:
                    logger.error("Required '--file-name' ('-f') parameter is not specified")
                    success = False
                if not success:
                    parser_config_add.print_help()
                    raise ExitOnError()
            if not success:
                parser_config.print_help()
                raise ExitOnError()

        elif args.command == "LOGIN":
            settings.command = args.command

        else:
            parser.print_help()
            raise ExitOnError()

        if settings.file_name:
            settings.file_name = os.path.abspath(os.path.expanduser(settings.file_name))

    except ExitOnError:
        exit(EXIT_CODE_CLI_PARAMETER_ERROR)


def print_settings(settings):
    """
    Print settings on the terminal in human-readable form. Only setting relevant fo
    the selected operation are printed.

    Parameters
    ----------
    settings: Settings
        Settings object with command line parameters.

    Returns
    -------
    None
    """
    operation = settings.command
    if settings.operation:
        operation += " " + settings.operation
    print(f"\nOperation: {operation}")
    print(f"Base URL: {settings.base_url}")
    print(f"User name: {settings.user_name}")
    print(f"User password: {'*********' if settings.user_password else None}")
    print(f"Verbose output: {settings.verbose_output}")
    if settings.command == "CONFIG":
        print(f"Config name: {settings.config_name}")
        print(f"Show data: {settings.show_data}")
        if settings.operation in ("ADD", "UPDATE"):
            print(f"Create folders: {settings.create_folders}")
            print(f"File name: {settings.file_name}")
            print(f"File format: {settings.file_format}")
    print("")


def set_username_password(settings):
    """
    Interactively ask for user name and password if necessary. If both 'user_name'
    and 'user_password' are not None, then the function does nothing. If only
    'user_name' is specified, the function prints the user name and asks for the password.
    If both 'user_name' and 'user_password' are None, the function asks for both.

    Parameters
    ----------
    settings: Settings
        Settings object with command line parameters.

    Returns
    -------
    None
    """
    user_name, password = settings.user_name, settings.user_password
    user_name_interactive = False
    if not isinstance(user_name, str) or not user_name:
        user_name_interactive = True
        print("Username: ", end="")
        user_name = input()
    if not isinstance(password, str):
        if not user_name_interactive:
            print(f"Username: {user_name}")
        password = getpass.getpass()
    settings.user_name = user_name
    settings.user_password = password
    print("")


def check_connection(SR):
    logger.debug("Connecting to the Save-and-Restore service ...")
    try:
        info = SR.info_get()
    except (SR.HTTPClientError, SR.HTTPRequestError) as ex:
        logger.debug("Failed to connect to Save-and-Restore service.")
        raise RuntimeError(f"Failed to connect to the Save-and-Restore service: {ex}") from ex
    logger.debug(f"Save-and-Restore info:\n{pprint.pformat(info)}")


def process_login_command(settings):
    """
    Process the LOGIN command, which checks of user name and password are valid.
    Raises an exception if the operation fails.

    Parameters
    ----------
    settings: Settings
        Settings object with command line parameters.

    Returns
    -------
    None
    """
    # Interactively ask for user name and password if necessary
    set_username_password(settings)

    with SaveRestoreAPI(base_url=settings.base_url, timeout=settings.timeout) as SR:
        try:
            check_connection(SR=SR)

            logger.debug("Sending 'login' request ...")
            response = SR.login(username=settings.user_name, password=settings.user_password)
            logger.debug(f"Response received: {response}")

            print("Login successful.")
        except Exception as ex:
            raise RuntimeError(f"Login failed: {ex}") from ex


def check_node_exists(SR, config_name, *, node_type="CONFIGURATION"):
    """
    Returns uniqueId of the node if 'config_name' points to an existing configuration node.
    Otherwise returns None.

    Parameters
    ----------
    SR : SaveRestoreAPI
        Current configured instance of SaveRestoreAPI.
    config_name: str
        Full config name including the path.
    node_type: str
        Type of the node to be checked.

    Returns
    -------
    str or None
        Unique ID of the node if it exists, otherwise None.
    """
    if node_type not in ("CONFIGURATION", "FOLDER"):
        raise ValueError(f"Unsupported node type: {node_type}")

    try:
        logger.debug(f"Sending 'structure_path_nodes' request for '{config_name}' ...")
        nodes = SR.structure_path_nodes(config_name)
        logger.debug(f"Response received: {nodes}")

    except SR.HTTPClientError:
        logger.debug(f"Node '{config_name}' does not exist.")
        nodes = []

    config_nodes = [_ for _ in nodes if _["nodeType"] == node_type]

    logger.debug(f"UIDs of the discovered config nodes: {config_nodes}")
    if config_nodes:
        return config_nodes[0]["uniqueId"]
    else:
        return None


def split_node_path(node_path):
    """
    Split full node path (e.g. ``/detectors/imaging/eiger_config``)
    into the list of folders (``["detectors", "imaging"]``) and the config name
    (``"eiger_config"``).

    Parameters
    ----------
    node_path: str
        Full config name including the path.

    Returns
    -------
    list(str)
        List of folders in the path.
    str
        Config name.
    """
    node_path = node_path.strip()
    node_path = node_path.strip("/")
    _ = node_path.split("/")
    folders, name = _[0:-1], _[-1]
    return folders, name


def create_missing_folders(SR, folder_name, *, create_folders=False):
    """
    Check if the folder ``folder_name`` exists. Create the folder if it it does not exist.
    Folders are created only if 'create_folders' is True. Returns ``node_uid`` for the existing
    or created folder node, or *None* if the operation fails.

    Parameters
    ----------
    SR : SaveRestoreAPI
        Current configured instance of SaveRestoreAPI.
    folder_name: str
        Full name of the folder node including the path.
    create_folders: bool
        If True, create missing folders if required. If False, the function only checks
        if the folder exists.

    Returns
    -------
    str or None
        Unique ID of the existing or created folder node, or None if the operation fails.
    """
    folders = folder_name.strip("/").split("/")

    node_uid = check_node_exists(SR, folder_name, node_type="FOLDER")
    if create_folders and not node_uid:
        path, parent_uid = "", SR.ROOT_NODE_UID
        for f in folders:
            path += f"/{f}"
            node_uid = check_node_exists(SR, path, node_type="FOLDER")
            if not node_uid:
                response = SR.node_add(parent_uid, node={"name": f, "nodeType": "FOLDER"})
                node_uid = response["uniqueId"]
            parent_uid = node_uid

    return node_uid


def load_pvs_from_file(file_name, *, file_format):
    """
    Load PV names from file.

    Parameters
    ----------
    file_name: str
        Name of the file containing PV names.
    file_format: str
        Format of the file. Supported formats: "autosave".

    Returns
    -------
    list(str)
        List of PV names loaded from file.
    """
    pv_names = []
    if file_format == "autosave":
        with open(file_name) as f:
            for line in f:
                ll = line.strip()
                if ll.startswith("#") or ll.startswith("<"):
                    continue
                pv_name = ll.split(" ")[0]
                if pv_name:
                    pv_names.append(pv_name)
        # Convert PV list to the format accepted by the API
        pv_names = [{"pvName": _} for _ in pv_names]
    else:
        raise ValueError(f"Unsupported file format: {file_format}.")
    return pv_names


def process_config_command(settings):
    """
    Process the CONFIG command.

    Parameters
    ----------
    settings: Settings
        Settings object with command line parameters.

    Returns
    -------
    None
    """
    if settings.file_name and not os.path.isfile(settings.file_name):
        raise ValueError(f"Input file {settings.file_name!r} does not exist.")

    # Interactively ask for user name and password if necessary
    if settings.operation != "GET":
        set_username_password(settings)

    with SaveRestoreAPI(base_url=settings.base_url, timeout=settings.timeout) as SR:
        if settings.operation != "GET":
            logger.debug("Configuring authentication parameters ...")
            SR.auth_set(username=settings.user_name, password=settings.user_password)

        check_connection(SR=SR)

        logger.debug(f"Checking if config node {settings.config_name!r} exists ...")
        node_uid = check_node_exists(SR, settings.config_name, node_type="CONFIGURATION")
        logger.debug(f"Config node UID: {node_uid}")

        logger.debug(f"Loading information for the node: {node_uid} ...")
        config_node = SR.node_get(node_uid) if node_uid else None

        logger.debug(f"Loading data for the node: {node_uid} ...")
        config_data = SR.config_get(node_uid) if node_uid else None

        if settings.operation == "GET":
            logger.debug("Executing 'CONFIG GET' operation ...")
            if node_uid is None:
                raise RuntimeError(f"Config node {settings.config_name!r} does not exist.")
            else:
                print(f"Config node:\n{pprint.pformat(config_node)}")
                if settings.show_data:
                    print(f"Config data:\n{pprint.pformat(config_data)}")

        elif settings.operation == "ADD" or (settings.operation == "ADD-OR-UPDATE" and not node_uid):
            logger.debug("Executing 'CONFIG ADD' operation ...")
            if node_uid:
                raise RuntimeError(f"Config node {settings.config_name!r} already exists.")

            else:
                logger.debug(f"Loading PV names from file {settings.file_name!r} ...")
                pv_list = load_pvs_from_file(settings.file_name, file_format=settings.file_format)

                print(f"Number of PVs loaded from file: {len(pv_list)}")

                _folders, _config_name = split_node_path(settings.config_name)
                _folder_name = "/" + "/".join(_folders)

                if not _config_name:
                    raise ValueError(f"Config name is an empty string: {settings.config_name!r}")

                logger.debug(f"Creating the folder {_folder_name!r} ...")
                parent_uid = create_missing_folders(SR, _folder_name, create_folders=settings.create_folders)
                if parent_uid is None:
                    raise RuntimeError(f"The folder {_folder_name!r} does not exist.")
                else:
                    logger.debug(f"Adding config node: parent UID: {parent_uid}, name: {_config_name!r}...")
                    response = SR.config_add(
                        parent_uid,
                        configurationNode={"name": _config_name},
                        configurationData={"pvList": pv_list},
                    )

                    print(f"Config node created:\n{pprint.pformat(response['configurationNode'])}")
                    if settings.show_data:
                        print(f"Config data:\n{pprint.pformat(response['configurationData'])}")

        elif settings.operation == "UPDATE" or (settings.operation == "ADD-OR-UPDATE" and node_uid):
            logger.debug(f"Executing 'CONFIG {settings.operation}' operation ...")
            if not node_uid:
                raise RuntimeError(f"Config node {settings.config_name!r} does not exist.")

            else:
                logger.debug(f"Loading PV names from file {settings.file_name!r} ...")
                pv_list = load_pvs_from_file(settings.file_name, file_format=settings.file_format)

                print(f"Number of PVs loaded from file: {len(pv_list)}")

                logger.debug(
                    f"Updating config node: node UID: {config_node['uniqueId']}, name: {config_node['name']!r} ..."
                )
                config_data["pvList"] = pv_list
                response = SR.config_update(
                    configurationNode=config_node,
                    configurationData=config_data,
                )

                print(f"Updated config node:\n{pprint.pformat(response['configurationNode'])}")
                if settings.show_data:
                    print(f"Updated config data:\n{pprint.pformat(response['configurationData'])}")


def main():
    logging.basicConfig(level=logging.WARNING)
    logging.getLogger("save-and-restore-api").setLevel("INFO")

    settings = Settings()
    parse_args(settings)
    print_settings(settings)

    setup_loggers(
        log_level=logging.DEBUG if settings.verbose_output else logging.INFO,
        name="save-and-restore-api",
    )

    logger.debug("Execution started.")
    time_start = time.time()
    try:
        if settings.command == "LOGIN":
            process_login_command(settings)
        elif settings.command == "CONFIG":
            process_config_command(settings)
        else:
            raise ValueError(f"Unsupported command: {settings.command}")

    except Exception as ex:
        logger.error(f"\nOperation failed: {ex}")
        if settings.verbose_output:
            logger.exception(ex)
        exit(EXIT_CODE_OPERATION_FAILED)

    else:
        logger.debug("Operation completed.")
    logger.debug(f"Execution time: {time.time() - time_start:.3f} s.")
