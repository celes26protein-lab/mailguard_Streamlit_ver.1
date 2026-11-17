# MailGuard_App_version / メール番人アプリ (Streamlit version)

**Not sure about an email? Check the sender before you click.**
**クリックする前に、送信元を確認しましょう。**

Japanese and English in one app (switch at the top of the page).
日本語と英語を、1つのアプリで切り替えられます。

Other versions that run only on your own computer / 自分のパソコンの中だけで動く版:
[mailguard_JPver.1](https://github.com/Celes26protein-lab/mailguard_JPver.1) ・
[mailguard_Eng_ver.1](https://github.com/Celes26protein-lab/mailguard_Eng_ver.1)

---

## English

Copy the **sender address** of an email you received, paste it into this app, and it rates how risky the sender looks (level 0 to 4). It uses rules and data only, with no AI.

### Built to be safe to put online

- **Nothing is stored on the server.** The trusted list and the history live only in the visitor's own browser tab. They disappear when the page is reloaded or closed. Visitors can save them as files (JSON for the trusted list, CSV for the history) and load the trusted list back later.
- **The message body is never asked for, stored or sent.** The subject and display name (both optional) are used only to judge, and are not saved.
- **Only the domain name leaves the app**, to look up when it was registered (RDAP). Results are kept in memory for a few days (domain names and dates only).
- **Lookups are rate-limited** so the app cannot be used to flood the lookup service: at most 30 real lookups per visitor session and 60 per minute for the whole app.
- Anything that comes from the email (address, domain) is shown as plain code text, never as a clickable link.
- Uploaded trusted-list files are checked strictly: size limit, entry limit, and each entry must be a valid address or domain.

### What it does

1. **Check**: enter a sender address (optionally a display name and subject) and get a level, the reasons and advice.
2. **Trusted list**: add the people and services you always receive mail from (an address or a domain). The "first-time sender" caution then stops appearing for them.
3. **History**: senders rated level 3 (Danger) or higher are added to this tab's history. Save it as CSV.

| Level | Meaning | Main conditions |
|---|---|---|
| 4 | Critical | On the blacklist, or a fake domain that imitates a real one |
| 3 | Danger | Disposable-email domain, claimed name does not match the domain, suspicious words in the subject |
| 2 | Caution | Domain registered less than 30 days ago, first-time sender (two of these together raise it to level 3) |
| 1 | Low risk | In your trusted list, or an official domain (including government domains) |
| 0 | Unknown | Nothing matched |

### Run it on your computer

You need Python 3.9 or newer.

```
cd path/to/mailguard_Streamlit_ver.1
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Run the tests with `python -m unittest -v`.


### Growing the data

Edit the text files in `data/` to tune the rules without changing any code.

- `blacklist.txt`: scam and spam domains (the contents are dummies, so add real ones yourself)
- `official_domains.txt`: names a sender may claim, with their official domains (check the official website before adding one)
- `disposable_domains.txt`: disposable-email domains
- `suspicious_keywords.txt`: suspicious words in the subject

### Limits (please read)

- This is a simple check of the sender address. **It cannot check email authentication (SPF/DKIM/DMARC), so it cannot detect a spoofed sender.** A sender in the trusted list is not guaranteed safe either.
- It does not inspect links or attachments.
- It misses new tricks that the rules do not cover. The result is only a guide; the final decision is yours.
- A domain's registration date cannot always be found. When it cannot, that rule is simply skipped.
- Times shown in the history use the server's clock (often UTC), not your local time.

---

## 日本語

受信したメールの**送信元アドレス**をコピーして貼ると、危険度(レベル0〜4)を判定します。AIは使わず、ルールとデータだけで判定します。

### インターネットに公開しても安全なように作ってあります

- **サーバーには何も保存しません。** 「よく使うリスト」と履歴は、利用者のブラウザのタブの中だけにあります。再読み込みしたり閉じたりすると消えます。利用者は、ファイル(リストはJSON、履歴はCSV)として保存でき、リストはあとで読み込めます。
- **メールの本文は、求めも、保存も、送信もしません。** 件名と表示名(どちらも任意)は、判定に使うだけで、保存しません。
- **外部に送るのは、ドメイン名だけです。** 取得日の照会(RDAP)のためです。結果は、数日間、メモリの中にだけ保持します(ドメイン名と日付だけ)。
- **照会には回数の制限があります。** 照会サービスに負担をかけないよう、1人の利用者につき最大30回、アプリ全体で1分あたり60回までです。
- メールに由来する文字(アドレスやドメイン)は、クリックできるリンクにならず、コード表示で出ます。
- 読み込むリストのファイルは、厳しく検査します(大きさと件数の上限、各項目がアドレスかドメインの形式か)。

### できること

1. **判定する**:送信元アドレス(任意で表示名・件名)を入れると、レベルと理由・対処法が出ます。
2. **よく使うリスト**:いつもの相手(アドレスまたはドメイン)を登録すると、「初めての相手」の注意が出なくなります。
3. **履歴**:レベル3(危険)以上の送信元が、このタブの履歴に入ります。CSVで保存できます。

レベルの意味は、上の英語の表と同じです。

### 自分のパソコンで動かす

Python 3.9 以上が必要です。

```
cd mailguard_Streamlit_ver.1 のある場所
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

テストは、`python -m unittest -v` で実行できます。


### データの育て方

`data/` のテキストファイルを編集すると、コードを変えずに判定を調整できます。

- `blacklist.txt`:詐欺・迷惑メールのドメイン(中身はダミーです。自分で追加してください)
- `official_domains.txt`:名乗りのキーワードと、正規ドメイン(追加前に公式サイトで確認してください)
- `disposable_domains.txt`:使い捨てメールのドメイン
- `suspicious_keywords.txt`:件名の怪しい言葉

### 限界(必ず読んでください)

- 送信元アドレスだけを見る簡易チェックです。**メールの認証(SPF/DKIM/DMARC)は確認できないので、送信元の偽装(なりすまし)は見抜けません。** 「よく使うリスト」にある相手でも、安全とは限りません。
- リンクや添付ファイルは調べません。
- ルールにない新しい手口は見逃します。結果は目安で、最終判断は人が行ってください。
- ドメインの取得日は、いつも調べられるとは限りません。調べられないときは、そのルールを使わずに判定します。
- 履歴の日時は、利用者のパソコンではなく、サーバーの時計(多くはUTC)です。

---

## License

MIT License. See the `LICENSE` file. / MITライセンス。`LICENSE` ファイルを見てください。
