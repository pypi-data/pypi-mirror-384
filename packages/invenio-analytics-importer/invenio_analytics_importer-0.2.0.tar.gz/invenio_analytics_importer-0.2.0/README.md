# README

CLI tool to retrieve and ingest analytics from a provider into current InvenioRDM instance.

For now, only Matomo is supported. If other provider added, slight refactor to support them will be planned.

## Install

```bash
pip install invenio-analytics-importer
```

## Usage

**Retrieve analytics**

```bash
pipenv run invenio analytics_importer retrieve [--views|--downloads] --from <YYYY-MM> --to <YYYY-MM> --output-dir <path>/<to>/<data>/
```

If neither `--views` nor `--downloads` is passed, views will be the default. If both are passed, the last one on the CLI will be chosen.
`--from` and `--to` are inclusive year-month dates.

This downloads analytics into files corresponding to each year-month. The structure of each file is e.g.,:

```json
{
    "2024-08-01": [
        {
            // 1 "raw" analytics entry from provider
            // corresponding to 1 URL
        },
        // ...
    ],
    "2024-08-02": [
    // ...
    ],
    // ...
}
```

**Ingest**

```bash
pipenv run invenio analytics_importer ingest [--views|--downloads] -f <analytics file 1> -f <analytics file 2> ...
```

Analytics files are of the shape described above, although there is no
requirements for 1 file to correspond to 1 month. However, there is an
assumption/requirement that each file's date (`YYYY-MM-DD`) in
`"YYYY-MM-DD": [...analytics...]` is unique across all files.
