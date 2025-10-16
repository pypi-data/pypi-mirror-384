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
    user_password,  # noqa: F401
    user_username,
)

# =============================================================================================
#                         CONFIGURATION-CONTROLLER API METHODS
# =============================================================================================


# fmt: off
@pytest.mark.parametrize("usesetauth", [True, False])
@pytest.mark.parametrize("library", ["THREADS", "ASYNC"])
# fmt: on
def test_config_add_01(clear_sar, library, usesetauth):  # noqa: F811
    """
    Tests for the 'config_add' and 'config_get' API.
    """

    root_folder_uid = create_root_folder()

    pv_list = [
            {
                "pvName": "13SIM1:{SimDetector-Cam:1}cam1:BinX"
            },
            {
                "pvName": "13SIM1:{SimDetector-Cam:1}cam1:BinY",
                "comparison": {
                    "comparisonMode": "ABSOLUTE",
                    "tolerance": 2.7
                }
            },
            {
                "pvName": "13SIM1:{SimDetector-Cam:2}cam2:BinX",
                "readbackPvName": None,
                "readOnly": False,
            },
            {
                "pvName": "13SIM1:{SimDetector-Cam:2}cam2:BinY",
                "readbackPvName": None,
                "readOnly": False,
            }
    ]

    configurationNode = {
        "name": "Config",
    }
    configurationData = {
        "pvList": pv_list,
    }

    if not _is_async(library):
        with SaveRestoreAPI_Threads(base_url=base_url, timeout=2) as SR:
            auth = _select_auth(SR=SR, usesetauth=usesetauth)

            response = SR.node_add(root_folder_uid, node={"name": "Child Folder", "nodeType": "FOLDER"}, **auth)
            folder_uid = response["uniqueId"]


            response = SR.config_add(
                folder_uid, configurationNode=configurationNode, configurationData=configurationData, **auth
            )
            assert response["configurationNode"]["name"] == "Config"
            assert response["configurationNode"]["nodeType"] == "CONFIGURATION"
            assert response["configurationNode"]["userName"] == user_username
            assert len(response["configurationData"]["pvList"]) == len(pv_list)

            config_uid = response["configurationNode"]["uniqueId"]

            response = SR.config_get(config_uid)
            assert response["uniqueId"] == config_uid
            assert len(response["pvList"]) == len(pv_list)

            response = SR.node_get(config_uid)
            assert response["uniqueId"] == config_uid
            assert response["name"] == "Config"
            assert response["nodeType"] == "CONFIGURATION"
            assert response["userName"] == user_username

    else:
        async def testing():
            async with SaveRestoreAPI_Async(base_url=base_url, timeout=2) as SR:
                auth = _select_auth(SR=SR, usesetauth=usesetauth)

                node = {"name": "Child Folder", "nodeType": "FOLDER"}
                response = await SR.node_add(root_folder_uid, node=node, **auth)
                folder_uid = response["uniqueId"]

                response = await SR.config_add(
                    folder_uid, configurationNode=configurationNode, configurationData=configurationData, **auth
                )
                assert response["configurationNode"]["name"] == "Config"
                assert response["configurationNode"]["nodeType"] == "CONFIGURATION"
                assert response["configurationNode"]["userName"] == user_username
                assert len(response["configurationData"]["pvList"]) == len(pv_list)

                config_uid = response["configurationNode"]["uniqueId"]

                response = await SR.config_get(config_uid)
                assert response["uniqueId"] == config_uid
                assert len(response["pvList"]) == len(pv_list)

                response = await SR.node_get(config_uid)
                assert response["uniqueId"] == config_uid
                assert response["name"] == "Config"
                assert response["nodeType"] == "CONFIGURATION"
                assert response["userName"] == user_username

        asyncio.run(testing())


# fmt: off
@pytest.mark.parametrize("usesetauth", [True, False])
@pytest.mark.parametrize("library", ["THREADS", "ASYNC"])
# fmt: on
def test_config_update_01(clear_sar, library, usesetauth):  # noqa: F811
    """
    Tests for the 'config_update' API.
    """

    root_folder_uid = create_root_folder()

    pv_list1 = [{"pvName": "13SIM1:{SimDetector-Cam:1}cam1:BinY"}]
    pv_list2 = [{"pvName": "13SIM1:{SimDetector-Cam:1}cam1:BinX"}]

    if not _is_async(library):
        with SaveRestoreAPI_Threads(base_url=base_url, timeout=2) as SR:
            auth = _select_auth(SR=SR, usesetauth=usesetauth)

            response = SR.node_add(root_folder_uid, node={"name": "Child Folder", "nodeType": "FOLDER"}, **auth)
            folder_uid = response["uniqueId"]

            response = SR.config_add(
                folder_uid, configurationNode={"name": "Config"}, configurationData={"pvList": pv_list1}, **auth
            )
            configurationNode = response["configurationNode"]
            configurationData = response["configurationData"]

            assert configurationNode["name"] == "Config"
            assert configurationNode["nodeType"] == "CONFIGURATION"
            assert configurationNode["userName"] == user_username
            assert len(configurationData["pvList"]) == 1
            assert configurationData["pvList"][0]["pvName"] == pv_list1[0]["pvName"]

            config_uid = configurationNode["uniqueId"]

            configurationData["pvList"] = pv_list2
            response = SR.config_update(
                configurationNode=configurationNode, configurationData=configurationData, **auth
            )

            configurationNode = response["configurationNode"]
            configurationData = response["configurationData"]

            assert configurationNode["name"] == "Config"
            assert configurationNode["uniqueId"] == config_uid
            assert configurationData["pvList"][0]["pvName"] == pv_list2[0]["pvName"]
            assert configurationData["uniqueId"] == config_uid

            response = SR.config_get(config_uid)
            assert response["uniqueId"] == config_uid
            assert len(response["pvList"]) == len(pv_list2)
            assert response["pvList"][0]["pvName"] == pv_list2[0]["pvName"]

            response = SR.node_get(config_uid)
            assert response["uniqueId"] == config_uid
            assert response["name"] == "Config"
            assert response["nodeType"] == "CONFIGURATION"
            assert response["userName"] == user_username

    else:
        async def testing():
            async with SaveRestoreAPI_Async(base_url=base_url, timeout=2) as SR:
                auth = _select_auth(SR=SR, usesetauth=usesetauth)

                node = {"name": "Child Folder", "nodeType": "FOLDER"}
                response = await SR.node_add(root_folder_uid, node=node, **auth)
                folder_uid = response["uniqueId"]

                response = await SR.config_add(
                    folder_uid,
                    configurationNode={"name": "Config"},
                    configurationData={"pvList": pv_list1},
                    **auth,
                )
                configurationNode = response["configurationNode"]
                configurationData = response["configurationData"]

                assert configurationNode["name"] == "Config"
                assert configurationNode["nodeType"] == "CONFIGURATION"
                assert configurationNode["userName"] == user_username
                assert len(configurationData["pvList"]) == 1
                assert configurationData["pvList"][0]["pvName"] == pv_list1[0]["pvName"]

                config_uid = configurationNode["uniqueId"]

                configurationData["pvList"] = pv_list2
                response = await SR.config_update(
                    configurationNode=configurationNode, configurationData=configurationData, **auth
                )

                configurationNode = response["configurationNode"]
                configurationData = response["configurationData"]

                assert configurationNode["name"] == "Config"
                assert configurationNode["uniqueId"] == config_uid
                assert configurationData["pvList"][0]["pvName"] == pv_list2[0]["pvName"]
                assert configurationData["uniqueId"] == config_uid

                response = await SR.config_get(config_uid)
                assert response["uniqueId"] == config_uid
                assert len(response["pvList"]) == len(pv_list2)
                assert response["pvList"][0]["pvName"] == pv_list2[0]["pvName"]

                response = await SR.node_get(config_uid)
                assert response["uniqueId"] == config_uid
                assert response["name"] == "Config"
                assert response["nodeType"] == "CONFIGURATION"
                assert response["userName"] == user_username

        asyncio.run(testing())
