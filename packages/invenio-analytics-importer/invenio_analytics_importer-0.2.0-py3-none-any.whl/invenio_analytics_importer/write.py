# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 Northwestern University.
#
# invenio-analytics-importer is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Write."""

import json


def write_json(
    filepath, content, sort_keys=True, indent=2, separators=(",", ": "), **kwargs  # noqa
):
    """Write json filepath."""
    with open(filepath, "w") as f:
        json.dump(
            content,
            f,
            sort_keys=sort_keys,
            indent=indent,
            separators=separators,
            **kwargs
        )
    return filepath
