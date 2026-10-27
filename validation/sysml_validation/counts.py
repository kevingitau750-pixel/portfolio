"""Extract per-subsystem counts from a parsed SysML v2 model.

Given the flat element list the API returns, this reconstructs containment from
each element's ``owner`` reference, identifies subsystems (top-level parts, or a
caller-supplied list of names), and counts the parts / ports / connections inside
each subsystem subtree — recording the actual elements so a mismatch can name
exactly what is missing.

The SysML v2 metatypes that count toward each category are configurable; the
defaults below match what a wirelist generator cares about. Override them to mirror
whatever the generator actually enumerates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from .model import CategoryResult, Element, SubsystemResult

Raw = Dict[str, Any]

#: category -> set of SysML v2 ``@type`` values counted toward it.
CATEGORIES: Dict[str, set[str]] = {
    "parts": {"PartUsage"},
    "ports": {"PortUsage"},
    "connections": {
        "ConnectionUsage",
        "InterfaceUsage",
        "FlowConnectionUsage",
        "FlowUsage",
        "BindingConnectorAsUsage",
    },
}

#: metatypes treated as a "part-like" container when auto-discovering subsystems.
PART_TYPES: set[str] = {"PartUsage", "PartDefinition"}


def _owner_id(elem: Raw) -> str | None:
    """Read the owning element's id from the several shapes the API uses."""
    owner = elem.get("owner")
    if owner is None:
        return None
    if isinstance(owner, str):
        return owner
    if isinstance(owner, Mapping):
        return owner.get("@id") or owner.get("id")
    return None


def _elem_id(elem: Raw) -> str:
    return elem.get("@id") or elem.get("id") or ""


def _elem_type(elem: Raw) -> str:
    # The API uses "@type"; tolerate a plain "type" too.
    return elem.get("@type") or elem.get("type") or ""


@dataclass
class _Index:
    by_id: Dict[str, Raw]
    children: Dict[str, List[str]] = field(default_factory=dict)

    @classmethod
    def build(cls, elements: Iterable[Raw]) -> "_Index":
        by_id: Dict[str, Raw] = {}
        children: Dict[str, List[str]] = {}
        for el in elements:
            eid = _elem_id(el)
            if not eid:
                continue
            by_id[eid] = el
        for eid, el in by_id.items():
            owner = _owner_id(el)
            if owner is not None and owner in by_id:
                children.setdefault(owner, []).append(eid)
        return cls(by_id=by_id, children=children)

    def descendants(self, root_id: str) -> List[str]:
        """Every element transitively owned by ``root_id`` (root excluded)."""
        out: List[str] = []
        stack = list(self.children.get(root_id, []))
        seen: set[str] = set()
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            out.append(cur)
            stack.extend(self.children.get(cur, []))
        return out


def _discover_subsystems(index: _Index, part_types: set[str]) -> List[str]:
    """Top-level parts: part-typed elements not owned by another part.

    This matches the usual model shape where each subsystem is a part usage sitting
    directly under a package / the model root.
    """
    roots: List[str] = []
    for eid, el in index.by_id.items():
        if _elem_type(el) not in part_types:
            continue
        owner = _owner_id(el)
        owner_type = _elem_type(index.by_id[owner]) if owner in index.by_id else ""
        if owner_type not in part_types:
            roots.append(eid)
    return roots


@dataclass
class SubsystemCounts:
    """Reference-side result: per-subsystem, per-category elements."""

    subsystems: Dict[str, SubsystemResult] = field(default_factory=dict)

    def as_counts(self) -> Dict[str, Dict[str, int]]:
        return {
            name: {cat: res.count for cat, res in sub.categories.items()}
            for name, sub in self.subsystems.items()
        }


def count_by_subsystem(
    elements: Sequence[Raw],
    *,
    categories: Mapping[str, set[str]] | None = None,
    subsystem_names: Sequence[str] | None = None,
    part_types: set[str] | None = None,
) -> SubsystemCounts:
    """Count parts/ports/connections per subsystem in a parsed model.

    Parameters
    ----------
    elements:
        The flat element list from ``client.list_elements(...)``.
    categories:
        ``{category: {metatype, ...}}``; defaults to :data:`CATEGORIES`.
    subsystem_names:
        Restrict to subsystems with these names. When omitted, subsystems are
        auto-discovered as top-level parts.
    part_types:
        Metatypes treated as part-like for subsystem discovery; defaults to
        :data:`PART_TYPES`.
    """
    cats = dict(categories or CATEGORIES)
    ptypes = set(part_types or PART_TYPES)
    index = _Index.build(elements)

    # type -> category lookup
    type_to_cat: Dict[str, str] = {}
    for cat, types in cats.items():
        for t in types:
            type_to_cat[t] = cat

    roots = _discover_subsystems(index, ptypes)
    wanted = set(subsystem_names) if subsystem_names is not None else None

    result = SubsystemCounts()
    for root_id in roots:
        root = index.by_id[root_id]
        name = root.get("name") or root_id
        if wanted is not None and name not in wanted:
            continue
        sub = SubsystemResult(name=name)
        for cat in cats:
            sub.category(cat)  # ensure every category present, even if empty
        for desc_id in index.descendants(root_id):
            el = index.by_id[desc_id]
            etype = _elem_type(el)
            cat = type_to_cat.get(etype)
            if cat is None:
                continue
            sub.category(cat).elements.append(
                Element(
                    name=el.get("name") or desc_id,
                    etype=etype,
                    eid=desc_id,
                )
            )
        result.subsystems[name] = sub

    # Report any requested subsystem the model did not contain.
    if wanted is not None:
        for missing in wanted - set(result.subsystems):
            empty = SubsystemResult(name=missing)
            for cat in cats:
                empty.category(cat)
            result.subsystems[missing] = empty
    return result
