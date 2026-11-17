"""Looks up a domain's registration date through RDAP (a public registration-data service).

Only the domain name is sent out (never the full email address or the message body).
If the lookup fails (network error, a domain type that is not supported, and so on),
None is returned.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from typing import Any, Dict, Optional

RDAP_URL = "https://rdap.org/domain/"
TIMEOUT_SECONDS = 5

# Markers for country domains whose second level describes the kind of holder (co.jp, co.uk ...)
_SECOND_LEVEL = {"co", "or", "ne", "ac", "go", "ed", "ad", "gr", "lg", "com", "net", "org", "gov", "edu"}


def registrable_domain(domain: str) -> str:
    """Pick out the part of a domain that is actually registered (simplified).
    mail.amazon.co.jp -> amazon.co.jp / a.b.example.com -> example.com
    Note: doing this properly needs the Public Suffix List, so unusual domains may be wrong."""
    parts = domain.lower().strip(".").split(".")
    if len(parts) >= 3 and len(parts[-1]) == 2 and parts[-2] in _SECOND_LEVEL:
        return ".".join(parts[-3:])
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return domain


def parse_registration_date(rdap_json: Dict[str, Any]) -> Optional[date]:
    """Take the registration date out of an RDAP response."""
    for event in rdap_json.get("events", []) or []:
        if event.get("eventAction") == "registration":
            text = str(event.get("eventDate", ""))[:10]
            try:
                return date.fromisoformat(text)
            except ValueError:
                return None
    return None


def fetch_registration_date(domain: str) -> Optional[date]:
    """Look up when a domain was registered. Returns None if it cannot be found."""
    url = RDAP_URL + urllib.parse.quote(domain)
    request = urllib.request.Request(url, headers={
        "Accept": "application/rdap+json",
        "User-Agent": "mailguard/0.1 (personal local tool)",
    })
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            body = response.read(1_000_000)
        return parse_registration_date(json.loads(body.decode("utf-8")))
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        return None
