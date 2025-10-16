# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 Northwestern University.
#
# invenio-analytics-importer is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

import dataclasses
import json

import pytest

from invenio_analytics_importer.retrieve import (
    DownloadsFetcher,
    MatomoAnalytics,
    ProviderClient,
    ViewsFetcher,
    fetch_monthly_analytics,
)


@dataclasses.dataclass
class FakeResponse:
    """Fake response."""

    json_body: str

    def raise_for_status(self):
        """Faked raise_for_status."""
        return False

    @property
    def text(self):
        """Faked text."""
        return self.json_body

    def json(self):
        """Faked json."""
        return json.loads(self.json_body)


class FakeClient:
    """Fake httpx client."""

    def __init__(self):
        """Constructor."""
        self._response_data = {}

    def set_response(self, criteria, json_body=""):
        """Register a response."""
        self._response_data[criteria] = {
            "json_body": json_body,
        }

    def get_response(self, criteria):
        """Get response."""
        data = self._response_data[criteria]
        return FakeResponse(**data)

    async def post(self, url, params=None, data=None):
        """Post."""
        return self.get_response((url, params["date"]))


@pytest.mark.asyncio
async def test_matomo_get_analytics_for_day(running_app):
    analytics_2024_08_01 = [
        {
            "label": f"prism.northwestern.edu/records/paah4-s0w35/files/PNB-7-75.txt?download=1",  # noqa
            "nb_hits": 1,
            "nb_uniq_visitors": 1,
            "nb_visits": 1,
            "sum_time_spent": 0,
        },
        {
            "label": f"prism.northwestern.edu/records/t8k1h-p8435/files/PNB 7 76.txt?download=1",  # noqa
            "nb_hits": 1,
            "nb_uniq_visitors": 1,
            "nb_visits": 1,
            "sum_time_spent": 0,
        },
    ]
    fake_client = FakeClient()
    base_url = "https://matomo.example.org/"
    fake_client.set_response(
        (base_url, "2024-08-01"),
        json.dumps(analytics_2024_08_01)
    )
    fake_client.set_response((base_url, "2024-08-02"), "No data available")
    site_id = 3
    token = "token"
    matomo = MatomoAnalytics(fake_client, base_url, site_id, token)

    # Test with data
    result = await matomo.get_analytics_for_day("aMethod", "2024-08-01")

    assert analytics_2024_08_01 == result

    # Test when no data available
    result = await matomo.get_analytics_for_day("aMethod", "2024-08-02")

    assert [] == result


class FakeProviderClient(ProviderClient):
    """Fave provider client."""

    async def fetch_downloads_for_day(self, day):
        """Fetch downloads for day."""
        return [{"downloads": 1}]

    async def fetch_views_for_day(self, day):
        """Fetch views for day."""
        return [{"views": 1}]


@pytest.mark.asyncio
async def test_downloads_fetcher():
    # We are simply testing interfaces here
    fetcher = DownloadsFetcher(FakeProviderClient())

    results = await fetcher.fetch_analytics_for_day("2024-08-31")

    assert [{"downloads": 1}] == results


@pytest.mark.asyncio
async def test_views_fetcher():
    # We are simply testing interfaces here
    fetcher = ViewsFetcher(FakeProviderClient())

    results = await fetcher.fetch_analytics_for_day("2024-08-31")

    assert [{"views": 1}] == results


class FakeFetcher:
    """Fetches downloads."""

    def __init__(self):
        """Constructor."""
        self._response_data = {}

    def set_response(self, day, json_list):
        """Register a response."""
        self._response_data[day] = json_list

    async def fetch_analytics_for_day(self, day):
        """Fetch download analytics for given day."""
        return self._response_data.get(day, [])


@pytest.mark.asyncio
async def test_fetch_monthly_analytics():
    fetcher = FakeFetcher()
    analytics_2023_12_01 = [
        {
            "label": f"prism.northwestern.edu/records/paah4-s0w35/files/PNB-7-75.txt?download=1",  # noqa
            "nb_hits": 1,
            "nb_uniq_visitors": 1,
            "nb_visits": 1,
            "sum_time_spent": 0,
        },
        {
            "label": f"prism.northwestern.edu/records/t8k1h-p8435/files/PNB 7 76.txt?download=1",  # noqa
            "nb_hits": 1,
            "nb_uniq_visitors": 1,
            "nb_visits": 1,
            "sum_time_spent": 0,
        },
    ]
    analytics_2024_01_31 = [
        {
            "label": f"/files/PNB 7 76.txt?download=1",
            "nb_hits": 4,
            "nb_uniq_visitors": 3,
            "nb_visits": 2,
            "sum_time_spent": 0,
        },
    ]
    # only fill 2 days
    fetcher.set_response("2023-12-01", analytics_2023_12_01)
    fetcher.set_response("2024-01-31", analytics_2024_01_31)
    period = ("2023-12", "2024-01")

    monthly_analytics = []
    async for e in fetch_monthly_analytics(fetcher, period):
        monthly_analytics.append(e)

    assert 2 == len(monthly_analytics)

    month, analytics = monthly_analytics[0]
    assert "2023-12" == month
    assert analytics_2023_12_01 == analytics["2023-12-01"]
    # non filled should just be []
    # just take 1 random entry
    assert [] == analytics["2023-12-28"]

    month, analytics = monthly_analytics[1]
    assert "2024-01" == month
    assert analytics_2024_01_31 == analytics["2024-01-31"]
    # non filled should just be []
    # just take 1 random entry
    assert [] == analytics["2024-01-02"]
