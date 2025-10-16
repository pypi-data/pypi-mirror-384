# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 Northwestern University.
#
# invenio-analytics-importer is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Cache of data needed for ingestion work."""

from invenio_db import db
from invenio_rdm_records.records import RDMRecord
from invenio_search import current_search_client
from invenio_search.engine import dsl
from sqlalchemy import select


def scan_records(record_cls, pids):
    """Retrieve SE record."""
    s = dsl.Search(
        using=current_search_client,
        index=record_cls.index.search_alias
    )

    s = s.filter({"terms": {"id": pids}})

    response = s.scan()

    return response


class Cache:
    """Cache of system info."""

    def __init__(self):
        """Constructor."""
        self._data = []
        self._pid_record_and_file_key_to_file_id = {}
        self._pid_record_to_bucket_id = {}
        self._file_id_to_size = {}
        self._pid_record_to_pid_parent = {}

    def get_file_id(self, pid_of_record, file_key):
        """Get file id."""
        return self._pid_record_and_file_key_to_file_id[(pid_of_record, file_key)]  # noqa

    def set_file_id(self, pid_of_record, file_key, file_id):
        """Set file id."""
        self._pid_record_and_file_key_to_file_id[(pid_of_record, file_key)] = file_id  # noqa

    def get_bucket_id(self, pid_of_record):
        """Get bucket id associated with record."""
        return self._pid_record_to_bucket_id[pid_of_record]

    def set_bucket_id(self, pid_of_record, bucket_id):
        """Set bucket id associated with record."""
        self._pid_record_to_bucket_id[pid_of_record] = str(bucket_id)

    def get_size(self, file_id):
        """Get size in bytes of file."""
        return self._file_id_to_size.get(file_id, 0)

    def set_size(self, file_id, size):
        """Set size in bytes of file."""
        self._file_id_to_size[file_id] = size

    def get_parent_pid(self, pid_of_record):
        """Get pid of parent of record."""
        return self._pid_record_to_pid_parent[pid_of_record]

    def set_parent_pid(self, pid_of_record, pid_of_parent):
        """Set pid of parent of record."""
        self._pid_record_to_pid_parent[pid_of_record] = pid_of_parent


def fill_downloads_cache(analytics):
    """Fill and return a downloads cache."""
    cache = Cache()

    pids_set = set(a.pid for a in analytics)

    record_cls = RDMRecord
    uuid_to_pid = {}

    # Get and populate file_ids, size, and parent_id
    results = scan_records(record_cls, list(pids_set))
    for hit in results:
        pid = hit["id"]
        pid_of_parent = hit["parent"]["id"]
        uuid = hit["uuid"]

        cache.set_parent_pid(pid, pid_of_parent)
        uuid_to_pid[uuid] = pid

        entries = hit.get("files", {}).get("entries", [])
        for e in entries:
            key = e["key"]
            file_id = e["file_id"]
            size = e["size"]

            cache.set_file_id(pid, key, file_id)
            cache.set_size(file_id, size)

    # Get and populate bucket id
    stmt = select(
        record_cls.model_cls.id,
        record_cls.model_cls.bucket_id,
    ).where(record_cls.model_cls.id.in_(list(uuid_to_pid.keys())))

    for uuid_of_record, bucket_id in db.session.execute(stmt):
        pid = uuid_to_pid[str(uuid_of_record)]
        cache.set_bucket_id(pid, bucket_id)

    return cache


def fill_views_cache(analytics):
    """Fill and return a views cache."""
    cache = Cache()

    pids_set = set(a.pid for a in analytics)

    # Get and populate parent_id
    record_cls = RDMRecord
    results = scan_records(record_cls, list(pids_set))
    for hit in results:
        pid = hit["id"]
        pid_of_parent = hit["parent"]["id"]
        cache.set_parent_pid(pid, pid_of_parent)

    return cache
