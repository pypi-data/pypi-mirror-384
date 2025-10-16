from __future__ import annotations

import asyncio

import pytest

from save_and_restore_api import SaveRestoreAPI as SaveRestoreAPI_Threads
from save_and_restore_api.aio import SaveRestoreAPI as SaveRestoreAPI_Async

from .common import (
    _is_async,
    _select_auth,
    base_url,
    clear_sar,  # noqa: F401
    create_root_folder,
)

# =============================================================================================
#                         TESTS FOR NODE-CONTROLLER API METHODS
# =============================================================================================


# fmt: off
@pytest.mark.parametrize("library", ["THREADS", "ASYNC"])
@pytest.mark.parametrize("node_uid, code", [
    (SaveRestoreAPI_Threads.ROOT_NODE_UID, 200),
    ("abc", 404),
])
# fmt: on
def test_node_get_01(clear_sar, node_uid, library, code):  # noqa: F811
    """
    Basic tests for the 'node_get' API.
    """

    if not _is_async(library):
        with SaveRestoreAPI_Threads(base_url=base_url, timeout=2) as SR:
            if code == 200:
                response = SR.node_get(node_uid)
                assert response["uniqueId"] == node_uid
            else:
                with pytest.raises(SR.HTTPClientError, match=f"{code}"):
                    SR.node_get(node_uid)
    else:
        async def testing():
            async with SaveRestoreAPI_Async(base_url=base_url, timeout=2) as SR:
                if code == 200:
                    response = await SR.node_get(node_uid)
                    assert response["uniqueId"] == node_uid
                else:
                    with pytest.raises(SR.HTTPClientError, match=f"{code}"):
                        await SR.node_get(node_uid)

        asyncio.run(testing())


# fmt: off
@pytest.mark.parametrize("usesetauth", [True, False])
@pytest.mark.parametrize("library", ["THREADS", "ASYNC"])
# fmt: on
def test_nodes_get_01(clear_sar, library, usesetauth):  # noqa: F811
    """
    Basic tests for the 'nodes_get' API.
    """
    root_folder_uid = create_root_folder()

    if not _is_async(library):
        with SaveRestoreAPI_Threads(base_url=base_url, timeout=2) as SR:
            auth = _select_auth(SR=SR, usesetauth=usesetauth)

            response = SR.node_add(root_folder_uid, node={"name": "Parent Folder", "nodeType": "FOLDER"}, **auth)
            parent_uid = response["uniqueId"]

            response = SR.node_add(parent_uid, node={"name": "Child Folder", "nodeType": "FOLDER"}, **auth)
            folder_uid = response["uniqueId"]

            response = SR.node_add(parent_uid, node={"name": "Child Config", "nodeType": "CONFIGURATION"}, **auth)
            node_uid = response["uniqueId"]

            node_uids = [parent_uid, folder_uid, node_uid]
            node_types = ["FOLDER", "FOLDER", "CONFIGURATION"]

            response = SR.nodes_get(node_uids)
            assert len(response) == 3
            assert [_["uniqueId"] for _ in response] == node_uids
            assert [_["nodeType"] for _ in response] == node_types

    else:
        async def testing():
            async with SaveRestoreAPI_Async(base_url=base_url, timeout=2) as SR:
                auth = _select_auth(SR=SR, usesetauth=usesetauth)

                response = await SR.node_add(
                    root_folder_uid, node={"name": "Parent Folder", "nodeType": "FOLDER"}, **auth
                )
                parent_uid = response["uniqueId"]

                response = await SR.node_add(
                    parent_uid, node={"name": "Child Folder", "nodeType": "FOLDER"}, **auth
                )
                folder_uid = response["uniqueId"]

                response = await SR.node_add(
                    parent_uid, node={"name": "Child Config", "nodeType": "CONFIGURATION"}, **auth
                )
                node_uid = response["uniqueId"]

                node_uids = [parent_uid, folder_uid, node_uid]
                node_types = ["FOLDER", "FOLDER", "CONFIGURATION"]

                response = await SR.nodes_get(node_uids)
                assert len(response) == 3
                assert [_["uniqueId"] for _ in response] == node_uids
                assert [_["nodeType"] for _ in response] == node_types

        asyncio.run(testing())



# fmt: off
@pytest.mark.parametrize("usesetauth", [True, False])
@pytest.mark.parametrize("library", ["THREADS", "ASYNC"])
# fmt: on
def test_node_add_01(clear_sar, library, usesetauth):  # noqa: F811
    """
    Basic tests for the 'node_add' API.
    """

    root_folder_uid = create_root_folder()

    if not _is_async(library):
        with SaveRestoreAPI_Threads(base_url=base_url, timeout=2) as SR:
            auth = _select_auth(SR=SR, usesetauth=usesetauth)

            response = SR.node_add(
                root_folder_uid, node={"name": "Test Folder", "nodeType": "FOLDER"}, **auth
            )
            assert response["name"] == "Test Folder"
            assert response["nodeType"] == "FOLDER"
            folder_uid = response["uniqueId"]

            response = SR.node_add(
                folder_uid, node={"name": "Test Config 1", "nodeType": "CONFIGURATION"}, **auth
            )
            assert response["name"] == "Test Config 1"
            assert response["nodeType"] == "CONFIGURATION"

            response = SR.node_add(
                folder_uid, node={"name": "Test Config 2", "nodeType": "CONFIGURATION"}, **auth
            )
            assert response["name"] == "Test Config 2"
            assert response["nodeType"] == "CONFIGURATION"

    else:
        async def testing():
            async with SaveRestoreAPI_Async(base_url=base_url, timeout=2) as SR:
                auth = _select_auth(SR=SR, usesetauth=usesetauth)

                response = await SR.node_add(
                    root_folder_uid, node={"name": "Test Folder", "nodeType": "FOLDER"}, **auth
                )
                assert response["name"] == "Test Folder"
                assert response["nodeType"] == "FOLDER"
                folder_uid = response["uniqueId"]

                response = await SR.node_add(
                    folder_uid, node={"name": "Test Config 1", "nodeType": "CONFIGURATION"}, **auth
                )
                assert response["name"] == "Test Config 1"
                assert response["nodeType"] == "CONFIGURATION"

                response = await SR.node_add(
                    folder_uid, node={"name": "Test Config 2", "nodeType": "CONFIGURATION"}, **auth
                )
                assert response["name"] == "Test Config 2"
                assert response["nodeType"] == "CONFIGURATION"


        asyncio.run(testing())


# fmt: off
@pytest.mark.parametrize("usesetauth", [True, False])
@pytest.mark.parametrize("library", ["THREADS", "ASYNC"])
# fmt: on
def test_node_delete_01(clear_sar, library, usesetauth):  # noqa: F811
    """
    Basic tests for the 'node_delete' API.
    """

    root_folder_uid = create_root_folder()

    if not _is_async(library):
        with SaveRestoreAPI_Threads(base_url=base_url, timeout=2) as SR:
            auth = _select_auth(SR=SR, usesetauth=usesetauth)

            response = SR.node_add(
                root_folder_uid, node={"name": "Test Folder", "nodeType": "FOLDER"}, **auth)
            folder_uid = response["uniqueId"]

            response = SR.node_add(
                folder_uid, node={"name": "Test Config 1", "nodeType": "CONFIGURATION"}, **auth
            )
            node_uid_1 = response["uniqueId"]

            response = SR.node_add(
                folder_uid, node={"name": "Test Config 2", "nodeType": "CONFIGURATION"}, **auth
            )
            node_uid_2 = response["uniqueId"]

            SR.node_delete(node_uid_1)
            SR.node_delete(node_uid_2)
            SR.node_delete(folder_uid)

    else:
        async def testing():
            async with SaveRestoreAPI_Async(base_url=base_url, timeout=2) as SR:
                auth = _select_auth(SR=SR, usesetauth=usesetauth)

                response = await SR.node_add(
                    root_folder_uid, node={"name": "Test Folder", "nodeType": "FOLDER"}, **auth
                )
                folder_uid = response["uniqueId"]

                response = await SR.node_add(
                    folder_uid, node={"name": "Test Config 1", "nodeType": "CONFIGURATION"}, **auth
                )
                node_uid_1 = response["uniqueId"]

                response = await SR.node_add(
                    folder_uid, node={"name": "Test Config 2", "nodeType": "CONFIGURATION"}, **auth
                )
                node_uid_2 = response["uniqueId"]

                await SR.node_delete(node_uid_1)
                await SR.node_delete(node_uid_2)
                await SR.node_delete(folder_uid)

        asyncio.run(testing())


# fmt: off
@pytest.mark.parametrize("usesetauth", [True, False])
@pytest.mark.parametrize("library", ["THREADS", "ASYNC"])
# fmt: on
def test_nodes_delete_01(clear_sar, library, usesetauth):  # noqa: F811
    """
    Basic tests for the 'nodes_delete' API.
    """

    root_folder_uid = create_root_folder()

    if not _is_async(library):
        with SaveRestoreAPI_Threads(base_url=base_url, timeout=2) as SR:
            auth = _select_auth(SR=SR, usesetauth=usesetauth)

            response = SR.node_add(
                root_folder_uid, node={"name": "Test Folder", "nodeType": "FOLDER"}, **auth
            )
            folder_uid = response["uniqueId"]

            response = SR.node_add(
                folder_uid, node={"name": "Test Config 1", "nodeType": "CONFIGURATION"}, **auth
            )
            node_uid_1 = response["uniqueId"]

            response = SR.node_add(
                folder_uid, node={"name": "Test Config 2", "nodeType": "CONFIGURATION"}, **auth
            )
            node_uid_2 = response["uniqueId"]

            SR.nodes_delete([node_uid_1, node_uid_2], **auth)
            SR.nodes_delete([folder_uid], **auth)

    else:
        async def testing():
            async with SaveRestoreAPI_Async(base_url=base_url, timeout=2) as SR:
                auth = _select_auth(SR=SR, usesetauth=usesetauth)

                response = await SR.node_add(
                    root_folder_uid, node={"name": "Test Folder", "nodeType": "FOLDER"}, **auth
                )
                folder_uid = response["uniqueId"]

                response = await SR.node_add(
                    folder_uid, node={"name": "Test Config 1", "nodeType": "CONFIGURATION"}, **auth
                )
                node_uid_1 = response["uniqueId"]

                response = await SR.node_add(
                    folder_uid, node={"name": "Test Config 2", "nodeType": "CONFIGURATION"}, **auth
                )
                node_uid_2 = response["uniqueId"]

                await SR.nodes_delete([node_uid_1, node_uid_2], **auth)
                await SR.nodes_delete([folder_uid], **auth)

        asyncio.run(testing())


# fmt: off
@pytest.mark.parametrize("usesetauth", [True, False])
@pytest.mark.parametrize("library", ["THREADS", "ASYNC"])
# fmt: on
def test_node_get_children_01(clear_sar, library, usesetauth):  # noqa: F811
    """
    Basic tests for the 'node_get_children' API.
    """

    root_folder_uid = create_root_folder()

    if not _is_async(library):
        with SaveRestoreAPI_Threads(base_url=base_url, timeout=2) as SR:
            auth = _select_auth(SR=SR, usesetauth=usesetauth)

            response = SR.node_add(
                root_folder_uid, node={"name": "Parent Folder", "nodeType": "FOLDER"}, **auth
            )
            parent_uid = response["uniqueId"]

            response = SR.node_add(
                parent_uid, node={"name": "Child Folder", "nodeType": "FOLDER"}, **auth
            )
            folder_uid = response["uniqueId"]

            response = SR.node_add(
                parent_uid, node={"name": "Child Config", "nodeType": "CONFIGURATION"}, **auth
            )
            node_uid = response["uniqueId"]

            response = SR.node_get_children(parent_uid)
            assert len(response) == 2
            assert response[0]["uniqueId"] == folder_uid
            assert response[0]["nodeType"] == "FOLDER"
            assert response[1]["uniqueId"] == node_uid
            assert response[1]["nodeType"] == "CONFIGURATION"

    else:
        async def testing():
            async with SaveRestoreAPI_Async(base_url=base_url, timeout=2) as SR:
                auth = _select_auth(SR=SR, usesetauth=usesetauth)

                response = await SR.node_add(
                    root_folder_uid, node={"name": "Parent Folder", "nodeType": "FOLDER"}, **auth
                )
                parent_uid = response["uniqueId"]

                response = await SR.node_add(
                    parent_uid, node={"name": "Child Folder", "nodeType": "FOLDER"}, **auth
                )
                folder_uid = response["uniqueId"]

                response = await SR.node_add(
                    parent_uid, node={"name": "Child Config", "nodeType": "CONFIGURATION"}, **auth
                )
                node_uid = response["uniqueId"]

                response = await SR.node_get_children(parent_uid)
                assert len(response) == 2
                assert response[0]["uniqueId"] == folder_uid
                assert response[0]["nodeType"] == "FOLDER"
                assert response[1]["uniqueId"] == node_uid
                assert response[1]["nodeType"] == "CONFIGURATION"

        asyncio.run(testing())


# fmt: off
@pytest.mark.parametrize("usesetauth", [True, False])
@pytest.mark.parametrize("library", ["THREADS", "ASYNC"])
# fmt: on
def test_node_get_parent_01(clear_sar, library, usesetauth):  # noqa: F811
    """
    Tests for the 'node_get_parent' API.
    """

    root_folder_uid = create_root_folder()

    if not _is_async(library):
        with SaveRestoreAPI_Threads(base_url=base_url, timeout=2) as SR:
            auth = _select_auth(SR=SR, usesetauth=usesetauth)

            response = SR.node_add(
                root_folder_uid, node={"name": "Child Folder", "nodeType": "FOLDER"}, **auth
            )
            folder_uid = response["uniqueId"]

            response = SR.node_get_parent(folder_uid)
            assert response["uniqueId"] == root_folder_uid
            assert response["nodeType"] == "FOLDER"

    else:
        async def testing():
            async with SaveRestoreAPI_Async(base_url=base_url, timeout=2) as SR:
                auth = _select_auth(SR=SR, usesetauth=usesetauth)

                response = await SR.node_add(
                    root_folder_uid, node={"name": "Child Folder", "nodeType": "FOLDER"}, **auth
                )
                folder_uid = response["uniqueId"]

                response = await SR.node_get_parent(folder_uid)
                assert response["uniqueId"] == root_folder_uid
                assert response["nodeType"] == "FOLDER"

        asyncio.run(testing())
