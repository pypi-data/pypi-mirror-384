# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 Northwestern University.
#
# invenio-analytics-importer is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Convert data from one format to another.

WARNING: all of the below assumes Matomo output for now.
"""

import dataclasses
import re

REGEX_PID = re.compile(r"/records/([^/]*)(?:/|$)")
REGEX_DOWNLOAD = re.compile(r"\?download=1$")


def is_record(analytics_raw):
    """Return if analytics is for a record."""
    label = analytics_raw.get("label", "")
    match = REGEX_PID.search(label)
    return bool(match.group(1)) if match else False


def is_download(analytics_raw):
    """Return if analytics is for a download.

    Although Matomo returns what it considers a download,
    this isn't always what we consider a download. For the purposes of
    InvenioRDM, a download is what Matomo returns + filtering on presence
    of `download=1` querystring parameter (i.e. not a preview, and always
    unique/at end of label).
    """
    label = analytics_raw.get("label", "")
    match = REGEX_DOWNLOAD.search(label)
    return bool(match)


@dataclasses.dataclass
class DownloadAnalytics:
    """Intermediate representation."""

    year_month_day: str  # keeping it simple for now
    pid: str
    file_key: str
    visits: int
    views: int

    @classmethod
    def create(cls, year_month_day, analytics_raw):
        """Create Entry from raw analytics."""
        label = analytics_raw.get("label", "")

        # extract "3s45v-k5m55" from ".../records/3s45v-k5m55[/...]"
        # assumes is_record was run on analytics_raw prior to this point
        pid = REGEX_PID.search(label).group(1)

        # extract file key
        regex_key = re.compile(r"/files/([^?]*)\?download=1")
        file_key = regex_key.search(label).group(1)

        return cls(
            year_month_day=year_month_day,
            pid=pid,
            file_key=file_key,
            visits=analytics_raw.get("nb_visits", 0),
            views=analytics_raw.get("nb_hits", 0),
        )


def generate_download_analytics(raw_analytics):
    """Yield DownloadAnalytics entries from raw entries."""
    for year_month_day, raw in raw_analytics:
        if is_record(raw) and is_download(raw):
            yield DownloadAnalytics.create(year_month_day, raw)


@dataclasses.dataclass
class ViewAnalytics:
    """Intermediate representation of view analytics."""

    year_month_day: str  # keeping it simple for now
    pid: str
    visits: int
    views: int

    @classmethod
    def create(cls, year_month_day, analytics_raw):
        """Create from raw analytics."""
        label = analytics_raw.get("label", "")

        # extract "3s45v-k5m55" from ".../records/3s45v-k5m55[/...]"
        # assumes is_record was run on analytics_raw prior to this point
        pid = REGEX_PID.search(label).group(1)

        return cls(
            year_month_day=year_month_day,
            pid=pid,
            visits=analytics_raw.get("nb_visits", 0),
            views=analytics_raw.get("nb_hits", 0),
        )


def generate_view_analytics(raw_analytics):
    """Yield ViewAnalytics entries from raw entries."""
    for year_month_day, raw in raw_analytics:
        if is_record(raw):
            yield ViewAnalytics.create(year_month_day, raw)
