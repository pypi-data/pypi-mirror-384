# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 Northwestern University.
#
# invenio-analytics-importer is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Command-line interface."""

import asyncio
from pathlib import Path

import click
import flask

from invenio_analytics_importer.cache import (
    fill_downloads_cache,
    fill_views_cache,
)
from invenio_analytics_importer.convert import (
    generate_download_analytics,
    generate_view_analytics,
)
from invenio_analytics_importer.ingest import (
    generate_download_stats,
    generate_view_stats,
    ingest_statistics,
)
from invenio_analytics_importer.read import read_raw_analytics_from_filepaths
from invenio_analytics_importer.retrieve import (
    retrieve_period_analytics,
)


@click.group()
@flask.cli.with_appcontext
def analytics():
    """Analytics importer commands."""


@analytics.command()
@click.option(
    "--views",
    "kind",
    flag_value="views",
    default="views",
    help="Retrieve views.",
)
@click.option(
    "--downloads",
    "kind",
    flag_value="downloads",
    help="Retrieve downloads.",
)
@click.option(
    "--from",
    "-f",
    "year_month_from",
    required=True,
    help="Download analytics from this month (inclusive).",
)
@click.option(
    "--to",
    "-t",
    "year_month_to",
    required=True,
    help="Download analytics to this month (inclusive).",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Place resulting analytics file in this directory.",
)
def retrieve(kind, year_month_from, year_month_to, output_dir):
    """Retrieve analytics from the web.

    For 'kind' the last --views/--downloads takes precedence.
    """
    asyncio.run(
        retrieve_period_analytics(
            provider="matomo",  # hardcoded for now
            kind=kind,
            period=(year_month_from, year_month_to),
            output_dir=output_dir,
        )
    )


@analytics.command()
@click.option(
    "--views",
    "kind",
    flag_value="views",
    default="views",
    help="Retrieve views.",
)
@click.option(
    "--downloads",
    "kind",
    flag_value="downloads",
    help="Retrieve downloads.",
)
@click.option(
    "-f", "--filepath", type=click.Path(exists=True, path_type=Path),
    multiple=True
)
def ingest(kind, filepath):
    """Ingest stats from given filepaths into your RDM instance."""
    # filepath is actually a list of filepaths
    filepaths = filepath

    # Raw read is same across views/downloads
    raw_analytics = read_raw_analytics_from_filepaths(filepaths)

    # Convert raw analytics to processed analytics
    if kind == "views":
        iter_analytics = generate_view_analytics(raw_analytics)
    elif kind == "downloads":
        iter_analytics = generate_download_analytics(raw_analytics)
    else:
        exit(1)

    # Prepare cache
    raw_analytics_for_cache = read_raw_analytics_from_filepaths(filepaths)
    if kind == "views":
        iter_analytics_for_cache = generate_view_analytics(
            raw_analytics_for_cache
        )
        cache = fill_views_cache(iter_analytics_for_cache)
    elif kind == "downloads":
        iter_analytics_for_cache = generate_download_analytics(
            raw_analytics_for_cache
        )
        cache = fill_downloads_cache(iter_analytics_for_cache)

    # Convert to ingestable
    if kind == "views":
        stats_for_ingest = generate_view_stats(iter_analytics, cache)
    elif kind == "downloads":
        stats_for_ingest = generate_download_stats(iter_analytics, cache)

    # ingest is same across kind
    ingest_statistics(stats_for_ingest)
