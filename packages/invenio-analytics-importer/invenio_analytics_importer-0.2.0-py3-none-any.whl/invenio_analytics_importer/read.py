# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 Northwestern University.
#
# invenio-analytics-importer is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Read."""

import json


def read_json(filepath):
    """Read json filepath."""
    with open(filepath) as f:
        return json.load(f)


def read_raw_analytics_from_filepaths(filepaths):
    """Iterate (YYYY-MM-DD, analytic) from all filepaths."""
    for fp in filepaths:
        analytics_from_fp = read_json(fp)
        for year_month_day, raw_analytics_list in analytics_from_fp.items():
            for raw_analytics in raw_analytics_list:
                yield (year_month_day, raw_analytics)
