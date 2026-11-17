"""Japanese and English texts for the judging results.

judge.py only produces a code and parameters (a Finding). This module turns them into
the words shown to the person.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Mapping, Optional, Tuple

LANGS = ("ja", "en")
DEFAULT_LANG = "ja"

LEVEL_LABELS = {
    "ja": {0: "判定不能", 1: "低リスク", 2: "注意", 3: "危険", 4: "超危険"},
    "en": {0: "Unknown", 1: "Low risk", 2: "Caution", 3: "Danger", 4: "Critical"},
}

_WORD_SEPARATOR = {"ja": "、", "en": ", "}

_LOW_ADVICE_JA = ("ただし、送信元の偽装(なりすまし)は、このアプリでは見抜けません。"
                  "リンク先のURLはご自身でも確認してください。")
_LOW_ADVICE_EN = ("This does not mean it is guaranteed safe: this app cannot detect a spoofed sender. "
                  "Check where links lead yourself.")

# code -> language -> (reason, advice). {name} placeholders are filled from the Finding's params.
FINDING_TEXT: Dict[str, Dict[str, Tuple[str, str]]] = {
    "blacklist": {
        "ja": ("送信元({domain})は、詐欺・迷惑メールとして報告されたものと一致します。",
               "リンクや添付ファイルは開かず、メールを削除してください。"),
        "en": ("The sender ({domain}) matches a domain or address that was reported for scams or spam.",
               "Do not open any links or attachments. Delete the email."),
    },
    "lookalike": {
        "ja": ("送信元ドメイン({domain})は、({ref})によく似た偽物の可能性があります。",
               "リンクは開かず、公式アプリや、自分で入力した公式サイトのURLから確認してください。"),
        "en": ("The sender domain ({domain}) may be a fake that imitates ({ref}).",
               "Do not click any links. Check through the official app, or type the official "
               "website address yourself."),
    },
    "disposable": {
        "ja": ("送信元({domain})は使い捨てメールのドメインです。",
               "心当たりがなければ、返信やリンクのクリックはしないでください。"),
        "en": ("The sender ({domain}) is a disposable-email domain.",
               "If you do not recognize it, do not reply and do not click any links."),
    },
    "brand_mismatch": {
        "ja": ("「{keyword}」を名乗っていますが、送信元({domain})は正規ドメインではありません。",
               "リンクは開かず、公式アプリや公式サイトから直接確認してください。"),
        "en": ('It claims to be "{keyword}", but the sender ({domain}) is not an official domain for it.',
               "Do not click any links. Check directly through the official app or website."),
    },
    "keywords": {
        "ja": ("件名に、詐欺で多く使われる言葉が含まれています: {words}",
               "あわてて操作せず、公式アプリや公式サイトから直接確認してください。"),
        "en": ("The subject contains words often used in scams: {words}",
               "Do not act in a hurry. Check directly through the official app or website."),
    },
    "new_domain": {
        "ja": ("送信元ドメインは取得から{days}日しか経っていません。",
               "心当たりのない内容なら、リンクを開く前に確認してください。"),
        "en": ("The sender's domain was registered only {days} day(s) ago.",
               "If the content is unexpected, check before opening any links."),
    },
    "first_time": {
        "ja": ("「よく使うリスト」にない、初めての相手です。",
               "よく使う相手なら、リストに追加してください。心当たりがなければ、"
               "リンクや添付ファイルは慎重に扱ってください。"),
        "en": ("This sender is not in your trusted list (first-time sender).",
               "If you know this sender, add them to the list. If not, handle links and "
               "attachments with care."),
    },
    "low_trusted": {
        "ja": ("よく使うリストにある相手です。現時点で不審な点は見つかりませんでした。", _LOW_ADVICE_JA),
        "en": ("This sender is in your trusted list. Nothing suspicious was found.", _LOW_ADVICE_EN),
    },
    "low_official": {
        "ja": ("正規ドメインからのメールです。現時点で不審な点は見つかりませんでした。", _LOW_ADVICE_JA),
        "en": ("This is an official domain. Nothing suspicious was found.", _LOW_ADVICE_EN),
    },
    "unknown": {
        "ja": ("ルールに該当する情報がなく、危険とも安全とも判定できませんでした。",
               "心当たりのないメールなら、リンクや添付ファイルは慎重に扱ってください。"),
        "en": ("No rule matched, so the sender can be judged neither dangerous nor safe.",
               "If you do not recognize the email, handle links and attachments with care."),
    },
}


def level_label(level: int, lang: str) -> str:
    return LEVEL_LABELS[_lang(lang)][int(level)]


def code_span(text: Any) -> str:
    """Show text exactly as it is inside Markdown. Anything in a code span is never turned into a
    link, an image or a style, so a sender's address or domain cannot become a clickable link."""
    return "`" + str(text).replace("`", "") + "`"


def render(code: str, params: Mapping[str, Any], lang: str,
           quote: Optional[Callable[[Any], str]] = None) -> Tuple[str, str]:
    """Return (reason, advice) for a finding in the given language.

    quote, if given, wraps every piece of text that came from outside (domains, keywords).
    Pass code_span when the result will be shown as Markdown; leave it out for plain text.
    """
    lang = _lang(lang)
    wrap = quote or str
    values: Dict[str, Any] = {}
    for key, value in params.items():
        if key == "words" and isinstance(value, (list, tuple)):
            values[key] = _WORD_SEPARATOR[lang].join(wrap(w) for w in value)
        elif isinstance(value, str):
            values[key] = wrap(value)
        else:
            values[key] = value
    reason, advice = FINDING_TEXT[code][lang]
    return reason.format(**values), advice.format(**values)


def _lang(lang: str) -> str:
    return lang if lang in LANGS else DEFAULT_LANG
