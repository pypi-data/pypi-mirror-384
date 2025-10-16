# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 Northwestern University.
#
# invenio-analytics-importer is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

import pytest

from invenio_analytics_importer.cache import (
    fill_downloads_cache,
    fill_views_cache,
)
from invenio_analytics_importer.convert import DownloadAnalytics, ViewAnalytics


def test_fill_downloads_cache(running_app, db, record_factory):
    file_key = "coffee.assess.nobmi.txt"
    r = record_factory.create_record(filenames=[file_key])
    r.index.refresh()
    pid = r.pid.pid_value
    iter_analytics = [
        DownloadAnalytics(
            year_month_day="2024-09-03",
            pid=pid,
            file_key=file_key,
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
    ]

    cache = fill_downloads_cache(iter_analytics)

    file_model = r.files[file_key].file.file_model
    file_id = cache.get_file_id(pid, file_key)
    assert str(file_model.id) == file_id
    assert r.parent.pid.pid_value == cache.get_parent_pid(pid)
    assert file_model.size == cache.get_size(file_id)
    assert str(r.bucket_id) == cache.get_bucket_id(pid)

    with pytest.raises(KeyError):
        cache.get_parent_pid("notin-cache")
    with pytest.raises(KeyError):
        cache.get_file_id("notin-cache", "doesnt_exist.txt")


def test_fill_views_cache(running_app, db, record_factory):
    r = record_factory.create_record()
    r.index.refresh()
    pid = r.pid.pid_value
    iter_analytics = [
        ViewAnalytics(
            year_month_day="2024-09-03",
            pid=pid,
            visits=2,
            views=3,
        ),
        ViewAnalytics(
            year_month_day="2024-09-03",
            pid="notin-cache",
            visits=1,
            views=1,
        ),
    ]

    cache = fill_views_cache(iter_analytics)

    assert r.parent.pid.pid_value == cache.get_parent_pid(pid)
    with pytest.raises(KeyError):
        cache.get_parent_pid("notin-cache")
