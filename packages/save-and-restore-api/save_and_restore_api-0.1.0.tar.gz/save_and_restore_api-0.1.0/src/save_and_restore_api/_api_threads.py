import httpx

from ._api_base import _SaveRestoreAPI_Base


class SaveRestoreAPI(_SaveRestoreAPI_Base):
    def open(self):
        """
        Open HTTP connection to the server. The function creates the HTTP client
        that is used to send requests to the server.

        Examples
        --------

        .. code-block:: python

            from save_and_restore_api import SaveRestoreAPI

            SR = SaveRestoreAPI(base_url="http://localhost:8080/save-restore")
            SR.open()
            info = SR.info_get()
            print(f"info={info}")
            SR.close()

        Async version:

        .. code-block:: python

            from save_and_restore_api.aio import SaveRestoreAPI

            SR = SaveRestoreAPI(base_url="http://localhost:8080/save-restore")
            await SR.open()
            info = await SR.info_get()
            print(f"info={info}")
            await SR.close()
        """
        if self._client is None:
            self._client = httpx.Client(base_url=self._base_url, timeout=self._timeout)

    def close(self):
        """
        Close HTTP connection to the server. The function closes the HTTP client.
        """
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self):
        """
        Support for the context manager protocol.

        Examples
        --------

        .. code-block:: python

            from save_and_restore_api import SaveRestoreAPI

            with SaveRestoreAPI(base_url="http://localhost:8080/save-restore") as SR:
                info = SR.info_get()
                print(f"info={info}")

        Async version:

        .. code-block:: python

            from save_and_restore_api.aio import SaveRestoreAPI

            async with SaveRestoreAPI(base_url="http://localhost:8080/save-restore") as SR:
                info = await SR.info_get()
                print(f"info={info}")
        """
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Support for the context manager protocol.
        """
        self.close()

    def send_request(
        self, method, url, *, body_json=None, params=None, headers=None, data=None, timeout=None, auth=None
    ):
        """
        Send HTTP request to the server.

        Parameters
        ----------
        method : str
            HTTP method: GET, POST, PUT, DELETE
        url : str
            URL (path) of the API endpoint. If ``base_url`` is set in the class constructor, then only
            the remaining part of the URL should be specified here.
        body_json : dict, optional
            Dictionary to be sent as JSON in the request body.
        params : dict, optional
            Dictionary of query parameters to be sent in the URL.
        headers : dict, optional
            Dictionary of HTTP headers to be sent with the request.
        data : dict, optional
            Dictionary of form data to be sent in the request body.
        timeout : float, optional
            Timeout for this request in seconds. If not specified or None, the default timeout set in the
            class constructor is used.
        auth : httpx.BasicAuth, optional
            Object with authentication data (generated using ``auth_gen()`` method). If not specified or None,
            then the authentication set using ``auth_set`` method is used.

        Returns
        -------
        dict, str
            Response from the server. If the response contains JSON data, then a dictionary is returned.
            Otherwise, the response text is returned.

        Raises
        ------
        RequestParameterError
            Invalid parameter value or type
        RequestTimeoutError
            Communication timeout error
        HTTPRequestError, HTTPClientError, HTTPServerError
            Error while processing the request or communicating with the server.
        """
        try:
            client_response = None
            kwargs = self._prepare_request(
                method=method,
                body_json=body_json,
                params=params,
                headers=headers,
                data=data,
                timeout=timeout,
                auth=auth,
            )
            client_response = self._client.request(method, url, **kwargs)
            response = self._process_response(client_response=client_response)
        except Exception:
            response = self._process_comm_exception(
                method=method, body_json=body_json, client_response=client_response
            )

        return response

    # =============================================================================================
    #                         INFO-CONTROLLER API METHODS
    # =============================================================================================

    def info_get(self):
        """
        Returns information about the Save and Restore service.

        API: GET /

        Returns
        -------
        dict
            Dictionary that contains service information.
        """
        method, url = self._prepare_info_get()
        return self.send_request(method, url)

    def version_get(self):
        """
        Returns information on the name and current version of the service.

        API: GET /verson

        Returns
        -------
        str
            String that contains service name (``service-save-and-restore``) and the service version
            number.
        """
        method, url = self._prepare_version_get()
        return self.send_request(method, url)

    # =============================================================================================
    #                         SEARCH-CONTROLLER API METHODS
    # =============================================================================================

    def search(self, allRequestParams):
        """
        Send search query to the database. Example search queries (``allRequestParams``):
        search for nodes with name containing 'test config': ``{"name": "test config"}``,
        search for nodes with the description containing 'backup pvs': ``{"description": "backup pvs"}``,

        Returns a dictionary with the following keys: ``hitCount`` - the number of matching nodes,
        ``nodes`` - a list of matching nodes (not including data).

        API: GET /search

        Parameters
        ----------
        allRequestParams : dict
            Dictionary with search parameters, e.g. ``{"name": "test config"}`` or
            ``{"description": "backup pvs"}``.

        Returns
        -------
        dict
            Dictionary with the following keys: ``hitCount`` - the number of matching nodes,
            ``nodes`` - a list of matching nodes (not including data).
        """
        method, url, params = self._prepare_search(allRequestParams=allRequestParams)
        return self.send_request(method, url, params=params)

    # =============================================================================================
    #                         HELP-RESOURCE API METHODS
    # =============================================================================================

    def help(self, what, *, lang=None):
        """
        Download help pages, e.g. ``/help/SearchHelp``

        API: GET /help/{what}?lang={lang}

        Parameters
        ----------
        what : str
            Name of the help page, e.g. ``/help/SearchHelp``.
        lang : str, optional
            Language code.
        """
        method, url, params = self._prepare_help(what=what, lang=lang)
        return self.send_request(method, url, params=params)

    # =============================================================================================
    #                         AUTHENTICATION-CONTROLLER API METHODS
    # =============================================================================================

    def login(self, *, username, password):
        """
        Validate user credentials and return user information. Raises ``HTTPClientError``
        if the login fails.

        API: POST /login

        Parameters
        ----------
        username : str
            User name.
        password : str
            User password.

        Returns
        -------
        None
        """
        method, url, body_json = self._prepare_login(username=username, password=password)
        return self.send_request(method, url, body_json=body_json)

    # =============================================================================================
    #                         NODE-CONTROLLER API METHODS
    # =============================================================================================

    def node_get(self, uniqueNodeId):
        """
        Returns the metadata for the node with specified node UID.

        API: GET /node/{uniqueNodeId}

        Parameters
        ----------
        uniqueNodeId : str
            Unique ID of the node.

        Returns
        -------
        dict
            Node metadata as returned by the server.

        Examples
        --------

        .. code-block:: python

            from save_and_restore_api import SaveRestoreAPI

            with SaveRestoreAPI(base_url="http://localhost:8080/save-restore") as SR:
                root_folder_uid = SR.ROOT_NODE_UID
                root_folder = SR.node_get(root_folder_uid)
                print(f"Root folder metadata: {root_folder}")

        Async version:
        .. code-block:: python

            from save_and_restore_api.aio import SaveRestoreAPI

            async with SaveRestoreAPI(base_url="http://localhost:8080/save-restore") as SR:
                root_folder_uid = SR.ROOT_NODE_UID
                root_folder = await SR.node_get(root_folder_uid)
                print(f"Root folder metadata: {root_folder}")
        """
        method, url = self._prepare_node_get(uniqueNodeId=uniqueNodeId)
        return self.send_request(method, url)

    def nodes_get(self, uniqueIds):
        """
        Returns metadata for multiple nodes specified by a list of UIDs. This API is
        similar to calling ``node_get()`` multiple times, but is more efficient.

        API: GET /nodes

        Parameters
        ----------
        uniqueIds : list of str
            List of node unique IDs.

        Returns
        -------
        list of dict
            List of node metadata as returned by the server.
        """
        method, url, body_json = self._prepare_nodes_get(uniqueIds=uniqueIds)
        return self.send_request(method, url, body_json=body_json)

    def node_add(self, parentNodeId, *, node, auth=None, **kwargs):
        """
        Creates a new node under the specified parent node.

        API: PUT /node?parentNodeId={parentNodeId}

        Parameters
        ----------
        parentNodeId : str
            Unique ID of the parent node.
        node : dict
            Node metadata. The required fields are ``name`` and ``nodeType``.
            Supported node types: ``"FOLDER"``, ``"CONFIGURATION"``.
        auth : httpx.BasicAuth
            Object with authentication data (generated using ``auth_gen()`` method).

        Returns
        -------
        dict
            Created node metadata as returned by the server.

        Examples
        --------

        .. code-block:: python

            from save_and_restore_api import SaveRestoreAPI

            with SaveRestoreAPI(base_url="http://localhost:8080/save-restore") as SR:
                SR.auth_set(username="user", password="user_password")
                root_folder_uid = SR.ROOT_NODE_UID
                node  = {"name": "My Folder", "nodeType": "FOLDER"}
                folder = SR.node_add(root_folder_uid, node=node)
                print(f"Created folder metadata: {folder}")

        Async version:

        .. code-block:: python

            from save_and_restore_api.aio import SaveRestoreAPI

            async with SaveRestoreAPI(base_url="http://localhost:8080/save-restore") as SR:
                await SR.auth_set(username="user", password="user_password")
                root_folder_uid = SR.ROOT_NODE_UID
                node  = {"name": "My Folder", "nodeType": "FOLDER"}
                folder = await SR.node_add(root_folder_uid, node=node)
                print(f"Created folder metadata: {folder}")
        """
        method, url, params, body_json = self._prepare_node_add(parentNodeId=parentNodeId, node=node)
        return self.send_request(method, url, params=params, body_json=body_json, auth=auth)

    def node_delete(self, nodeId, *, auth=None):
        """
        Deletes the node with specified node ID. The call fails if the node can
        not be deleted, e.g. the node is a non-empty folder.

        API: DELETE /node/{nodeId}

        Parameters
        ----------
        nodeId : str
            Unique ID of the node to be deleted.
        auth : httpx.BasicAuth
            Object with authentication data (generated using ``auth_gen()`` method).

        Returns
        -------
        None
        """
        method, url = self._prepare_node_delete(nodeId=nodeId)
        return self.send_request(method, url, auth=auth)

    def nodes_delete(self, uniqueIds, *, auth=None):
        """
        Deletes multiple nodes specified by the list of UIDs. The API goes through the nodes in the list
        and deletes the nodes. It fails if the node can not be deleted and does not try to delete the
        following nodes.

        API: DELETE /node

        Parameters
        ----------
        uniqueIds : list[str]
            List of UIDs of the nodes to delete.
        auth : httpx.BasicAuth
            Object with authentication data (generated using ``auth_gen()`` method).

        Returns
        -------
        None
        """
        method, url, body_json = self._prepare_nodes_delete(uniqueIds=uniqueIds)
        return self.send_request(method, url, body_json=body_json, auth=auth)

    def node_get_children(self, uniqueNodeId):
        """
        Returns the list of child nodes for the node with specified UID.

        API: GET /node/{uniqueNodeId}/children

        Parameters
        ----------
        uniqueNodeId : str
            Unique ID of the node.

        Returns
        -------
        list[dict]
            List of child node nodes. The list elements are dictionaries containing
            the node metadata as returned by the server.
        """
        method, url = self._prepare_node_get_children(uniqueNodeId=uniqueNodeId)
        return self.send_request(method, url)

    def node_get_parent(self, uniqueNodeId):
        """
        Returns the parent node for the specified node UID.

        API: GET /node/{uniqueNodeId}/parent

        Parameters
        ----------
        uniqueNodeId : str
            Unique ID of the node.

        Returns
        -------
        dict
            Parent node metadata as returned by the server.
        """
        method, url = self._prepare_node_get_parent(uniqueNodeId=uniqueNodeId)
        return self.send_request(method, url)

    # =============================================================================================
    #                         CONFIGURATION-CONTROLLER API METHODS
    # =============================================================================================

    def config_get(self, uniqueNodeId):
        """
        Returns the configuration data for the node with specified node UID. Returns only
        the configuration data. To get the node metadata use ``node_get()``.

        API: GET /config/{uniqueNodeId}

        Parameters
        ----------
        uniqueNodeId : str
            Unique ID of the configuration node.

        Returns
        -------
        dict
            Configuration data (``configurationData``) as returned by the server.
        """
        method, url = self._prepare_config_get(uniqueNodeId=uniqueNodeId)
        return self.send_request(method, url)

    def config_add(self, parentNodeId, *, configurationNode, configurationData, auth=None):
        """
        Creates a new configuration node under the specified parent node. Parameters:
        ``configurationNode`` - the node metadata, ``configurationData`` - the configuration data.

        Minimum required fields:

        .. code-block:: python

            configurationNode = {"name": "test_config"}
            configurationData = {"pvList": [{"pvName": "PV1"}, {"pvName": "PV2"}]}

        The fields ``uniqueId``, ``nodeType``, ``userName`` in ``configurationNode`` are ignored
        and overwritten by the server.

        The function returns the dictionary with ``configurationNode`` and ``configurationData``
        as returned by the server.

        API: PUT /config?parentNodeId={parentNodeId}

        Parameters
        ----------
        parentNodeId : str
            Unique ID of the parent node.
        configurationNode : dict
            Configuration node (``configurationNode``) metadata. The required field is ``name``.
        configurationData : dict
            Configuration data (``configurationData``). The required field is ``pvList``.

        Returns
        -------
        dict
            Dictionary contains configuration node metadata and configuration data of the node
            that was added. The dictionary contains two keys: ``configurationNode`` and
            ``configurationData`` as returned by the server.
        """
        method, url, body_json = self._prepare_config_add(
            parentNodeId=parentNodeId, configurationNode=configurationNode, configurationData=configurationData
        )
        return self.send_request(method, url, body_json=body_json, auth=auth)

    def config_update(self, *, configurationNode, configurationData, auth=None):
        """
        Update an existing configuration node. It is best if ``configurationNode`` and ``configurationData``
        are loaded using ``node_get()`` and ``config_get()`` APIs respectively and then modified in the
        application code. Both dictionaries can also be created from scratch in the application code if
        necessary. Both dictionaries must contain correct correct UID (``uniqueID``) of an existing
        configuration node.

        API: POST /config

        Parameters
        ----------
        configurationNode : dict
            Configuration node (``configurationNode``) metadata. ``uniqueId`` field must be point to
            an existing configuration node.
        configurationData : dict
            Configuration data (``configurationData``). ``uniqueId`` field must be identical to the
            ``uniqueId`` field in ``configurationNode``.
        auth : httpx.BasicAuth
            Object with authentication data (generated using ``auth_gen()`` method).

        Returns
        -------
        dict
            Dictionary contains configuration node metadata and configuration data of the node
            that was updated. The dictionary contains two keys: ``configurationNode`` and
            ``configurationData`` as returned by the server.
        """
        method, url, body_json = self._prepare_config_update(
            configurationNode=configurationNode, configurationData=configurationData
        )
        return self.send_request(method, url, body_json=body_json, auth=auth)

    # =============================================================================================
    #                         TAG-CONTROLLER API METHODS
    # =============================================================================================

    def tags_get(self):
        """
        Returns the list of all existing tags.

        API: GET /tags

        Returns
        -------
        list[dict]
            List of all tags in the database. Each tag is dictionary with the following keys: ``name``
            - tag name, ``comment`` - tag comment (may be empty). The list may contain repeated elements.
            Tags do not contain pointers to tagged nodes.
        """
        method, url = self._prepare_tags_get()
        return self.send_request(method, url)

    def tags_add(self, *, uniqueNodeIds, tag, auth=None):
        """
        Adds ``tag`` to nodes specified by a list of UIDs ``uniqueNodeIds``. The ``tag``
        dictionary must contain the ``name`` key and optionally ``comment`` key.

        API: POST /tags

        Parameters
        ----------
        uniqueNodeIds : list of str
            List of node unique IDs to which the tag should be added.
        tag : dict
            Tag to be added. The dictionary must contain the ``name`` key and optionally ``comment`` key.
        auth : httpx.BasicAuth, optional
            Object with authentication data (generated using ``auth_gen()`` method).

        Returns
        -------
        list[dict]
            List of node metadata for the nodes to which the tag was added.
        """
        method, url, body_json = self._prepare_tags_add(uniqueNodeIds=uniqueNodeIds, tag=tag)
        return self.send_request(method, url, body_json=body_json, auth=auth)

    def tags_delete(self, *, uniqueNodeIds, tag, auth=None):
        """
        Deletes ``tag`` from the nodes specified by a list of UIDs ``uniqueNodeIds``. The deleted
        tag is identified by the ``"name"`` in the ``tag`` dictionary. The ``tag``
        dictionary may optionally ``comment`` key, but it is ignored by the API.

        API: DELETE /tags

        Parameters
        ----------
        uniqueNodeIds : list[str]
            List of node unique IDs from which the tag should be deleted.
        tag : dict
            Tag to be deleted. The dictionary must contain the ``name`` key. The ``comment`` key
            is optional and ignored by the API.
        auth : httpx.BasicAuth, optional
            Object with authentication data (generated using ``auth_gen()`` method).

        Returns
        -------
        list[dict]
            List of node metadata for the nodes from ``uniqueNodeIds`` list.
        """
        method, url, body_json = self._prepare_tags_delete(uniqueNodeIds=uniqueNodeIds, tag=tag)
        return self.send_request(method, url, body_json=body_json, auth=auth)

    # =============================================================================================
    #                         TAKE-SNAPSHOT-CONTROLLER API METHODS
    # =============================================================================================

    def take_snapshot_get(self, uniqueNodeId):
        """
        Reads and returns a list of PV values based on configuration specified by
        ``uniqueNodeId``. The API does not create any nodes in the database.
        The returned list format matches the format of ``snapshotData["snapshotItems"]``.

        API: GET /take-snapshot/{uniqueNodeId}

        Parameters
        ----------
        uniqueNodeId : str
            Unique ID of the configuration node.

        Returns
        -------
        list[dict]
            List of PV values read from the control system. Each PV is represented as a dictionary
            of parameters. The format is consistent with the format of ``snapshotData["snapshotItems"]``.
        """
        method, url = self._prepare_take_snapshot_get(uniqueNodeId=uniqueNodeId)
        return self.send_request(method, url)

    def take_snapshot_save(self, uniqueNodeId, *, name=None, comment=None, auth=None):
        """
        Reads PV values based on configuration specified by ``uniqueNodeId`` and
        saves the values in a new snapshot node. The parameter ``name`` specifies
        the name of the snapshot node and ``comment`` specifies the node description.

        API: PUT /take-snapshot/{uniqueNodeId}

        Parameters
        ----------
        uniqueNodeId : str
            Unique ID of the configuration node.
        name : str, optional
            Name of the new snapshot node. If not specified or None, the name is set to
            the date and time of the snapshot, e.g. ``2025-10-12 22:49:50.577``.
        comment : str, optional
            Description of the new snapshot node. If not specified or None, the comment
            is set to date and time of the snapshot, e.g. ``2025-10-12 22:49:50.577``.
        auth : httpx.BasicAuth, optional
            Object with authentication data (generated using ``auth_gen()`` method).

        Returns
        -------
        dict
            Dictionary contains snapshot node metadata and snapshot data of the node
            that was created. The dictionary contains two keys: ``snapshotNode`` and
            ``snapshotData`` as returned by the server.
        """
        method, url, params = self._prepare_take_snapshot_save(
            uniqueNodeId=uniqueNodeId, name=name, comment=comment
        )
        return self.send_request(method, url, params=params, auth=auth)

    # =============================================================================================
    #                         SNAPSHOT-CONTROLLER API METHODS
    # =============================================================================================

    def snapshot_get(self, uniqueId):
        """
        Returns snapshot data (``snapshotData``) for the snapshot specified by ``uniqueId``.

        API: GET /snapshot/{uniqueId}

        Parameters
        ----------
        uniqueId : str
            Unique ID of the snapshot node.

        Returns
        -------
        dict
            Snapshot data (``snapshotData``) as returned by the server.
        """
        method, url = self._prepare_snapshot_get(uniqueId=uniqueId)
        return self.send_request(method, url)

    def snapshot_add(self, parentNodeId, *, snapshotNode, snapshotData, auth=None):
        """
        Upload data for the new snapshot and save it to the database. The new node is created
        under the existing configuration node specified by ``parentNodeId``.

        API: PUT /snapshot?parentNodeId={parentNodeId}

        Parameters
        ----------
        parentNodeId : str
            Unique ID of the parent configuration node.
        snapshotNode : dict
            Snapshot node (``snapshotNode``) metadata. The required field is ``"name"``.
        snapshotData : dict
            Snapshot data (``snapshotData``). The required field is ``"snapshotItems"``.
        auth : httpx.BasicAuth, optional
            Object with authentication data (generated using ``auth_gen()`` method).

        Returns
        -------
        dict
            Dictionary contains snapshot node metadata and snapshot data of the node
            that was added. The dictionary contains two keys: ``snapshotNode`` and
            ``snapshotData`` as returned by the server.
        """
        method, url, params, body_json = self._prepare_snapshot_add(
            parentNodeId=parentNodeId, snapshotNode=snapshotNode, snapshotData=snapshotData
        )
        return self.send_request(method, url, body_json=body_json, params=params, auth=auth)

    def snapshot_update(self, *, snapshotNode, snapshotData, auth=None):
        """
        Upload and update data for an existing snapshot. Both ``snapshotNode`` and ``snapshotData``
        must have valid ``uniqueId`` fields pointing to an existing node.

        API: POST /snapshot

        Parameters
        ----------
        snapshotNode : dict
            Snapshot node (``snapshotNode``) metadata. ``uniqueId`` field must point to
            an existing snapshot node.
        snapshotData : dict
            Snapshot data (``snapshotData``). ``uniqueId`` field must be identical to the
            ``uniqueId`` field in ``snapshotNode``.
        auth : httpx.BasicAuth, optional
            Object with authentication data (generated using ``auth_gen()`` method).

        Returns
        -------
        dict
            Dictionary contains snapshot node metadata and snapshot data of the node
            that was updated. The dictionary contains two keys: ``snapshotNode`` and
            ``snapshotData`` as returned by the server.
        """
        method, url, body_json = self._prepare_snapshot_update(
            snapshotNode=snapshotNode, snapshotData=snapshotData
        )
        return self.send_request(method, url, body_json=body_json, auth=auth)

    def snapshots_get(self):
        """
        Returns a list of all existing snapshots (list of ``snapshotNode`` objects).

        API: GET /snapshots

        Returns
        -------
        list[dict]
            List of snapshot nodes (``snapshotNode``) as returned by the server. The list
            does not include snapshot data.
        """
        method, url = self._prepare_snapshots_get()
        return self.send_request(method, url)

    # =============================================================================================
    #                         COMPOSITE-SNAPSHOT-CONTROLLER API METHODS
    # =============================================================================================

    def composite_snapshot_get(self, uniqueId):
        """
        Returns composite snapshot data (``compositeSnapshotData``) specified by ``uniqueId``.
        The data includes uniqueId and the list of referencedSnapshotNodes (no PV information).
        The composite snapshot node metadata can be obtained using ``node_get()``.

        API: GET /composite-snapshot/{uniqueId}

        Parameters
        ----------
        uniqueId : str
            Unique ID of the composite snapshot node.

        Returns
        -------
        dict
            Composite snapshot data (``compositeSnapshotData``) as returned by the server.
        """
        method, url = self._prepare_composite_snapshot_get(uniqueId=uniqueId)
        return self.send_request(method, url)

    def composite_snapshot_get_nodes(self, uniqueId):
        """
        Returns a list of nodes referenced by the composite snapshot. The composite snapshot is
        specified by ``uniqueId``.

        API: GET /composite-snapshot/{uniqueId}/nodes

        Parameters
        ----------
        uniqueId : str
            Unique ID of the composite snapshot node.

        Returns
        -------
        list[dict]
            List of snapshot nodes. Each snapshot node is represented as a dictionary with
            node metadata. No composite snapshot data is returned.
        """
        method, url = self._prepare_composite_snapshot_get_nodes(uniqueId=uniqueId)
        return self.send_request(method, url)

    def composite_snapshot_get_items(self, uniqueId):
        """
        Returns a list of restorable items (PV data) referenced by the composite snapshot.
        The composite snapshot is specified by ``uniqueId``.

        API: GET /composite-snapshot/{uniqueId}/items

        Parameters
        ----------
        uniqueId : str
            Unique ID of the composite snapshot node.

        Returns
        -------
        list[dict]
            List of snapshot items (PVs). The format is consistent with the format of
            ``snapshotData["snapshotItems"]``.
        """
        method, url = self._prepare_composite_snapshot_get_items(uniqueId=uniqueId)
        return self.send_request(method, url)

    def composite_snapshot_add(self, parentNodeId, *, compositeSnapshotNode, compositeSnapshotData, auth=None):
        """
        Create a new composite snapshot node. The new node is created under the existing configuration node
        specified by ``parentNodeId``.

        API: PUT /composite-snapshot?parentNodeId={parentNodeId}

        Parameters
        ----------
        parentNodeId : str
            Unique ID of the parent configuration node.
        compositeSnapshotNode : dict
            Composite snapshot node (``compositeSnapshotNode``) metadata. The required field is ``"name"``.
        compositeSnapshotData : dict
            Composite snapshot data (``compositeSnapshotData``). The required field is
            ``"referencedSnapshotNodes"``, which points to the list of UIDs of the nodes included in
            the composite snapshot.
        auth : httpx.BasicAuth, optional
            Object with authentication data (generated using ``auth_gen()`` method).

        Returns
        -------
        dict
            Dictionary contains composite snapshot node metadata and composite snapshot data
            of the node that was added. The dictionary contains two keys: ``compositeSnapshotNode`` and
            ``compositeSnapshotData`` as returned by the server.
        """
        method, url, params, body_json = self._prepare_composite_snapshot_add(
            parentNodeId=parentNodeId,
            compositeSnapshotNode=compositeSnapshotNode,
            compositeSnapshotData=compositeSnapshotData,
        )
        return self.send_request(method, url, params=params, body_json=body_json, auth=auth)

    def composite_snapshot_update(self, *, compositeSnapshotNode, compositeSnapshotData, auth=None):
        """
        Update the existing snapshot. Both ``compositeSnapshotNode`` and ``compositeSnapshotNode``
        must have valid ``uniqueId`` fields pointing to an existing node.

        API: POST /composite-snapshot

        Parameters
        ----------
        compositeSnapshotNode : dict
            Composite snapshot node (``compositeSnapshotNode``) metadata. ``uniqueId`` field must point to
            an existing composite snapshot node.
        compositeSnapshotData : dict
            Composite snapshot data (``compositeSnapshotData``). ``uniqueId`` field must be identical to the
            ``uniqueId`` field in ``compositeSnapshotNode``.
        auth : httpx.BasicAuth, optional
            Object with authentication data (generated using ``auth_gen()`` method).

        Returns
        -------
        dict
            Dictionary contains composite snapshot node metadata and composite snapshot data
            of the node that was updated. The dictionary contains two keys: ``compositeSnapshotNode`` and
            ``compositeSnapshotData`` as returned by the server.
        """
        method, url, body_json = self._prepare_composite_snapshot_update(
            compositeSnapshotNode=compositeSnapshotNode,
            compositeSnapshotData=compositeSnapshotData,
        )
        return self.send_request(method, url, body_json=body_json, auth=auth)

    def composite_snapshot_consistency_check(self, uniqueNodeIds, *, auth=None):
        """
        Check consistency of the composite snapshots. The snapshot is specified by the list of
        UIDs of snapshots and composite snapshots included in the composite snapshot.
        One of the use cases is to check if a snapshot can be added to an existing composite
        snapshot. In this case the list of UIDs includes the UID of the exisitng composite
        snapshot and the UID of the new snapshot to be added. The function returns a list
        of PV data for each conflicting PV (composite snapshot items may not contain duplicate
        PVs).

        API: POST /composite-snapshot-consistency-check

        Parameters
        ----------
        uniqueNodeIds : list of str
            List of UIDs of snapshots and composite snapshots included in the composite snapshot.
        auth : httpx.BasicAuth, optional
            Object with authentication data (generated using ``auth_gen()`` method).

        Returns
        -------
        list[dict]
            List of conflicting PVs. Each PV is represented as a dictionary of parameters.
            If the list is empty, then there are no conflicts and the composite snapshot
            can be created or updated. The format is consistent with the format of
            ``snapshotData["snapshotItems"]``.
        """
        method, url, body_json = self._prepare_composite_snapshot_consistency_check(uniqueNodeIds=uniqueNodeIds)
        return self.send_request(method, url, body_json=body_json, auth=auth)

    # =============================================================================================
    #                     SNAPSHOT-RESTORE-CONTROLLER API METHODS
    # =============================================================================================

    def restore_node(self, nodeId, *, auth=None):
        """
        Restore PVs based on the data from an existing snapshot node specified by nodeId.
        Returns a list of snapshotItems that were NOT restored. Ideally the list should be empty.

        API: POST /restore/node

        Parameters
        ----------
        nodeId : str
            Unique ID of the snapshot node.
        auth : httpx.BasicAuth, optional
            Object with authentication data (generated using ``auth_gen()`` method).

        Returns
        -------
        list[dict]
            List of snapshot items (PVs) that were NOT restored. The format is consistent with
            the format of ``snapshotData["snapshotItems"]``.
        """
        method, url, params = self._prepare_restore_node(nodeId=nodeId)
        return self.send_request(method, url, params=params, auth=auth)

    def restore_items(self, *, snapshotItems, auth=None):
        """
        Restore PVs based on the list of snapshot items passed with the request. The list
        format matches the format of ``snapshotData["snapshotItems"]``

        Returns a list of snapshotItems that were NOT restored. Ideally the list should be empty.

        API: POST /restore/items

        Parameters
        ----------
        snapshotItems : list of dict
            List of snapshot items (PVs) to be restored. The format is consistent with
            the format of ``snapshotData["snapshotItems"]``.
        auth : httpx.BasicAuth, optional
            Object with authentication data (generated using ``auth_gen()`` method).

        Returns
        -------
        list[dict]
            List of snapshot items (PVs) that were NOT restored. The format is consistent with
            the format of ``snapshotData["snapshotItems"]``.
        """
        method, url, body_json = self._prepare_restore_items(snapshotItems=snapshotItems)
        return self.send_request(method, url, body_json=body_json, auth=auth)

    # =============================================================================================
    #                     COMPARISON-CONTROLLER API METHODS
    # =============================================================================================

    def compare(self, nodeId, *, tolerance=None, compareMode=None, skipReadback=None):
        """
        Compare stored PV values with live values for the selected snapshot or composite snapshot.
        The snapshot is selected by ``nodeId``. The API returns a list of results for each PV in
        the snapshot.

        API: GET /compare/{nodeId}

        Parameters
        ----------
        nodeId : str
            Unique ID of the snapshot or composite snapshot node.
        tolerance : float, optional
            Tolerance for numerical comparisons. If not specified or None, the default is 0.
        compareMode : str, optional
            Comparison mode. Supported values: ``"ABSOLUTE"``, ``"RELATIVE"``.
        skipReadback : bool, optional
            If True, then ``pvName`` live value is used for PVs with specified ``readbackPvName``.
            If not specified, then the default is False and the readback PV is used for comparison.

        Returns
        -------
        list[dict]
            List of comparison results for each PV in the snapshot. Each PV is represented as a
            dictionary with the following keys: ``pvName``, ``equal``, ``compare``, ``storedValue``,
            ``liveValue``.
        """
        method, url, params = self._prepare_compare(
            nodeId=nodeId, tolerance=tolerance, compareMode=compareMode, skipReadback=skipReadback
        )
        return self.send_request(method, url, params=params)

    # =============================================================================================
    #                     FILTER-CONTROLLER API METHODS
    # =============================================================================================

    def filter_add(self, filter, *, auth=None):
        """
        Add a filter to the list stored in the database.

        API: PUT /filter

        Parameters
        ----------
        filter : dict
            Filter to be added. The dictionary must contain the ``name`` and ``filter`` keys.
        auth : httpx.BasicAuth, optional
            Object with authentication data (generated using ``auth_gen()`` method).

        Returns
        -------
        dict
            Added filter as returned by the server.
        """
        method, url, body_json = self._prepare_filter_add(filter=filter)
        return self.send_request(method, url, body_json=body_json, auth=auth)

    def filters_get(self):
        """
        Get the list of all the filters from the database.

        API: GET /filters

        Returns
        -------
        list[dict]
            List of all filters in the database.
        """
        method, url = self._prepare_filters_get()
        return self.send_request(method, url)

    def filter_delete(self, name, *, auth=None):
        """
        Delete filter with the given name from the database.

        API: DELETE /filter/{name}

        Parameters
        ----------
        name : str
            Name of the filter to be deleted.
        auth : httpx.BasicAuth, optional
            Object with authentication data (generated using ``auth_gen()`` method).

        Returns
        -------
        None
        """
        method, url = self._prepare_filter_delete(name=name)
        return self.send_request(method, url, auth=auth)

    # =============================================================================================
    #                     STRUCTURE-CONTROLLER API METHODS
    # =============================================================================================

    def structure_move(self, nodeIds, *, newParentNodeId, auth=None):
        """
        Move nodes specified by a list of UIDs ``nodeIds`` to a new parent node specified
        by ``newParentNodeId``. The API requires 'admin' priviledges.

        API: POST /move

        Parameters
        ----------
        nodeIds : list[str]
            List of node unique IDs to be moved.
        newParentNodeId : str
            Unique ID of the new parent node.
        auth : httpx.BasicAuth, optional
            Object with authentication data (generated using ``auth_gen()`` method).

        Returns
        -------
        dict
            Dictionary with metadata for the new parent node.
        """
        method, url, body_json, params = self._prepare_structure_move(
            nodeIds=nodeIds, newParentNodeId=newParentNodeId
        )
        return self.send_request(method, url, body_json=body_json, params=params, auth=auth)

    def structure_copy(self, nodeIds, *, newParentNodeId, auth=None):
        """
        Copy nodes specified by a list of UIDs ``nodeIds`` to the new parent node specified
        by ``newParentNodeId``. The API requires 'admin' priviledges.

        API: POST /copy

        Parameters
        ----------
        nodeIds : list[str]
            List of node unique IDs to be moved.
        newParentNodeId : str
            Unique ID of the new parent node.
        auth : httpx.BasicAuth, optional
            Object with authentication data (generated using ``auth_gen()`` method).

        Returns
        -------
        dict
            Dictionary with metadata for the new parent node.
        """
        method, url, body_json, params = self._prepare_structure_copy(
            nodeIds=nodeIds, newParentNodeId=newParentNodeId
        )
        return self.send_request(method, url, body_json=body_json, params=params, auth=auth)

    def structure_path_get(self, uniqueNodeId):
        """
        Get path for the node with specified uniqueNodeId. The path contains a sequence
        of nodes starting from the root node. Node names are separated by '/' character.

        API: GET /path/{uniqueNodeId}

        Parameters
        ----------
        uniqueNodeId : str
            Unique ID of the node.

        Returns
        -------
        str
            Path of the node with names of nodes separated by '/' character.
        """
        method, url = self._prepare_structure_path_get(uniqueNodeId=uniqueNodeId)
        return self.send_request(method, url)

    def structure_path_nodes(self, path):
        """
        Get a list of nodes that match the specified path. The path can point to multiple
        nodes as long as node type is different (e.g. a folder and a configuration may have
        the same name and may be simultaneously present in the list).

        API: GET /path

        Parameters
        ----------
        path : str
            Path of the node with names of nodes separated by '/' character.

        Returns
        -------
        list[dict]
            List of nodes that match the specified path. Each node is represented as a dictionary
            with node metadata as returned by the server.
        """
        method, url, params = self._prepare_structure_path_nodes(path=path)
        return self.send_request(method, url, params=params)
