# import getpass
import json
from urllib.parse import quote

import httpx


class RequestParameterError(Exception): ...


class HTTPRequestError(httpx.RequestError): ...


class HTTPClientError(httpx.HTTPStatusError): ...


class HTTPServerError(httpx.HTTPStatusError): ...


class RequestTimeoutError(TimeoutError):
    def __init__(self, msg, request):
        msg = f"Request timeout: {msg}"
        self.request = request
        super().__init__(msg)


class _SaveRestoreAPI_Base:
    RequestParameterError = RequestParameterError
    RequestTimeoutError = RequestTimeoutError
    HTTPRequestError = HTTPRequestError
    HTTPClientError = HTTPClientError
    HTTPServerError = HTTPServerError

    ROOT_NODE_UID = "44bef5de-e8e6-4014-af37-b8f6c8a939a2"

    def __init__(self, *, base_url, timeout=5.0):
        self._base_url = base_url
        self._timeout = timeout
        self._client = None
        self._auth = None

    @staticmethod
    def auth_gen(username, password):
        """
        Generate and return httpx.BasicAuth object based on username and password.
        The object can be passed as a value of  ``auth`` parameter in API calls.
        Explicitly passing the authentication object may be useful if requests
        are made on behalf of multiple users in the same session. If a single user
        is authenticated per session, then use ``auth_set()`` to set authentication
        once.

        Parameters
        ----------
        username : str
            Username.
        password : str
            Password.

        Returns
        -------
        httpx.BasicAuth
            Basic authentication object.

        Examples
        --------

        .. code-block:: python

            from save_and_restore_api import SaveRestoreAPI

            auth = SaveRestoreAPI.auth_gen(username="user", password="userPass")
        """
        return httpx.BasicAuth(username=username, password=password)

    def auth_set(self, *, username, password):
        """
        Set authentication for the session. Once the authentication is configured, the
        authentication object is automatically passed with each API call. Calling
        this function again overwrites the previous authentication. Use ``auth_clear()``
        function to clear authentication.

        Parameters
        ----------
        username : str
            Username.
        password : str
            Password.

        Returns
        -------
        None

        Examples
        --------

        .. code-block:: python

            from save_and_restore_api import SaveRestoreAPI

            SR = SaveRestoreAPI(base_url="http://localhost:8080/save-restore")
            SR.auth_set(username="user", password="userPass")
            # ...........
            SR.auth_set(username="admin", password="adminPass")
            # ...........
            SR.auth_clear()

        """
        self._auth = self.auth_gen(username=username, password=password)

    def auth_clear(self):
        """
        Clear authentication for the session.
        """
        self._auth = None

    def _prepare_request(
        self, *, method, body_json=None, params=None, headers=None, data=None, timeout=None, auth=None
    ):
        kwargs = {}
        if body_json:
            kwargs.update({"json": body_json})
        if params:
            kwargs.update({"params": params})
        if headers:
            kwargs.update({"headers": headers})
        if data:
            kwargs.update({"data": data})
        if timeout is not None:
            kwargs.update({"timeout": self._adjust_timeout(timeout)})
        if method.upper() != "GET":
            auth = auth or self._auth
            if auth is not None:
                kwargs.update({"auth": auth})
        return kwargs

    def _process_response(self, *, client_response):
        client_response.raise_for_status()
        response = ""
        if client_response.content:
            try:
                response = client_response.json()
            except json.JSONDecodeError:
                response = client_response.text
        return response

    def _process_comm_exception(self, *, method, body_json, client_response):
        """
        The function must be called from ``except`` block and returns response with an error message
        or raises an exception.
        """
        try:
            raise

        except httpx.TimeoutException as ex:
            raise self.RequestTimeoutError(ex, {"method": method, "body_json": body_json}) from ex

        except httpx.RequestError as ex:
            raise self.HTTPRequestError(f"HTTP request error: {ex}") from ex

        except httpx.HTTPStatusError as exc:
            common_params = {"request": exc.request, "response": exc.response}
            if client_response and (client_response.status_code < 500):
                # Include more detail that httpx does by default.
                response_text = ""
                if client_response.content:
                    try:
                        _, response_text = exc.response.json(), ""
                        if isinstance(_, dict):
                            if "detail" in _:
                                response_text = _["detail"]
                            elif "error" in _:
                                response_text = _["error"]
                            else:
                                response_text = exc.response.text
                    except json.JSONDecodeError:
                        response_text = exc.response.text
                message = f"{exc.response.status_code}: {response_text} {exc.request.url}"
                raise self.HTTPClientError(message, **common_params) from exc
            else:
                raise self.HTTPServerError(exc, **common_params) from exc

    # =============================================================================================
    #                         INFO-CONTROLLER API METHODS
    # =============================================================================================

    def _prepare_info_get(self):
        method, url = "GET", "/"
        return method, url

    def _prepare_version_get(self):
        method, url = "GET", "/version"
        return method, url

    # =============================================================================================
    #                         SEARCH-CONTROLLER API METHODS
    # =============================================================================================

    def _prepare_search(self, *, allRequestParams):
        method, url = "GET", "/search"
        params = allRequestParams
        return method, url, params

    # =============================================================================================
    #                         HELP-RESOURCE API METHODS
    # =============================================================================================

    def _prepare_help(self, *, what, lang):
        method, url = "GET", f"/help/{what}"
        params = {"lang": lang} if lang else None
        return method, url, params

    # =============================================================================================
    #                         AUTHENTICATION-CONTROLLER API METHODS
    # =============================================================================================

    def _prepare_login(self, *, username=None, password=None):
        method, url = "POST", "/login"
        body_json = {"username": username, "password": password}
        return method, url, body_json

    # =============================================================================================
    #                         NODE-CONTROLLER API METHODS
    # =============================================================================================

    def _prepare_node_get(self, *, uniqueNodeId):
        method, url = "GET", f"/node/{uniqueNodeId}"
        return method, url

    def _prepare_nodes_get(self, *, uniqueIds):
        method, url = "GET", "/nodes"
        body_json = uniqueIds
        return method, url, body_json

    def _prepare_node_add(self, *, parentNodeId, node):
        if "name" not in node or "nodeType" not in node:
            raise self.RequestParameterError(f"Parameters 'name' and 'nodeType' are required in 'node': {node!r}.")
        node_type, node_types = node["nodeType"], ("FOLDER", "CONFIGURATION")
        if node_type not in node_types:
            raise self.RequestParameterError(f"Invalid 'nodeType': {node_type!r}. Supported types: {node_types}.")
        method, url, params = "PUT", "/node", {"parentNodeId": parentNodeId}
        body_json = node
        return method, url, params, body_json

    def _prepare_node_delete(self, *, nodeId):
        method, url = "DELETE", f"/node/{nodeId}"
        return method, url

    def _prepare_nodes_delete(self, *, uniqueIds):
        method, url = "DELETE", "/node"
        body_json = uniqueIds
        return method, url, body_json

    def _prepare_node_get_children(self, *, uniqueNodeId):
        method, url = "GET", f"/node/{uniqueNodeId}/children"
        return method, url

    def _prepare_node_get_parent(self, *, uniqueNodeId):
        method, url = "GET", f"/node/{uniqueNodeId}/parent"
        return method, url

    # =============================================================================================
    #                         CONFIGURATION-CONTROLLER API METHODS
    # =============================================================================================

    def _prepare_config_get(self, *, uniqueNodeId):
        method, url = "GET", f"/config/{uniqueNodeId}"
        return method, url

    def _prepare_config_add(self, *, parentNodeId, configurationNode, configurationData):
        method, url = "PUT", f"/config?parentNodeId={parentNodeId}"
        configurationData = configurationData or {}
        body_json = {"configurationNode": configurationNode, "configurationData": configurationData}
        return method, url, body_json

    def _prepare_config_update(self, *, configurationNode, configurationData):
        method, url = "POST", "/config"
        body_json = {"configurationNode": configurationNode, "configurationData": configurationData}
        return method, url, body_json

    # =============================================================================================
    #                         TAG-CONTROLLER API METHODS
    # =============================================================================================

    def _prepare_tags_get(self):
        method, url = "GET", "/tags"
        return method, url

    def _prepare_tags_add(self, *, uniqueNodeIds, tag):
        method, url = "POST", "/tags"
        body_json = {"uniqueNodeIds": uniqueNodeIds, "tag": tag}
        return method, url, body_json

    def _prepare_tags_delete(self, *, uniqueNodeIds, tag):
        method, url = "DELETE", "/tags"
        body_json = {"uniqueNodeIds": uniqueNodeIds, "tag": tag}
        return method, url, body_json

    # =============================================================================================
    #                         TAKE-SNAPSHOT-CONTROLLER API METHODS
    # =============================================================================================

    def _prepare_take_snapshot_get(self, *, uniqueNodeId):
        method, url = "GET", f"/take-snapshot/{uniqueNodeId}"
        return method, url

    def _prepare_take_snapshot_save(self, *, uniqueNodeId, name, comment):
        method, url = "PUT", f"/take-snapshot/{uniqueNodeId}"
        params = {"name": name, "comment": comment}
        return method, url, params

    # =============================================================================================
    #                         SNAPSHOT-CONTROLLER API METHODS
    # =============================================================================================

    def _prepare_snapshot_get(self, *, uniqueId):
        method, url = "GET", f"/snapshot/{uniqueId}"
        return method, url

    def _prepare_snapshot_add(self, *, parentNodeId, snapshotNode, snapshotData):
        method, url = "PUT", "/snapshot"
        body_json = {"snapshotNode": snapshotNode, "snapshotData": snapshotData}
        params = {"parentNodeId": parentNodeId}
        return method, url, params, body_json

    def _prepare_snapshot_update(self, *, snapshotNode, snapshotData):
        method, url = "POST", "/snapshot"
        body_json = {"snapshotNode": snapshotNode, "snapshotData": snapshotData}
        return method, url, body_json

    def _prepare_snapshots_get(self):
        method, url = "GET", "/snapshots"
        return method, url

    # =============================================================================================
    #                         COMPOSITE-SNAPSHOT-CONTROLLER API METHODS
    # =============================================================================================

    def _prepare_composite_snapshot_get(self, *, uniqueId):
        method, url = "GET", f"/composite-snapshot/{uniqueId}"
        return method, url

    def _prepare_composite_snapshot_get_nodes(self, *, uniqueId):
        method, url = "GET", f"/composite-snapshot/{uniqueId}/nodes"
        return method, url

    def _prepare_composite_snapshot_get_items(self, *, uniqueId):
        method, url = "GET", f"/composite-snapshot/{uniqueId}/items"
        return method, url

    def _prepare_composite_snapshot_add(self, *, parentNodeId, compositeSnapshotNode, compositeSnapshotData):
        method, url = "PUT", "/composite-snapshot"
        body_json = {
            "compositeSnapshotNode": compositeSnapshotNode,
            "compositeSnapshotData": compositeSnapshotData,
        }
        params = {"parentNodeId": parentNodeId}
        return method, url, params, body_json

    def _prepare_composite_snapshot_update(self, *, compositeSnapshotNode, compositeSnapshotData):
        method, url = "POST", "/composite-snapshot"
        body_json = {
            "compositeSnapshotNode": compositeSnapshotNode,
            "compositeSnapshotData": compositeSnapshotData,
        }
        return method, url, body_json

    def _prepare_composite_snapshot_consistency_check(self, *, uniqueNodeIds):
        method, url = "POST", "/composite-snapshot-consistency-check"
        body_json = uniqueNodeIds
        return method, url, body_json

    # =============================================================================================
    #                     SNAPSHOT-RESTORE-CONTROLLER API METHODS
    # =============================================================================================

    def _prepare_restore_node(self, *, nodeId):
        method, url = "POST", "/restore/node"
        params = {"nodeId": nodeId}
        return method, url, params

    def _prepare_restore_items(self, *, snapshotItems):
        method, url = "POST", "/restore/items"
        body_json = snapshotItems
        return method, url, body_json

    # =============================================================================================
    #                     COMPARISON-CONTROLLER API METHODS
    # =============================================================================================

    def _prepare_compare(self, *, nodeId, tolerance, compareMode, skipReadback):
        method, url = "GET", f"/compare/{nodeId}"
        params = {}
        if tolerance:
            params["tolerance"] = tolerance
        if compareMode:
            params["compareMode"] = compareMode
        if skipReadback is not None:
            params["skipReadback"] = str(skipReadback).lower()
        if not params:
            params = None
        return method, url, params

    # =============================================================================================
    #                     FILTER-CONTROLLER API METHODS
    # =============================================================================================

    def _prepare_filter_add(self, *, filter):
        method, url = "PUT", "/filter"
        body_json = filter
        return method, url, body_json

    def _prepare_filters_get(self):
        method, url = "GET", "/filters"
        return method, url

    def _prepare_filter_delete(self, *, name):
        # URL may contain spaces and special characters
        method, url = "DELETE", quote(f"/filter/{name}")
        return method, url

    # =============================================================================================
    #                     STRUCTURE-CONTROLLER API METHODS
    # =============================================================================================

    def _prepare_structure_move(self, *, nodeIds, newParentNodeId):
        method, url = "POST", "/move"
        params = {"to": newParentNodeId}
        body_json = nodeIds
        return method, url, body_json, params

    def _prepare_structure_copy(self, *, nodeIds, newParentNodeId):
        method, url = "POST", "/copy"
        params = {"to": newParentNodeId}
        body_json = nodeIds
        return method, url, body_json, params

    def _prepare_structure_path_get(self, *, uniqueNodeId):
        method, url = "GET", f"/path/{uniqueNodeId}"
        return method, url

    def _prepare_structure_path_nodes(self, *, path):
        method, url = "GET", "/path"
        params = {"path": path}
        return method, url, params
