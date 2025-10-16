# save-and-restore-api

`save-and-restore-api` is a Python library for communicating with Save-and-Restore service
(CS Studio Phoebus). The package provides syncronous (thread-based) and asynchronous (asyncio)
versions of the API functions.

## How to Use the Library

The following example code creates a folder node named "My Folder" under the root node:

```python

from save_and_restore_api import SaveRestoreAPI

with SaveRestoreAPI(base_url="http://localhost:8080/save-restore") as SR:
    SR.auth_set(username="user", password="user_password")

    root_folder_uid = SR.ROOT_NODE_UID
    node={"name": "My Folder", "nodeType": "FOLDER"}

    folder = SR.node_add(root_folder_uid, node=node)

    print(f"Created folder metadata: {folder}")
```

Here is an async version of the same code:

```python

from save_and_restore_api.aio import SaveRestoreAPI

async with SaveRestoreAPI(base_url="http://localhost:8080/save-restore") as SR:
    await SR.auth_set(username="user", password="user_password")

    root_folder_uid = SR.ROOT_NODE_UID
    node={"name": "My Folder", "nodeType": "FOLDER"}

    folder = await SR.node_add(root_folder_uid, node=node)
    print(f"Created folder metadata: {folder}")
```

## `save-and-restore` CLI Tool

`save-and-restore` CLI tool is installed with the package. The tool allows performing
a limited set of basic operations on the nodes of the Save-and-Restore service.
The currently selected set of operations:

- LOGIN: test login credentials;

- CONFIG ADD: create configuration node based on a list of PVs read from a file;

- CONFIG UPDATE: update an existing configuration node based on a list of PVs read from a file;

- CONFIG GET: get information about an existing configuration node, including the list of PVs.

The tool was primarily developed for adding snapshot configurations to Save-and-Restore
based on lists of PVs loaded from local files. Typical use case is to create a configuration
based on a list of PVs read from an autosave (`.sav`) file saved by an IOC. Currently only
autosave files are supported, but support for other formats can be added if needed.
The list of supported functions can also be extended.

## How to use `save-and-restore` CLI Tool


Check login credentials. User password is requested interactively. Alternatively, the
password can be passed using environment variable `SAVE_AND_RESTORE_API_USER_PASSWORD``.

```bash
save-and-restore --base-url http://localhost:8080/save-restore --user-name=user LOGIN
```

Read the configuration node named 'eiger_config'. Print the full configuration data
(the list of PVs):

```bash
save-and-restore --base-url http://localhost:8080/save-restore \
CONFIG GET --config-name /detectors/imaging/eiger_config --show-data=ON
```

Create a new configuration node named 'eiger_config'. Load the list of PVs from
file ``eiger_pvs.sav``. Automatically create any missing parent folders in
the path:

```bash
save-and-restore --base-url=http://localhost:8080/save-restore --user-name=user \
--create-folders=ON CONFIG ADD --config-name=/detectors/imaging/eiger_config \
--file-name=eiger_pvs.sav --file-format=autosave
```

Update the existing configuration node named 'eiger_config'. Load the list of PVs
from the file ``eiger_pvs.sav``:

```bash
save-and-restore --base-url http://localhost:8080/save-restore --user-name=user \
CONFIG UPDATE --config-name /detectors/imaging/eiger_config \
--file-name eiger_pvs.sav --file-format autosave
```

Add new or update the existing configuration node named 'eiger_config'. Load the list of PVs
from the file ``eiger_pvs.sav``:

```bash
save-and-restore --base-url http://localhost:8080/save-restore --user-name=user \
CONFIG ADD-OR-UPDATE --config-name /detectors/imaging/eiger_config \
--file-name eiger_pvs.sav --file-format autosave
```

Print full list of options:

```bash
save-and-restore -h
```
