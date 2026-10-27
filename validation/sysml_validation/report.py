"""Render a :class:`~sysml_validation.compare.ComparisonReport` for humans."""

from __future__ import annotations

import json
from typing import Any, Dict, List

from .compare import ComparisonReport


def to_table(report: ComparisonReport) -> str:
    """A fixed-width table: one row per subsystem/category cell."""
    header = ("Subsystem", "Category", "Ref", "Gen", "Δ", "Status")
    rows = [
        (
            r.subsystem,
            r.category,
            str(r.reference),
            str(r.generator),
            f"{r.delta:+d}" if r.delta else "0",
            r.status,
        )
        for r in report.rows
    ]
    widths = [
        max(len(header[i]), *(len(row[i]) for row in rows)) if rows else len(header[i])
        for i in range(len(header))
    ]

    def fmt(cols: tuple[str, ...]) -> str:
        return "  ".join(c.ljust(widths[i]) for i, c in enumerate(cols))

    lines = [fmt(header), fmt(tuple("-" * w for w in widths))]
    lines += [fmt(row) for row in rows]
    return "\n".join(lines)


def to_detail(report: ComparisonReport) -> str:
    """For each mismatch, list the specific missing / extra elements."""
    out: List[str] = []
    for r in report.mismatches:
        out.append(f"\n{r.subsystem} / {r.category}: reference={r.reference} generator={r.generator} ({r.status})")
        if r.counts_only:
            out.append("  (generator reported counts only — element-level diff unavailable)")
            continue
        for name in r.missing:
            out.append(f"  - MISSING (in reference, not generator): {name}")
        for name in r.extra:
            out.append(f"  + EXTRA   (in generator, not reference): {name}")
    return "\n".join(out) if out else "\nNo mismatches — every cell agrees."


def to_text(report: ComparisonReport) -> str:
    totals = report.totals()
    verdict = "PASS" if report.ok else "FAIL"
    summary = (
        f"\n{verdict}: {totals['ok']}/{totals['cells']} cells agree; "
        f"{totals['mismatched']} mismatched, "
        f"{totals['missing_elements']} missing + {totals['extra_elements']} extra elements."
    )
    return to_table(report) + "\n" + to_detail(report) + "\n" + summary


def to_dict(report: ComparisonReport) -> Dict[str, Any]:
    return {
        "ok": report.ok,
        "totals": report.totals(),
        "rows": [
            {
                "subsystem": r.subsystem,
                "category": r.category,
                "reference": r.reference,
                "generator": r.generator,
                "delta": r.delta,
                "status": r.status,
                "missing": r.missing,
                "extra": r.extra,
                "counts_only": r.counts_only,
            }
            for r in report.rows
        ],
    }


def to_json(report: ComparisonReport, *, indent: int = 2) -> str:
    return json.dumps(to_dict(report), indent=indent)
