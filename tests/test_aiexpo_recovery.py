"""AI EXPO recovery through an independent, public exhibition record."""
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))
from collectors.opportunities import pipeline, rules, urlsafe
from collectors.opportunities.errors import FetchError, StructureError
from collectors.opportunities.sources import aiexpo
from collectors.opportunities.sources.base import SourceSpec
from test_opportunities import FakeFetcher, FakeResp, OK_ROBOTS, fixture, make_fetcher

ALTERNATE = "https://www.showala.com/ex/ex_detail.php?idx=4273"
NOW = datetime(2026, 10, 12, 8, 0, tzinfo=timezone.utc)
NOW_ISO = "2026-10-12T08:00:00Z"


class AiExpoRecoveryTest(unittest.TestCase):
    def collect(self, html=None, primary=None):
        f = FakeFetcher({aiexpo.OVERVIEW_URL: primary or FetchError("blocked", "robots HTTP 202"),
                         ALTERNATE: html or fixture("aiexpo_showala.html")})
        return aiexpo.collect(f, NOW), f

    def test_network_failure_recovers_with_observed_provenance_and_same_identity(self):
        result, f = self.collect()
        raw = result.items[0]
        self.assertEqual(raw["sourceUrl"], ALTERNATE)
        self.assertEqual(raw["url"], aiexpo.OVERVIEW_URL)
        self.assertIn("SHOWALA", raw["dateNote"])
        self.assertIn("SHOWALA", result.message)
        self.assertEqual((raw["startDate"], raw["endDate"]), ("2027-04-14", "2027-04-16"))
        self.assertEqual(raw["title"], "AI EXPO KOREA 2027 (국제인공지능대전)")
        self.assertIsNone(raw["deadlineDate"])
        self.assertEqual(raw["fee"], rules.UNKNOWN_TEXT)
        self.assertEqual(f.calls, [aiexpo.OVERVIEW_URL, ALTERNATE])
        primary = aiexpo.collect(FakeFetcher({aiexpo.OVERVIEW_URL: fixture("aiexpo_overview.html")}), NOW).items[0]
        before = rules.normalize_item(primary, "aiexpo", NOW_ISO)
        after = rules.normalize_item(raw, "aiexpo", NOW_ISO)
        self.assertEqual(before["id"], after["id"])
        self.assertTrue(rules.meets_contract(after))

    def test_primary_success_does_not_fetch_alternate(self):
        _, f = self.collect(primary=fixture("aiexpo_overview.html"))
        self.assertEqual(f.calls, [aiexpo.OVERVIEW_URL])

    def test_primary_structure_error_is_not_hidden(self):
        with self.assertRaises(StructureError):
            self.collect(primary="<main>Missing event table</main>")

    def test_alternate_rejects_wrong_event_year_dates_and_expired_record(self):
        base = fixture("aiexpo_showala.html")
        for html in (
            base.replace("AI EXPO KOREA", "AI EXPO TOKYO"),
            base.replace("국제인공지능대전", "다른 전시회"),
            base.replace("https://aiexpo.co.kr/", "https://evil.example/"),
            base.replace("AI EXPO KOREA 2027", "AI EXPO KOREA 2026"),
            base.replace("2027-04-14", "2027-04-30"),
            base.replace("2027-04-14", "2027-04-44"),
            base.replace("2027-04-14", "04-14"),
            base.replace("2027", "2026"),
        ):
            with self.subTest(html=html[:60]), self.assertRaises(StructureError):
                self.collect(html)

    def test_alternate_year_is_read_from_page(self):
        result, _ = self.collect(fixture("aiexpo_showala.html").replace("2027", "2028"))
        self.assertEqual(result.items[0]["startDate"], "2028-04-14")

    def test_both_network_failures_preserve_previous_data(self):
        primary = aiexpo.collect(FakeFetcher({aiexpo.OVERVIEW_URL: fixture("aiexpo_overview.html")}), NOW).items[0]
        item = rules.normalize_item(primary, "aiexpo", NOW_ISO)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "opportunities.json"
            old = {"schemaVersion": 2, "updatedAt": NOW_ISO, "lastAttemptAt": NOW_ISO,
                   "items": [item], "sources": []}
            output.write_text(json.dumps(old), encoding="utf-8")
            before = output.read_bytes()
            f = FakeFetcher({aiexpo.OVERVIEW_URL: FetchError("blocked", "202"),
                             ALTERNATE: FetchError("blocked", "robots denied")})
            report = pipeline.run(output, sources=[SourceSpec(aiexpo.SOURCE_ID, aiexpo.SOURCE_NAME,
                aiexpo.SOURCE_URL, aiexpo.collect)], fetcher=f, now=NOW)
            self.assertFalse(report["updated"])
            self.assertEqual(output.read_bytes(), before)

    def test_allowlist_is_exact(self):
        self.assertTrue(urlsafe.is_fetch_allowed(ALTERNATE))
        for host in ("showala.com", "evil.showala.com", "www.showala.com.evil.example"):
            self.assertFalse(urlsafe.is_fetch_allowed("https://" + host + "/"))

    def test_real_fetcher_never_fetches_content_after_robots_challenge(self):
        f, session, _ = make_fetcher({
            "https://aiexpo.co.kr/robots.txt": FakeResp(202, b"<html>challenge</html>"),
            "https://www.showala.com/robots.txt": OK_ROBOTS,
            ALTERNATE: FakeResp(200, fixture("aiexpo_showala.html").encode("utf-8")),
        })
        result = aiexpo.collect(f, NOW)
        self.assertEqual(len(result.items), 1)
        self.assertNotIn(aiexpo.OVERVIEW_URL, session.calls)

    def test_alternate_robots_deny_still_blocks(self):
        f, session, _ = make_fetcher({
            "https://aiexpo.co.kr/robots.txt": FakeResp(202, b"challenge"),
            "https://www.showala.com/robots.txt": FakeResp(200, b"User-agent: *\nDisallow: /\n"),
        })
        with self.assertRaises(FetchError):
            aiexpo.collect(f, NOW)
        self.assertNotIn(ALTERNATE, session.calls)

    def test_alternate_redirect_does_not_expand_allowlist(self):
        f, session, _ = make_fetcher({
            "https://aiexpo.co.kr/robots.txt": FakeResp(202, b"challenge"),
            "https://www.showala.com/robots.txt": OK_ROBOTS,
            ALTERNATE: FakeResp(302, b"", {"Location": "https://evil.example/"}),
        })
        with self.assertRaises(FetchError) as cm:
            aiexpo.collect(f, NOW)
        self.assertEqual(cm.exception.status, "blocked")
        self.assertNotIn("https://evil.example/", session.calls)

    def test_alternate_keeps_response_size_cap(self):
        f, _, _ = make_fetcher({
            "https://aiexpo.co.kr/robots.txt": FakeResp(202, b"challenge"),
            "https://www.showala.com/robots.txt": OK_ROBOTS,
            ALTERNATE: FakeResp(200, b"x" * 2_600_000),
        })
        with self.assertRaises(FetchError):
            aiexpo.collect(f, NOW)


if __name__ == "__main__":
    unittest.main()
