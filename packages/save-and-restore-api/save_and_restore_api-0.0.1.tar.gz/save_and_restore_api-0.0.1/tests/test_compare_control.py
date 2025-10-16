from __future__ import annotations

import asyncio

import pytest
from epics import caput

from save_and_restore_api import SaveRestoreAPI as SaveRestoreAPI_Threads
from save_and_restore_api.aio import SaveRestoreAPI as SaveRestoreAPI_Async

from .common import (
    _is_async,
    _select_auth,
    base_url,
    clear_sar,  # noqa: F401
    create_root_folder,
    ioc,  # noqa: F401
    ioc_pvs,
)

# =============================================================================================
#                         TESTS FOR COMPARISON-CONTROLLER API METHODS
# =============================================================================================


# fmt: off
@pytest.mark.parametrize("usesetauth", [True, False])
@pytest.mark.parametrize("library", ["THREADS", "ASYNC"])
# fmt: on
def test_compare_01(clear_sar, ioc, library, usesetauth):  # noqa: F811
    """
    Basic tests for the 'compare' API.
    """
    root_folder_uid = create_root_folder()

    if not _is_async(library):
        with SaveRestoreAPI_Threads(base_url=base_url, timeout=10) as SR:
            auth = _select_auth(SR=SR, usesetauth=usesetauth)

            configurationNode = {"name": "Test Config"}
            configurationData = {"pvList": [{"pvName": _} for _ in ioc_pvs.keys()]}

            response = SR.config_add(
                root_folder_uid,
                configurationNode=configurationNode,
                configurationData=configurationData,
                **auth
            )
            config_uid = response["configurationNode"]["uniqueId"]

            response = SR.take_snapshot_save(config_uid)
            shot_uid = response["snapshotData"]["uniqueId"]

            caput("simulated:C", 100)
            caput("simulated:D", 200)

            response = SR.compare(shot_uid)
            pv_sim_C, pv_sim_D = None, None
            for v in response:
                if v["pvName"] == "simulated:C":
                    pv_sim_C = v
                if v["pvName"] == "simulated:D":
                    pv_sim_D = v

            assert pv_sim_C["equal"] is False
            assert pv_sim_C["storedValue"]["value"] == 3
            assert pv_sim_C["liveValue"]["value"] == 100
            assert pv_sim_D["equal"] is False
            assert pv_sim_D["storedValue"]["value"] == 4
            assert pv_sim_D["liveValue"]["value"] == 200

    else:
        async def testing():
            async with SaveRestoreAPI_Async(base_url=base_url, timeout=2) as SR:
                auth = _select_auth(SR=SR, usesetauth=usesetauth)

                configurationNode = {"name": "Test Config"}
                configurationData = {"pvList": [{"pvName": _} for _ in ioc_pvs.keys()]}

                response = await SR.config_add(
                    root_folder_uid,
                    configurationNode=configurationNode,
                    configurationData=configurationData,
                    **auth
                )
                config_uid = response["configurationNode"]["uniqueId"]

                response = await SR.take_snapshot_save(config_uid)
                shot_uid = response["snapshotData"]["uniqueId"]

                caput("simulated:C", 100)
                caput("simulated:D", 200)

                response = await SR.compare(shot_uid)
                pv_sim_C, pv_sim_D = None, None
                for v in response:
                    if v["pvName"] == "simulated:C":
                        pv_sim_C = v
                    if v["pvName"] == "simulated:D":
                        pv_sim_D = v

                assert pv_sim_C["equal"] is False
                assert pv_sim_C["storedValue"]["value"] == 3
                assert pv_sim_C["liveValue"]["value"] == 100
                assert pv_sim_D["equal"] is False
                assert pv_sim_D["storedValue"]["value"] == 4
                assert pv_sim_D["liveValue"]["value"] == 200

        asyncio.run(testing())
