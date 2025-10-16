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
#                         TAG-CONTROLLER API METHODS
# =============================================================================================


# fmt: off
@pytest.mark.parametrize("usesetauth", [True, False])
@pytest.mark.parametrize("library", ["THREADS", "ASYNC"])
# fmt: on
def test_tags_01(clear_sar, library, usesetauth):  # noqa: F811
    """
    Tests for the 'tags_get', 'tags_add' and 'tags_delete' API.
    """

    root_folder_uid = create_root_folder()

    if not _is_async(library):
        with SaveRestoreAPI_Threads(base_url=base_url, timeout=2) as SR:
            auth = _select_auth(SR=SR, usesetauth=usesetauth)

            response = SR.node_add(root_folder_uid, node={"name": "folder", "nodeType": "FOLDER"}, **auth)
            folder_uid = response["uniqueId"]

            response = SR.config_add(
                folder_uid, configurationNode={"name": "config_1"}, configurationData={"pvList": []}, **auth
            )
            config_1_uid = response["configurationNode"]["uniqueId"]

            response = SR.config_add(
                folder_uid, configurationNode={"name": "config_2"}, configurationData={"pvList": []}, **auth
            )
            config_2_uid = response["configurationNode"]["uniqueId"]

            tag_1 = {"name": "tag_1"}
            tag_2 = {"name": "tag_2", "comment": "This is tag 2"}

            # Baseline number of tags (database may contain tags that are not created by the test)
            response = SR.tags_get()
            n_tags_baseline = len(response)

            response = SR.tags_add(uniqueNodeIds=[config_1_uid], tag=tag_1, **auth)
            assert len(response) == 1
            assert response[0]["uniqueId"] == config_1_uid
            assert [_["name"] for _ in response[0]["tags"]] == ["tag_1"]

            response = SR.tags_add(uniqueNodeIds=[config_1_uid, config_2_uid, folder_uid], tag=tag_2, **auth)
            assert len(response) == 3
            assert response[0]["uniqueId"] == config_1_uid
            assert [_["name"] for _ in response[0]["tags"]] == ["tag_1", "tag_2"]
            assert response[1]["uniqueId"] == config_2_uid
            assert [_["name"] for _ in response[1]["tags"]] == ["tag_2"]
            assert response[2]["uniqueId"] == folder_uid
            assert [_["name"] for _ in response[2]["tags"]] == ["tag_2"]

            response = SR.tags_get()  # Returns the list of ALL tags
            assert len(response) == 4 + n_tags_baseline

            response = SR.tags_delete(uniqueNodeIds=[config_1_uid, folder_uid], tag={"name": "tag_2"}, **auth)
            assert len(response) == 2
            assert response[0]["uniqueId"] == config_1_uid
            assert [_["name"] for _ in response[0]["tags"]] == ["tag_1"]
            assert response[1]["uniqueId"] == folder_uid
            assert [_["name"] for _ in response[1]["tags"]] == []

            response = SR.tags_get()
            assert len(response) == 2 + n_tags_baseline

    else:
        async def testing():
            async with SaveRestoreAPI_Async(base_url=base_url, timeout=2) as SR:
                auth = _select_auth(SR=SR, usesetauth=usesetauth)

                response = await SR.node_add(
                    root_folder_uid, node={"name": "folder", "nodeType": "FOLDER"}, **auth
                )
                folder_uid = response["uniqueId"]

                response = await SR.config_add(
                    folder_uid, configurationNode={"name": "config_1"}, configurationData={"pvList": []}, **auth
                )
                config_1_uid = response["configurationNode"]["uniqueId"]

                response = await SR.config_add(
                    folder_uid, configurationNode={"name": "config_2"}, configurationData={"pvList": []}, **auth
                )
                config_2_uid = response["configurationNode"]["uniqueId"]

                tag_1 = {"name": "tag_1"}
                tag_2 = {"name": "tag_2", "comment": "This is tag 2"}

                response = await SR.tags_get()
                n_tags_baseline = len(response)

                response = await SR.tags_add(uniqueNodeIds=[config_1_uid], tag=tag_1, **auth)
                assert len(response) == 1
                assert response[0]["uniqueId"] == config_1_uid
                assert [_["name"] for _ in response[0]["tags"]] == ["tag_1"]

                response = await SR.tags_add(
                    uniqueNodeIds=[config_1_uid, config_2_uid, folder_uid], tag=tag_2, **auth
                )
                assert len(response) == 3
                assert response[0]["uniqueId"] == config_1_uid
                assert [_["name"] for _ in response[0]["tags"]] == ["tag_1", "tag_2"]
                assert response[1]["uniqueId"] == config_2_uid
                assert [_["name"] for _ in response[1]["tags"]] == ["tag_2"]
                assert response[2]["uniqueId"] == folder_uid
                assert [_["name"] for _ in response[2]["tags"]] == ["tag_2"]

                response = await SR.tags_get()  # Returns the list of ALL tags
                assert len(response) == 4 + n_tags_baseline

                response = await SR.tags_delete(
                    uniqueNodeIds=[config_1_uid, folder_uid], tag={"name": "tag_2"}, **auth
                )
                assert len(response) == 2
                assert response[0]["uniqueId"] == config_1_uid
                assert [_["name"] for _ in response[0]["tags"]] == ["tag_1"]
                assert response[1]["uniqueId"] == folder_uid
                assert [_["name"] for _ in response[1]["tags"]] == []

                response = await SR.tags_get()
                assert len(response) == 2 + n_tags_baseline


        asyncio.run(testing())
