=============
API Reference
=============

.. currentmodule:: save_and_restore_api

Synchronous Communication with Save-And-Restore Server
------------------------------------------------------

.. autosummary::
   :nosignatures:
   :toctree: generated

    SaveRestoreAPI
    SaveRestoreAPI.send_request
    SaveRestoreAPI.open
    SaveRestoreAPI.close
    SaveRestoreAPI.__enter__
    SaveRestoreAPI.__exit__

Authentication
**************

.. autosummary::
   :nosignatures:
   :toctree: generated

    SaveRestoreAPI.auth_gen
    SaveRestoreAPI.auth_set
    SaveRestoreAPI.auth_clear
    SaveRestoreAPI.login

Info Controller API
*******************

.. autosummary::
   :nosignatures:
   :toctree: generated

    SaveRestoreAPI.info_get
    SaveRestoreAPI.version_get

Search Controller API
*********************

.. autosummary::
   :nosignatures:
   :toctree: generated

    SaveRestoreAPI.search

Help Controller API
*******************

.. autosummary::
   :nosignatures:
   :toctree: generated

    SaveRestoreAPI.help


Node Controller API
*******************

.. autosummary::
   :nosignatures:
   :toctree: generated

      SaveRestoreAPI.node_get
      SaveRestoreAPI.nodes_get
      SaveRestoreAPI.node_add
      SaveRestoreAPI.node_delete
      SaveRestoreAPI.nodes_delete
      SaveRestoreAPI.node_get_children
      SaveRestoreAPI.node_get_parent


Configuration Controller API
****************************

.. autosummary::
   :nosignatures:
   :toctree: generated

      SaveRestoreAPI.config_get
      SaveRestoreAPI.config_add
      SaveRestoreAPI.config_update


Tag Controller API
******************

.. autosummary::
   :nosignatures:
   :toctree: generated

      SaveRestoreAPI.tags_get
      SaveRestoreAPI.tags_add
      SaveRestoreAPI.tags_delete


Take Snapshot Controller API
****************************

.. autosummary::
   :nosignatures:
   :toctree: generated

      SaveRestoreAPI.take_snapshot_get
      SaveRestoreAPI.take_snapshot_save


Snapshot Controller API
***********************

.. autosummary::
   :nosignatures:
   :toctree: generated

      SaveRestoreAPI.snapshot_get
      SaveRestoreAPI.snapshot_add
      SaveRestoreAPI.snapshot_update
      SaveRestoreAPI.snapshots_get


Composite Snapshot Controller API
*********************************

.. autosummary::
   :nosignatures:
   :toctree: generated

      SaveRestoreAPI.composite_snapshot_get
      SaveRestoreAPI.composite_snapshot_get_nodes
      SaveRestoreAPI.composite_snapshot_get_items
      SaveRestoreAPI.composite_snapshot_add
      SaveRestoreAPI.composite_snapshot_update
      SaveRestoreAPI.composite_snapshot_consistency_check


Snapshot Restore Controller API
*******************************

.. autosummary::
   :nosignatures:
   :toctree: generated

      SaveRestoreAPI.restore_node
      SaveRestoreAPI.restore_items


Comparison Controller API
*************************

.. autosummary::
   :nosignatures:
   :toctree: generated

      SaveRestoreAPI.compare


Filter Controller API
*********************

.. autosummary::
   :nosignatures:
   :toctree: generated

      SaveRestoreAPI.filter_add
      SaveRestoreAPI.filters_get
      SaveRestoreAPI.filter_delete


Structure Controller API
************************

.. autosummary::
   :nosignatures:
   :toctree: generated

      SaveRestoreAPI.structure_move
      SaveRestoreAPI.structure_copy
      SaveRestoreAPI.structure_path_get
      SaveRestoreAPI.structure_path_nodes


Asynchronous Communication with 0MQ Server
------------------------------------------

.. autosummary::
   :nosignatures:
   :toctree: generated

    aio.SaveRestoreAPI
