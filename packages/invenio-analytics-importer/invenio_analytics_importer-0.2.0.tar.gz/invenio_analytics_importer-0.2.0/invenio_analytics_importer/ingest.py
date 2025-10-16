# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 Northwestern University.
#
# invenio-analytics-importer is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Ingest analytics into InvenioRDM's stats indices."""

from datetime import datetime, timezone

from invenio_search import current_search_client
from invenio_search.engine import search


def record_exists(entry, cache):
    """Checks if the record of passed analytic exists.

    Really this checks if the analytic is for a record in the system and uses
    the cache as the proxy for that.
    """
    try:
        # This would work for views or downloads, so is used to assess presence
        # in cache (assumes some knowledge of how cache is filled)
        return cache.get_parent_pid(entry.pid) is not None
    except KeyError:
        return False


def file_key_exists(entry, cache):
    """Checks if the file key of passed analytic exists.

    Really this checks if the file of the record exists in the system and uses
    the cache as the proxy for that.
    """
    try:
        return cache.get_file_id(entry.pid, entry.file_key) is not None
    except KeyError:
        return False


def to_download(entry, cache):
    """To download."""
    file_id = cache.get_file_id(entry.pid, entry.file_key)
    bucket_id = cache.get_bucket_id(entry.pid)
    year_month_day = entry.year_month_day
    event_name = "file-download"
    year_month = year_month_day.rsplit("-", 1)[0]
    count = entry.views
    unique_count = entry.visits
    volume = count * cache.get_size(file_id)
    file_key = entry.file_key
    recid = entry.pid
    parent_recid = cache.get_parent_pid(recid)

    return {
        "_id": f"{bucket_id}_{file_id}-{year_month_day}",
        "_index": f"stats-{event_name}-{year_month}",
        "_source": {
            # Since those entries are synthetic anyway, we place them at
            # the start of the day
            "timestamp": f"{year_month_day}T00:00:00",
            "unique_id": f"{bucket_id}_{file_id}",
            "count": count,
            "updated_timestamp": datetime.now(timezone.utc).isoformat(),
            "unique_count": unique_count,
            "volume": volume,
            "file_key": file_key,
            "bucket_id": bucket_id,
            "file_id": file_id,
            "recid": recid,
            "parent_recid": parent_recid,
        },
    }


def generate_download_stats(analytics, cache):
    """Generator for download statistics actions."""
    for analytic in analytics:
        if record_exists(analytic, cache) and file_key_exists(analytic, cache):
            yield to_download(analytic, cache)


def to_view(entry, cache):
    """To view."""
    recid = entry.pid
    year_month_day = entry.year_month_day
    event_name = "record-view"
    year_month = year_month_day.rsplit("-", 1)[0]
    count = entry.views
    unique_count = entry.visits
    parent_recid = cache.get_parent_pid(recid)

    return {
        "_id": f"ui_{recid}-{year_month_day}",
        "_index": f"stats-{event_name}-{year_month}",
        "_source": {
            # Since those entries are synthetic anyway, we place them at
            # the start of the day
            "timestamp": f"{year_month_day}T00:00:00",
            "unique_id": f"ui_{recid}",
            "count": count,
            "updated_timestamp": datetime.now(timezone.utc).isoformat(),
            "unique_count": unique_count,
            "recid": recid,
            "parent_recid": parent_recid,
            "via_api": False,
        },
    }


def generate_view_stats(analytics, cache):
    """Generator for view statistics actions."""
    for analytic in analytics:
        if record_exists(analytic, cache):
            yield to_view(analytic, cache)


def ingest_statistics(actions):
    """Ingest statistics actions."""
    search.helpers.bulk(
        current_search_client,
        actions,
        stats_only=True,
        chunk_size=50,
    )
