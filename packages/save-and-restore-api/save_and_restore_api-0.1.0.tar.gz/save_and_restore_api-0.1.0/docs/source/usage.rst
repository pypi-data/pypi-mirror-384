=====
Usage
=====

The **save-and-restore-api** package provides a Python API library and **save-and-restore**
CLI tool. The library is Python developer-friendly interface for communication with
Save-and-Restore service via REST API. The **save-and-restore** CLI tool allows to perform
some operations on Save-and-Restore nodes from the command line and can be used in Bash
scripts.

'save-and-restore-api' Python library
=====================================

**save-and-restore-api** is a Python library for communicating with Save-and-Restore service
(CS Studio Phoebus). The package provides syncronous (thread-based) and asynchronous (asyncio)
versions of the API classes. The synchronous ``SaveRestoreAPI`` class is located in the
``save_and_restore_api`` module and the asynchronous counterpart is located in the
``save_and_restore_api.aio`` module. Both classes provide the same set of methods and properties.
The library is built on top of the **httpx** package.

All API requests to Save-and-Restore service except GET requests require authentication.
There are two ways to set authentication credentials. The first way is to call the ``auth_set()``
method of the API class instance. The method sets credentials for all subsequent API calls.
Repeatedly calling the method overwrites previously set credentials. The second way is to
generate the authentication object by calling the ``auth_gen()`` method and pass the returned
object to the ``auth`` parameter of the API methods. This method may be useful if the application
simultaneously supports multiple users with different credentials.

The ``SaveRestoreAPI`` class supports context manager protocol. The class can be used with
and without context manager. The choice depends on the application architecture. The context
manager automatically opens and closes the underlying HTTP socket:

.. code-block:: python

    from save_and_restore_api import SaveRestoreAPI

    with SaveRestoreAPI(base_url="http://localhost:8080/save-restore") as SR:

        # < Set authentication if necessary >
        SR.auth_set(username="user", password="user_password")

        # < The code that communicates with Save-and-Restore service using SR object>

If using the class without context manager, the application is responsible for opening
and closing the HTTP socket:

.. code-block:: python

    try:
        SR = SaveRestoreAPI(base_url="http://localhost:8080/save-restore")
        SR.open()

        # < Set authentication if necessary >
        SR.auth_set(username="user", password="user_password")

        # < The code that communicates with Save-and-Restore service using SR object>

    finally:
        SR.close()


Examples
========

The following example code creates a folder node named "My Folder" under the root node:

.. code-block:: python

    from save_and_restore_api import SaveRestoreAPI

    with SaveRestoreAPI(base_url="http://localhost:8080/save-restore") as SR:
        SR.auth_set(username="user", password="user_password")

        root_folder_uid = SR.ROOT_NODE_UID
        node={"name": "My Folder", "nodeType": "FOLDER"}

        folder = SR.node_add(root_folder_uid, node=node)

        print(f"Created folder metadata: {folder}")

Here is an async version of the same code:

.. code-block:: python

    from save_and_restore_api.aio import SaveRestoreAPI

    async with SaveRestoreAPI(base_url="http://localhost:8080/save-restore") as SR:
        await SR.auth_set(username="user", password="user_password")

        root_folder_uid = SR.ROOT_NODE_UID
        node={"name": "My Folder", "nodeType": "FOLDER"}

        folder = await SR.node_add(root_folder_uid, node=node)
        print(f"Created folder metadata: {folder}")

'save-and-restore' CLI tool
===========================

**save-and-restore** CLI tool is installed with the package. The tool allows performing
a limited set of basic operations on the nodes of the Save-and-Restore service.
The currently selected set of operations:

- **LOGIN**: test login credentials;

- **CONFIG ADD**: create configuration node based on a list of PVs read from a file;

- **CONFIG UPDATE**: update an existing configuration node based on a list of PVs read from a file;

- **CONFIG GET**: get information about an existing configuration node, including the list of PVs.

The tool was primarily developed for adding snapshot configurations to Save-and-Restore
based on lists of PVs loaded from local files. Typical use case is to create a configuration
based on a list of PVs read from an autosave (``.sav``) file saved by an IOC. Currently only
autosave files are supported, but support for other formats can be added if needed.
The list of supported functions can also be extended.

There are multiple ways to pass authentication credentials to the tool. The credentials include
user name and password. The user name can be passed using the ``--user-name`` command line
parameter. The tool interactively prompts for the password of the operation requires
authentication. If the user name is not specified, then the tool also prompts for it.
Alternatively, the user name and/or password can be passed using environment variables.

The following environment variables are supported:

- ``SAVE_AND_RESTORE_API_BASE_URL``: host URL (see '--base-url' parameter)
- ``SAVE_AND_RESTORE_API_USER_NAME``: user name (see '--user-name' parameter);
- ``SAVE_AND_RESTORE_API_USER_PASSWORD``: user password.

Examples of using 'save-and-restore' CLI tool
=============================================

Check login credentials. User password is requested interactively. Alternatively, the
password can be passed using environment variable ``SAVE_AND_RESTORE_API_USER_PASSWORD``.

.. code-block:: bash

    save-and-restore --base-url http://localhost:8080/save-restore --user-name=user LOGIN

Read the configuration node named 'eiger_config'. Print the full configuration data
(the list of PVs):

.. code-block:: bash

    save-and-restore --base-url http://localhost:8080/save-restore \
    CONFIG GET --config-name /detectors/imaging/eiger_config --show-data=ON

Create a new configuration node named 'eiger_config'. Load the list of PVs from
file ``eiger_pvs.sav``. Automatically create any missing parent folders in
the path:

.. code-block:: bash

    save-and-restore --base-url=http://localhost:8080/save-restore --user-name=user \
    --create-folders=ON CONFIG ADD --config-name=/detectors/imaging/eiger_config \
    --file-name=eiger_pvs.sav --file-format=autosave

Update the existing configuration node named 'eiger_config'. Load the list of PVs
from the file ``eiger_pvs.sav``:

.. code-block:: bash

    save-and-restore --base-url http://localhost:8080/save-restore --user-name=user \
    CONFIG UPDATE --config-name /detectors/imaging/eiger_config \
    --file-name eiger_pvs.sav --file-format autosave

Add new or update the existing configuration node named 'eiger_config'. Load the list of PVs
from the file ``eiger_pvs.sav``:

.. code-block:: bash

    save-and-restore --base-url http://localhost:8080/save-restore --user-name=user \
    CONFIG ADD-OR-UPDATE --config-name /detectors/imaging/eiger_config \
    --file-name eiger_pvs.sav --file-format autosave

Print full list of options:

.. code-block:: bash

    save-and-restore -h
