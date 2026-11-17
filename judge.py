"""Rates how risky an email sender looks (rules only, no AI).

Level 4 Critical : on the blacklist / a fake domain that looks like a real one
Level 3 Danger   : disposable-email domain / the claimed name does not match the domain /
                   suspicious words in the subject
Level 2 Caution  : domain registered less than 30 days ago / first-time sender
                   (not in the trusted list)
Level 1 Low risk : in the trusted list, or an official domain (including government
                   domains), and nothing else found
Level 0 Unknown  : nothing matched

The final level is the highest level among the findings.
If two or more level-2 findings add up, the level is raised by one.

This module does no network work and has no text in any language. A Finding carries a
code and parameters; messages.py turns them into Japanese or English text.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from email.utils import parseaddr
from enum import IntEnum
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from ruledata import RuleData

NEW_DOMAIN_DAYS = 30          # a domain younger than this many days counts as "new"
LOOKALIKE_MAX_DISTANCE = 2    # largest edit distance that still counts as a look-alike
LOOKALIKE_MIN_LENGTH = 6      # shortest official domain used for look-alike checks
# Endings that only real government bodies can register
OFFICIAL_SUFFIXES = (".go.jp", ".lg.jp", ".gov", ".gov.uk")

_ADDRESS_RE = re.compile(r"^[a-z0-9._%+\-']+@(?:[a-z0-9\-]+\.)+[a-z0-9\-]{2,}$")
_DOMAIN_RE = re.compile(r"^(?:[a-z0-9\-]+\.)+[a-z0-9\-]{2,}$")


class Level(IntEnum):
    UNKNOWN = 0
    LOW = 1
    CAUTION = 2
    DANGER = 3
    CRITICAL = 4

    def raised(self) -> "Level":
        return Level(min(int(self) + 1, int(Level.CRITICAL)))


@dataclass(frozen=True)
class Finding:
    level: Level
    code: str                                   # which message to show (see messages.py)
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Result:
    level: Level
    findings: List[Finding] = field(default_factory=list)


@dataclass
class TrustedList:
    """The trusted list. Entries are full addresses or domains (subdomains are included)."""

    addresses: Set[str] = field(default_factory=set)
    domains: Set[str] = field(default_factory=set)

    @classmethod
    def from_values(cls, values: Iterable[str]) -> "TrustedList":
        t = cls()
        for v in values:
            v = v.strip().lower()
            if not v:
                continue
            (t.addresses if "@" in v else t.domains).add(v)
        return t

    def matches(self, address: str, domain: str) -> bool:
        if address in self.addresses:
            return True
        return any(belongs_to(domain, d) for d in self.domains)

    def reference_domains(self) -> Set[str]:
        return self.domains | {a.rsplit("@", 1)[1] for a in self.addresses}


# ---------------------------------------------------------------- input cleanup

def parse_address(raw: str) -> Optional[Tuple[str, str]]:
    """Pull (display name, address) out of 'Amazon <info@example.com>' or 'info@example.com'.
    Returns None if it is not a valid address."""
    name, addr = parseaddr(raw.strip())
    addr = addr.strip().lower()
    if len(addr) > 254 or not _ADDRESS_RE.match(addr):
        return None
    return name.strip(), addr


def domain_of(address: str) -> str:
    return address.rsplit("@", 1)[1]


def normalize_trusted_value(raw: str) -> Optional[Tuple[str, str]]:
    """Clean up text entered for the trusted list. Returns (value, 'address' or 'domain'),
    or None if it is not valid."""
    v = raw.strip().lower()
    if v.startswith("@"):
        v = v[1:]
    if len(v) > 254:
        return None
    if "@" in v:
        return (v, "address") if _ADDRESS_RE.match(v) else None
    return (v, "domain") if _DOMAIN_RE.match(v) else None


# ---------------------------------------------------------------- helpers

def belongs_to(domain: str, target: str) -> bool:
    """True if domain is target itself or one of its subdomains."""
    return domain == target or domain.endswith("." + target)


def tail(domain: str, n: int) -> str:
    """The last n labels of a domain. tail('mail.a.b.com', 2) -> 'b.com'"""
    parts = domain.split(".")
    return domain if len(parts) <= n else ".".join(parts[-n:])


def levenshtein(a: str, b: str) -> int:
    """Edit distance: how many insertions, deletions or substitutions turn a into b."""
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i]
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            curr.append(min(curr[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost))
        prev = curr
    return prev[-1]


def is_official(domain: str, data: RuleData) -> bool:
    if any(belongs_to(domain, d) for d in data.official_domains()):
        return True
    return domain.endswith(OFFICIAL_SUFFIXES)


def is_blacklisted(address: str, domain: str, data: RuleData) -> bool:
    return address in data.blacklist or any(belongs_to(domain, d) for d in data.blacklist)


def needs_age_lookup(address: str, data: RuleData, trusted: TrustedList) -> bool:
    """Is it worth looking up the domain's registration date?
    (Not needed for known senders or blacklisted ones.)"""
    domain = domain_of(address)
    if trusted.matches(address, domain) or is_official(domain, data):
        return False
    return not is_blacklisted(address, domain, data)


# ---------------------------------------------------------------- judging

def judge(
    address: str,
    data: RuleData,
    trusted: TrustedList,
    display_name: str = "",
    subject: str = "",
    domain_age_days: Optional[int] = None,
) -> Result:
    """address must already be validated with parse_address."""
    address = address.strip().lower()
    domain = domain_of(address)

    is_trusted = trusted.matches(address, domain)
    official = is_official(domain, data)
    known = is_trusted or official

    findings: List[Finding] = []

    # --- level 4
    if is_blacklisted(address, domain, data):
        findings.append(Finding(Level.CRITICAL, "blacklist", {"domain": domain}))

    if not known:
        lookalike = _find_lookalike(domain, data, trusted)
        if lookalike:
            findings.append(Finding(Level.CRITICAL, "lookalike", {"domain": domain, "ref": lookalike}))

    # --- level 3
    if any(belongs_to(domain, d) for d in data.disposable):
        findings.append(Finding(Level.DANGER, "disposable", {"domain": domain}))

    if not is_trusted:
        findings.extend(_check_brand_claim(domain, display_name, subject, data))
        findings.extend(_check_keywords(subject, data))

    # --- level 2
    if domain_age_days is not None and domain_age_days < NEW_DOMAIN_DAYS:
        findings.append(Finding(Level.CAUTION, "new_domain", {"days": domain_age_days}))

    if not known:
        findings.append(Finding(Level.CAUTION, "first_time"))

    # --- level 1
    if known and not findings:
        findings.append(Finding(Level.LOW, "low_trusted" if is_trusted else "low_official"))

    return _finish(findings)


def _find_lookalike(domain: str, data: RuleData, trusted: TrustedList) -> Optional[str]:
    """If the domain resembles an official or trusted domain, return the one it resembles."""
    references = data.official_domains() | trusted.reference_domains()
    for ref in sorted(references):
        if len(ref) < LOOKALIKE_MIN_LENGTH:
            continue
        labels = len(ref.split("."))
        if 1 <= levenshtein(tail(domain, labels), ref) <= LOOKALIKE_MAX_DISTANCE:
            return ref
    return None


def _check_brand_claim(domain: str, display_name: str, subject: str, data: RuleData) -> List[Finding]:
    text = (display_name + " " + subject).lower()
    for keyword, domains in data.brand_domains.items():
        if keyword in text and not any(belongs_to(domain, d) for d in domains):
            return [Finding(Level.DANGER, "brand_mismatch", {"keyword": keyword, "domain": domain})]
    return []


def _check_keywords(subject: str, data: RuleData) -> List[Finding]:
    s = subject.lower()
    hits = [kw for kw in dict.fromkeys(data.keywords) if kw in s]
    if not hits:
        return []
    return [Finding(Level.DANGER, "keywords", {"words": hits})]


def _finish(findings: List[Finding]) -> Result:
    if not findings:
        return Result(Level.UNKNOWN, [Finding(Level.UNKNOWN, "unknown")])

    level = max(f.level for f in findings)
    caution_count = sum(1 for f in findings if f.level == Level.CAUTION)
    if level == Level.CAUTION and caution_count >= 2:
        level = level.raised()
    return Result(level, findings)
