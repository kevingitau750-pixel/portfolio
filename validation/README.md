# SysML v2 Wirelist Generator — differential validation

Validate the wirelist (signal list) generator's parser by comparing its output
against the authoritative **SysML v2 reference implementation**. Same `.sysml`
input, two parsers, compared per subsystem. Where they disagree the reference is
authoritative, and the diff names the exact element — hence the construct — the
generator missed.

See `docs/wirelist-generator-validation.md` (in the portfolio repo) for the
methodology narrative; this is the runnable implementation of it.

## How it fits together

```
 .sysml model ─┬─► SysML v2 reference impl ──► API Services ──► api_client ─┐
               │       (make spin-up, Jupyter publish)                      ├─► compare ─► report
               └─► wirelist generator ──► spreadsheet ──► generator_adapter ┘
```

- `api_client.py` — query the SysML v2 API Services. `RestClient` talks to a live
  server (what `make spin-up` starts); `InMemoryClient` serves a JSON model so the
  pipeline runs with no Docker.
- `counts.py` — reconstruct containment from each element's `owner`, find the
  subsystems, and count parts / ports / connections in each subsystem subtree.
- `generator_adapter.py` — read the generator's output: `from_json` (neutral
  schema) or `from_spreadsheet` (the real `.xlsx`, with a column mapping).
- `compare.py` — join the two sides on element name and report per-cell deltas
  plus the specific missing / extra elements.
- `report.py` — render a table, a per-mismatch detail list, or JSON.
- `mock_server.py` — a stdlib HTTP mock of the API, to exercise `RestClient`
  locally.

## Run it

Locally, no Docker (in-memory mock model):

```sh
python -m sysml_validation \
    --mock-model examples/sample_model.json \
    --generator-json examples/generator_report.json
```

Against the real reference implementation:

```sh
# 1. On a Docker-capable machine, start the reference implementation:
make spin-up
# 2. Publish the .sysml model to it from the Jupyter notebook.
# 3. Point the validator at the API server and the generator's spreadsheet:
python -m sysml_validation \
    --api-url http://localhost:9000 \
    --generator-xlsx wirelist.xlsx \
    --xlsx-subsystem-col Subsystem --xlsx-category-col Type --xlsx-name-col Name
```

Exit status is non-zero on any mismatch, so it works as a CI gate. Add `--json`
for machine-readable output, `--subsystems EPS "Thermal Control"` to restrict,
`--project`/`--commit` to pin a specific model revision.

## What to wire up for the real generator

1. **Category metatypes.** `counts.CATEGORIES` lists the SysML v2 `@type` values
   counted as parts / ports / connections. Adjust to match exactly what the
   generator enumerates (e.g. whether it counts `InterfaceUsage` as a connection).
2. **Spreadsheet layout.** `from_spreadsheet` takes the column names; set them to
   the generator's actual sheet, or add a thin wrapper that knows its layout.
3. **Subsystem identity.** By default subsystems are the top-level parts. If the
   generator keys subsystems differently, pass `--subsystems` or extend
   `counts._discover_subsystems`.

## Tests

```sh
python -m unittest discover -s tests -v
```

Covers count extraction (including nested ports), the diff (missing / extra /
count-only), and a round-trip through the mock HTTP server with pagination. No
third-party dependencies; `openpyxl` is only needed for `from_spreadsheet`.
