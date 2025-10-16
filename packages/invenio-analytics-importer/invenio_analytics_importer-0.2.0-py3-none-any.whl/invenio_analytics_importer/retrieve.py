# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 Northwestern University.
#
# invenio-analytics-importer is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Retrieve aggregate analytics from provider."""

import abc
import asyncio
import calendar
import dataclasses
from typing import Any

import httpx
from flask import current_app

from invenio_analytics_importer.write import write_json


class ProviderClient(abc.ABC):
    """Provider client interface."""

    @abc.abstractmethod
    async def fetch_views_for_day(self, day):
        """Fetch views for given day."""

    @abc.abstractmethod
    async def fetch_downloads_for_day(self, day):
        """Fetch downloads for given day."""


@dataclasses.dataclass
class MatomoAnalytics(ProviderClient):
    """Matomo API client."""

    client: Any
    base_url: str
    site_id: int
    token_auth: str

    async def get_analytics_for_day(self, method, day):
        """Get analytics for given YYYY-MM-DD in json format.

        Response format:

        {
            "label": "example.org/records/0dfv3-cmw61/files/f.pdf?download=1]",
            "nb_hits": 1,
            "nb_uniq_visitors": 1,
            "nb_visits": 1,
        },
        """
        params = {
            "module": "API",
            "format": "json",
            "idSite": self.site_id,
            "period": "day",
            "date": day,
            "method": method,
            "flat": 1,
            "showMetadata": 0,
        }

        try:
            response = await self.client.post(
                self.base_url,
                params=params,
                data={"token_auth": self.token_auth}
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            print(f"Error : {exc.request.url} : {exc}")
            return []

        if response.text == "No data available":
            return []

        return response.json()

    async def fetch_downloads_for_day(self, day):
        """Fetch downloads analytics for day."""
        return await self.get_analytics_for_day("Actions.getDownloads", day)

    async def fetch_views_for_day(self, day):
        """Fetch views analytics for day."""
        return await self.get_analytics_for_day("Actions.getPageUrls", day)


class ViewsFetcher:
    """Fetches views."""

    def __init__(self, client):
        """Constructor."""
        self.client = client

    async def fetch_analytics_for_day(self, day):
        """Fetch views analytics for given day."""
        return await self.client.fetch_views_for_day(day)


class DownloadsFetcher:
    """Fetches downloads."""

    def __init__(self, client):
        """Constructor."""
        self.client = client

    async def fetch_analytics_for_day(self, day):
        """Fetch download analytics for given day."""
        return await self.client.fetch_downloads_for_day(day)


def generate_days_by_year_month(period):
    """
    Yield (YYYY-MM, (YYYY-MM-DD1, ..., YYYY-MM-DDN)) for each month of period.

    :param period: tuple. (date_from, date_to)
        :param date_from: str. YYYY-MM-DD from inclusive.
        :param date_to: str. YYYY-MM-DD to inclusive.
    """
    date_from, date_to = period
    tmp = date_from.split("-")
    year_from, month_from = int(tmp[0]), int(tmp[1])
    tmp = date_to.split("-")
    year_to, month_to = int(tmp[0]), int(tmp[1])

    y = year_from
    m = month_from
    while (y, m) <= (year_to, month_to):
        days_in_month = calendar.monthrange(y, m)[1]
        year_month = f"{y:4}-{m:02}"
        days = (
            f"{y:4}-{m:02}-{d:02}" for d in range(1, days_in_month + 1)
        )

        yield year_month, days

        m += 1
        if m > 12:
            y += 1
            m = 1


async def fetch_monthly_analytics(fetcher, period):
    """Yield fetched analytics by month (and day within month)."""
    days_by_yr_m = generate_days_by_year_month(period)

    for year_month, days in days_by_yr_m:
        days_l = list(days)
        # This maps to 30~ concurrent network calls at a time which has been
        # fine so far. It may return lots of data to hold in memory though.
        # This has been fine for us so far as well, but it's a trade-off in
        # favor of less files and more understandable periods.
        analytics_daily = await asyncio.gather(
            *[fetcher.fetch_analytics_for_day(day) for day in days_l]
        )
        analytics_monthly = dict(zip(days_l, analytics_daily))
        yield year_month, analytics_monthly


async def retrieve_period_analytics(provider, kind, period, output_dir):
    """Framing device."""
    async with httpx.AsyncClient() as client:
        # If other providers, do selection + creation here.
        # For now, there isn't, so no selection logic.
        client_of_provider = MatomoAnalytics(
            client,
            base_url=current_app.config.get("ANALYTICS_IMPORTER_MATOMO_URL"),
            site_id=current_app.config.get("ANALYTICS_IMPORTER_MATOMO_SITE_ID"),  # noqa
            token_auth=current_app.config.get("ANALYTICS_IMPORTER_MATOMO_TOKEN"),  # noqa
        )

        if kind == "views":
            fetcher = ViewsFetcher(client_of_provider)
        elif kind == "downloads":
            fetcher = DownloadsFetcher(client_of_provider)
        else:
            exit(1)

        async for yr_m, analytics in fetch_monthly_analytics(fetcher, period):
            write_json(output_dir / f"{kind}_{yr_m}.json", analytics)
