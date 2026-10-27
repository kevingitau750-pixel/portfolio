"""Shared data structures for both sides of the comparison.

The reference side (SysML v2 API) and the generator side (its spreadsheet) are
normalised into the same shape — a mapping of subsystem -> category -> the
elements found in it — so the diff engine never has to care where the numbers
came from.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Mapping


@dataclass(frozen=True)
class Element:
    """One named model element found inside a subsystem.

    ``eid`` is the SysML v2 element id when known (the reference side always has
    it; the generator side may not). ``name`` is the qualified or simple name used
    to line elements up across the two parsers. ``etype`` is the SysML v2
    metatype, e.g. ``PartUsage`` or ``PortUsage``.
    """

    name: str
    etype: str = ""
    eid: str = ""


@dataclass
class CategoryResult:
    """The elements found in one subsystem for one category (parts/ports/...)."""

    elements: List[Element] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.elements)


@dataclass
class SubsystemResult:
    """Per-category results for a single subsystem."""

    name: str
    categories: Dict[str, CategoryResult] = field(default_factory=dict)

    def category(self, category: str) -> CategoryResult:
        return self.categories.setdefault(category, CategoryResult())


@dataclass
class GeneratorReport:
    """Normalised view of what the wirelist generator reported.

    Built either from the generator's spreadsheet (see
    :mod:`sysml_validation.generator_adapter`) or, in count-only mode, from bare
    per-subsystem/category counts. When only counts are known, synthetic
    placeholder elements are created so the two sides still line up on count; the
    element-level diff is then unavailable for that cell and the report says so.
    """

    subsystems: Dict[str, SubsystemResult] = field(default_factory=dict)
    #: subsystems/categories for which only a count (no element names) was known
    counts_only: set[tuple[str, str]] = field(default_factory=set)

    @classmethod
    def from_counts(
        cls, counts: Mapping[str, Mapping[str, int]]
    ) -> "GeneratorReport":
        """Build a report from ``{subsystem: {category: count}}`` only."""
        report = cls()
        for sub_name, cats in counts.items():
            sub = SubsystemResult(name=sub_name)
            for category, n in cats.items():
                cat = sub.category(category)
                cat.elements = [
                    Element(name=f"<{category}#{i}>") for i in range(int(n))
                ]
                report.counts_only.add((sub_name, category))
            report.subsystems[sub_name] = sub
        return report

    def subsystem(self, name: str) -> SubsystemResult:
        return self.subsystems.setdefault(name, SubsystemResult(name=name))
