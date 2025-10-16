import pytest
from epics import caget, caput

from save_and_restore_api import SaveRestoreAPI

base_url = "http://localhost:8080/save-restore"

admin_username, admin_password = "admin", "adminPass"
user_username, user_password = "user", "userPass"
read_username, read_password = "johndoe", "1234"

# Unit tests will create this folder and add nodes only inside this folder.
# This folder will be deleted after each test to ensure clean state.
root_folder_node_name = "unit-test-root-folder"
filter_prefix = "UNITTESTFILTER"


def _is_async(library):
    if library == "ASYNC":
        return True
    elif library == "THREADS":
        return False
    else:
        raise ValueError(f"Unknown library: {library!r}")


def _select_auth(*, SR, usesetauth):
    """
    Switch between using ``SR.auth_set()`` to set authentication for the whole session or
    using ``SR.auth_gen()`` to generate authentication object and pass it with each request.

    Parameters
    ----------
    SR : SaveRestoreAPI
        Instance of SaveRestoreAPI
    usesetauth : bool
        If True, use ``SR.auth_set()``, otherwise use ``SR.auth_gen()``.

    Returns
    -------
    dict
        If ``usesetauth`` is False, returns dictionary with authentication to be passed with each request,
        otherwise returns empty dictionary.
    """
    auth = {}
    if usesetauth:
        SR.auth_set(username=user_username, password=user_password)
    else:
        auth["auth"] = SR.auth_gen(username=user_username, password=user_password)
    return auth


def create_root_folder():
    """
    Create the root folder for unit tests if it does not exist. The folder
    is created using 'admin' user. Unit tests are not expected to delete it.
    The function is expected to be called at the beginning of the tests.
    It is expected that the folder does not exist, so the created folder is empty.

    Returns
    -------
    str
        Unique ID of the root folder.
    """
    with SaveRestoreAPI(base_url=base_url, timeout=2) as SR:
        SR.auth_set(username=admin_username, password=admin_password)
        res = SR.node_add(SR.ROOT_NODE_UID, node={"name": root_folder_node_name, "nodeType": "FOLDER"})
        return res["uniqueId"]


@pytest.fixture
def clear_sar():
    """
    Clear save-and-restore database before and after the experiment.
    """

    def _clear():
        """
        Remove all nodes from the database.
        """
        with SaveRestoreAPI(base_url=base_url, timeout=2) as SR:
            SR.auth_set(username=admin_username, password=admin_password)

            # Check if the root folder for unit tests exists
            res = SR.node_get_children(SR.ROOT_NODE_UID)
            root_folder_uid = None
            for node in res:
                if node["name"] == root_folder_node_name and node["nodeType"] == "FOLDER":
                    root_folder_uid = node["uniqueId"]
                    break

            if root_folder_uid is not None:
                # Create all nodes. Children always follow the parent
                n_uid = 0
                uids = [root_folder_uid]
                while n_uid < len(uids):
                    uid = uids[n_uid]
                    children = SR.node_get_children(uid)
                    ch_uids = [_["uniqueId"] for _ in children]
                    if ch_uids:
                        uids.extend(ch_uids)
                    n_uid += 1

                # Delete all nodes starting with children, including the root folder
                # First delete all composite snapshots
                uids_remaining = []
                for uid in reversed(uids):
                    resp = SR.node_get(uid)
                    if resp["nodeType"] == "COMPOSITE_SNAPSHOT":
                        SR.nodes_delete([uid])
                    else:
                        uids_remaining.append(uid)
                # Then delete all other nodes
                uids = uids_remaining
                for uid in uids:
                    SR.nodes_delete([uid])

            # Delete all filters
            filters = SR.filters_get()
            for f in filters:
                f_name = f["name"]
                if f_name.startswith(filter_prefix):
                    SR.filter_delete(f_name)

    _clear()
    yield
    _clear()


ioc_pvs = {
    "simulated:A": 1.0,
    "simulated:B": 2.0,
    "simulated:C": 3.0,
    "simulated:D": 4.0,
    "simulated:E": 5.0,
    "simulated:F": 6.0,
    "simulated:G": 7.0,
    "simulated:H": 8.0,
    "simulated:I": 9.0,
    "simulated:J": 10.0,
}


@pytest.fixture
def ioc():
    """
    Reset simulated IOC to initial values before and after the test
    """

    def _reset_ioc():
        for pv, val in ioc_pvs.items():
            v = caget(pv)
            if v != val:
                caput(pv, val)

    _reset_ioc()
    yield
    _reset_ioc()
