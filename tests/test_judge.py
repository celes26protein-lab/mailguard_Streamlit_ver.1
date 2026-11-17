import unittest

import messages
from judge import (
    Level,
    TrustedList,
    judge,
    levenshtein,
    needs_age_lookup,
    normalize_trusted_value,
    parse_address,
    tail,
)
from ruledata import RuleData

DATA = RuleData.load()
TRUSTED = TrustedList.from_values(["family@example.com", "mybank.example"])


def run(address, display="", subject="", age=None, trusted=TRUSTED):
    return judge(address, DATA, trusted, display_name=display, subject=subject, domain_age_days=age)


def codes(result):
    return [f.code for f in result.findings]


class JudgeTest(unittest.TestCase):
    def test_official_domain_is_low(self):
        self.assertEqual(run("shipment@amazon.com", "Amazon", "Your order has shipped").level, Level.LOW)

    def test_official_domain_japan_is_low(self):
        self.assertEqual(run("shipment@amazon.co.jp", "Amazon", "ご注文の発送のお知らせ").level, Level.LOW)

    def test_blacklist_is_critical(self):
        r = run("news@evil-example.test")
        self.assertEqual(r.level, Level.CRITICAL)
        self.assertIn("blacklist", codes(r))

    def test_blacklist_matches_subdomain(self):
        self.assertEqual(run("a@mail.evil-example.test").level, Level.CRITICAL)

    def test_lookalike_of_official_is_critical(self):
        r = run("service@paypa1.com", "PayPal")
        self.assertEqual(r.level, Level.CRITICAL)
        self.assertEqual(r.findings[0].params["ref"], "paypal.com")

    def test_lookalike_of_official_japan_is_critical(self):
        self.assertEqual(run("info@amazom.co.jp", "Amazon").level, Level.CRITICAL)

    def test_lookalike_of_trusted_domain_is_critical(self):
        self.assertEqual(run("info@mybamk.example").level, Level.CRITICAL)

    def test_brand_mismatch_is_danger(self):
        r = run("support@random-shop.example", "PayPal", "Please update your payment details", age=3000)
        self.assertEqual(r.level, Level.DANGER)
        self.assertIn("brand_mismatch", codes(r))

    def test_disposable_is_danger(self):
        self.assertEqual(run("john@mailinator.com", age=3000).level, Level.DANGER)

    def test_keyword_in_subject_is_danger(self):
        r = run("help@unknown-shop.example", "Support", "URGENT: your account suspended", age=3000)
        self.assertEqual(r.level, Level.DANGER)

    def test_japanese_keyword_in_subject_is_danger(self):
        r = run("help@unknown-shop.example", "サポート", "【緊急】アカウント停止のお知らせ", age=3000)
        self.assertEqual(r.level, Level.DANGER)

    def test_new_domain_and_first_time_raise_to_danger(self):
        self.assertEqual(run("info@newshop-sample.example", age=5).level, Level.DANGER)

    def test_unknown_old_domain_is_caution(self):
        self.assertEqual(run("friend@unknown-domain.example", age=4000).level, Level.CAUTION)

    def test_unknown_age_is_caution_only(self):
        self.assertEqual(run("friend@unknown-domain.example", age=None).level, Level.CAUTION)

    def test_brand_keyword_does_not_match_inside_other_words(self):
        r = run("a@unknown-domain.example", "Landlord", "First day of the new lease", age=4000)
        self.assertEqual(r.level, Level.CAUTION)

    def test_trusted_address_is_low(self):
        self.assertEqual(run("family@example.com").level, Level.LOW)

    def test_trusted_domain_covers_subdomain(self):
        self.assertEqual(run("x@mail.mybank.example").level, Level.LOW)

    def test_trusted_but_new_domain_is_caution(self):
        self.assertEqual(run("family@example.com", age=2).level, Level.CAUTION)

    def test_trusted_ignores_keywords(self):
        self.assertEqual(run("family@example.com", subject="Urgent: please call me").level, Level.LOW)

    def test_government_suffixes_are_low(self):
        for address in ["info@city.example.lg.jp", "info@agency.gov", "info@service.gov.uk"]:
            self.assertEqual(run(address).level, Level.LOW, address)

    def test_blacklist_wins_even_if_trusted(self):
        trusted = TrustedList.from_values(["evil-example.test"])
        self.assertEqual(run("a@evil-example.test", trusted=trusted).level, Level.CRITICAL)

    def test_age_lookup_skipped_for_known_senders(self):
        self.assertFalse(needs_age_lookup("family@example.com", DATA, TRUSTED))
        self.assertFalse(needs_age_lookup("a@amazon.com", DATA, TRUSTED))
        self.assertFalse(needs_age_lookup("a@evil-example.test", DATA, TRUSTED))
        self.assertTrue(needs_age_lookup("a@unknown-domain.example", DATA, TRUSTED))

    def test_every_finding_can_be_shown_in_both_languages(self):
        samples = [
            run("news@evil-example.test"),
            run("service@paypa1.com", "PayPal"),
            run("john@mailinator.com", age=3000),
            run("a@random-shop.example", "PayPal", "Urgent", age=3000),
            run("info@newshop-sample.example", age=5),
            run("family@example.com"),
            run("shipment@amazon.com"),
        ]
        for result in samples:
            for finding in result.findings:
                for lang in messages.LANGS:
                    reason, advice = messages.render(finding.code, finding.params, lang)
                    self.assertTrue(reason and advice, (finding.code, lang))
                    self.assertNotIn("{", reason + advice)


class HelperTest(unittest.TestCase):
    def test_parse_address_with_name(self):
        self.assertEqual(parse_address("Amazon <Info@Example.com>"), ("Amazon", "info@example.com"))

    def test_parse_plain_address(self):
        self.assertEqual(parse_address("  info@example.com "), ("", "info@example.com"))

    def test_parse_rejects_garbage(self):
        for bad in ["", "not-an-address", "a@b", "@example.com", "a b@example.com", "a@@example.com"]:
            self.assertIsNone(parse_address(bad), bad)

    def test_normalize_trusted(self):
        self.assertEqual(normalize_trusted_value(" Info@Example.com "), ("info@example.com", "address"))
        self.assertEqual(normalize_trusted_value("@Example.com"), ("example.com", "domain"))
        self.assertIsNone(normalize_trusted_value("hello"))
        self.assertIsNone(normalize_trusted_value("a b.com"))

    def test_levenshtein_and_tail(self):
        self.assertEqual(levenshtein("amazon.co.jp", "amazom.co.jp"), 1)
        self.assertEqual(levenshtein("", "abc"), 3)
        self.assertEqual(tail("mail.a.b.com", 2), "b.com")
        self.assertEqual(tail("b.com", 3), "b.com")


class MessagesTest(unittest.TestCase):
    def test_all_codes_exist_in_both_languages(self):
        for code, versions in messages.FINDING_TEXT.items():
            self.assertEqual(set(versions), set(messages.LANGS), code)

    def test_level_labels_cover_all_levels(self):
        for lang in messages.LANGS:
            self.assertEqual(sorted(messages.LEVEL_LABELS[lang]), [0, 1, 2, 3, 4])

    def test_keywords_are_joined_per_language(self):
        ja, _ = messages.render("keywords", {"words": ["緊急", "当選"]}, "ja")
        en, _ = messages.render("keywords", {"words": ["urgent", "final notice"]}, "en")
        self.assertIn("緊急、当選", ja)
        self.assertIn("urgent, final notice", en)

    def test_unknown_language_falls_back_to_default(self):
        self.assertEqual(messages.level_label(3, "xx"), "危険")

    def test_code_span_wraps_text_and_drops_backticks(self):
        self.assertEqual(messages.code_span("www.evil.example"), "`www.evil.example`")
        self.assertEqual(messages.code_span("a`b"), "`ab`")

    def test_render_wraps_outside_text_only_when_asked(self):
        plain, _ = messages.render("lookalike", {"domain": "paypa1.com", "ref": "paypal.com"}, "en")
        quoted, _ = messages.render("lookalike", {"domain": "paypa1.com", "ref": "paypal.com"}, "en",
                                    quote=messages.code_span)
        self.assertIn("(paypa1.com)", plain)
        self.assertIn("(`paypa1.com`)", quoted)
        self.assertIn("(`paypal.com`)", quoted)

    def test_render_wraps_each_keyword_and_leaves_numbers_alone(self):
        text, _ = messages.render("keywords", {"words": ["urgent", "final notice"]}, "en",
                                  quote=messages.code_span)
        self.assertIn("`urgent`, `final notice`", text)
        days, _ = messages.render("new_domain", {"days": 5}, "en", quote=messages.code_span)
        self.assertIn(" 5 day(s)", days)


if __name__ == "__main__":
    unittest.main()
