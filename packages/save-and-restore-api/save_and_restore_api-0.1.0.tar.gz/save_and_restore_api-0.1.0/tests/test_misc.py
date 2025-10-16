from __future__ import annotations

import asyncio
import importlib.metadata

import pytest

import save_and_restore_api
from save_and_restore_api import SaveRestoreAPI as SaveRestoreAPI_Threads
from save_and_restore_api.aio import SaveRestoreAPI as SaveRestoreAPI_Async

from .common import (
    _is_async,
    _select_auth,
    admin_password,
    admin_username,
    base_url,
    clear_sar,  # noqa: F401
    create_root_folder,
    read_password,
    read_username,
    user_password,
    user_username,
)


def test_version_01():
    """
    Test that the versioning works correctly.
    """
    assert importlib.metadata.version("save_and_restore_api") == save_and_restore_api.__version__


# # fmt: off
# @pytest.mark.parametrize("library", ["THREADS", "ASYNC"])
# # fmt: on
# def test_api_call_01(library):
#     """
#     Test generic API call
#     """
#     username, password = user_username, user_password

#     if not _is_async(library):
#         SR = SaveRestoreAPI_Threads(base_url=base_url, timeout=2)
#         SR.auth_set(username=user_username, password=user_password)
#         SR.open()
#         response = SR.login(username=username, password=password)
#         assert response["userName"] == username
#         SR.close()
#         SR.open()
#         response = SR.login(username=username, password=password)
#         assert response["userName"] == username
#         SR.close()
#     else:
#         async def testing():
#             SR = SaveRestoreAPI_Async(base_url=base_url, timeout=2)
#             SR.auth_set(username=user_username, password=user_password)
#             SR.open()
#             response = await SR.login(username=username, password=password)
#             assert response["userName"] == username
#             await SR.close()
#             SR.open()
#             response = await SR.login(username=username, password=password)
#             assert response["userName"] == username
#             await SR.close()

#         asyncio.run(testing())


# =============================================================================================
#                         INFO-CONTROLLER API METHODS
# =============================================================================================


# fmt: off
@pytest.mark.parametrize("library", ["THREADS", "ASYNC"])
# fmt: on
def test_info_get_01(library):
    """
    Tests for the 'info_get' API.
    """
    if not _is_async(library):
        with SaveRestoreAPI_Threads(base_url=base_url, timeout=2) as SR:

            info = SR.info_get()
            assert info["name"] == "service-save-and-restore"

    else:
        async def testing():
            async with SaveRestoreAPI_Async(base_url=base_url, timeout=2) as SR:

                info = await SR.info_get()
                assert info["name"] == "service-save-and-restore"

        asyncio.run(testing())

# fmt: off
@pytest.mark.parametrize("library", ["THREADS", "ASYNC"])
# fmt: on
def test_version_get_01(library):
    """
    Tests for the 'version_get' API.
    """
    if not _is_async(library):
        with SaveRestoreAPI_Threads(base_url=base_url, timeout=2) as SR:

            info = SR.version_get()
            isinstance(info, str)
            assert "service-save-and-restore" in info
            assert "version" in info

    else:
        async def testing():
            async with SaveRestoreAPI_Async(base_url=base_url, timeout=2) as SR:

                info = await SR.version_get()
                isinstance(info, str)
                assert "service-save-and-restore" in info
                assert "version" in info

        asyncio.run(testing())


# =============================================================================================
#                         TESTS FOR SEARCH-CONTROLLER API METHODS
# =============================================================================================

# fmt: off
@pytest.mark.parametrize("library", ["THREADS", "ASYNC"])
# fmt: on
def test_search_01(clear_sar, library):  # noqa: F811
    """
    Tests for the 'search' API.
    """
    root_folder_uid = create_root_folder()

    if not _is_async(library):
        with SaveRestoreAPI_Threads(base_url=base_url, timeout=2) as SR:
            _select_auth(SR=SR, usesetauth=True)

            configurationNode = {"name": "Test Config", "description": "Created for testing"}
            configurationData = {"pvList": []}

            response = SR.config_add(
                root_folder_uid,
                configurationNode=configurationNode,
                configurationData=configurationData,
            )
            config_uid = response["configurationNode"]["uniqueId"]

            response = SR.search({"name": "Test Config"})
            assert response["hitCount"] == 1
            assert response["nodes"][0]["name"] == "Test Config"
            assert response["nodes"][0]["uniqueId"] == config_uid

            response = SR.search({"description": "for testing"})
            assert response["hitCount"] == 1
            assert response["nodes"][0]["name"] == "Test Config"
            assert response["nodes"][0]["uniqueId"] == config_uid

            response = SR.search({"name": "No such config"})
            assert response["hitCount"] == 0

    else:
        async def testing():
            async with SaveRestoreAPI_Async(base_url=base_url, timeout=2) as SR:
                _select_auth(SR=SR, usesetauth=True)

                configurationNode = {"name": "Test Config", "description": "Created for testing"}
                configurationData = {"pvList": []}

                response = await SR.config_add(
                    root_folder_uid,
                    configurationNode=configurationNode,
                    configurationData=configurationData,
                )
                config_uid = response["configurationNode"]["uniqueId"]

                response = await SR.search({"name": "Test Config"})
                assert response["hitCount"] == 1
                assert response["nodes"][0]["name"] == "Test Config"
                assert response["nodes"][0]["uniqueId"] == config_uid

                response = await SR.search({"description": "for testing"})
                assert response["hitCount"] == 1
                assert response["nodes"][0]["name"] == "Test Config"
                assert response["nodes"][0]["uniqueId"] == config_uid

                response = await SR.search({"name": "No such config"})
                assert response["hitCount"] == 0

        asyncio.run(testing())

# =============================================================================================
#                         HELP-RESOURCE API METHODS
# =============================================================================================

# fmt: off
@pytest.mark.parametrize("library", ["THREADS", "ASYNC"])
# fmt: on
def test_help_01(library):
    """
    Tests for the 'help' API.
    """
    if not _is_async(library):
        with SaveRestoreAPI_Threads(base_url=base_url, timeout=2) as SR:
            response = SR.help(what="SearchHelp")
            isinstance(response, str)
            assert "Save-and-restore Search Help Reference" in response

    else:
        async def testing():
            async with SaveRestoreAPI_Async(base_url=base_url, timeout=2) as SR:
                response = await SR.help(what="SearchHelp")
                isinstance(response, str)
                assert "Save-and-restore Search Help Reference" in response

        asyncio.run(testing())


# =============================================================================================
#                         TESTS FOR AUTHENTICATION-CONTROLLER API METHODS
# =============================================================================================

# fmt: off
@pytest.mark.parametrize("library", ["THREADS", "ASYNC"])
@pytest.mark.parametrize("username, password, roles, code", [
    (admin_username, admin_password,  ["ROLE_SAR-ADMIN"], 200),
    (user_username, user_password,  ["ROLE_SAR-USER"], 200),
    (read_username, read_password,  [], 200),
    (user_username, read_password,  [], 401),  # Incorrect password
    (user_username + "_a", user_password,  [], 401),  # Incorrect login
])
# fmt: on
def test_login_01(username, password, roles, library, code):
    """
    Tests for the 'login' API.
    """
    if not _is_async(library):
        with SaveRestoreAPI_Threads(base_url=base_url, timeout=2) as SR:
            if code == 200:
                SR.login(username=username, password=password)
            else:
                with pytest.raises(SR.HTTPClientError, match=f"{code}"):
                    SR.login(username=username, password=password)
    else:
        async def testing():
            async with SaveRestoreAPI_Async(base_url=base_url, timeout=2) as SR:
                if code == 200:
                    await SR.login(username=username, password=password)
                else:
                    with pytest.raises(SR.HTTPClientError, match=f"{code}"):
                        await SR.login(username=username, password=password)

        asyncio.run(testing())
