"""Differential validation of the SysML v2 Wirelist Generator.

Same input, two parsers, compare the outputs. We feed one ``.sysml`` model into
both the wirelist generator and the authoritative SysML v2 reference
implementation, then compare per-subsystem counts of parts, ports and
connections. Where they disagree the reference is authoritative, and the gap
names the construct the generator's parser does not yet handle.

The reference side is reached through the SysML v2 API Services REST API (what
``make spin-up`` starts). This package talks to that API through the
:class:`~sysml_validation.api_client.SysMLv2Client` protocol, so the exact same
code runs against a real server or an in-memory mock.
"""

from __future__ import annotations

from .api_client import InMemoryClient, RestClient, SysMLv2Client
from .counts import CATEGORIES, SubsystemCounts, count_by_subsystem
from .compare import ComparisonRow, compare
from .model import GeneratorReport

__all__ = [
    "SysMLv2Client",
    "RestClient",
    "InMemoryClient",
    "CATEGORIES",
    "SubsystemCounts",
    "count_by_subsystem",
    "GeneratorReport",
    "ComparisonRow",
    "compare",
]
