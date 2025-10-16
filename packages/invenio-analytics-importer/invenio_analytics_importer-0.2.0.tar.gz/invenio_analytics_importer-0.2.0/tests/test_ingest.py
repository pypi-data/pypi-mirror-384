# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 Northwestern University.
#
# invenio-analytics-importer is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

import datetime as dt

import time_machine
from invenio_search import current_search_client
from invenio_search.engine import dsl

from invenio_analytics_importer.cache import Cache
from invenio_analytics_importer.convert import DownloadAnalytics, ViewAnalytics
from invenio_analytics_importer.ingest import (
    generate_download_stats,
    generate_view_stats,
    ingest_statistics,
)


def test_generate_download_stats():
    cache = Cache()
    cache.set_size("cb297587-b25c-4675-832a-d5d2634551c7", 9)
    cache.set_file_id(
        "5ret9-dwz86",
        file_key="coffee.assess.nobmi.txt",
        file_id="cb297587-b25c-4675-832a-d5d2634551c7",
    )
    cache.set_bucket_id("5ret9-dwz86", "1741e723-420a-4023-ad89-7aedebab7bb1")
    cache.set_parent_pid("5ret9-dwz86", "tb2gj-axd97")

    iter_analytics = [
        DownloadAnalytics(
            year_month_day="2024-09-03",
            pid="5ret9-dwz86",
            file_key="coffee.assess.nobmi.txt",
            visits=2,
            views=3,
        ),
        DownloadAnalytics(
            year_month_day="2024-09-03",
            pid="notin-cache",
            file_key="doesnt_exist.txt",
            visits=1,
            views=1,
        ),
        DownloadAnalytics(
            year_month_day="2024-09-03",
            pid="5ret9-dwz86",  # in cache
            file_key="doesnt_exist.txt",  # not in cache
            visits=2,
            views=2,
        ),
    ]

    pit = dt.datetime(2025, 9, 23, 0, 0, 0, tzinfo=dt.timezone.utc)
    with time_machine.travel(pit):
        stats = generate_download_stats(iter_analytics, cache)
        stats = list(stats)

    expected = {
        "_id": "1741e723-420a-4023-ad89-7aedebab7bb1_cb297587-b25c-4675-832a-d5d2634551c7-2024-09-03",  # noqa
        "_index": f"stats-file-download-2024-09",
        "_source": {
            "timestamp": f"2024-09-03T00:00:00",
            "unique_id": "1741e723-420a-4023-ad89-7aedebab7bb1_cb297587-b25c-4675-832a-d5d2634551c7",  # noqa
            "count": 3,
            "updated_timestamp": "2025-09-23T00:00:00+00:00",
            "unique_count": 2,
            "volume": 27,
            "file_id": "cb297587-b25c-4675-832a-d5d2634551c7",
            "file_key": "coffee.assess.nobmi.txt",
            "bucket_id": "1741e723-420a-4023-ad89-7aedebab7bb1",
            "recid": "5ret9-dwz86",
            "parent_recid": "tb2gj-axd97",
        },
    }
    assert 1 == len(stats)
    assert expected == stats[0]


def test_generate_view_stats():
    cache = Cache()
    cache.set_parent_pid("0c8rx-zsn76", "by5n4-x1h80")

    iter_analytics = [
        ViewAnalytics(
            year_month_day="2024-08-30",
            pid="0c8rx-zsn76",
            visits=2,
            views=3,
        ),
        ViewAnalytics(
            year_month_day="2024-09-23",
            pid="notin-cache",
            visits=1,
            views=1,
        ),
    ]

    pit = dt.datetime(2025, 9, 23, 0, 0, 0, tzinfo=dt.timezone.utc)
    with time_machine.travel(pit):
        stats = list(generate_view_stats(iter_analytics, cache))

    expected = {
        "_id": f"ui_0c8rx-zsn76-2024-08-30",
        "_index": f"stats-record-view-2024-08",
        "_source": {
            "timestamp": f"2024-08-30T00:00:00",
            "unique_id": "ui_0c8rx-zsn76",
            "count": 3,
            "updated_timestamp": "2025-09-23T00:00:00+00:00",
            "unique_count": 2,
            "recid": "0c8rx-zsn76",
            "parent_recid": "by5n4-x1h80",
            "via_api": False,
        },
    }
    assert 1 == len(stats)
    assert expected == stats[0]


def test_ingest_statistics(running_app):
    stats_for_ingest = [
        {
            "_id": f"ui_0c8rx-zsn76-2024-08-30",
            "_index": f"stats-record-view-2024-08",
            "_source": {
                "timestamp": f"2024-08-30T00:00:00",
                "unique_id": "ui_0c8rx-zsn76",
                "count": 1,
                "updated_timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),  # noqa
                "unique_count": 1,
                "recid": "0c8rx-zsn76",
                "parent_recid": "by5n4-x1h80",
                "via_api": False,
            },
        },
        {
            "_id": "1741e723-420a-4023-ad89-7aedebab7bb1_cb297587-b25c-4675-832a-d5d2634551c7-2024-09-03",  # noqa
            "_index": f"stats-file-download-2024-09",
            "_source": {
                "timestamp": f"2024-09-03T00:00:00",
                "unique_id": "1741e723-420a-4023-ad89-7aedebab7bb1_cb297587-b25c-4675-832a-d5d2634551c7",  # noqa
                "count": 3,
                "updated_timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),  # noqa
                "unique_count": 2,
                "volume": 27,
                "file_id": "cb297587-b25c-4675-832a-d5d2634551c7",
                "file_key": "coffee.assess.nobmi.txt",
                "bucket_id": "1741e723-420a-4023-ad89-7aedebab7bb1",
                "recid": "5ret9-dwz86",
                "parent_recid": "tb2gj-axd97",
            },
        },
    ]

    # Actual function under test
    ingest_statistics(stats_for_ingest)
    current_search_client.indices.refresh(index="stats-file-*")
    current_search_client.indices.refresh(index="stats-record-*")

    s = dsl.Search(
        using=current_search_client,
        index="stats-record-view-2024-08"
    )
    unique_id = "ui_0c8rx-zsn76"
    result = next(
        (h for h in s.scan() if h["unique_id"] == unique_id),
        None
    )
    assert "timestamp" in result
    assert 1 == result["count"]
    assert "updated_timestamp" in result
    assert 1 == result["unique_count"]
    assert "0c8rx-zsn76" == result["recid"]
    assert "by5n4-x1h80" == result["parent_recid"]
    assert result["via_api"] is False

    s = dsl.Search(
        using=current_search_client,
        index="stats-file-download-2024-09"
    )
    unique_id = "1741e723-420a-4023-ad89-7aedebab7bb1_cb297587-b25c-4675-832a-d5d2634551c7"  # noqa
    result = next(
        (
            h for h in s.scan()
            if h["unique_id"] == unique_id
        ),
        None
    )
    assert "timestamp" in result
    assert 3 == result["count"]
    assert "updated_timestamp" in result
    assert 2 == result["unique_count"]
    assert 27 == result["volume"]
    assert "cb297587-b25c-4675-832a-d5d2634551c7" == result["file_id"]
    assert "coffee.assess.nobmi.txt" == result["file_key"]
    assert "1741e723-420a-4023-ad89-7aedebab7bb1" == result["bucket_id"]
    assert "5ret9-dwz86" == result["recid"]
    assert "tb2gj-axd97" == result["parent_recid"]
