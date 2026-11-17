import unittest
from datetime import date

from rdap import parse_registration_date, registrable_domain


class RdapTest(unittest.TestCase):
    def test_registrable_domain(self):
        self.assertEqual(registrable_domain("mail.amazon.co.jp"), "amazon.co.jp")
        self.assertEqual(registrable_domain("a.b.example.com"), "example.com")
        self.assertEqual(registrable_domain("example.com"), "example.com")
        self.assertEqual(registrable_domain("shop.example.org.uk"), "example.org.uk")

    def test_parse_registration_date(self):
        body = {"events": [
            {"eventAction": "last changed", "eventDate": "2024-05-05T00:00:00Z"},
            {"eventAction": "registration", "eventDate": "2020-01-02T03:04:05Z"},
        ]}
        self.assertEqual(parse_registration_date(body), date(2020, 1, 2))

    def test_parse_registration_date_missing_or_broken(self):
        self.assertIsNone(parse_registration_date({}))
        self.assertIsNone(parse_registration_date({"events": []}))
        self.assertIsNone(parse_registration_date({"events": [{"eventAction": "registration", "eventDate": "xx"}]}))


if __name__ == "__main__":
    unittest.main()
