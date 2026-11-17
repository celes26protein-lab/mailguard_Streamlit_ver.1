"""MailGuard (Streamlit version) - メール番人

Check an email sender's address and get a risk level from 0 to 4.
Nothing is stored on the server: the trusted list and the history live only in the
visitor's own browser session, and can be saved to / loaded from files.

Run:  streamlit run app.py
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, Optional

import streamlit as st

import judge as jg
import messages
import rdap
import storage
from judge import Level, TrustedList
from lookup import AgeLookup, SlidingWindowLimiter
from messages import code_span
from ruledata import RuleData
from ui_text import UI

SAVE_MIN_LEVEL = Level.DANGER          # senders at or above this level go to the history
MAX_NET_LOOKUPS_PER_SESSION = 30       # real network lookups one visitor may trigger
GLOBAL_LOOKUPS_PER_MINUTE = 60         # real network lookups the whole app may make per minute
MAX_HISTORY = 500

LANG_NAMES = {"ja": "日本語", "en": "English"}


# ---------------------------------------------------------------- shared services

@st.cache_resource
def get_services():
    """Things shared by all visitors: the rule data and the domain-age lookup."""
    data = RuleData.load()
    rdap_on = os.environ.get("MAILGUARD_RDAP") != "0"
    lookup = AgeLookup(
        rdap.fetch_registration_date if rdap_on else None,
        SlidingWindowLimiter(GLOBAL_LOOKUPS_PER_MINUTE, 60),
    )
    return data, lookup


# ---------------------------------------------------------------- session state

def init_state() -> None:
    ss = st.session_state
    if "lang" not in ss:
        wanted = st.query_params.get("lang", messages.DEFAULT_LANG)
        ss.lang = wanted if wanted in messages.LANGS else messages.DEFAULT_LANG
    ss.setdefault("trusted", [])        # [{"value", "kind", "label"}]
    ss.setdefault("history", [])        # [{"time", "address", "domain", "level", "findings"}]
    ss.setdefault("last", None)         # the most recent check
    ss.setdefault("check_error", False)
    ss.setdefault("net_lookups", 0)
    ss.setdefault("flash", None)        # (kind, key, params) shown once at the top


def T(key: str, **kwargs: Any) -> str:
    text = UI[st.session_state.lang][key]
    return text.format(**kwargs) if kwargs else text


def set_flash(kind: str, key: str, **params: Any) -> None:
    st.session_state.flash = (kind, key, params)


def show_flash() -> None:
    flash = st.session_state.flash
    if flash:
        kind, key, params = flash
        {"success": st.success, "error": st.error, "info": st.info}[kind](T(key, **params))
        st.session_state.flash = None


# ---------------------------------------------------------------- actions

def trusted_list() -> TrustedList:
    return TrustedList.from_values(e["value"] for e in st.session_state.trusted)


def add_trusted(raw_value: str, label: str = "") -> str:
    """Returns 'added', 'duplicate', 'invalid' or 'limit' (and the normalized value via flash)."""
    ss = st.session_state
    normalized = jg.normalize_trusted_value(raw_value)
    if normalized is None:
        set_flash("error", "trusted_invalid")
        return "invalid"
    value, kind = normalized
    if any(e["value"] == value for e in ss.trusted):
        set_flash("error", "trusted_duplicate", value=code_span(value))
        return "duplicate"
    if len(ss.trusted) >= storage.MAX_TRUSTED:
        set_flash("error", "trusted_limit", max=storage.MAX_TRUSTED)
        return "limit"
    ss.trusted.append({"value": value, "kind": kind, "label": label.strip()[:storage.MAX_LABEL]})
    set_flash("success", "trusted_added", value=code_span(value))
    return "added"


def run_check(raw_address: str, display_name: str, subject: str) -> None:
    ss = st.session_state
    parsed = jg.parse_address(raw_address[:300])
    if parsed is None:
        ss.check_error = True
        ss.last = None
        return
    ss.check_error = False

    name, address = parsed
    domain = jg.domain_of(address)
    data, lookup = get_services()
    trusted = trusted_list()

    age_days: Optional[int] = None
    age_status = "skipped"
    if jg.needs_age_lookup(address, data, trusted):
        if ss.net_lookups >= MAX_NET_LOOKUPS_PER_SESSION:
            age_status = "limited"
        else:
            found = lookup.lookup(domain)
            age_days, age_status = found.age_days, found.status
            if found.fetched:
                ss.net_lookups += 1

    result = jg.judge(address, data, trusted,
                      display_name=(display_name[:200] or name),
                      subject=subject[:300],
                      domain_age_days=age_days)

    record: Dict[str, Any] = {
        "time": datetime.now().isoformat(timespec="seconds").replace("T", " "),
        "address": address,
        "domain": domain,
        "level": int(result.level),
        "findings": [{"code": f.code, "params": dict(f.params)} for f in result.findings],
        "age_days": age_days,
        "age_status": age_status,
        "saved": False,
    }
    if result.level >= SAVE_MIN_LEVEL:
        record["saved"] = True
        ss.history.append({k: record[k] for k in ("time", "address", "domain", "level", "findings")})
        del ss.history[:-MAX_HISTORY]
    ss.last = record


# ---------------------------------------------------------------- screens

def registered_text(rec: Dict[str, Any]) -> str:
    status = rec["age_status"]
    if rec["age_days"] is not None:
        return T("reg_days", days=rec["age_days"])
    return T({"limited": "reg_limited", "off": "reg_off", "skipped": "reg_skipped"}.get(status, "reg_unknown"))


def render_result(rec: Dict[str, Any]) -> None:
    lang = st.session_state.lang
    level = rec["level"]
    box = {4: st.error, 3: st.warning, 2: st.info, 1: st.success, 0: st.info}[level]

    # Anything that came from the email (address, domain, keywords) is shown as a code span,
    # so it can never turn into a clickable link.
    lines = [
        f"**{T('level_word')} {level}: {messages.level_label(level, lang)}**",
        f"{code_span(rec['address'])}  \n"
        f"{T('domain_word')}: {code_span(rec['domain'])} / {T('registered_word')}: {registered_text(rec)}",
        "",
    ]
    for f in rec["findings"]:
        reason, advice = messages.render(f["code"], f["params"], lang, quote=code_span)
        lines.append(f"- {reason}  \n  → {advice}")
    box("\n".join(lines))

    if rec["saved"]:
        st.caption(T("saved_note"))
    if not trusted_list().matches(rec["address"], rec["domain"]):
        if st.button(T("add_trusted_btn"), key="add_last"):
            add_trusted(rec["address"])
            st.rerun()


def check_tab() -> None:
    st.write(T("check_hint"))
    with st.form("check_form"):
        address = st.text_input(T("address_label"), placeholder=T("address_placeholder"),
                                max_chars=300, key="in_address")
        with st.expander(T("details_label")):
            display_name = st.text_input(T("display_name_label"), placeholder=T("display_name_placeholder"),
                                         max_chars=200, key="in_display")
            subject = st.text_input(T("subject_label"), placeholder=T("subject_placeholder"),
                                    max_chars=300, key="in_subject")
        submitted = st.form_submit_button(T("submit"))

    if submitted:
        run_check(address, display_name, subject)

    if st.session_state.check_error:
        st.error(T("err_invalid"))
    elif st.session_state.last:
        render_result(st.session_state.last)

    with st.expander(T("legend_title")):
        for line in T("legend"):
            st.markdown(line)


def trusted_tab() -> None:
    ss = st.session_state
    st.write(T("trusted_hint"))

    with st.form("trusted_form", clear_on_submit=True):
        value = st.text_input(T("trusted_value_label"), placeholder=T("trusted_value_placeholder"),
                              max_chars=254, key="in_trusted_value")
        label = st.text_input(T("trusted_note_label"), placeholder=T("trusted_note_placeholder"),
                              max_chars=storage.MAX_LABEL, key="in_trusted_label")
        if st.form_submit_button(T("trusted_add_btn")):
            add_trusted(value, label)
            st.rerun()

    st.subheader(T("trusted_count", count=len(ss.trusted)))
    if ss.trusted:
        st.dataframe(
            [{T("col_entry"): e["value"],
              T("col_type"): T("type_address") if e["kind"] == "address" else T("type_domain"),
              T("col_note"): e["label"]} for e in ss.trusted],
            hide_index=True)

        chosen = st.multiselect(T("trusted_delete_label"), [e["value"] for e in ss.trusted], key="del_trusted")
        if st.button(T("trusted_delete_btn")) and chosen:
            ss.trusted = [e for e in ss.trusted if e["value"] not in chosen]
            set_flash("success", "trusted_deleted")
            st.rerun()

        st.download_button(T("trusted_download"), storage.export_trusted_json(ss.trusted),
                           file_name="mailguard_trusted.json", mime="application/json")
    else:
        st.caption(T("trusted_empty"))

    uploaded = st.file_uploader(T("trusted_upload_label"), type=["json"], key="up_trusted")
    if st.button(T("trusted_import_btn")):
        if uploaded is None:
            st.warning(T("trusted_import_none"))
        else:
            entries, skipped, error = storage.import_trusted_json(uploaded.getvalue())
            if error:
                set_flash("error", {"too_large": "import_too_large", "invalid_json": "import_invalid_json"}
                          .get(error, "import_invalid_format"))
            else:
                existing = {e["value"] for e in ss.trusted}
                added = 0
                for e in entries:
                    if e["value"] in existing or len(ss.trusted) >= storage.MAX_TRUSTED:
                        skipped += 1
                        continue
                    ss.trusted.append(e)
                    existing.add(e["value"])
                    added += 1
                set_flash("success", "trusted_import_done", added=added, skipped=skipped)
            st.rerun()


def history_tab() -> None:
    ss = st.session_state
    lang = ss.lang
    st.write(T("history_hint"))
    st.subheader(T("history_count", count=len(ss.history)))
    if not ss.history:
        st.caption(T("history_empty"))
        return

    rows = []
    newest_first = sorted(ss.history, key=lambda r: r["time"], reverse=True)
    for rec in sorted(newest_first, key=lambda r: r["level"], reverse=True):  # most dangerous first
        reasons = " / ".join(messages.render(f["code"], f["params"], lang)[0] for f in rec["findings"])
        rows.append({
            T("col_time"): rec["time"],
            T("col_address"): rec["address"],
            T("col_level"): f"{rec['level']} {messages.level_label(rec['level'], lang)}",
            T("col_reasons"): reasons,
        })
    st.dataframe(rows, hide_index=True)

    st.download_button(T("history_download"), storage.history_to_csv(ss.history, lang),
                       file_name="mailguard_history.csv", mime="text/csv")
    if st.button(T("history_clear")):
        ss.history = []
        set_flash("success", "history_cleared")
        st.rerun()


# ---------------------------------------------------------------- page

def main() -> None:
    st.set_page_config(page_title="MailGuard", layout="centered")
    init_state()

    st.radio(UI["en"]["language"], list(LANG_NAMES), key="lang", horizontal=True,
             format_func=lambda code: LANG_NAMES[code])
    st.title(T("title"))
    st.caption(T("tagline"))
    show_flash()

    tab_check, tab_trusted, tab_history = st.tabs([T("tab_check"), T("tab_trusted"), T("tab_history")])
    with tab_check:
        check_tab()
    with tab_trusted:
        trusted_tab()
    with tab_history:
        history_tab()

    st.info(T("session_note"))
    st.caption(T("footer_limits"))
    st.caption(T("footer_privacy"))


main()
