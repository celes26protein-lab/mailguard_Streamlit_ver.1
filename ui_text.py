"""Text shown on the screen, in Japanese and English."""
from __future__ import annotations

UI = {
    "ja": {
        "title": "メール番人",
        "tagline": "クリックする前に、送信元を確認しましょう。",
        "language": "Language / 言語",
        "tab_check": "判定する",
        "tab_trusted": "よく使うリスト",
        "tab_history": "履歴",
        "session_note": "「よく使うリスト」と履歴は、この画面(ブラウザのタブ)の中だけに保持されます。"
                        "再読み込みしたり閉じたりすると消えるので、残したいときは、ファイルとして保存してください。"
                        "サーバーには保存されません。",
        # check tab
        "check_hint": "受信したメールの送信元アドレスをコピーして、貼り付けてください。"
                      "(`名前 <info@example.com>` の形でも大丈夫です)",
        "address_label": "送信元アドレス",
        "address_placeholder": "info@example.com",
        "details_label": "くわしく調べる(任意)",
        "display_name_label": "表示名(メールソフトに表示される送信者名)",
        "display_name_placeholder": "Amazon",
        "subject_label": "件名",
        "subject_placeholder": "アカウント停止のお知らせ",
        "submit": "判定する",
        "err_invalid": "メールアドレスの形式が正しくありません。(例: `info@example.com`)",
        "level_word": "レベル",
        "domain_word": "ドメイン",
        "registered_word": "取得日",
        "reg_days": "約{days}日前",
        "reg_unknown": "不明",
        "reg_limited": "未確認(照会が混み合っているため)",
        "reg_off": "未確認(照会はオフです)",
        "reg_skipped": "照会不要",
        "saved_note": "怪しい送信元として、この画面の履歴に保存しました。",
        "add_trusted_btn": "よく使う相手として登録する",
        "legend_title": "レベルの見かた",
        "legend": [
            "**4 超危険** — ブラックリスト該当、正規ドメインに似せた偽物",
            "**3 危険** — 使い捨てドメイン、名乗りとドメインの食い違い、怪しい件名",
            "**2 注意** — 新しいドメイン、初めての相手",
            "**1 低リスク** — よく使う相手、正規ドメイン",
            "**0 判定不能** — どれにも当てはまらない",
        ],
        # trusted tab
        "trusted_hint": "いつもメールを受け取る相手を登録しておくと、「初めての相手」の注意が出なくなります。"
                        "アドレス(`info@example.com`)か、ドメイン(`example.com`)で登録できます。"
                        "ドメインで登録すると、そのサブドメインも対象になります。",
        "trusted_value_label": "アドレスまたはドメイン",
        "trusted_value_placeholder": "info@example.com または example.com",
        "trusted_note_label": "メモ(任意)",
        "trusted_note_placeholder": "家族、会社、よく使う通販サイト など",
        "trusted_add_btn": "追加する",
        "trusted_added": "{value} を追加しました。",
        "trusted_duplicate": "{value} は、すでに登録されています。",
        "trusted_invalid": "形式が正しくありません。アドレス(`info@example.com`)か、ドメイン(`example.com`)を入れてください。",
        "trusted_limit": "登録できるのは、{max}件までです。",
        "trusted_count": "登録済み({count}件)",
        "trusted_empty": "まだ登録されていません。",
        "col_entry": "登録内容",
        "col_type": "種類",
        "col_note": "メモ",
        "type_address": "アドレス",
        "type_domain": "ドメイン",
        "trusted_delete_label": "削除する項目を選ぶ",
        "trusted_delete_btn": "選んだ項目を削除",
        "trusted_deleted": "削除しました。",
        "trusted_download": "リストをファイルに保存(JSON)",
        "trusted_upload_label": "保存したファイルから読み込む(JSON)",
        "trusted_import_btn": "読み込む",
        "trusted_import_done": "{added}件を読み込みました。(スキップ: {skipped}件)",
        "trusted_import_none": "ファイルを選んでください。",
        "import_too_large": "ファイルが大きすぎます。",
        "import_invalid_json": "JSONファイルとして読み込めませんでした。",
        "import_invalid_format": "ファイルの形式が正しくありません。",
        # history tab
        "history_hint": "レベル3(危険)以上と判定した送信元だけが、ここに保存されます。"
                        "保存されるのは、アドレス・ドメイン・レベル・理由・日時だけです。"
                        "メールの本文や件名は、保存しません。",
        "history_count": "怪しい送信元の履歴({count}件)",
        "history_empty": "まだ履歴はありません。",
        "col_time": "日時",
        "col_address": "アドレス",
        "col_level": "レベル",
        "col_reasons": "理由",
        "history_download": "履歴をファイルに保存(CSV)",
        "history_clear": "履歴をすべて削除",
        "history_cleared": "履歴をすべて削除しました。",
        # footer
        "footer_limits": "このアプリはルールによる目安です。最終的な判断はご自身で行ってください。"
                         "メールの認証(SPF/DKIM/DMARC)は確認できないため、送信元の偽装(なりすまし)は見抜けません。"
                         "リンクや添付ファイルも調べません。",
        "footer_privacy": "外部に送るのは、ドメイン名だけです(取得日の照会のため)。"
                          "メールの本文や件名は、保存も送信もしません。",
    },
    "en": {
        "title": "MailGuard",
        "tagline": "Not sure about an email? Check the sender before you click.",
        "language": "Language / 言語",
        "tab_check": "Check",
        "tab_trusted": "Trusted list",
        "tab_history": "History",
        "session_note": "Your trusted list and history are kept only in this screen (this browser tab). "
                        "They disappear when you reload or close it, so save them as files if you want to keep them. "
                        "Nothing is stored on the server.",
        # check tab
        "check_hint": "Copy the sender's address from the email you received and paste it here. "
                      "(The form `Name <info@example.com>` also works.)",
        "address_label": "Sender address",
        "address_placeholder": "info@example.com",
        "details_label": "Look closer (optional)",
        "display_name_label": "Display name (the sender name your mail app shows)",
        "display_name_placeholder": "Amazon",
        "subject_label": "Subject",
        "subject_placeholder": "Your account has been suspended",
        "submit": "Check",
        "err_invalid": "That is not a valid email address. (Example: `info@example.com`)",
        "level_word": "Level",
        "domain_word": "Domain",
        "registered_word": "Registered",
        "reg_days": "about {days} day(s) ago",
        "reg_unknown": "unknown",
        "reg_limited": "not checked (lookups are busy)",
        "reg_off": "not checked (lookup is turned off)",
        "reg_skipped": "no lookup needed",
        "saved_note": "Saved to this screen's history as a suspicious sender.",
        "add_trusted_btn": "Add this sender to the trusted list",
        "legend_title": "What the levels mean",
        "legend": [
            "**4 Critical** — on the blacklist, or a fake that imitates a real domain",
            "**3 Danger** — disposable domain, claimed name does not match the domain, suspicious subject",
            "**2 Caution** — newly registered domain, first-time sender",
            "**1 Low risk** — trusted sender or official domain",
            "**0 Unknown** — nothing matched",
        ],
        # trusted tab
        "trusted_hint": "Add the people and services you always receive mail from, and the "
                        "\"first-time sender\" caution will no longer appear for them. "
                        "You can add a full address (`info@example.com`) or a domain (`example.com`). "
                        "A domain also covers its subdomains.",
        "trusted_value_label": "Address or domain",
        "trusted_value_placeholder": "info@example.com or example.com",
        "trusted_note_label": "Note (optional)",
        "trusted_note_placeholder": "Family, work, a shop I use, ...",
        "trusted_add_btn": "Add",
        "trusted_added": "Added {value}.",
        "trusted_duplicate": "{value} is already in the list.",
        "trusted_invalid": "That format is not valid. Enter an address (`info@example.com`) or a domain (`example.com`).",
        "trusted_limit": "The list can hold up to {max} entries.",
        "trusted_count": "Saved entries ({count})",
        "trusted_empty": "Nothing has been added yet.",
        "col_entry": "Entry",
        "col_type": "Type",
        "col_note": "Note",
        "type_address": "Address",
        "type_domain": "Domain",
        "trusted_delete_label": "Choose entries to delete",
        "trusted_delete_btn": "Delete the chosen entries",
        "trusted_deleted": "Deleted.",
        "trusted_download": "Save the list as a file (JSON)",
        "trusted_upload_label": "Load from a saved file (JSON)",
        "trusted_import_btn": "Load",
        "trusted_import_done": "Loaded {added} entries. (Skipped: {skipped})",
        "trusted_import_none": "Choose a file first.",
        "import_too_large": "The file is too large.",
        "import_invalid_json": "The file could not be read as JSON.",
        "import_invalid_format": "The file format is not valid.",
        # history tab
        "history_hint": "Only senders judged level 3 (Danger) or higher are saved here. "
                        "What is saved: the address, domain, level, reasons and time. "
                        "The message body and subject are never saved.",
        "history_count": "Suspicious senders ({count})",
        "history_empty": "There is no history yet.",
        "col_time": "Time",
        "col_address": "Address",
        "col_level": "Level",
        "col_reasons": "Reasons",
        "history_download": "Save the history as a file (CSV)",
        "history_clear": "Delete the whole history",
        "history_cleared": "The whole history was deleted.",
        # footer
        "footer_limits": "This app gives a rough guide based on rules. The final decision is yours. "
                         "It cannot check email authentication (SPF/DKIM/DMARC), so it cannot detect a spoofed sender. "
                         "It does not inspect links or attachments.",
        "footer_privacy": "Only the domain name is sent outside (to look up its registration date). "
                          "The message body and subject are never stored or sent.",
    },
}
