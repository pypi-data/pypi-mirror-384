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
    root_folder_node_name,
)

# =============================================================================================
#                         TESTS FOR COMPARISON-CONTROLLER API METHODS
# =============================================================================================


# fmt: off
@pytest.mark.parametrize("usemove", [True, False])
@pytest.mark.parametrize("usesetauth", [True, False])
@pytest.mark.parametrize("library", ["THREADS", "ASYNC"])
# fmt: on
def test_structure_move_01(clear_sar, library, usesetauth, usemove):  # noqa: F811
    """
    Basic tests for the 'move' and 'copy' API.
    """
    root_folder_uid = create_root_folder()

    if not _is_async(library):
        with SaveRestoreAPI_Threads(base_url=base_url, timeout=10) as SR:
            auth = _select_auth(SR=SR, usesetauth=usesetauth)
            auth_admin = {"auth": SR.auth_gen(username="admin", password="adminPass")}

            # Create two folders
            response = SR.node_add(
                root_folder_uid, node={"name": "Folder1", "nodeType": "FOLDER"}, **auth
            )
            folder1_uid = response["uniqueId"]
            response = SR.node_add(
                root_folder_uid, node={"name": "Folder2", "nodeType": "FOLDER"}, **auth
            )
            folder2_uid = response["uniqueId"]

            # Create two configurations in folder1
            response = SR.config_add(
                folder1_uid,
                configurationNode={"name": "Config1"},
                configurationData={"pvList": []},
                **auth
            )
            config1_uid = response["configurationNode"]["uniqueId"]
            response = SR.config_add(
                folder1_uid,
                configurationNode={"name": "Config2"},
                configurationData={"pvList": []},
                **auth
            )
            config2_uid = response["configurationNode"]["uniqueId"]

            response = SR.node_get_children(folder1_uid)
            assert len(response) == 2
            response = SR.node_get_children(folder2_uid)
            assert len(response) == 0

            if usemove:
                response = SR.structure_move([config1_uid, config2_uid], newParentNodeId=folder2_uid, **auth_admin)
                assert response["uniqueId"] == folder2_uid
                n_folder1, n_folder2 = 0, 2
            else:
                response = SR.structure_copy([config1_uid, config2_uid], newParentNodeId=folder2_uid, **auth_admin)
                assert response["uniqueId"] == folder2_uid
                n_folder1, n_folder2 = 2, 2

            response = SR.node_get_children(folder1_uid)
            assert len(response) == n_folder1
            response = SR.node_get_children(folder2_uid)
            assert len(response) == n_folder2

    else:
        async def testing():
            async with SaveRestoreAPI_Async(base_url=base_url, timeout=2) as SR:
                auth = _select_auth(SR=SR, usesetauth=usesetauth)
                auth_admin = {"auth": SR.auth_gen(username="admin", password="adminPass")}

                # Create two folders
                response = await SR.node_add(
                    root_folder_uid, node={"name": "Folder1", "nodeType": "FOLDER"}, **auth
                )
                folder1_uid = response["uniqueId"]
                response = await SR.node_add(
                    root_folder_uid, node={"name": "Folder2", "nodeType": "FOLDER"}, **auth
                )
                folder2_uid = response["uniqueId"]

                # Create two configurations in folder1
                response = await SR.config_add(
                    folder1_uid,
                    configurationNode={"name": "Config1"},
                    configurationData={"pvList": []},
                    **auth
                )
                config1_uid = response["configurationNode"]["uniqueId"]
                response = await SR.config_add(
                    folder1_uid,
                    configurationNode={"name": "Config2"},
                    configurationData={"pvList": []},
                    **auth
                )
                config2_uid = response["configurationNode"]["uniqueId"]

                response = await SR.node_get_children(folder1_uid)
                assert len(response) == 2
                response = await SR.node_get_children(folder2_uid)
                assert len(response) == 0

                if usemove:
                    response = await SR.structure_move(
                        [config1_uid, config2_uid], newParentNodeId=folder2_uid, **auth_admin
                    )
                    assert response["uniqueId"] == folder2_uid
                    n_folder1, n_folder2 = 0, 2
                else:
                    response = await SR.structure_copy(
                        [config1_uid, config2_uid], newParentNodeId=folder2_uid, **auth_admin
                    )
                    assert response["uniqueId"] == folder2_uid
                    n_folder1, n_folder2 = 2, 2

                response = await SR.node_get_children(folder1_uid)
                assert len(response) == n_folder1
                response = await SR.node_get_children(folder2_uid)
                assert len(response) == n_folder2

        asyncio.run(testing())



# fmt: off
@pytest.mark.parametrize("usesetauth", [True, False])
@pytest.mark.parametrize("library", ["THREADS", "ASYNC"])
# fmt: on
def test_structure_path_01(clear_sar, library, usesetauth):  # noqa: F811
    """
    Basic tests for the 'path_get' and 'path_nodes' API.
    """
    root_folder_uid = create_root_folder()

    if not _is_async(library):
        with SaveRestoreAPI_Threads(base_url=base_url, timeout=10) as SR:
            auth = _select_auth(SR=SR, usesetauth=usesetauth)

            # Create two folders
            folder1_name = "Folder1"
            response = SR.node_add(
                root_folder_uid, node={"name": folder1_name, "nodeType": "FOLDER"}, **auth
            )
            folder1_uid = response["uniqueId"]

            node_name = "Node Name"
            response = SR.node_add(
                folder1_uid, node={"name": node_name, "nodeType": "FOLDER"}, **auth
            )
            folder2_uid = response["uniqueId"]

            # Create two configurations in folder1
            response = SR.config_add(
                folder1_uid,
                configurationNode={"name": node_name},
                configurationData={"pvList": []},
                **auth
            )

            folder1_path = SR.structure_path_get(folder2_uid)
            assert folder1_path == "/" + root_folder_node_name + "/" + folder1_name + "/" + node_name

            response = SR.structure_path_nodes(folder1_path)
            assert len(response) == 2

    else:
        async def testing():
            async with SaveRestoreAPI_Async(base_url=base_url, timeout=2) as SR:
                auth = _select_auth(SR=SR, usesetauth=usesetauth)

                # Create two folders
                folder1_name = "Folder1"
                response = await SR.node_add(
                    root_folder_uid, node={"name": folder1_name, "nodeType": "FOLDER"}, **auth
                )
                folder1_uid = response["uniqueId"]

                node_name = "Node Name"
                response = await SR.node_add(
                    folder1_uid, node={"name": node_name, "nodeType": "FOLDER"}, **auth
                )
                folder2_uid = response["uniqueId"]

                # Create two configurations in folder1
                response = await SR.config_add(
                    folder1_uid,
                    configurationNode={"name": node_name},
                    configurationData={"pvList": []},
                    **auth
                )

                folder1_path = await SR.structure_path_get(folder2_uid)
                assert folder1_path == "/" + root_folder_node_name + "/" + folder1_name + "/" + node_name

                response = await SR.structure_path_nodes(folder1_path)
                assert len(response) == 2

        asyncio.run(testing())
