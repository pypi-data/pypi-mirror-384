from __future__ import annotations

import os
import subprocess

import pytest

from save_and_restore_api import SaveRestoreAPI as SaveRestoreAPI_Threads

from .common import (
    _select_auth,
    base_url,
    clear_sar,  # noqa: F401
    create_root_folder,
    root_folder_node_name,
    user_password,
    user_username,
)

EXIT_CODE_SUCCESS = 0
EXIT_CODE_CLI_PARAMETER_ERROR = 1
EXIT_CODE_OPERATION_FAILED = 2


_BASE_URL = base_url
_BASE_URL_INVALID1 = "http://localhost:8080/invalid"
_BASE_URL_INVALID2 = "http://localhost:8081/save-restore"


def sp_call(*args, **kwargs):
    """
    Wrapper for 'subprocess.call'.
    """
    return subprocess.call(*args, **kwargs)


# =============================================================================================
#                         TESTS FOR CLI TOOL
# =============================================================================================


# fmt: off
@pytest.mark.parametrize("use_cli_params", [True, False])
@pytest.mark.parametrize("verbose", [False, True])
@pytest.mark.parametrize("host_base_url, username, password, exit_code", [
    (f"{_BASE_URL}", user_username, user_password, EXIT_CODE_SUCCESS),
    (f"{_BASE_URL_INVALID1}", user_username, user_password, EXIT_CODE_OPERATION_FAILED),
    (f"{_BASE_URL_INVALID2}", user_username, user_password, EXIT_CODE_OPERATION_FAILED),
    (f"{_BASE_URL}", user_username + "a", user_password, EXIT_CODE_OPERATION_FAILED),
    (f"{_BASE_URL}", user_username, user_password + "a", EXIT_CODE_OPERATION_FAILED),
    (None, user_username, user_password, EXIT_CODE_CLI_PARAMETER_ERROR),
])
# fmt: on
def test_cli_tool_login_01(
    monkeypatch,
    host_base_url,
    username,
    password,
    exit_code,
    use_cli_params,
    verbose
):
    """
    Test for LOGIN command.
    """
    monkeypatch.setenv("SAVE_AND_RESTORE_API_USER_PASSWORD", password)
    params = []
    if use_cli_params:
        if host_base_url is not None:
            params = params + [f"--base-url={host_base_url}"]
        if username is not None:
            params = params + [f"--user-name={username}"]
    else:
        if host_base_url is not None:
            monkeypatch.setenv("SAVE_AND_RESTORE_API_BASE_URL", host_base_url)
        if username is not None:
            monkeypatch.setenv("SAVE_AND_RESTORE_API_USER_NAME", username)
    if verbose:
        params = params + ["--verbose"]

    params = ["save-and-restore"] + params + ["LOGIN"]
    assert sp_call(params) == exit_code



# fmt: off
@pytest.mark.parametrize("show_data", [False, True])
@pytest.mark.parametrize("verbose", [False, True])
@pytest.mark.parametrize("host_base_url, username, password, cfg_name, fld_create, exit_code", [
    (f"{_BASE_URL}", user_username, user_password, "Test Config 1", False, EXIT_CODE_SUCCESS),
    (f"{_BASE_URL}", user_username, user_password, "Test Config 1", True, EXIT_CODE_SUCCESS),
    (f"{_BASE_URL}", user_username, user_password, "some folder/Test Config 1", False, EXIT_CODE_OPERATION_FAILED),
    (f"{_BASE_URL}", user_username, user_password, "some folder/Test Config 1", True, EXIT_CODE_SUCCESS),
    (f"{_BASE_URL}", user_username, user_password + "a", "Test Config 1", False, EXIT_CODE_OPERATION_FAILED),
    (f"{_BASE_URL}", user_username, user_password, "", False, EXIT_CODE_OPERATION_FAILED),
])
# fmt: on
def test_cli_tool_config_add_01(
    clear_sar,  # noqa: F811
    monkeypatch,
    host_base_url,
    username,
    password,
    cfg_name,
    fld_create,
    exit_code,
    verbose,
    show_data,
):
    """
    Test for CONFIG ADD command.
    """
    create_root_folder()

    monkeypatch.setenv("SAVE_AND_RESTORE_API_USER_PASSWORD", password)
    if host_base_url is not None:
        monkeypatch.setenv("SAVE_AND_RESTORE_API_BASE_URL", host_base_url)
    if username is not None:
        monkeypatch.setenv("SAVE_AND_RESTORE_API_USER_NAME", username)

    # Execute CONFIG ADD command

    params = []
    if verbose:
        params = params + ["--verbose"]
    if fld_create:
        params = params + ["--create-folders=ON"]

    params = ["save-and-restore"] + params + ["CONFIG", "ADD"]
    if show_data:
        params = params + ["--show-data=ON"]
    params = params + ["--file-format=autosave"]

    config_name = f"/{root_folder_node_name}/{cfg_name}"
    file_name = os.path.join(os.path.split(__file__)[0], "data", "auto_settings_17.sav")

    params = params + [f"--config-name={config_name}"]
    params = params + [f"--file-name={file_name}"]

    assert sp_call(params) == exit_code

    # Check that the configuration was created and contains expected number of PVs
    with SaveRestoreAPI_Threads(base_url=base_url, timeout=10) as SR:
        _select_auth(SR=SR, usesetauth=True)

        if exit_code == EXIT_CODE_SUCCESS:
            nodes = SR.structure_path_nodes(config_name)
            assert len(nodes) == 1
            config_uid = nodes[0]["uniqueId"]

            response = SR.node_get(config_uid)
            assert response["nodeType"] == "CONFIGURATION"
            assert response["name"] == "Test Config 1"

            response = SR.config_get(config_uid)
            assert len(response["pvList"]) == 17
        else:
            # The configuration does not exist
            with pytest.raises(SR.HTTPClientError):
                SR.structure_path_nodes(config_name)


# fmt: off
@pytest.mark.parametrize("show_data", [False, True])
@pytest.mark.parametrize("verbose", [False, True])
@pytest.mark.parametrize("host_base_url, username, password, cfg_name, add_or_update, exit_code", [
    (f"{_BASE_URL}", user_username, user_password, "some folder/Test Config 1", False, EXIT_CODE_SUCCESS),
    (f"{_BASE_URL}", user_username, user_password, "some folder/Test Config 1", True, EXIT_CODE_SUCCESS),
    (f"{_BASE_URL}", user_username, user_password + "a", "some folder/Test Config 1",
     False, EXIT_CODE_OPERATION_FAILED),
    (f"{_BASE_URL}", user_username, user_password + "a", "some folder/Test Config 1",
     True, EXIT_CODE_OPERATION_FAILED),
    (f"{_BASE_URL}", user_username, user_password, "Test Config 1", False, EXIT_CODE_OPERATION_FAILED),
    (f"{_BASE_URL}", user_username, user_password, "", False, EXIT_CODE_OPERATION_FAILED),
    (f"{_BASE_URL}", user_username, user_password, "", True, EXIT_CODE_OPERATION_FAILED),
])
# fmt: on
def test_cli_tool_config_update_01(
    clear_sar,  # noqa: F811
    monkeypatch,
    host_base_url,
    username,
    password,
    cfg_name,
    add_or_update,
    exit_code,
    verbose,
    show_data,
):
    """
    Test for CONFIG UPDATE and CONFIG ADD-OR-UPDATE commands.
    """
    create_root_folder()

    if host_base_url is not None:
        monkeypatch.setenv("SAVE_AND_RESTORE_API_BASE_URL", host_base_url)
    if username is not None:
        monkeypatch.setenv("SAVE_AND_RESTORE_API_USER_NAME", username)

    # Create config node using CONFIG ADD command
    monkeypatch.setenv("SAVE_AND_RESTORE_API_USER_PASSWORD", user_password)
    config_name_true = f"/{root_folder_node_name}/some folder/Test Config 1"
    params = [
        "save-and-restore",
        "--create-folders=ON",
        "CONFIG",
        "ADD" if not add_or_update else "ADD-OR-UPDATE",
        "--file-format=autosave",
        f"--config-name={config_name_true}",
        f"--file-name={os.path.join(os.path.split(__file__)[0], 'data', 'auto_settings_17.sav')}",
    ]
    assert sp_call(params) == EXIT_CODE_SUCCESS

    # Modify pvList of the configuration
    monkeypatch.setenv("SAVE_AND_RESTORE_API_USER_PASSWORD", password)
    params = []
    if verbose:
        params = params + ["--verbose"]

    params = ["save-and-restore"] + params + ["CONFIG", "UPDATE" if not add_or_update else "ADD-OR-UPDATE"]
    if show_data:
        params = params + ["--show-data=ON"]
    params = params + ["--file-format=autosave"]

    config_name = f"/{root_folder_node_name}/{cfg_name}"
    params = params + [f"--config-name={config_name}"]

    # Try loading non-existing file
    file_name = os.path.join(os.path.split(__file__)[0], "data", "auto_settings_3__.sav")
    params_ = params + [f"--file-name={file_name}"]
    assert sp_call(params_) == EXIT_CODE_OPERATION_FAILED

    file_name = os.path.join(os.path.split(__file__)[0], "data", "auto_settings_3.sav")
    params = params + [f"--file-name={file_name}"]
    assert sp_call(params) == exit_code

    # Check that the configuration was created and contains expected number of PVs
    with SaveRestoreAPI_Threads(base_url=base_url, timeout=10) as SR:
        _select_auth(SR=SR, usesetauth=True)

        nodes = SR.structure_path_nodes(config_name_true)
        assert len(nodes) == 1
        config_uid = nodes[0]["uniqueId"]

        response = SR.node_get(config_uid)
        assert response["nodeType"] == "CONFIGURATION"
        assert response["name"] == "Test Config 1"

        response = SR.config_get(config_uid)
        if exit_code == EXIT_CODE_SUCCESS:
            assert len(response["pvList"]) == 3
        else:
            assert len(response["pvList"]) == 17  # Configuration not modified


# fmt: off
@pytest.mark.parametrize("show_data", [False, True])
@pytest.mark.parametrize("verbose", [False, True])
@pytest.mark.parametrize("host_base_url, cfg_name, exit_code", [
    (f"{_BASE_URL}", "some folder/Test Config 1", EXIT_CODE_SUCCESS),
    (f"{_BASE_URL}", "Test Config 1", EXIT_CODE_OPERATION_FAILED),
])
# fmt: on
def test_cli_tool_config_get_01(
    clear_sar,  # noqa: F811
    monkeypatch,
    host_base_url,
    cfg_name,
    exit_code,
    verbose,
    show_data,
):
    """
    Test for CONFIG GET command.
    """
    create_root_folder()

    if host_base_url is not None:
        monkeypatch.setenv("SAVE_AND_RESTORE_API_BASE_URL", host_base_url)
    monkeypatch.setenv("SAVE_AND_RESTORE_API_USER_NAME", user_username)

    # Create config node using CONFIG ADD command
    monkeypatch.setenv("SAVE_AND_RESTORE_API_USER_PASSWORD", user_password)
    config_name_true = f"/{root_folder_node_name}/some folder/Test Config 1"
    params = [
        "save-and-restore",
        "--create-folders=ON",
        "CONFIG",
        "ADD",
        "--file-format=autosave",
        f"--config-name={config_name_true}",
        f"--file-name={os.path.join(os.path.split(__file__)[0], 'data', 'auto_settings_17.sav')}",
    ]
    assert sp_call(params) == EXIT_CODE_SUCCESS

    # Execute CONFIG GET command
    params = []
    if verbose:
        params = params + ["--verbose"]

    params = ["save-and-restore"] + params + ["CONFIG", "GET"]
    if show_data:
        params = params + ["--show-data=ON"]

    config_name = f"/{root_folder_node_name}/{cfg_name}"
    params = params + [f"--config-name={config_name}"]

    assert sp_call(params) == exit_code
