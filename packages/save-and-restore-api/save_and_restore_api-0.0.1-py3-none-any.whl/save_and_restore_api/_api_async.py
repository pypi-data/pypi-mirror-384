import httpx

from ._api_base import _SaveRestoreAPI_Base
from ._api_threads import SaveRestoreAPI as _SaveRestoreAPI_Threads


class SaveRestoreAPI(_SaveRestoreAPI_Base):
    def open(self):
        # Reusing docstrings from the threaded version
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout)

    async def close(self):
        # Reusing docstrings from the threaded version
        await self._client.aclose()
        self._client = None

    async def __aenter__(self):
        # Reusing docstrings from the threaded version
        self.open()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        # Reusing docstrings from the threaded version
        await self.close()

    async def send_request(
        self, method, url, *, body_json=None, params=None, headers=None, data=None, timeout=None, auth=None
    ):
        # Reusing docstrings from the threaded version
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
            client_response = await self._client.request(method, url, **kwargs)
            response = self._process_response(client_response=client_response)
        except Exception:
            response = self._process_comm_exception(
                method=method, body_json=body_json, client_response=client_response
            )

        return response

    # =============================================================================================
    #                         INFO-CONTROLLER API METHODS
    # =============================================================================================

    async def info_get(self):
        # Reusing docstrings from the threaded version
        method, url = self._prepare_info_get()
        return await self.send_request(method, url)

    async def version_get(self):
        # Reusing docstrings from the threaded version
        method, url = self._prepare_version_get()
        return await self.send_request(method, url)

    # =============================================================================================
    #                         SEARCH-CONTROLLER API METHODS
    # =============================================================================================

    async def search(self, allRequestParams):
        # Reusing docstrings from the threaded version
        method, url, params = self._prepare_search(allRequestParams=allRequestParams)
        return await self.send_request(method, url, params=params)

    # =============================================================================================
    #                         HELP-RESOURCE API METHODS
    # =============================================================================================

    async def help(self, what, *, lang=None):
        # Reusing docstrings from the threaded version
        method, url, params = self._prepare_help(what=what, lang=lang)
        return await self.send_request(method, url, params=params)

    # =============================================================================================
    #                         AUTHENTICATION-CONTROLLER API METHODS
    # =============================================================================================

    async def login(self, *, username, password):
        # Reusing docstrings from the threaded version
        method, url, body_json = self._prepare_login(username=username, password=password)
        return await self.send_request(method, url, body_json=body_json)

    # =============================================================================================
    #                         NODE-CONTROLLER API METHODS
    # =============================================================================================

    async def node_get(self, uniqueNodeId):
        # Reusing docstrings from the threaded version
        method, url = self._prepare_node_get(uniqueNodeId=uniqueNodeId)
        return await self.send_request(method, url)

    async def nodes_get(self, uniqueIds):
        # Reusing docstrings from the threaded version
        method, url, body_json = self._prepare_nodes_get(uniqueIds=uniqueIds)
        return await self.send_request(method, url, body_json=body_json)

    async def node_add(self, parentNodeId, *, node, auth=None, **kwargs):
        # Reusing docstrings from the threaded version
        method, url, params, body_json = self._prepare_node_add(parentNodeId=parentNodeId, node=node)
        return await self.send_request(method, url, params=params, body_json=body_json, auth=auth)

    async def node_delete(self, nodeId, *, auth=None):
        # Reusing docstrings from the threaded version
        method, url = self._prepare_node_delete(nodeId=nodeId)
        return await self.send_request(method, url, auth=auth)

    async def nodes_delete(self, uniqueIds, *, auth=None):
        # Reusing docstrings from the threaded version
        method, url, body_json = self._prepare_nodes_delete(uniqueIds=uniqueIds)
        return await self.send_request(method, url, body_json=body_json, auth=auth)

    async def node_get_children(self, uniqueNodeId):
        # Reusing docstrings from the threaded version
        method, url = self._prepare_node_get_children(uniqueNodeId=uniqueNodeId)
        return await self.send_request(method, url)

    async def node_get_parent(self, uniqueNodeId):
        # Reusing docstrings from the threaded version
        method, url = self._prepare_node_get_parent(uniqueNodeId=uniqueNodeId)
        return await self.send_request(method, url)

    # =============================================================================================
    #                         CONFIGURATION-CONTROLLER API METHODS
    # =============================================================================================

    async def config_get(self, uniqueNodeId):
        # Reusing docstrings from the threaded version
        method, url = self._prepare_config_get(uniqueNodeId=uniqueNodeId)
        return await self.send_request(method, url)

    async def config_add(self, parentNodeId, *, configurationNode, configurationData, auth=None):
        # Reusing docstrings from the threaded version
        method, url, body_json = self._prepare_config_add(
            parentNodeId=parentNodeId, configurationNode=configurationNode, configurationData=configurationData
        )
        return await self.send_request(method, url, body_json=body_json, auth=auth)

    async def config_update(self, *, configurationNode, configurationData, auth=None):
        # Reusing docstrings from the threaded version
        method, url, body_json = self._prepare_config_update(
            configurationNode=configurationNode, configurationData=configurationData
        )
        return await self.send_request(method, url, body_json=body_json, auth=auth)

    # =============================================================================================
    #                         TAG-CONTROLLER API METHODS
    # =============================================================================================

    async def tags_get(self):
        # Reusing docstrings from the threaded version
        method, url = self._prepare_tags_get()
        return await self.send_request(method, url)

    async def tags_add(self, *, uniqueNodeIds, tag, auth=None):
        # Reusing docstrings from the threaded version
        method, url, body_json = self._prepare_tags_add(uniqueNodeIds=uniqueNodeIds, tag=tag)
        return await self.send_request(method, url, body_json=body_json, auth=auth)

    async def tags_delete(self, *, uniqueNodeIds, tag, auth=None):
        # Reusing docstrings from the threaded version
        method, url, body_json = self._prepare_tags_delete(uniqueNodeIds=uniqueNodeIds, tag=tag)
        return await self.send_request(method, url, body_json=body_json, auth=auth)

    # =============================================================================================
    #                         TAKE-SNAPSHOT-CONTROLLER API METHODS
    # =============================================================================================

    async def take_snapshot_get(self, uniqueNodeId):
        # Reusing docstrings from the threaded version
        method, url = self._prepare_take_snapshot_get(uniqueNodeId=uniqueNodeId)
        return await self.send_request(method, url)

    async def take_snapshot_save(self, uniqueNodeId, *, name=None, comment=None, auth=None):
        # Reusing docstrings from the threaded version
        method, url, params = self._prepare_take_snapshot_save(
            uniqueNodeId=uniqueNodeId, name=name, comment=comment
        )
        return await self.send_request(method, url, params=params, auth=auth)

    # =============================================================================================
    #                         SNAPSHOT-CONTROLLER API METHODS
    # =============================================================================================

    async def snapshot_get(self, uniqueId):
        # Reusing docstrings from the threaded version
        method, url = self._prepare_snapshot_get(uniqueId=uniqueId)
        return await self.send_request(method, url)

    async def snapshot_add(self, parentNodeId, *, snapshotNode, snapshotData, auth=None):
        # Reusing docstrings from the threaded version
        method, url, params, body_json = self._prepare_snapshot_add(
            parentNodeId=parentNodeId, snapshotNode=snapshotNode, snapshotData=snapshotData
        )
        return await self.send_request(method, url, body_json=body_json, params=params, auth=auth)

    async def snapshot_update(self, *, snapshotNode, snapshotData, auth=None):
        # Reusing docstrings from the threaded version
        method, url, body_json = self._prepare_snapshot_update(
            snapshotNode=snapshotNode, snapshotData=snapshotData
        )
        return await self.send_request(method, url, body_json=body_json, auth=auth)

    async def snapshots_get(self):
        # Reusing docstrings from the threaded version
        method, url = self._prepare_snapshots_get()
        return await self.send_request(method, url)

    # =============================================================================================
    #                         COMPOSITE-SNAPSHOT-CONTROLLER API METHODS
    # =============================================================================================

    async def composite_snapshot_get(self, uniqueId):
        # Reusing docstrings from the threaded version
        method, url = self._prepare_composite_snapshot_get(uniqueId=uniqueId)
        return await self.send_request(method, url)

    async def composite_snapshot_get_nodes(self, uniqueId):
        # Reusing docstrings from the threaded version
        method, url = self._prepare_composite_snapshot_get_nodes(uniqueId=uniqueId)
        return await self.send_request(method, url)

    async def composite_snapshot_get_items(self, uniqueId):
        # Reusing docstrings from the threaded version
        method, url = self._prepare_composite_snapshot_get_items(uniqueId=uniqueId)
        return await self.send_request(method, url)

    async def composite_snapshot_add(
        self, parentNodeId, *, compositeSnapshotNode, compositeSnapshotData, auth=None
    ):
        # Reusing docstrings from the threaded version
        method, url, params, body_json = self._prepare_composite_snapshot_add(
            parentNodeId=parentNodeId,
            compositeSnapshotNode=compositeSnapshotNode,
            compositeSnapshotData=compositeSnapshotData,
        )
        return await self.send_request(method, url, params=params, body_json=body_json, auth=auth)

    async def composite_snapshot_update(self, *, compositeSnapshotNode, compositeSnapshotData, auth=None):
        # Reusing docstrings from the threaded version
        method, url, body_json = self._prepare_composite_snapshot_update(
            compositeSnapshotNode=compositeSnapshotNode,
            compositeSnapshotData=compositeSnapshotData,
        )
        return await self.send_request(method, url, body_json=body_json, auth=auth)

    async def composite_snapshot_consistency_check(self, uniqueNodeIds, *, auth=None):
        # Reusing docstrings from the threaded version
        method, url, body_json = self._prepare_composite_snapshot_consistency_check(uniqueNodeIds=uniqueNodeIds)
        return await self.send_request(method, url, body_json=body_json, auth=auth)

    # =============================================================================================
    #                     SNAPSHOT-RESTORE-CONTROLLER API METHODS
    # =============================================================================================

    async def restore_node(self, nodeId, *, auth=None):
        # Reusing docstrings from the threaded version
        method, url, params = self._prepare_restore_node(nodeId=nodeId)
        return await self.send_request(method, url, params=params, auth=auth)

    async def restore_items(self, *, snapshotItems, auth=None):
        # Reusing docstrings from the threaded version
        method, url, body_json = self._prepare_restore_items(snapshotItems=snapshotItems)
        return await self.send_request(method, url, body_json=body_json, auth=auth)

    # =============================================================================================
    #                     COMPARISON-CONTROLLER API METHODS
    # =============================================================================================

    async def compare(self, nodeId, *, tolerance=None, compareMode=None, skipReadback=None):
        # Reusing docstrings from the threaded version
        method, url, params = self._prepare_compare(
            nodeId=nodeId, tolerance=tolerance, compareMode=compareMode, skipReadback=skipReadback
        )
        return await self.send_request(method, url, params=params)

    # =============================================================================================
    #                     FILTER-CONTROLLER API METHODS
    # =============================================================================================

    async def filter_add(self, filter, *, auth=None):
        # Reusing docstrings from the threaded version
        method, url, body_json = self._prepare_filter_add(filter=filter)
        return await self.send_request(method, url, body_json=body_json, auth=auth)

    async def filters_get(self):
        # Reusing docstrings from the threaded version
        method, url = self._prepare_filters_get()
        return await self.send_request(method, url)

    async def filter_delete(self, name, *, auth=None):
        # Reusing docstrings from the threaded version
        method, url = self._prepare_filter_delete(name=name)
        return await self.send_request(method, url, auth=auth)

    # =============================================================================================
    #                     STRUCTURE-CONTROLLER API METHODS
    # =============================================================================================

    async def structure_move(self, nodeIds, newParentNodeId, *, auth=None):
        # Reusing docstrings from the threaded version
        method, url, body_json, params = self._prepare_structure_move(
            nodeIds=nodeIds, newParentNodeId=newParentNodeId
        )
        return await self.send_request(method, url, body_json=body_json, params=params, auth=auth)

    async def structure_copy(self, nodeIds, newParentNodeId, *, auth=None):
        # Reusing docstrings from the threaded version
        method, url, body_json, params = self._prepare_structure_copy(
            nodeIds=nodeIds, newParentNodeId=newParentNodeId
        )
        return await self.send_request(method, url, body_json=body_json, params=params, auth=auth)

    async def structure_path_get(self, uniqueNodeId):
        # Reusing docstrings from the threaded version
        method, url = self._prepare_structure_path_get(uniqueNodeId=uniqueNodeId)
        return await self.send_request(method, url)

    async def structure_path_nodes(self, path):
        # Reusing docstrings from the threaded version
        method, url, params = self._prepare_structure_path_nodes(path=path)
        return await self.send_request(method, url, params=params)


SaveRestoreAPI.open.__doc__ = _SaveRestoreAPI_Threads.open.__doc__
SaveRestoreAPI.close.__doc__ = _SaveRestoreAPI_Threads.close.__doc__
SaveRestoreAPI.__aenter__.__doc__ = _SaveRestoreAPI_Threads.__enter__.__doc__
SaveRestoreAPI.__aexit__.__doc__ = _SaveRestoreAPI_Threads.__exit__.__doc__

SaveRestoreAPI.send_request.__doc__ = _SaveRestoreAPI_Threads.send_request.__doc__

SaveRestoreAPI.info_get.__doc__ = _SaveRestoreAPI_Threads.info_get.__doc__
SaveRestoreAPI.version_get.__doc__ = _SaveRestoreAPI_Threads.version_get.__doc__
SaveRestoreAPI.login.__doc__ = _SaveRestoreAPI_Threads.login.__doc__
SaveRestoreAPI.search.__doc__ = _SaveRestoreAPI_Threads.search.__doc__
SaveRestoreAPI.node_get.__doc__ = _SaveRestoreAPI_Threads.node_get.__doc__
SaveRestoreAPI.nodes_get.__doc__ = _SaveRestoreAPI_Threads.nodes_get.__doc__
SaveRestoreAPI.node_add.__doc__ = _SaveRestoreAPI_Threads.node_add.__doc__
SaveRestoreAPI.node_delete.__doc__ = _SaveRestoreAPI_Threads.node_delete.__doc__
SaveRestoreAPI.nodes_delete.__doc__ = _SaveRestoreAPI_Threads.nodes_delete.__doc__
SaveRestoreAPI.node_get_children.__doc__ = _SaveRestoreAPI_Threads.node_get_children.__doc__
SaveRestoreAPI.node_get_parent.__doc__ = _SaveRestoreAPI_Threads.node_get_parent.__doc__
SaveRestoreAPI.config_get.__doc__ = _SaveRestoreAPI_Threads.config_get.__doc__
SaveRestoreAPI.config_add.__doc__ = _SaveRestoreAPI_Threads.config_add.__doc__
SaveRestoreAPI.config_update.__doc__ = _SaveRestoreAPI_Threads.config_update.__doc__
SaveRestoreAPI.tags_get.__doc__ = _SaveRestoreAPI_Threads.tags_get.__doc__
SaveRestoreAPI.tags_add.__doc__ = _SaveRestoreAPI_Threads.tags_add.__doc__
SaveRestoreAPI.tags_delete.__doc__ = _SaveRestoreAPI_Threads.tags_delete.__doc__
SaveRestoreAPI.take_snapshot_get.__doc__ = _SaveRestoreAPI_Threads.take_snapshot_get.__doc__
SaveRestoreAPI.take_snapshot_save.__doc__ = _SaveRestoreAPI_Threads.take_snapshot_save.__doc__
SaveRestoreAPI.snapshot_get.__doc__ = _SaveRestoreAPI_Threads.snapshot_get.__doc__
SaveRestoreAPI.snapshot_add.__doc__ = _SaveRestoreAPI_Threads.snapshot_add.__doc__
SaveRestoreAPI.snapshot_update.__doc__ = _SaveRestoreAPI_Threads.snapshot_update.__doc__
SaveRestoreAPI.snapshots_get.__doc__ = _SaveRestoreAPI_Threads.snapshots_get.__doc__

SaveRestoreAPI.composite_snapshot_get.__doc__ = _SaveRestoreAPI_Threads.composite_snapshot_get.__doc__
SaveRestoreAPI.composite_snapshot_get_nodes.__doc__ = _SaveRestoreAPI_Threads.composite_snapshot_get_nodes.__doc__
SaveRestoreAPI.composite_snapshot_get_items.__doc__ = _SaveRestoreAPI_Threads.composite_snapshot_get_items.__doc__
SaveRestoreAPI.composite_snapshot_add.__doc__ = _SaveRestoreAPI_Threads.composite_snapshot_add.__doc__
SaveRestoreAPI.composite_snapshot_update.__doc__ = _SaveRestoreAPI_Threads.composite_snapshot_update.__doc__
SaveRestoreAPI.composite_snapshot_consistency_check.__doc__ = (
    _SaveRestoreAPI_Threads.composite_snapshot_consistency_check.__doc__
)

SaveRestoreAPI.restore_node.__doc__ = _SaveRestoreAPI_Threads.restore_node.__doc__
SaveRestoreAPI.restore_items.__doc__ = _SaveRestoreAPI_Threads.restore_items.__doc__
SaveRestoreAPI.compare.__doc__ = _SaveRestoreAPI_Threads.compare.__doc__
SaveRestoreAPI.structure_move.__doc__ = _SaveRestoreAPI_Threads.structure_move.__doc__
SaveRestoreAPI.structure_copy.__doc__ = _SaveRestoreAPI_Threads.structure_copy.__doc__
SaveRestoreAPI.structure_path_get.__doc__ = _SaveRestoreAPI_Threads.structure_path_get.__doc__
SaveRestoreAPI.structure_path_nodes.__doc__ = _SaveRestoreAPI_Threads.structure_path_nodes.__doc__
