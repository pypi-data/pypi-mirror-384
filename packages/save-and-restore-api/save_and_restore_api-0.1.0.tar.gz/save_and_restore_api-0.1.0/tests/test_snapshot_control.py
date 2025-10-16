from __future__ import annotations

import asyncio

import pytest
from epics import caget, caput

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
#                         TESTS FOR SNAPSHOT-CONTROLLER API METHODS
# =============================================================================================


def test_epics(ioc):  # noqa: F811
    for pv, value in ioc_pvs.items():
        assert caget(pv) == value, f"PV {pv} has value {caget(pv)}, expected {value}"


# fmt: off
@pytest.mark.parametrize("usesetauth", [True, False])
@pytest.mark.parametrize("library", ["THREADS", "ASYNC"])
# fmt: on
def test_take_snapshot_get_01(clear_sar, library, usesetauth):  # noqa: F811
    """
    Basic tests for the 'take_snapshot_get' API.
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

            response = SR.take_snapshot_get(config_uid)

            snapshot_pv_values = {}
            for data in response:
                pv_name, val = data["configPv"]["pvName"], data["value"]["value"]
                snapshot_pv_values[pv_name] = val

            for pv, value in ioc_pvs.items():
                assert snapshot_pv_values[pv] == value, \
                    print(f"pv: {pv}, expected: {value}, got: {snapshot_pv_values[pv]}")

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

                response = await SR.take_snapshot_get(config_uid)

                snapshot_pv_values = {}
                for data in response:
                    pv_name, val = data["configPv"]["pvName"], data["value"]["value"]
                    snapshot_pv_values[pv_name] = val

                for pv, value in ioc_pvs.items():
                    assert snapshot_pv_values[pv] == value, \
                        print(f"pv: {pv}, expected: {value}, got: {snapshot_pv_values[pv]}")

        asyncio.run(testing())


# fmt: off
@pytest.mark.parametrize("usesetauth", [True, False])
@pytest.mark.parametrize("library", ["THREADS", "ASYNC"])
# fmt: on
def test_take_snapshot_save_01(clear_sar, library, usesetauth):  # noqa: F811
    """
    Basic tests for the 'take_snapshot_save', 'snapshot_get' API.
    """
    root_folder_uid = create_root_folder()
    name, comment = "test snapshot", "This is a test snapshot"

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

            response = SR.take_snapshot_save(config_uid, name=name, comment=comment, **auth)
            shot_uid = response["snapshotNode"]["uniqueId"]
            assert response["snapshotNode"]["name"] == name
            assert response["snapshotNode"]["description"] == comment
            assert response["snapshotData"]["uniqueId"] == shot_uid

            pv_data_list = response["snapshotData"]["snapshotItems"]

            snapshot_pv_values = {}
            for data in pv_data_list:
                pv_name, val = data["configPv"]["pvName"], data["value"]["value"]
                snapshot_pv_values[pv_name] = val

            for pv, value in ioc_pvs.items():
                assert snapshot_pv_values[pv] == value, \
                    print(f"pv: {pv}, expected: {value}, got: {snapshot_pv_values[pv]}")

            # Make sure the snapshot node is actually created
            response = SR.node_get(shot_uid)
            assert response["name"] == name
            assert response["description"] == comment
            assert response["uniqueId"] == shot_uid

            response = SR.snapshot_get(shot_uid)
            assert response["uniqueId"] == shot_uid
            assert len(response["snapshotItems"]) == len(ioc_pvs)

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

                response = await SR.take_snapshot_save(config_uid, name=name, comment=comment, **auth)
                shot_uid = response["snapshotNode"]["uniqueId"]
                assert response["snapshotNode"]["name"] == name
                assert response["snapshotNode"]["description"] == comment
                assert response["snapshotData"]["uniqueId"] == shot_uid

                pv_data_list = response["snapshotData"]["snapshotItems"]

                snapshot_pv_values = {}
                for data in pv_data_list:
                    pv_name, val = data["configPv"]["pvName"], data["value"]["value"]
                    snapshot_pv_values[pv_name] = val

                for pv, value in ioc_pvs.items():
                    assert snapshot_pv_values[pv] == value, \
                        print(f"pv: {pv}, expected: {value}, got: {snapshot_pv_values[pv]}")

                # Make sure the snapshot node is actually created
                response = await SR.node_get(shot_uid)
                assert response["name"] == name
                assert response["description"] == comment
                assert response["uniqueId"] == shot_uid

                response = await SR.snapshot_get(shot_uid)
                assert response["uniqueId"] == shot_uid
                assert len(response["snapshotItems"]) == len(ioc_pvs)

        asyncio.run(testing())


# fmt: off
@pytest.mark.parametrize("usesetauth", [True, False])
@pytest.mark.parametrize("library", ["THREADS", "ASYNC"])
# fmt: on
def test_snapshot_add_01(clear_sar, library, usesetauth):  # noqa: F811
    """
    Basic tests for the 'snapshot_add', 'snapshot_update' and 'snapshots_get' API.
    """
    root_folder_uid = create_root_folder()
    name1, comment1 = "test snapshot 1", "This is a test snapshot 1"
    name2, comment2 = "test snapshot 2", "This is a test snapshot 2"

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

            # Take a single snapshot (snapshot #1)
            response = SR.take_snapshot_save(config_uid, name=name1, comment=comment1, **auth)
            shot_uid_1 = response["snapshotNode"]["uniqueId"]
            snapshotNode1 = response["snapshotNode"]
            snapshotData1 = response["snapshotData"]

            # Create a copy of the first snapshot. Replace name, comment and delete uniqueId
            #   Note: uniqueId MUST be deleted
            #   As a result we get snapshot #2
            node = snapshotNode1.copy()
            node["name"] = name2
            del(node["uniqueId"])
            node["description"] = comment2
            data = snapshotData1.copy()
            del(data["uniqueId"])

            response = SR.snapshot_add(config_uid, snapshotNode=node, snapshotData=data, **auth)
            assert response["snapshotNode"]["uniqueId"] == response["snapshotData"]["uniqueId"]
            shot_uid_2 = response["snapshotNode"]["uniqueId"]
            snapshotNode2 = response["snapshotNode"]
            snapshotData2 = response["snapshotData"]
            assert snapshotData1["snapshotItems"] == snapshotData2["snapshotItems"]

            response = SR.node_get_children(config_uid)
            assert len(response) == 2

            # Now try updating the snapshot #2. Reduce the number of PVs to the first 5.
            data2 = snapshotData2.copy()
            data2["snapshotItems"] = data2["snapshotItems"][:5]
            response = SR.snapshot_update(snapshotNode=snapshotNode2, snapshotData=data2, **auth)
            assert len(response["snapshotData"]["snapshotItems"]) == 5
            assert response["snapshotNode"]["uniqueId"] == shot_uid_2
            assert response["snapshotData"]["uniqueId"] == shot_uid_2

            response = SR.node_get_children(config_uid)
            assert len(response) == 2

            # Get all the snapshots in the database (we created only two)
            #   We use only one directory node for the tests. There could be other
            #   snapshots in the database and they should not affect the test.
            response = SR.snapshots_get()
            assert len(response) >= 2
            uids = [_["uniqueId"] for _ in response]
            assert {shot_uid_1, shot_uid_2}.issubset(set(uids))

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

                # Take a single snapshot (snapshot #1)
                response = await SR.take_snapshot_save(config_uid, name=name1, comment=comment1, **auth)
                shot_uid_1 = response["snapshotNode"]["uniqueId"]
                snapshotNode1 = response["snapshotNode"]
                snapshotData1 = response["snapshotData"]

                # Create a copy of the first snapshot. Replace name, comment and delete uniqueId
                #   Note: uniqueId MUST be deleted
                #   As a result we get snapshot #2
                node = snapshotNode1.copy()
                node["name"] = name2
                del(node["uniqueId"])
                node["description"] = comment2
                data = snapshotData1.copy()
                del(data["uniqueId"])

                response = await SR.snapshot_add(config_uid, snapshotNode=node, snapshotData=data, **auth)
                assert response["snapshotNode"]["uniqueId"] == response["snapshotData"]["uniqueId"]
                shot_uid_2 = response["snapshotNode"]["uniqueId"]
                snapshotNode2 = response["snapshotNode"]
                snapshotData2 = response["snapshotData"]
                assert snapshotData1["snapshotItems"] == snapshotData2["snapshotItems"]

                response = await SR.node_get_children(config_uid)
                assert len(response) == 2

                # Now try updating the snapshot #2. Reduce the number of PVs to the first 5.
                data2 = snapshotData2.copy()
                data2["snapshotItems"] = data2["snapshotItems"][:5]
                response = await SR.snapshot_update(snapshotNode=snapshotNode2, snapshotData=data2, **auth)
                assert len(response["snapshotData"]["snapshotItems"]) == 5
                assert response["snapshotNode"]["uniqueId"] == shot_uid_2
                assert response["snapshotData"]["uniqueId"] == shot_uid_2

                response = await SR.node_get_children(config_uid)
                assert len(response) == 2

                # Get all the snapshots in the database (we created only two)
                #   We use only one directory node for the tests. There could be other
                #   snapshots in the database and they should not affect the test.
                response = await SR.snapshots_get()
                assert len(response) >= 2
                uids = [_["uniqueId"] for _ in response]
                assert {shot_uid_1, shot_uid_2}.issubset(set(uids))

        asyncio.run(testing())


# =============================================================================================
#                     TESTS FOR SNAPSHOT-RESTORE-CONTROLLER API METHODS
# =============================================================================================

# fmt: off
@pytest.mark.parametrize("restorenode", [True, False])
@pytest.mark.parametrize("usesetauth", [True, False])
@pytest.mark.parametrize("library", ["THREADS", "ASYNC"])
# fmt: on
def test_restore_node_01(clear_sar, library, usesetauth, restorenode):  # noqa: F811
    """
    Basic tests for the 'restore_node' and 'restore_items' API.
    """
    root_folder_uid = create_root_folder()
    name, comment = "test snapshot", "This is a test snapshot"

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

            # Take a single snapshot (snapshot #1)
            response = SR.take_snapshot_save(config_uid, name=name, comment=comment, **auth)
            shot_uid = response["snapshotNode"]["uniqueId"]
            snapshotData = response["snapshotData"]
            print(f"snapshotData: {snapshotData}")

            # Change all the PVs to zero
            for pv in ioc_pvs.keys():
                caput(pv, "0")

            if restorenode:
                response = SR.restore_node(shot_uid, **auth)
            else:
                response = SR.restore_items(snapshotItems=snapshotData["snapshotItems"], **auth)

            print(f"response: {response}")
            assert len(response) == 0

            for pv, v in ioc_pvs.items():
                assert int(caget(pv, "0")) == int(v), f"PV {pv} has value {caget(pv)}, expected {v}"

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

                # Take a single snapshot (snapshot #1)
                response = await SR.take_snapshot_save(config_uid, name=name, comment=comment, **auth)
                shot_uid = response["snapshotNode"]["uniqueId"]
                snapshotData = response["snapshotData"]
                print(f"snapshotData: {snapshotData}")

                # Change all the PVs to zero
                for pv in ioc_pvs.keys():
                    caput(pv, "0")

                if restorenode:
                    response = await SR.restore_node(shot_uid, **auth)
                else:
                    response = await SR.restore_items(snapshotItems=snapshotData["snapshotItems"], **auth)

                print(f"response: {response}")
                assert len(response) == 0  # Empty if restoration succeeded

                for pv, v in ioc_pvs.items():
                    assert int(caget(pv, "0")) == int(v), f"PV {pv} has value {caget(pv)}, expected {v}"

        asyncio.run(testing())


# =============================================================================================
#                         TESTS FOR COMPOSITE-SNAPSHOT-CONTROLLER API METHODS
# =============================================================================================

# fmt: off
@pytest.mark.parametrize("usesetauth", [True, False])
@pytest.mark.parametrize("library", ["THREADS", "ASYNC"])
# fmt: on
def test_composite_snapshot_add_01(clear_sar, ioc, library, usesetauth):  # noqa: F811
    """
    Test functionality of 'composite_snapshot_add', 'composite_snapshot_update'
    'composite_snapshot_consistency_check', 'composite_snapshot_get', 'composite_snapshot_get_nodes'
    and 'composite_snapshot_get_items' API.
    """
    root_folder_uid = create_root_folder()

    if not _is_async(library):
        with SaveRestoreAPI_Threads(base_url=base_url, timeout=10) as SR:
            auth = _select_auth(SR=SR, usesetauth=usesetauth)

            configurationNode1 = {"name": "Test Config1"}
            configurationData1 = {"pvList": [{"pvName": _} for _ in ioc_pvs.keys()][:5]}
            configurationNode2 = {"name": "Test Config2"}
            configurationData2 = {"pvList": [{"pvName": _} for _ in ioc_pvs.keys()][5:]}

            # Create two configurations
            response = SR.config_add(
                root_folder_uid,
                configurationNode=configurationNode1,
                configurationData=configurationData1,
                **auth
            )
            config_uid1 = response["configurationNode"]["uniqueId"]

            response = SR.config_add(
                root_folder_uid,
                configurationNode=configurationNode2,
                configurationData=configurationData2,
                **auth
            )
            config_uid2 = response["configurationNode"]["uniqueId"]

            response = SR.take_snapshot_save(config_uid1, name="Snapshot1", **auth)
            snapshot_uid1 = response["snapshotData"]["uniqueId"]
            response = SR.take_snapshot_save(config_uid2, name="Snapshot2", **auth)
            snapshot_uid2 = response["snapshotData"]["uniqueId"]

            response = SR.composite_snapshot_add(root_folder_uid,
                compositeSnapshotNode={
                    "name": "Composite Snapshot",
                    "nodeType": "COMPOSITE_SNAPSHOT",
                    "description": "Test composite snapshot",
                },
                compositeSnapshotData={"referencedSnapshotNodes": [snapshot_uid1, snapshot_uid2]},
                **auth,
            )
            composite_snapshot_uid = response["compositeSnapshotNode"]["uniqueId"]

            response = SR.composite_snapshot_get(composite_snapshot_uid)
            assert response["uniqueId"] == composite_snapshot_uid
            assert len(response["referencedSnapshotNodes"]) == 2

            response = SR.composite_snapshot_get_nodes(composite_snapshot_uid)
            assert len(response) == 2
            assert {response[0]["name"], response[1]["name"]} == {"Snapshot1", "Snapshot2"}

            response = SR.composite_snapshot_get_items(composite_snapshot_uid)
            assert len(response) == 10
            assert {_["configPv"]["pvName"] for _ in response} == set(ioc_pvs.keys())

            # Consistency check succeeds for the existing snapshot
            response = SR.composite_snapshot_consistency_check([composite_snapshot_uid])
            assert len(response) == 0

            # Attempt to add snapshot_uid1 the second time. This should result in 5 conflicting PVs
            response = SR.composite_snapshot_consistency_check([composite_snapshot_uid, snapshot_uid1])
            assert len(response) == 5

            # Update the composite snapshot
            compositeSnapshotNode = SR.node_get(composite_snapshot_uid)
            compositeSnapshotData = SR.composite_snapshot_get(composite_snapshot_uid)
            compositeSnapshotData["referencedSnapshotNodes"] = [snapshot_uid1]
            response = SR.composite_snapshot_update(
                compositeSnapshotNode=compositeSnapshotNode,
                compositeSnapshotData=compositeSnapshotData,
                **auth
            )
            assert response["compositeSnapshotNode"]["uniqueId"] == composite_snapshot_uid

            response = SR.composite_snapshot_get_items(composite_snapshot_uid)
            assert len(response) == 5

    else:
        async def testing():
            async with SaveRestoreAPI_Async(base_url=base_url, timeout=2) as SR:
                auth = _select_auth(SR=SR, usesetauth=usesetauth)

                configurationNode1 = {"name": "Test Config1"}
                configurationData1 = {"pvList": [{"pvName": _} for _ in ioc_pvs.keys()][:5]}
                configurationNode2 = {"name": "Test Config2"}
                configurationData2 = {"pvList": [{"pvName": _} for _ in ioc_pvs.keys()][5:]}

                # Create two configurations
                response = await SR.config_add(
                    root_folder_uid,
                    configurationNode=configurationNode1,
                    configurationData=configurationData1,
                    **auth
                )
                config_uid1 = response["configurationNode"]["uniqueId"]

                response = await SR.config_add(
                    root_folder_uid,
                    configurationNode=configurationNode2,
                    configurationData=configurationData2,
                    **auth
                )
                config_uid2 = response["configurationNode"]["uniqueId"]

                response = await SR.take_snapshot_save(config_uid1, name="Snapshot1", **auth)
                snapshot_uid1 = response["snapshotData"]["uniqueId"]
                response = await SR.take_snapshot_save(config_uid2, name="Snapshot2", **auth)
                snapshot_uid2 = response["snapshotData"]["uniqueId"]

                response = await SR.composite_snapshot_add(root_folder_uid,
                    compositeSnapshotNode={
                        "name": "Composite Snapshot",
                        "nodeType": "COMPOSITE_SNAPSHOT",
                        "description": "Test composite snapshot",
                    },
                    compositeSnapshotData={"referencedSnapshotNodes": [snapshot_uid1, snapshot_uid2]},
                    **auth,
                )
                composite_snapshot_uid = response["compositeSnapshotNode"]["uniqueId"]

                response = await SR.composite_snapshot_get(composite_snapshot_uid)
                assert response["uniqueId"] == composite_snapshot_uid
                assert len(response["referencedSnapshotNodes"]) == 2

                response = await SR.composite_snapshot_get_nodes(composite_snapshot_uid)
                assert len(response) == 2
                assert {response[0]["name"], response[1]["name"]} == {"Snapshot1", "Snapshot2"}

                response = await SR.composite_snapshot_get_items(composite_snapshot_uid)
                assert len(response) == 10
                assert {_["configPv"]["pvName"] for _ in response} == set(ioc_pvs.keys())

                # Consistency check succeeds for the existing snapshot
                response = await SR.composite_snapshot_consistency_check([composite_snapshot_uid])
                assert len(response) == 0

                # Attempt to add snapshot_uid1 the second time. This should result in 5 conflicting PVs
                response = await SR.composite_snapshot_consistency_check([composite_snapshot_uid, snapshot_uid1])
                assert len(response) == 5

                # Update the composite snapshot
                compositeSnapshotNode = await SR.node_get(composite_snapshot_uid)
                compositeSnapshotData = await SR.composite_snapshot_get(composite_snapshot_uid)
                compositeSnapshotData["referencedSnapshotNodes"] = [snapshot_uid1]
                response = await SR.composite_snapshot_update(
                    compositeSnapshotNode=compositeSnapshotNode,
                    compositeSnapshotData=compositeSnapshotData,
                    **auth
                )
                assert response["compositeSnapshotNode"]["uniqueId"] == composite_snapshot_uid

                response = await SR.composite_snapshot_get_items(composite_snapshot_uid)
                assert len(response) == 5

        asyncio.run(testing())
