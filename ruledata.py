"""Loading of the rule data (blacklist and so on).

Reads the text files in the data/ folder. Blank lines and lines starting with # are ignored.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Union

DATA_DIR = Path(__file__).parent / "data"


def _read_lines(path: Path) -> List[str]:
    lines: List[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        lines.append(s.lower())
    return lines


@dataclass
class RuleData:
    blacklist: Set[str]                  # domains/addresses reported for scams or spam
    brand_domains: Dict[str, List[str]]  # keyword a sender may claim -> official domains
    disposable: Set[str]                 # disposable-email domains
    keywords: List[str]                  # suspicious words in the subject

    def official_domains(self) -> Set[str]:
        return {d for domains in self.brand_domains.values() for d in domains}

    @classmethod
    def load(cls, data_dir: Optional[Union[str, Path]] = None) -> "RuleData":
        base = Path(data_dir) if data_dir else DATA_DIR

        brands: Dict[str, List[str]] = {}
        for line in _read_lines(base / "official_domains.txt"):
            parts = line.split(",", 1)
            if len(parts) != 2:
                continue
            keyword, domain = parts[0].strip(), parts[1].strip()
            if keyword and domain:
                brands.setdefault(keyword, []).append(domain)

        return cls(
            blacklist=set(_read_lines(base / "blacklist.txt")),
            brand_domains=brands,
            disposable=set(_read_lines(base / "disposable_domains.txt")),
            keywords=_read_lines(base / "suspicious_keywords.txt"),
        )
