"""本地选择、CSV 结构与工作台导入的一致性回归。"""

import csv
from dataclasses import fields
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pilot.api import preflight_import
from src import config
from src.material import (
    MaterialSupply, load_demands_csv, load_supplies_csv, run_material,
)


SUPPLY_HEADER = "supply_id,supplier_name,material_code,available_mass_t"
DEMAND_HEADER = "demand_id,buyer_name,target_material_code,required_mass_t"


class TestInputSelection(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.supply = Path(self.folder.name) / "supply.csv"
        self.demand = Path(self.folder.name) / "demand.csv"
        for name, value in (("MATERIAL_SUPPLY_CSV", self.supply),
                            ("MATERIAL_DEMAND_CSV", self.demand)):
            p = patch.object(config, name, value)
            p.start()
            self.addCleanup(p.stop)

    def test_unknown_demand_never_selects_first_record(self):
        self.supply.write_text(SUPPLY_HEADER + "\nS1,甲,PP,5\n", encoding="utf-8")
        self.demand.write_text(DEMAND_HEADER + "\nD1,甲,PP,5\nD2,乙,PP,8\n",
                               encoding="utf-8")
        for mode in ("local", "auto"):
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, "D9"):
                run_material(mode, demand_id="D9")

    def test_explicit_selection_is_used(self):
        self.supply.write_text(SUPPLY_HEADER + "\nS1,甲,PP,5\n", encoding="utf-8")
        self.demand.write_text(DEMAND_HEADER + "\nD1,甲,PP,5\nD2,乙,PP,8\n",
                               encoding="utf-8")
        with patch("src.material._build_result", side_effect=lambda d, *a: d):
            self.assertEqual(run_material("local", "D2").demand_id, "D2")

    def test_partial_local_input_never_falls_back_to_demo(self):
        for path in (self.supply, self.demand):
            with self.subTest(path=path.name):
                path.write_text("fixture", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "local"):
                    run_material("auto")
                path.unlink()

    def test_auto_with_explicit_id_requires_local_input(self):
        with self.assertRaises(ValueError):
            run_material("auto", "D9")

    def test_unknown_mode_never_runs_demo(self):
        with self.assertRaises(ValueError):
            run_material("locla")

    def test_demo_rejects_unknown_demand_id(self):
        with self.assertRaisesRegex(ValueError, "D9"):
            run_material("demo", "D9")


class TestCSVStructure(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / "input.csv"

    def test_duplicate_headers_rejected_in_both_loaders(self):
        for header, loader in ((SUPPLY_HEADER, load_supplies_csv),
                               (DEMAND_HEADER, load_demands_csv)):
            self.path.write_text(header + "," + header.split(",")[-1]
                                 + "\nX1,甲,PP,5,8\n", encoding="utf-8")
            with self.subTest(loader=loader.__name__), self.assertRaisesRegex(ValueError, "重复"):
                loader(self.path)

    def test_ragged_rows_rejected_with_line_number(self):
        for row in ("S1,甲,PP,5,unexpected", "S1,甲,PP"):
            self.path.write_text(SUPPLY_HEADER + "\n" + row + "\n", encoding="utf-8")
            with self.subTest(row=row), self.assertRaisesRegex(ValueError, "第 2 行"):
                load_supplies_csv(self.path)

    def test_unclosed_quotes_report_structural_error(self):
        self.path.write_text(SUPPLY_HEADER + '\nS1,"甲,PP,5\n', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "结构错误"):
            load_supplies_csv(self.path)

    def test_permissive_import_rejects_all_structurally_invalid_rows(self):
        self.path.write_text(
            SUPPLY_HEADER + ",available_from,available_to\n"
            "GOOD,甲,PP,5,2026-09-01,2026-09-30\n"
            "NEG,乙,PP,-5,2026-09-01,2026-09-30\n"
            "DATE,丙,PP,5,2026-09-31,2026-10-30\n"
            "GOOD,甲,PP,7,2026-09-01,2026-09-30\n"
            ",丁,PP,5,2026-09-01,2026-09-30\n"
            "SHORT,戊,PP,5\n", encoding="utf-8")
        supplies, stats = load_supplies_csv(self.path, strict=False)
        self.assertEqual([s.supply_id for s in supplies], ["GOOD"])
        self.assertEqual((stats["read"], stats["accepted"], stats["rejected"]), (6, 1, 5))
        self.assertTrue(stats["warnings"])

    def test_permissive_demands_reject_range_errors(self):
        self.path.write_text(DEMAND_HEADER + ",mfi_min,mfi_max\n"
                             "D1,甲,PP,5,8,16\nD2,乙,PP,-5,8,16\n"
                             "D3,丙,PP,5,16,8\n", encoding="utf-8")
        demands, stats = load_demands_csv(self.path, strict=False)
        self.assertEqual([d.demand_id for d in demands], ["D1"])
        self.assertEqual(stats["read"], stats["accepted"] + stats["rejected"])
        self.assertEqual(stats["rejected"], 2)

    def test_bad_headers_reject_entire_permissive_import(self):
        for suffix in (",available_mass_t", ","):
            self.path.write_text(SUPPLY_HEADER + suffix + "\nS1,甲,PP,5,8\n",
                                 encoding="utf-8")
            with self.subTest(suffix=suffix):
                supplies, stats = load_supplies_csv(self.path, strict=False)
                self.assertEqual(supplies, [])
                self.assertEqual((stats["read"], stats["rejected"]), (1, 1))

    def test_malformed_tail_does_not_hide_valid_prefix_in_permissive_mode(self):
        self.path.write_text(SUPPLY_HEADER + '\nGOOD,甲,PP,5\nBAD,"乙,PP,5\n',
                             encoding="utf-8")
        supplies, stats = load_supplies_csv(self.path, strict=False)
        self.assertEqual([s.supply_id for s in supplies], ["GOOD"])
        self.assertEqual((stats["read"], stats["accepted"], stats["rejected"]), (2, 1, 1))
        self.assertTrue(any(i["row"] == 3 and "结构错误" in i["problem"]
                            for i in stats["issues"]))

    def test_line_numbers_follow_multiline_cells_and_blank_lines(self):
        self.path.write_text(SUPPLY_HEADER + '\nGOOD,"甲\n乙",PP,5\n\nBAD,丙,PP,-5\n',
                             encoding="utf-8")
        _, stats = load_supplies_csv(self.path, strict=False)
        self.assertEqual(stats["rejected"], 1)
        self.assertTrue(any(i["row"] == 5 and i["col"] == "available_mass_t"
                            for i in stats["issues"]))

    def test_utf8_bom_and_quoted_thousands_remain_supported(self):
        text = '\ufeff' + SUPPLY_HEADER + '\nS1,"甲,乙",PP,"1,000"\n'
        self.path.write_text(text, encoding="utf-8")
        supplies, stats = load_supplies_csv(self.path)
        self.assertEqual(supplies[0].available_mass_t, 1000)
        self.assertEqual(supplies[0].supplier_name, "甲,乙")
        self.assertEqual(stats["rejected"], 0)
        self.assertEqual(preflight_import({}, text, "supply")["structural"], [])

    def test_workbench_preview_detects_csv_structure(self):
        for text in (SUPPLY_HEADER + ",available_mass_t\nS1,甲,PP,5,8\n",
                     SUPPLY_HEADER + "\nS1,甲,PP,5,extra\n",
                     SUPPLY_HEADER + "\nS1,甲,PP\n",
                     'supply_id,available_mass_t\nS1,5\n',
                     SUPPLY_HEADER + '\nS1,"甲,PP,5\n'):
            with self.subTest(text=text):
                self.assertTrue(preflight_import({}, text, "supply")["structural"])

    def test_supply_template_includes_all_supported_fields(self):
        with (config.BASE_DIR / "templates/material_supply.csv").open(
                encoding="utf-8-sig", newline="") as stream:
            header = csv.DictReader(stream).fieldnames
        self.assertEqual(set(header), {f.name for f in fields(MaterialSupply)})


class TestWorkbenchCSVCommit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from pilot import server
        from tests.test_pilot import Client, DEMAND, PilotTestServer
        server._login_attempts.clear()
        cls.server = PilotTestServer()
        cls.client = Client(cls.server.port)
        status, _ = cls.client.post("/api/auth/init",
                                    {"username": "admin", "password": "test-pass-123"}, csrf=False)
        assert status == 200
        status, data = cls.client.post("/api/auth/login",
                                       {"username": "admin", "password": "test-pass-123"}, csrf=False)
        assert status == 200
        cls.client.csrf = data["csrf"]
        status, _ = cls.client.post("/api/tasks", {"task_id": "CSV", "demand": DEMAND})
        assert status == 201

    @classmethod
    def tearDownClass(cls):
        cls.server.close()

    def test_invalid_batch_never_writes_valid_prefix(self):
        csv_text = SUPPLY_HEADER + "\nPREFIX,甲,PP,5\nBAD,乙,PP,5,extra\n"
        status, preview = self.client.post("/api/tasks/CSV/supplies/import",
                                            {"csv_text": csv_text})
        self.assertEqual(status, 200)
        self.assertFalse(preview["can_commit"])
        status, _ = self.client.post("/api/tasks/CSV/supplies/import",
                                     {"csv_text": csv_text, "commit": True})
        self.assertEqual(status, 400)
        with self.server.db.request():
            for table in ("supplies", "batches"):
                count = self.server.db.execute(
                    f"SELECT COUNT(*) AS n FROM {table} WHERE "
                    + ("supply_id" if table == "supplies" else "batch_id")
                    + "='PREFIX'").fetchone()["n"]
                self.assertEqual(count, 0)

    def test_bom_preview_and_commit_import_same_record(self):
        csv_text = "\ufeff" + SUPPLY_HEADER + '\nBOM,甲,PP,"1,000"\n'
        status, preview = self.client.post("/api/tasks/CSV/supplies/import",
                                            {"csv_text": csv_text})
        self.assertEqual(status, 200)
        self.assertTrue(preview["can_commit"])
        status, result = self.client.post("/api/tasks/CSV/supplies/import",
                                          {"csv_text": csv_text, "commit": True})
        self.assertEqual(status, 200)
        self.assertEqual(result["written"], 1)
        with self.server.db.request():
            batch = self.server.db.execute(
                "SELECT original_mass_t FROM batches WHERE batch_id='BOM'").fetchone()
            self.assertEqual(batch["original_mass_t"], 1000)
