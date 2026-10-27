"""End-to-end tests for the differential validation, stdlib unittest only.

Run from the package root::

    python -m unittest discover -s tests -v
"""

from __future__ import annotations

import os
import threading
import unittest
from http.server import ThreadingHTTPServer

from sysml_validation.api_client import InMemoryClient, RestClient
from sysml_validation.compare import compare
from sysml_validation.counts import count_by_subsystem
from sysml_validation.generator_adapter import from_json
from sysml_validation.mock_server import _load_elements, make_handler
from sysml_validation import report as report_mod

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL = os.path.join(HERE, "examples", "sample_model.json")
GENREPORT = os.path.join(HERE, "examples", "generator_report.json")


class CountTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = InMemoryClient.from_json_file(MODEL)
        self.elements = self.client.list_elements("p", "c")

    def test_subsystems_discovered(self) -> None:
        counts = count_by_subsystem(self.elements)
        self.assertEqual(set(counts.subsystems), {"EPS", "ThermalControl"})

    def test_eps_counts(self) -> None:
        counts = count_by_subsystem(self.elements).as_counts()
        # 2 parts, 2 ports (one nested under batteryPack), 2 connections
        self.assertEqual(counts["EPS"], {"parts": 2, "ports": 2, "connections": 2})

    def test_thermal_counts(self) -> None:
        counts = count_by_subsystem(self.elements).as_counts()
        self.assertEqual(
            counts["ThermalControl"], {"parts": 2, "ports": 1, "connections": 1}
        )

    def test_nested_port_captured(self) -> None:
        counts = count_by_subsystem(self.elements)
        names = {e.name for e in counts.subsystems["EPS"].categories["ports"].elements}
        self.assertIn("telemetry", names)  # the nested one

    def test_restrict_subsystems(self) -> None:
        counts = count_by_subsystem(self.elements, subsystem_names=["EPS"])
        self.assertEqual(set(counts.subsystems), {"EPS"})

    def test_requested_missing_subsystem_reported_empty(self) -> None:
        counts = count_by_subsystem(self.elements, subsystem_names=["Nope"])
        self.assertEqual(counts.as_counts()["Nope"], {"parts": 0, "ports": 0, "connections": 0})


class CompareTests(unittest.TestCase):
    def setUp(self) -> None:
        elements = InMemoryClient.from_json_file(MODEL).list_elements("p", "c")
        self.reference = count_by_subsystem(elements)
        self.generator = from_json(GENREPORT)

    def test_detects_missing_nested_port(self) -> None:
        result = compare(self.reference, self.generator)
        self.assertFalse(result.ok)
        row = next(
            r for r in result.rows if r.subsystem == "EPS" and r.category == "ports"
        )
        self.assertEqual(row.reference, 2)
        self.assertEqual(row.generator, 1)
        self.assertEqual(row.status, "MISSING")
        self.assertTrue(any("telemetry" in m for m in row.missing))

    def test_all_other_cells_ok(self) -> None:
        result = compare(self.reference, self.generator)
        oks = [r for r in result.rows if r.ok]
        # 6 cells total, only EPS/ports mismatches
        self.assertEqual(len(result.rows), 6)
        self.assertEqual(len(oks), 5)

    def test_perfect_match_passes(self) -> None:
        # Compare the reference against itself-as-generator: everything agrees.
        perfect = from_json(GENREPORT)
        eps_ports = perfect.subsystem("EPS").category("ports")
        from sysml_validation.model import Element

        eps_ports.elements.append(Element(name="telemetry"))
        result = compare(self.reference, perfect)
        self.assertTrue(result.ok, report_mod.to_text(result))

    def test_counts_only_marks_cell(self) -> None:
        from sysml_validation.model import GeneratorReport

        gen = GeneratorReport.from_counts(
            {"EPS": {"parts": 2, "ports": 1, "connections": 2}}
        )
        result = compare(self.reference, gen)
        row = next(
            r for r in result.rows if r.subsystem == "EPS" and r.category == "ports"
        )
        self.assertTrue(row.counts_only)
        self.assertEqual(row.missing, [])  # element-level diff unavailable


class RestClientIntegrationTests(unittest.TestCase):
    """Exercise the real RestClient against the in-process mock HTTP server."""

    @classmethod
    def setUpClass(cls) -> None:
        elements = _load_elements(MODEL)
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(elements))
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()

    def test_roundtrip_through_http(self) -> None:
        client = RestClient(f"http://127.0.0.1:{self.port}", page_size=3)
        project = client.list_projects()[0]["@id"]
        commit = client.list_commits(project)[0]["@id"]
        elements = client.list_elements(project, commit)
        # pagination (size 3 over 13 elements) must reassemble fully
        self.assertEqual(len(elements), 13)
        counts = count_by_subsystem(elements).as_counts()
        self.assertEqual(counts["EPS"], {"parts": 2, "ports": 2, "connections": 2})


if __name__ == "__main__":
    unittest.main()
