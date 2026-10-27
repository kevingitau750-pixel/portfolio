"""Diff engine: line up the reference counts against the generator's.

For every (subsystem, category) cell we compare the authoritative reference count
to what the generator reported. When both sides carry element names we also take
the set difference, so a mismatch names the specific elements the generator
missed (present in the reference, absent from the generator) — which is what
reveals the unhandled SysML v2 construct — and any spurious extras.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List

from .counts import SubsystemCounts
from .model import GeneratorReport


@dataclass
class ComparisonRow:
    subsystem: str
    category: str
    reference: int
    generator: int
    #: reference element names absent from the generator (the parser gaps)
    missing: List[str] = field(default_factory=list)
    #: generator element names absent from the reference (spurious output)
    extra: List[str] = field(default_factory=list)
    #: True when element-level diff was not possible (count-only on a side)
    counts_only: bool = False

    @property
    def delta(self) -> int:
        return self.generator - self.reference

    @property
    def ok(self) -> bool:
        return self.delta == 0

    @property
    def status(self) -> str:
        return "OK" if self.ok else ("MISSING" if self.delta < 0 else "EXTRA")


@dataclass
class ComparisonReport:
    rows: List[ComparisonRow] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(r.ok for r in self.rows)

    @property
    def mismatches(self) -> List[ComparisonRow]:
        return [r for r in self.rows if not r.ok]

    def totals(self) -> Dict[str, int]:
        return {
            "cells": len(self.rows),
            "ok": sum(1 for r in self.rows if r.ok),
            "mismatched": len(self.mismatches),
            "missing_elements": sum(len(r.missing) for r in self.rows),
            "extra_elements": sum(len(r.extra) for r in self.rows),
        }


def compare(
    reference: SubsystemCounts, generator: GeneratorReport
) -> ComparisonReport:
    """Compare reference counts against a generator report, cell by cell.

    The union of subsystems and categories seen on either side is compared, so a
    subsystem the generator dropped entirely (or invented) still shows up.
    """
    report = ComparisonReport()

    subsystems = sorted(
        set(reference.subsystems) | set(generator.subsystems)
    )
    for sub_name in subsystems:
        ref_sub = reference.subsystems.get(sub_name)
        gen_sub = generator.subsystems.get(sub_name)
        categories = sorted(
            set(ref_sub.categories if ref_sub else {})
            | set(gen_sub.categories if gen_sub else {})
        )
        for cat in categories:
            ref_cat = ref_sub.categories.get(cat) if ref_sub else None
            gen_cat = gen_sub.categories.get(cat) if gen_sub else None

            ref_count = ref_cat.count if ref_cat else 0
            gen_count = gen_cat.count if gen_cat else 0

            counts_only = (sub_name, cat) in generator.counts_only
            missing: List[str] = []
            extra: List[str] = []
            if not counts_only and ref_cat is not None and gen_cat is not None:
                # Join on element name — the common denominator between the API
                # (which also has ids) and the generator (which usually has only
                # names). Use multisets so repeated names stay consistent with the
                # counts: an element missing k times appears k times.
                ref_names = Counter(e.name for e in ref_cat.elements)
                gen_names = Counter(e.name for e in gen_cat.elements)
                etype = {e.name: e.etype for e in ref_cat.elements}

                missing_counts = ref_names - gen_names  # in ref, short in gen
                extra_counts = gen_names - ref_names     # in gen, not in ref
                missing = sorted(
                    f"{name} ({etype[name]})" if etype.get(name) else name
                    for name, n in missing_counts.items()
                    for _ in range(n)
                )
                extra = sorted(
                    name for name, n in extra_counts.items() for _ in range(n)
                )

            report.rows.append(
                ComparisonRow(
                    subsystem=sub_name,
                    category=cat,
                    reference=ref_count,
                    generator=gen_count,
                    missing=missing,
                    extra=extra,
                    counts_only=counts_only,
                )
            )
    return report
