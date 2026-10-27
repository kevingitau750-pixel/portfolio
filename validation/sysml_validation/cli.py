"""Command-line entry point for the differential validation.

Examples
--------
Against the local mock model (runs anywhere, no Docker)::

    python -m sysml_validation \
        --mock-model examples/sample_model.json \
        --generator-json examples/generator_report.json

Against a real reference server started by ``make spin-up``::

    python -m sysml_validation \
        --api-url http://localhost:9000 \
        --generator-xlsx wirelist.xlsx \
        --xlsx-subsystem-col Subsystem --xlsx-category-col Type --xlsx-name-col Name

Exit status is non-zero when any cell disagrees, so this doubles as a CI gate.
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Sequence

from . import report as report_mod
from .api_client import InMemoryClient, RestClient, SysMLv2Client
from .compare import compare
from .counts import count_by_subsystem
from .generator_adapter import from_json, from_spreadsheet


def _pick_commit(client: SysMLv2Client, project_id: str, commit_id: str | None) -> str:
    if commit_id:
        return commit_id
    commits = client.list_commits(project_id)
    if not commits:
        raise SystemExit(f"project {project_id!r} has no commits")
    first = commits[0]
    return first.get("@id") or first.get("id") or ""


def _pick_project(client: SysMLv2Client, project_id: str | None) -> str:
    if project_id:
        return project_id
    projects = client.list_projects()
    if not projects:
        raise SystemExit("server has no projects — was the model published?")
    if len(projects) > 1:
        names = ", ".join(p.get("name") or p.get("@id") or "?" for p in projects)
        raise SystemExit(f"multiple projects ({names}); pass --project")
    first = projects[0]
    return first.get("@id") or first.get("id") or ""


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="sysml_validation", description=__doc__)

    ref = p.add_argument_group("reference (SysML v2 API Services)")
    src = ref.add_mutually_exclusive_group(required=True)
    src.add_argument("--api-url", help="base URL of a running API server")
    src.add_argument("--mock-model", help="path to a mock model JSON (in-memory client)")
    ref.add_argument("--project", help="project id (default: the only/sole project)")
    ref.add_argument("--commit", help="commit id (default: first listed)")
    ref.add_argument(
        "--subsystems", nargs="*", help="restrict to these subsystem names"
    )

    gen = p.add_argument_group("generator output")
    gsrc = gen.add_mutually_exclusive_group(required=True)
    gsrc.add_argument("--generator-json", help="neutral JSON report")
    gsrc.add_argument("--generator-xlsx", help="generator spreadsheet")
    gen.add_argument("--xlsx-sheet", help="sheet name/index (default: active)")
    gen.add_argument("--xlsx-subsystem-col")
    gen.add_argument("--xlsx-category-col")
    gen.add_argument("--xlsx-name-col")

    out = p.add_argument_group("output")
    out.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    return p


def _load_reference(args: argparse.Namespace):
    if args.mock_model:
        client: SysMLv2Client = InMemoryClient.from_json_file(args.mock_model)
    else:
        client = RestClient(args.api_url)
    project = _pick_project(client, args.project)
    commit = _pick_commit(client, project, args.commit)
    elements = client.list_elements(project, commit)
    return count_by_subsystem(elements, subsystem_names=args.subsystems)


def _load_generator(args: argparse.Namespace):
    if args.generator_json:
        return from_json(args.generator_json)
    if not (args.xlsx_subsystem_col and args.xlsx_category_col):
        raise SystemExit(
            "--generator-xlsx needs --xlsx-subsystem-col and --xlsx-category-col"
        )
    sheet: str | int | None = args.xlsx_sheet
    if isinstance(sheet, str) and sheet.isdigit():
        sheet = int(sheet)
    return from_spreadsheet(
        args.generator_xlsx,
        sheet=sheet,
        subsystem_col=args.xlsx_subsystem_col,
        category_col=args.xlsx_category_col,
        name_col=args.xlsx_name_col,
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    reference = _load_reference(args)
    generator = _load_generator(args)
    result = compare(reference, generator)

    if args.json:
        print(report_mod.to_json(result))
    else:
        print(report_mod.to_text(result))
    return 0 if result.ok else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
