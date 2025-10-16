# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 Northwestern University.
#
# invenio-analytics-importer is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

from invenio_analytics_importer.read import read_raw_analytics_from_filepaths
from invenio_analytics_importer.write import write_json


def test_read_raw_analytics_from_filepaths(tmp_path):
    download_dict_2024_08_31_2 = {
        "label": f"prism.northwestern.edu/records/3s45v-k5m55/files/PNB 7 76.txt?download=1",  # noqa
        "nb_hits": 1,
        "nb_uniq_visitors": 1,
        "nb_visits": 1,
        "sum_time_spent": 0,
    }

    fp1 = write_json(
        tmp_path / "downloads_2024-08.json",
        {
            "2024-08-31": [
                {
                    "label": f"prism.northwestern.edu/records/3s45v-k5m55/files/PNB-7-75.txt?download=1",  # noqa
                    "nb_hits": 1,
                    "nb_uniq_visitors": 1,
                    "nb_visits": 1,
                    "sum_time_spent": 0,
                },
                download_dict_2024_08_31_2,
            ]
        }
    )
    view_dict_2024_08_30 = {
        "avg_page_load_time": 1.904,
        "avg_time_dom_completion": 0.629,
        "avg_time_dom_processing": 0.412,
        "avg_time_network": 0.473,
        "avg_time_on_page": 454,
        "avg_time_server": 0.294,
        "avg_time_transfer": 0.096,
        "bounce_rate": "100%",
        "entry_bounce_count": "1",
        "entry_nb_actions": "1",
        "entry_nb_uniq_visitors": 1,
        "entry_nb_visits": "1",
        "entry_sum_visit_length": "0",
        "exit_nb_uniq_visitors": 1,
        "exit_nb_visits": "2",
        "exit_rate": "67%",
        "label": "/records/3s45v-k5m55",
        "max_time_dom_completion": "0.6440",
        "max_time_dom_processing": "0.7940",
        "max_time_network": "1.3810",
        "max_time_server": "0.4350",
        "max_time_transfer": "0.1760",
        "min_time_dom_completion": "0.6130",
        "min_time_dom_processing": "0.2180",
        "min_time_network": "0.0000",
        "min_time_server": "0.0020",
        "min_time_transfer": "0.0020",
        "nb_hits": 4,
        "nb_hits_following_search": "3",
        "nb_hits_with_time_dom_completion": "2",
        "nb_hits_with_time_dom_processing": "4",
        "nb_hits_with_time_network": "4",
        "nb_hits_with_time_server": "4",
        "nb_hits_with_time_transfer": "4",
        "nb_uniq_visitors": 1,
        "nb_visits": 3,
        "sum_time_spent": 1817,
    }
    fp2 = write_json(
        tmp_path / "views_2024-08.json", {"2024-08-30": [view_dict_2024_08_30]}
    )
    filepaths = [fp1, fp2]

    raw_analytics = list(read_raw_analytics_from_filepaths(filepaths))

    assert 3 == len(raw_analytics)
    # just check the 2nd and 3rd
    assert "2024-08-31" == raw_analytics[1][0]
    assert download_dict_2024_08_31_2 == raw_analytics[1][1]
    assert "2024-08-30" == raw_analytics[2][0]
    assert view_dict_2024_08_30 == raw_analytics[2][1]
