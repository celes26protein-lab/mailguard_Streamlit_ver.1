"""Click-through tests of the Streamlit screen, using Streamlit's own test runner.
The network lookup is turned off, so these tests never go online."""
import os
import unittest

os.environ["MAILGUARD_RDAP"] = "0"

from streamlit.testing.v1 import AppTest  # noqa: E402

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")


def new_app():
    return AppTest.from_file(APP, default_timeout=30).run()


def check(at, address, display="", subject=""):
    at.text_input(key="in_address").set_value(address)
    if display:
        at.text_input(key="in_display").set_value(display)
    if subject:
        at.text_input(key="in_subject").set_value(subject)
    # the first form's submit button
    at.button[0].click().run()
    return at


def all_text(at):
    parts = []
    for group in (at.markdown, at.error, at.warning, at.info, at.success, at.caption):
        parts += [str(e.value) for e in group]
    return "\n".join(parts)


class StreamlitAppTest(unittest.TestCase):
    def test_app_starts_without_errors_in_japanese(self):
        at = new_app()
        self.assertFalse(at.exception)
        self.assertEqual(at.title[0].value, "メール番人")

    def test_language_switch(self):
        at = new_app()
        at.radio(key="lang").set_value("en").run()
        self.assertFalse(at.exception)
        self.assertEqual(at.title[0].value, "MailGuard")
        at.radio(key="lang").set_value("ja").run()
        self.assertEqual(at.title[0].value, "メール番人")

    def test_language_from_query_parameter(self):
        at = AppTest.from_file(APP, default_timeout=30)
        at.query_params["lang"] = "en"
        at.run()
        self.assertEqual(at.title[0].value, "MailGuard")

    def test_invalid_address_shows_error(self):
        at = check(new_app(), "hello")
        self.assertIn("メールアドレスの形式が正しくありません", all_text(at))

    def test_dangerous_sender_is_rated_and_saved(self):
        at = check(new_app(), "john@mailinator.com")
        self.assertFalse(at.exception)
        self.assertEqual(len(at.session_state["history"]), 1)
        self.assertEqual(at.session_state["history"][0]["level"], 3)
        self.assertIn("危険", all_text(at))

    def test_result_is_shown_in_the_chosen_language(self):
        at = new_app()
        at.radio(key="lang").set_value("en").run()
        at = check(at, "john@mailinator.com")
        text = all_text(at)
        self.assertIn("Danger", text)
        self.assertIn("disposable-email domain", text)

    def test_history_keeps_no_subject_or_name(self):
        at = check(new_app(), "x@mailinator.com", display="SECRET NAME", subject="SECRET SUBJECT")
        self.assertNotIn("SECRET", str(at.session_state["history"]))

    def test_caution_is_not_saved_to_history(self):
        at = check(new_app(), "friend@unknown-domain.example")
        self.assertEqual(at.session_state["history"], [])
        self.assertEqual(at.session_state["last"]["level"], 2)

    def test_add_to_trusted_then_low_risk(self):
        at = check(new_app(), "friend@unknown-domain.example")
        at.button(key="add_last").click().run()
        self.assertEqual([e["value"] for e in at.session_state["trusted"]], ["friend@unknown-domain.example"])
        at = check(at, "friend@unknown-domain.example")
        self.assertEqual(at.session_state["last"]["level"], 1)

    def test_trusted_form_adds_and_rejects(self):
        at = new_app()
        at.text_input(key="in_trusted_value").set_value("Family@Example.com")
        at.text_input(key="in_trusted_label").set_value("family")
        at.button[1].click().run()          # second form's submit button
        self.assertEqual(at.session_state["trusted"][0]["value"], "family@example.com")

        at.text_input(key="in_trusted_value").set_value("not valid")
        at.button[1].click().run()
        self.assertEqual(len(at.session_state["trusted"]), 1)

    def test_markdown_in_display_name_is_never_shown(self):
        at = check(new_app(), "a@example.com", display="[x](http://evil.example)")
        self.assertFalse(at.exception)
        self.assertNotIn("http://evil.example", all_text(at))

    def test_sender_text_is_shown_as_code_so_it_cannot_become_a_link(self):
        at = check(new_app(), "service@www.paypa1.com", display="PayPal")
        result_markdown = str(at.error[0].value)
        self.assertIn("`service@www.paypa1.com`", result_markdown)
        self.assertIn("`www.paypa1.com`", result_markdown)
        # no bare (unquoted) copy of the address or domain anywhere in the result
        without_code = result_markdown.replace("`service@www.paypa1.com`", "").replace("`www.paypa1.com`", "")
        self.assertNotIn("paypa1.com", without_code)

    def test_flash_value_is_shown_as_code(self):
        at = new_app()
        at.text_input(key="in_trusted_value").set_value("family@example.com")
        at.button[1].click().run()
        self.assertIn("`family@example.com`", all_text(at))


if __name__ == "__main__":
    unittest.main()
