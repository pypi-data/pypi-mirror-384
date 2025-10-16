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
    filter_prefix,
)

# =============================================================================================
#                         TESTS FOR FILTER-CONTROLLER API METHODS
# =============================================================================================


# fmt: off
@pytest.mark.parametrize("usesetauth", [True, False])
@pytest.mark.parametrize("library", ["THREADS", "ASYNC"])
# fmt: on
def test_filter_add_01(clear_sar, library, usesetauth):  # noqa: F811
    """
    Basic tests for the 'filter_add', 'filters_get' and 'filter_delete' API.
    """
    if not _is_async(library):
        with SaveRestoreAPI_Threads(base_url=base_url, timeout=10) as SR:
            auth = _select_auth(SR=SR, usesetauth=usesetauth)

            response = SR.filters_get()
            n_filters_baseline = len(response)

            f1_name = filter_prefix + " Test Filter #01"
            f2_name = filter_prefix + " Test Filter #02"
            response = SR.filter_add({"name": f1_name, "filter": "name=ISrc&type=snapshot"}, **auth)
            response = SR.filter_add({"name": f2_name, "filter": "type=snapshot&tags=TimingTables"}, **auth)

            response = SR.filters_get()
            assert len(response) == n_filters_baseline + 2

            response = SR.filter_delete(f1_name, **auth)
            response = SR.filter_delete(f2_name, **auth)

            response = SR.filters_get()
            assert len(response) == n_filters_baseline

    else:
        async def testing():
            async with SaveRestoreAPI_Async(base_url=base_url, timeout=2) as SR:
                auth = _select_auth(SR=SR, usesetauth=usesetauth)

                response = await SR.filters_get()
                n_filters_baseline = len(response)

                f1_name = filter_prefix + " Test Filter #01"
                f2_name = filter_prefix + " Test Filter #02"
                response = await SR.filter_add(
                    {"name": f1_name, "filter": "name=ISrc&type=snapshot"}, **auth
                )
                response = await SR.filter_add(
                    {"name": f2_name, "filter": "type=snapshot&tags=TimingTables"}, **auth
                )

                response = await SR.filters_get()
                assert len(response) == n_filters_baseline + 2

                response = await SR.filter_delete(f1_name, **auth)
                response = await SR.filter_delete(f2_name, **auth)

                response = await SR.filters_get()
                assert len(response) == n_filters_baseline

        asyncio.run(testing())
