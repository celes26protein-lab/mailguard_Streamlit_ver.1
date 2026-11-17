import json
import unittest

import storage


class TrustedFileTest(unittest.TestCase):
    def test_round_trip(self):
        entries = [{"value": "family@example.com", "kind": "address", "label": "family"},
                   {"value": "example.org", "kind": "domain", "label": ""}]
        raw = storage.export_trusted_json(entries)
        loaded, skipped, error = storage.import_trusted_json(raw)
        self.assertIsNone(error)
        self.assertEqual(skipped, 0)
        self.assertEqual([e["value"] for e in loaded], ["family@example.com", "example.org"])
        self.assertEqual(loaded[0]["kind"], "address")
        self.assertEqual(loaded[0]["label"], "family")

    def test_accepts_plain_list_of_strings(self):
        loaded, skipped, error = storage.import_trusted_json(b'["A@Example.com", "example.org"]')
        self.assertEqual((error, skipped), (None, 0))
        self.assertEqual([e["value"] for e in loaded], ["a@example.com", "example.org"])

    def test_bad_entries_are_skipped_not_trusted(self):
        raw = json.dumps({"trusted": [
            {"value": "ok@example.com"}, {"value": "not valid"}, 42, {"nope": 1},
            {"value": "ok@example.com"}, "<script>@example.com",
        ]}).encode()
        loaded, skipped, error = storage.import_trusted_json(raw)
        self.assertIsNone(error)
        self.assertEqual([e["value"] for e in loaded], ["ok@example.com"])
        self.assertEqual(skipped, 5)

    def test_label_is_trimmed_and_must_be_text(self):
        raw = json.dumps([{"value": "a@example.com", "label": "x" * 500},
                          {"value": "b@example.com", "label": {"evil": 1}}]).encode()
        loaded, _, _ = storage.import_trusted_json(raw)
        self.assertEqual(len(loaded[0]["label"]), storage.MAX_LABEL)
        self.assertEqual(loaded[1]["label"], "")

    def test_errors(self):
        self.assertEqual(storage.import_trusted_json(b"not json")[2], "invalid_json")
        self.assertEqual(storage.import_trusted_json(b'{"trusted": 5}')[2], "invalid_format")
        self.assertEqual(storage.import_trusted_json(b'"text"')[2], "invalid_format")
        self.assertEqual(storage.import_trusted_json(b" " * (storage.MAX_IMPORT_BYTES + 1))[2], "too_large")
        self.assertEqual(storage.import_trusted_json(b"\xff\xfe")[2], "invalid_json")

    def test_entry_count_is_capped(self):
        many = [f"user{i}@example.com" for i in range(storage.MAX_TRUSTED + 25)]
        loaded, skipped, error = storage.import_trusted_json(json.dumps(many).encode())
        self.assertIsNone(error)
        self.assertEqual(len(loaded), storage.MAX_TRUSTED)
        self.assertEqual(skipped, 25)


class HistoryCsvTest(unittest.TestCase):
    RECORD = {
        "time": "2026-11-17 10:00:00", "address": "+evil@example.com", "domain": "example.com", "level": 3,
        "findings": [{"code": "disposable", "params": {"domain": "example.com"}}],
    }

    def test_csv_has_bom_header_and_localized_rows(self):
        ja = storage.history_to_csv([self.RECORD], "ja").decode("utf-8")
        en = storage.history_to_csv([self.RECORD], "en").decode("utf-8")
        self.assertTrue(ja.startswith("﻿日時"))
        self.assertIn("危険", ja)
        self.assertTrue(en.startswith("﻿Time"))
        self.assertIn("Danger", en)

    def test_csv_cells_cannot_become_formulas(self):
        text = storage.history_to_csv([self.RECORD], "en").decode("utf-8")
        self.assertIn("'+evil@example.com", text)
        for risky in ["=1+1", "+1", "-1", "@x", "\tx"]:
            self.assertTrue(storage.csv_safe(risky).startswith("'"), risky)
        self.assertEqual(storage.csv_safe("hello"), "hello")


if __name__ == "__main__":
    unittest.main()
