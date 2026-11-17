"""Saving and loading the trusted list and the history as files the person downloads and uploads.

The server never keeps these. Anything uploaded is checked strictly before it is used.
"""
from __future__ import annotations

import csv
import io
import json
from typing import Any, Dict, List, Optional, Sequence, Tuple

import messages
from judge import normalize_trusted_value

MAX_IMPORT_BYTES = 200_000
MAX_TRUSTED = 1000
MAX_LABEL = 100


def export_trusted_json(entries: Sequence[Dict[str, str]]) -> bytes:
    payload = {
        "app": "mailguard",
        "version": 1,
        "trusted": [{"value": e["value"], "label": e.get("label", "")} for e in entries],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def import_trusted_json(raw: bytes) -> Tuple[List[Dict[str, str]], int, Optional[str]]:
    """Read an uploaded trusted-list file.

    Returns (entries, skipped_count, error_code). error_code is None on success, otherwise
    "too_large", "invalid_json" or "invalid_format". Each entry is {"value", "kind", "label"}.
    """
    if len(raw) > MAX_IMPORT_BYTES:
        return [], 0, "too_large"
    try:
        data = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, ValueError):
        return [], 0, "invalid_json"

    items = data.get("trusted") if isinstance(data, dict) else data
    if not isinstance(items, list):
        return [], 0, "invalid_format"

    entries: List[Dict[str, str]] = []
    seen = set()
    skipped = 0
    for item in items:
        if isinstance(item, str):
            value, label = item, ""
        elif isinstance(item, dict) and isinstance(item.get("value"), str):
            label = item.get("label", "")
            value = item["value"]
            if not isinstance(label, str):
                label = ""
        else:
            skipped += 1
            continue

        normalized = normalize_trusted_value(value)
        if normalized is None or normalized[0] in seen or len(entries) >= MAX_TRUSTED:
            skipped += 1
            continue
        seen.add(normalized[0])
        entries.append({"value": normalized[0], "kind": normalized[1], "label": label.strip()[:MAX_LABEL]})
    return entries, skipped, None


def csv_safe(value: Any) -> str:
    """Stop spreadsheet programs from running a cell as a formula."""
    text = str(value)
    return "'" + text if text[:1] in ("=", "+", "-", "@", "\t", "\r") else text


def history_to_csv(history: Sequence[Dict[str, Any]], lang: str) -> bytes:
    """The history as CSV (UTF-8 with a BOM, so Excel shows Japanese correctly)."""
    header = {
        "ja": ["日時", "アドレス", "ドメイン", "レベル", "判定", "理由"],
        "en": ["Time", "Address", "Domain", "Level", "Rating", "Reasons"],
    }[lang if lang in messages.LANGS else messages.DEFAULT_LANG]

    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(header)
    for rec in history:
        reasons = " / ".join(messages.render(f["code"], f["params"], lang)[0] for f in rec["findings"])
        writer.writerow([
            csv_safe(rec["time"]),
            csv_safe(rec["address"]),
            csv_safe(rec["domain"]),
            rec["level"],
            csv_safe(messages.level_label(rec["level"], lang)),
            csv_safe(reasons),
        ])
    return ("﻿" + out.getvalue()).encode("utf-8")
