"""AI 기회 수집 파이프라인 테스트 — 네트워크 없이 fixture/가짜 세션만 사용한다."""
import copy
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from collectors.opportunities import cli, pipeline, robots, rules, urlsafe  # noqa: E402
from collectors.opportunities.errors import ExistingDataError, FetchError, SourceError, StructureError  # noqa: E402
from collectors.opportunities.http import FetchResult, Fetcher  # noqa: E402
from collectors.opportunities.sources import aisummit, dacon, devpost, wevity  # noqa: E402
from collectors.opportunities.sources.base import CollectResult, SourceSpec  # noqa: E402

FIX = ROOT / "tests" / "fixtures" / "backend"
UTC = timezone.utc
NOW = datetime(2026, 10, 2, 8, 0, 0, tzinfo=UTC)
NOW_ISO = "2026-10-02T08:00:00Z"
REQUIRED_KEYS = {
    "id", "kind", "title", "organizer", "description", "tags", "mode", "region", "country",
    "startDate", "endDate", "registrationStartDate", "deadlineDate", "deadlineAt", "eligibility",
    "eligibilityVerified", "fee", "prize", "url", "sourceUrl", "sourceId", "sourceName",
    "verifiedAt", "dateNote", "sourceStatus", "stale",
}


def fixture(name):
    return (FIX / name).read_text(encoding="utf-8")


def make_raw(**over):
    raw = {
        "kind": "hackathon", "title": "AI 해커톤 테스트", "organizer": "테스트 주최", "description": "테스트용 설명",
        "tags": ["AI"], "mode": "online", "region": "국내 온라인", "country": "KR",
        "startDate": "2026-10-10", "endDate": "2026-10-20", "registrationStartDate": None,
        "deadlineDate": "2026-10-15", "deadlineAt": None, "eligibility": "확인 필요",
        "eligibilityVerified": False, "fee": "확인 필요", "prize": None,
        "url": "https://dacon.io/competitions/official/1/overview/",
        "sourceUrl": "https://dacon.io/competitions/official/1/overview/",
        "sourceName": "DACON", "dateNote": None, "sourceStatus": "open",
    }
    raw.update(over)
    return raw


def make_item(source_id="dacon", n=1, verified="2026-09-01T00:00:00Z", **over):
    raw = make_raw(
        title=f"AI 해커톤 {n}",
        url=f"https://dacon.io/competitions/official/{n}/overview/",
        sourceUrl=f"https://dacon.io/competitions/official/{n}/overview/",
        **over,
    )
    item = rules.normalize_item(raw, source_id, verified)
    assert item is not None, raw
    return item


class FakeFetcher:
    def __init__(self, pages):
        self.pages = pages
        self.calls = []

    def get(self, url, prefix_bytes=None):
        self.calls.append(url)
        value = self.pages.get(url)
        if value is None:
            raise FetchError("error", f"no page {url}")
        if isinstance(value, Exception):
            raise value
        return FetchResult(text=value, url=url)


class FakeResp:
    def __init__(self, status=200, body=b"", headers=None):
        self.status_code = status
        self.headers = headers or {}
        self._body = body
        self.encoding = None

    def iter_content(self, chunk_size=65536):
        for i in range(0, len(self._body), chunk_size):
            yield self._body[i:i + chunk_size]

    def close(self):
        pass


class FakeSession:
    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def get(self, url, headers=None, timeout=None, allow_redirects=False, stream=True):
        self.calls.append(url)
        value = self.routes.get(url)
        if value is None:
            return FakeResp(404, b"")
        if isinstance(value, Exception):
            raise value
        return value


def make_fetcher(routes, **kw):
    clock = {"t": 0.0}
    sleeps = []

    def sleep(s):
        sleeps.append(s)
        clock["t"] += s

    session = FakeSession(routes)
    fetcher = Fetcher(session=session, sleep=sleep, monotonic=lambda: clock["t"], **kw)
    return fetcher, session, sleeps


OK_ROBOTS = FakeResp(200, b"User-agent: *\nDisallow:\n")


def spec(source_id, items=None, error=None):
    def collect(fetcher, now, max_items):
        if error is not None:
            raise error
        return CollectResult(items=list(items or []), message="ok")

    return SourceSpec(id=source_id, name=source_id.upper(), url=f"https://{source_id}.example/list", collect=collect)


class RulesTest(unittest.TestCase):
    def test_ai_word_boundary(self):
        for text in ("chair design", "paid internship", "Thailand trip", "Maintain Mail", "AI2Bot"):
            self.assertFalse(rules.is_ai_related(text), text)

    def test_ai_positive(self):
        for text in ("AI hackathon", "2026 AI·SW 경진대회", "인공지능 경진대회", "LLM Agent Jam", "생성형 모델 공모전", "머신러닝 챌린지", "AI로 금산 공모전"):
            self.assertTrue(rules.is_ai_related(text), text)

    def test_ai_in_tags_or_description(self):
        self.assertTrue(rules.is_ai_related("데이터 경진대회", ["Machine Learning/AI"]))
        self.assertTrue(rules.is_ai_related("데이터 경진대회", [], "딥러닝 모델을 만드는 대회"))
        self.assertFalse(rules.is_ai_related("데이터 경진대회", ["Web"], "chair"))

    def test_kind_priority(self):
        self.assertEqual(rules.classify_kind("AI 해커톤 공모전"), "hackathon")
        self.assertEqual(rules.classify_kind("AI 경진대회"), "contest")
        self.assertEqual(rules.classify_kind("AI Summit Seoul 컨퍼런스"), "event")
        self.assertIsNone(rules.classify_kind("그냥 AI 소개"))

    def test_kind_excludes_course_and_job_but_not_hackathon_with_job_tag(self):
        self.assertIsNone(rules.classify_kind("AI 부트캠프 수강생 모집"))
        self.assertIsNone(rules.classify_kind("AI 개발자 신입 채용 공고"))
        self.assertEqual(rules.classify_kind("채용연계 AI 해커톤"), "hackathon")

    def test_mask_contacts(self):
        text = "문의 help@example.com 010-1234-5678 또는 02-123-4567, +82 10 1234 5678 이다"
        masked = rules.mask_contacts(text)
        for bad in ("@", "010-1234", "02-123-4567", "1234 5678"):
            self.assertNotIn(bad, masked)
        keep = "접수 2026-09-21 ~ 2026-10-10 상금 1,000만 원"
        self.assertEqual(rules.mask_contacts(keep), keep)

    def test_parse_date(self):
        self.assertEqual(rules.parse_date("2026-10-02"), "2026-10-02")
        self.assertEqual(rules.parse_date("2026.8.1"), "2026-08-01")
        for bad in ("2026-02-30", "2026-13-01", "26-10-01", "", None, "내일", 20261002):
            self.assertIsNone(rules.parse_date(bad), bad)

    def test_exact_timezone_to_seoul_date(self):
        self.assertEqual(rules.seoul_date_from_iso("2026-10-26T17:00:00-04:00"), "2026-10-27")
        self.assertEqual(rules.seoul_date_from_iso("2026-10-26T23:59:00+09:00"), "2026-10-26")
        self.assertIsNone(rules.seoul_date_from_iso("2026-10-26T17:00:00"))
        self.assertIsNone(rules.seoul_date_from_iso("garbage"))

    def test_korea_allowed(self):
        yes = [
            "All countries/territories, excluding standard exceptions (Brazil, Crimea, Cuba, Iran, North Korea, Quebec, Russia)",
            "Worldwide",
            "Residents of Japan, South Korea, Singapore",
            "All countries/territories, excluding Korea, Democratic People's Republic of",
        ]
        no = [
            "All countries/territories, excluding standard exceptions (Cuba, South Korea, Iran)",
            "All countries/territories, excluding Republic of Korea",
            "Residents of United States, Canada",
            "All countries/territories, excluding standard exceptions",
            "",
        ]
        for t in yes:
            self.assertTrue(rules.korea_allowed(t), t)
        for t in no:
            self.assertFalse(rules.korea_allowed(t), t)

    def test_normalize_valid_has_exact_schema_keys(self):
        item = rules.normalize_item(make_raw(), "dacon", NOW_ISO)
        self.assertEqual(set(item), REQUIRED_KEYS)
        self.assertEqual(item["sourceId"], "dacon")
        self.assertEqual(item["verifiedAt"], NOW_ISO)
        self.assertFalse(item["stale"])
        self.assertIsNone(item["prize"])
        again = rules.normalize_item(make_raw(), "dacon", "2026-12-01T00:00:00Z")
        self.assertEqual(item["id"], again["id"])

    def test_normalize_rejections(self):
        cases = {
            "non-ai": make_raw(title="의자 디자인 공모전", tags=[], description=""),
            "invalid date": make_raw(startDate="2026-02-30"),
            "end before start": make_raw(startDate="2026-10-20", endDate="2026-10-10"),
            "naive deadlineAt": make_raw(deadlineAt="2026-10-15T10:00:00"),
            "http url": make_raw(url="http://dacon.io/x"),
            "javascript url": make_raw(url="javascript:alert(1)"),
            "userinfo url": make_raw(url="https://a:b@dacon.io/x"),
            "bad source url": make_raw(sourceUrl="ftp://dacon.io/x"),
            "overseas offline": make_raw(country="GLOBAL", mode="offline", eligibilityVerified=True),
            "overseas hybrid": make_raw(country="GLOBAL", mode="hybrid", eligibilityVerified=True),
            "overseas unverified": make_raw(country="GLOBAL", mode="online", eligibilityVerified=False),
            "bootcamp": make_raw(title="AI 부트캠프 수강생 모집"),
            "bad kind": make_raw(kind="news"),
        }
        for name, raw in cases.items():
            self.assertIsNone(rules.normalize_item(raw, "dacon", NOW_ISO), name)

    def test_normalize_overseas_online_verified_ok(self):
        raw = make_raw(country="GLOBAL", mode="online", eligibilityVerified=True, region="해외 온라인")
        self.assertIsNotNone(rules.normalize_item(raw, "devpost", NOW_ISO))

    def test_deadline_at_overrides_deadline_date_with_seoul_date(self):
        raw = make_raw(deadlineAt="2026-10-26T17:00:00-04:00", deadlineDate="2026-10-26")
        item = rules.normalize_item(raw, "devpost", NOW_ISO)
        self.assertEqual(item["deadlineDate"], "2026-10-27")
        self.assertEqual(item["deadlineAt"], "2026-10-26T17:00:00-04:00")

    def test_normalize_masks_contacts_and_shortens_description(self):
        raw = make_raw(description="문의 a@b.com 010-1111-2222 " + "설명 " * 300, organizer="주최 (c@d.org)")
        item = rules.normalize_item(raw, "dacon", NOW_ISO)
        blob = json.dumps(item, ensure_ascii=False)
        self.assertNotIn("@", blob)
        self.assertNotIn("010-1111", blob)
        self.assertLessEqual(len(item["description"]), 240)

    def test_normalize_keeps_unknowns_null_and_strips_html(self):
        item = rules.normalize_item(make_raw(startDate=None, endDate=None, deadlineDate=None, title="<b>AI</b> 해커톤"), "dacon", NOW_ISO)
        self.assertIsNone(item["startDate"])
        self.assertIsNone(item["deadlineDate"])
        self.assertNotIn("<", item["title"])


class UrlSafetyTest(unittest.TestCase):
    def test_safe_https(self):
        self.assertTrue(urlsafe.is_safe_https_url("https://dacon.io/competitions"))
        self.assertTrue(urlsafe.is_safe_https_url("https://app.notion.com/p/x"))
        for bad in (
            "http://dacon.io/", "https://user:pw@dacon.io/", "https://dacon.io:8443/", "https://127.0.0.1/",
            "https://localhost/", "https://[::1]/", "https://10.0.0.5/", "javascript:alert(1)", "//dacon.io/x", "", None,
        ):
            self.assertFalse(urlsafe.is_safe_https_url(bad), bad)

    def test_fetch_allowlist(self):
        for ok in ("https://devpost.com/api/hackathons", "https://learn-ai-basics.devpost.com/", "https://www.wevity.com/", "https://wevity.com/",
                   "https://dacon.io/competitions", "https://www.dacon.io/", "https://www.aisummit.co.kr/", "https://aisummit.co.kr/"):
            self.assertTrue(urlsafe.is_fetch_allowed(ok), ok)
        for bad in ("https://evil.com/", "https://devpost.com.evil.com/", "https://notdevpost.com/", "http://dacon.io/", "https://aisummit.ai.kr/"):
            self.assertFalse(urlsafe.is_fetch_allowed(bad), bad)

    def test_canonical_url(self):
        a = urlsafe.canonical_url("HTTPS://Dacon.IO:443/competitions/official/1/overview/?utm_source=x#frag")
        b = urlsafe.canonical_url("https://dacon.io/competitions/official/1/overview")
        self.assertEqual(a, b)


class RobotsTest(unittest.TestCase):
    SQUARESPACE = "User-agent: GPTBot\nDisallow: /\n\nUser-agent: *\nDisallow: /api/\nAllow: /api/ui-extensions/\nDisallow:/*?format=json\n"

    def test_wildcard_and_longest_match(self):
        r = robots.RobotsRules(self.SQUARESPACE)
        self.assertTrue(r.allowed("ai-opportunity-board", "/"))
        self.assertFalse(r.allowed("ai-opportunity-board", "/api/x"))
        self.assertTrue(r.allowed("ai-opportunity-board", "/api/ui-extensions/a"))
        self.assertFalse(r.allowed("ai-opportunity-board", "/page?format=json"))

    def test_empty_disallow_allows_all(self):
        self.assertTrue(robots.RobotsRules("User-agent: *\nDisallow:\n").allowed("x", "/anything"))

    def test_specific_group_beats_wildcard(self):
        r = robots.RobotsRules("User-agent: ai-opportunity-board\nDisallow: /\n\nUser-agent: *\nDisallow:\n")
        self.assertFalse(r.allowed("ai-opportunity-board/1.0", "/"))


class FetcherTest(unittest.TestCase):
    def test_rejects_disallowed_host_and_http(self):
        fetcher, session, _ = make_fetcher({})
        for url in ("https://evil.com/", "http://dacon.io/"):
            with self.assertRaises(FetchError) as cm:
                fetcher.get(url)
            self.assertEqual(cm.exception.status, "blocked")
        self.assertEqual(session.calls, [])

    def test_fetch_ok_with_robots_cache_and_throttle(self):
        routes = {
            "https://dacon.io/robots.txt": OK_ROBOTS,
            "https://dacon.io/a": FakeResp(200, "안녕".encode("utf-8")),
            "https://dacon.io/b": FakeResp(200, b"b"),
        }
        fetcher, session, sleeps = make_fetcher(routes)
        self.assertEqual(fetcher.get("https://dacon.io/a").text, "안녕")
        fetcher.get("https://dacon.io/b")
        self.assertEqual(session.calls.count("https://dacon.io/robots.txt"), 1)
        self.assertEqual(len(session.calls), 3)
        self.assertGreaterEqual(sum(sleeps), 2.0)

    def test_robots_disallow_blocks(self):
        routes = {"https://dacon.io/robots.txt": FakeResp(200, b"User-agent: *\nDisallow: /competitions\n"), "https://dacon.io/competitions": FakeResp(200, b"x")}
        fetcher, session, _ = make_fetcher(routes)
        with self.assertRaises(FetchError) as cm:
            fetcher.get("https://dacon.io/competitions")
        self.assertEqual(cm.exception.status, "blocked")
        self.assertNotIn("https://dacon.io/competitions", session.calls)

    def test_robots_errors_are_blocked_not_permissive(self):
        import requests
        for robots_resp in (requests.Timeout("slow"), FakeResp(500, b""), FakeResp(403, b"no")):
            routes = {"https://dacon.io/robots.txt": robots_resp, "https://dacon.io/a": FakeResp(200, b"x")}
            fetcher, session, _ = make_fetcher(routes)
            with self.assertRaises(FetchError) as cm:
                fetcher.get("https://dacon.io/a")
            self.assertEqual(cm.exception.status, "blocked")
            self.assertNotIn("https://dacon.io/a", session.calls)

    def test_robots_404_means_no_rules(self):
        routes = {"https://dacon.io/robots.txt": FakeResp(404, b""), "https://dacon.io/a": FakeResp(200, b"x")}
        fetcher, _, _ = make_fetcher(routes)
        self.assertEqual(fetcher.get("https://dacon.io/a").text, "x")

    def test_redirect_to_unsafe_host_rejected(self):
        routes = {
            "https://dacon.io/robots.txt": OK_ROBOTS,
            "https://dacon.io/a": FakeResp(302, b"", {"Location": "https://evil.com/x"}),
        }
        fetcher, session, _ = make_fetcher(routes)
        with self.assertRaises(FetchError):
            fetcher.get("https://dacon.io/a")
        self.assertNotIn("https://evil.com/x", session.calls)

    def test_redirect_downgrade_and_loop_capped(self):
        routes = {
            "https://dacon.io/robots.txt": OK_ROBOTS,
            "https://dacon.io/a": FakeResp(302, b"", {"Location": "http://dacon.io/b"}),
            "https://dacon.io/loop": FakeResp(302, b"", {"Location": "https://dacon.io/loop"}),
        }
        fetcher, _, _ = make_fetcher(routes, max_redirects=3)
        with self.assertRaises(FetchError):
            fetcher.get("https://dacon.io/a")
        with self.assertRaises(FetchError) as cm:
            fetcher.get("https://dacon.io/loop")
        self.assertIn("redirect", str(cm.exception).lower())

    def test_safe_redirect_followed(self):
        routes = {
            "https://dacon.io/robots.txt": OK_ROBOTS,
            "https://dacon.io/a": FakeResp(301, b"", {"Location": "/b"}),
            "https://dacon.io/b": FakeResp(200, b"done"),
        }
        fetcher, _, _ = make_fetcher(routes)
        result = fetcher.get("https://dacon.io/a")
        self.assertEqual((result.text, result.url), ("done", "https://dacon.io/b"))

    def test_response_size_cap_and_http_error_and_timeout(self):
        import requests
        routes = {
            "https://dacon.io/robots.txt": OK_ROBOTS,
            "https://dacon.io/big": FakeResp(200, b"x" * 5000),
            "https://dacon.io/err": FakeResp(503, b""),
            "https://dacon.io/slow": requests.Timeout("t"),
        }
        fetcher, _, _ = make_fetcher(routes, max_bytes=1000)
        for path in ("big", "err", "slow"):
            with self.assertRaises(FetchError) as cm:
                fetcher.get(f"https://dacon.io/{path}")
            self.assertEqual(cm.exception.status, "error", path)


class DevpostTest(unittest.TestCase):
    def pages(self, detail="devpost_detail_basics.html"):
        return {devpost.LISTING_URL: fixture("devpost_listing.json"), "https://learn-ai-basics.devpost.com/": fixture(detail)}

    def test_listing_filters_ai_online_non_invite(self):
        cands = devpost.parse_listing(fixture("devpost_listing.json"))
        self.assertEqual([c["url"] for c in cands], ["https://learn-ai-basics.devpost.com/"])

    def test_listing_structure_error_and_legit_empty(self):
        with self.assertRaises(StructureError):
            devpost.parse_listing('{"error": "x"}')
        with self.assertRaises(StructureError):
            devpost.parse_listing("<html>blocked</html>")
        self.assertEqual(devpost.parse_listing('{"hackathons": [], "meta": {}}'), [])

    def test_collect_exact_deadline_and_korea_evidence(self):
        result = devpost.collect(FakeFetcher(self.pages()), NOW, 10)
        self.assertEqual(len(result.items), 1)
        raw = result.items[0]
        self.assertEqual(raw["deadlineAt"], "2026-10-26T17:00:00-04:00")
        self.assertEqual(raw["deadlineDate"], "2026-10-27")
        self.assertEqual(raw["startDate"], "2026-09-22")
        self.assertEqual(raw["endDate"], "2026-10-27")
        self.assertIn("-04:00", raw["dateNote"])
        self.assertIn("Ages 18+", raw["eligibility"])
        self.assertIn("North Korea", raw["eligibility"])
        self.assertTrue(raw["eligibilityVerified"])
        self.assertEqual((raw["country"], raw["mode"], raw["kind"]), ("GLOBAL", "online", "hackathon"))
        self.assertEqual(raw["prize"], "$2,500")
        self.assertEqual(raw["sourceStatus"], "open")
        self.assertEqual(raw["fee"], "확인 필요")
        item = rules.normalize_item(raw, "devpost", NOW_ISO)
        self.assertIsNotNone(item)

    def test_zero_prize_is_none(self):
        listing = json.loads(fixture("devpost_listing.json"))
        listing["hackathons"][0]["prize_amount"] = "$<span data-currency-value>0</span>"
        self.assertIsNone(devpost.parse_listing(json.dumps(listing))[0]["prize"])

    def test_north_korea_exclusion_is_not_south_korea_exclusion(self):
        self.assertTrue(rules.korea_allowed("All countries/territories, excluding (North Korea)"))

    def test_south_korea_excluded_is_skipped(self):
        result = devpost.collect(FakeFetcher(self.pages("devpost_detail_korea_excluded.html")), NOW, 10)
        self.assertEqual(result.items, [])
        self.assertIn("1", result.message)

    def test_restricted_without_korea_skipped_and_with_korea_kept(self):
        self.assertEqual(devpost.collect(FakeFetcher(self.pages("devpost_detail_restricted.html")), NOW, 10).items, [])
        kept = devpost.collect(FakeFetcher(self.pages("devpost_detail_restricted_korea.html")), NOW, 10).items
        self.assertEqual(len(kept), 1)
        self.assertIn("Students only", kept[0]["eligibility"])
        self.assertEqual(kept[0]["deadlineDate"], "2026-11-01")

    def test_detail_fetch_failure_for_all_is_error(self):
        pages = {devpost.LISTING_URL: fixture("devpost_listing.json"), "https://learn-ai-basics.devpost.com/": FetchError("error", "boom")}
        with self.assertRaises(SourceError):
            devpost.collect(FakeFetcher(pages), NOW, 10)

    def test_max_items_caps_detail_requests(self):
        listing = json.loads(fixture("devpost_listing.json"))
        base = listing["hackathons"][0]
        listing["hackathons"] = [dict(base, id=i, url=f"https://h{i}.devpost.com/") for i in range(30)]
        pages = {devpost.LISTING_URL: json.dumps(listing)}
        for i in range(30):
            pages[f"https://h{i}.devpost.com/"] = fixture("devpost_detail_basics.html")
        fetcher = FakeFetcher(pages)
        result = devpost.collect(fetcher, NOW, 3)
        self.assertEqual(len(result.items), 3)
        self.assertEqual(len(fetcher.calls), 4)


class DaconTest(unittest.TestCase):
    def test_listing_rows_and_status(self):
        rows = dacon.parse_listing(fixture("dacon_listing.html"))
        by_id = {r["cptId"]: r for r in rows}
        self.assertEqual(set(by_id), {"236771", "236749", "236767", "236800"})
        self.assertEqual(by_id["236771"]["sourceStatus"], "open")
        self.assertEqual(by_id["236749"]["sourceStatus"], "closed")
        self.assertIn("해운물류", by_id["236771"]["tags"])

    def test_listing_structure_error(self):
        with self.assertRaises(StructureError):
            dacon.parse_listing("<html><body>점검중</body></html>")
        self.assertEqual(dacon.parse_listing('<div class="official-comp"></div>'), [])

    def test_detail_parses_inert_strings_only(self):
        d = dacon.parse_detail(fixture("dacon_overview.html"))
        self.assertEqual(d["submission_end"], "2026-11-01 10:00:00")
        self.assertEqual(d["period_start"], "2026-10-12 10:00:00")
        self.assertEqual(d["prize_info"], "950 만원")
        self.assertNotIn("description", d)
        with self.assertRaises(StructureError):
            dacon.parse_detail("<html>no script</html>")

    def test_infer_mode(self):
        self.assertEqual(dacon.infer_mode("Aimers 9기 : AI 오프라인 해커톤", ""), "offline")
        self.assertEqual(dacon.infer_mode("Aimers 9기 : AI 온라인 해커톤", ""), "online")
        self.assertEqual(dacon.infer_mode("AI 경진대회", "알고리즘 | 코드 제출 평가"), "online")
        self.assertEqual(dacon.infer_mode("AI 경진대회", "정형"), "unknown")

    def test_collect_builds_submission_deadline_not_merge_deadline(self):
        pages = {
            dacon.LISTING_URL: fixture("dacon_listing.html"),
            dacon.detail_url("236771"): fixture("dacon_overview.html"),
        }
        result = dacon.collect(FakeFetcher(pages), NOW, 20)
        self.assertEqual(len(result.items), 1)
        raw = result.items[0]
        self.assertEqual(raw["deadlineAt"], "2026-11-01T10:00:00+09:00")
        self.assertEqual(raw["deadlineDate"], "2026-11-01")
        self.assertNotEqual(raw["deadlineDate"], "2026-10-26")
        self.assertEqual((raw["startDate"], raw["endDate"]), ("2026-10-12", "2026-11-02"))
        self.assertIsNone(raw["registrationStartDate"])
        self.assertIn("제출 마감", raw["dateNote"])
        self.assertEqual(raw["sourceStatus"], "open")
        self.assertEqual(raw["mode"], "online")
        self.assertEqual(raw["prize"], "950 만원")
        self.assertEqual((raw["eligibility"], raw["eligibilityVerified"]), ("확인 필요", False))
        self.assertEqual(raw["kind"], "contest")
        self.assertIsNotNone(rules.normalize_item(raw, "dacon", NOW_ISO))

    def test_submission_end_before_start_is_not_used_as_deadline(self):
        row = {"cptId": "1", "title": "AI 경진대회", "tags": [], "sourceStatus": "unknown"}
        raw = dacon.build_raw(row, {"period_start": "2026-07-06 10:00:00", "period_end": "2026-08-14 10:00:00", "submission_end": "2025-07-01 23:59:59"})
        self.assertIsNone(raw["deadlineAt"])
        self.assertIsNone(raw["deadlineDate"])
        self.assertEqual(raw["startDate"], "2026-07-06")

    def test_collect_all_detail_failures_is_error(self):
        pages = {dacon.LISTING_URL: fixture("dacon_listing.html")}
        with self.assertRaises(SourceError):
            dacon.collect(FakeFetcher(pages), NOW, 20)

    def test_collect_limit_and_priority(self):
        rows = "".join(
            f'<a href="/competitions/official/{i}/overview/"><p class="name">AI 경진대회 {i}</p><p class="keyword">x</p><div class="dday">{"마감" if i < 5 else "참가신청중"}</div></a>'
            for i in range(1, 41)
        )
        pages = {dacon.LISTING_URL: f'<div class="official-comp">{rows}</div>'}
        fetcher = FakeFetcher(pages)
        with self.assertRaises(SourceError):
            dacon.collect(fetcher, NOW, 20)
        details = [c for c in fetcher.calls if "/overview/" in c]
        self.assertEqual(len(details), 20)
        self.assertTrue(all(int(c.split("/official/")[1].split("/")[0]) >= 5 for c in details))


class WevityTest(unittest.TestCase):
    def test_listing_requires_search_param(self):
        self.assertIn("sp=name", wevity.LISTING_URL)
        self.assertIn("sw=AI", wevity.LISTING_URL)

    def test_listing_rows(self):
        rows = wevity.parse_listing(fixture("wevity_listing.html"))
        self.assertEqual([r["ix"] for r in rows], ["111322", "111306", "999001", "999002"])
        self.assertEqual(rows[0]["organizer"], "하이어에이아이")
        self.assertEqual(rows[1]["sourceStatus"], "open")

    def test_listing_empty_scaffold_ok_but_missing_scaffold_error(self):
        self.assertEqual(wevity.parse_listing(fixture("wevity_empty.html")), [])
        with self.assertRaises(StructureError):
            wevity.parse_listing("<html><body>forbidden</body></html>")

    def test_detail(self):
        d = wevity.parse_detail(fixture("wevity_detail.html"))
        self.assertEqual(d["period"], ("2026-09-21", "2026-10-10"))
        self.assertEqual(d["target"], "대학생")
        self.assertEqual(d["homepage"], "https://app.notion.com/p/2026-SNU-Croche-AI-3e1fbb01ebbb815ca8f6eab806ecbfcc")
        with self.assertRaises(StructureError):
            wevity.parse_detail("<html>x</html>")

    def test_detail_prize_without_amount_and_own_site_homepage(self):
        html = fixture("wevity_detail.html").replace("1천만원이하", "다양한 혜택").replace(
            "https://app.notion.com/p/2026-SNU-Croche-AI-3e1fbb01ebbb815ca8f6eab806ecbfcc", "https://www.wevity.com/?c=find&gbn=view&ix=1")
        d = wevity.parse_detail(html)
        self.assertEqual(d["prize"], "다양한 혜택 / 1등 500만원")
        self.assertIsNone(d["homepage"])

    def test_build_raw_reads_mode_deadline_time_and_fee_from_body(self):
        html = fixture("wevity_detail.html").replace(
            "<div>문의:", "<div>■ 접수기간 : 2026. 9. 21.(월) ~ 10. 10.(토) 18:00까지</div><div>- 접수 방법 : 구글폼 제출</div>"
                          "<div>- 참가비: 무료</div><div>문의:")
        row = {"ix": "111322", "title": "2026 AI 활용 숏폼 영상 공모전", "organizer": None, "sourceStatus": "open"}
        raw = wevity.build_raw(row, wevity.parse_detail(html))
        self.assertEqual((raw["mode"], raw["region"]), ("online", "국내 온라인"))
        self.assertEqual(raw["deadlineAt"], "2026-10-10T18:00:00+09:00")
        self.assertEqual(raw["fee"], "무료")
        self.assertIn("본문", raw["dateNote"])
        plain = wevity.build_raw(row, wevity.parse_detail(fixture("wevity_detail.html")))
        self.assertEqual((plain["mode"], plain["deadlineAt"], plain["fee"]), ("unknown", None, "확인 필요"))

    def test_collect_filters_locally_and_masks(self):
        pages = {wevity.LISTING_URL: fixture("wevity_listing.html"), f"{wevity.LISTING_URL}&gp=2": fixture("wevity_empty.html"),
                 wevity.detail_url("111322"): fixture("wevity_detail.html")}
        fetcher = FakeFetcher(pages)
        result = wevity.collect(fetcher, NOW, 20)
        self.assertEqual(len(result.items), 1)
        raw = result.items[0]
        fetched_ix = " ".join(fetcher.calls)
        self.assertNotIn("999001", fetched_ix)
        self.assertNotIn("999002", fetched_ix)
        self.assertEqual(raw["kind"], "hackathon")
        self.assertEqual((raw["registrationStartDate"], raw["deadlineDate"]), ("2026-09-21", "2026-10-10"))
        self.assertIsNone(raw["deadlineAt"])
        self.assertIn("날짜만", raw["dateNote"])
        self.assertEqual(raw["eligibility"], "대학생")
        self.assertIn("1천만원이하", raw["prize"])
        self.assertTrue(raw["sourceUrl"].endswith("ix=111322"))
        self.assertTrue(raw["url"].startswith("https://app.notion.com/"))
        item = rules.normalize_item(raw, "wevity", NOW_ISO)
        blob = json.dumps(item, ensure_ascii=False)
        self.assertNotIn("@", blob)
        self.assertNotIn("1234-5678", blob)


class AiSummitTest(unittest.TestCase):
    def test_parse_promoted_year_not_title_year(self):
        data = aisummit.parse_main(fixture("aisummit.html"))
        self.assertEqual((data["startDate"], data["endDate"]), ("2027-08-11", "2027-08-13"))
        self.assertEqual(data["titleYear"], "2026")

    def test_ambiguous_year_is_structure_error(self):
        with self.assertRaises(StructureError):
            aisummit.parse_main("<html><title>AI Summit 2026</title><main>행사 안내 준비중</main></html>")

    def test_collect_item(self):
        result = aisummit.collect(FakeFetcher({aisummit.MAIN_URL: fixture("aisummit.html")}), NOW, 20)
        self.assertEqual(len(result.items), 1)
        raw = result.items[0]
        self.assertEqual((raw["kind"], raw["mode"], raw["country"]), ("event", "offline", "KR"))
        self.assertEqual((raw["startDate"], raw["endDate"]), ("2027-08-11", "2027-08-13"))
        self.assertIsNone(raw["deadlineDate"])
        self.assertEqual((raw["fee"], raw["eligibility"]), ("확인 필요", "확인 필요"))
        self.assertIn("DMK Global", raw["organizer"])
        self.assertIn("2026", result.message)
        item = rules.normalize_item(raw, "aisummit", NOW_ISO)
        self.assertIsNotNone(item)
        self.assertNotIn("@", item["description"])


class ValidationTest(unittest.TestCase):
    def doc(self, items=None):
        return {"schemaVersion": 2, "updatedAt": NOW_ISO, "lastAttemptAt": NOW_ISO, "sources": [], "items": items or []}

    def test_valid_and_invalid_documents(self):
        pipeline.validate_document(self.doc([make_item()]))
        bad_docs = []
        d = self.doc(); d["schemaVersion"] = 1; bad_docs.append(d)
        d = self.doc([make_item()]); d["items"][0]["url"] = "http://x.com"; bad_docs.append(d)
        d = self.doc([make_item()]); d["items"][0]["startDate"] = "2026-02-30"; bad_docs.append(d)
        d = self.doc([make_item()]); del d["items"][0]["title"]; bad_docs.append(d)
        d = self.doc([make_item()]); d["items"][0]["kind"] = "news"; bad_docs.append(d)
        d = self.doc([make_item(), make_item()]); bad_docs.append(d)
        for doc in bad_docs:
            with self.assertRaises(ExistingDataError):
                pipeline.validate_document(doc)


class PipelineTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        self.out = self.dir / "opportunities.json"
        self.status = self.dir / "ingest-status.json"
        self.curated = self.dir / "curated.json"

    def run_pipeline(self, specs, now=NOW, **kw):
        return pipeline.run(self.out, status_path=self.status, curated_path=self.curated, fetcher=None, sources=specs, now=now, **kw)

    def raw_for(self, n, **over):
        return make_raw(
            title=f"AI 해커톤 {n}",
            url=f"https://dacon.io/competitions/official/{n}/overview/",
            sourceUrl=f"https://dacon.io/competitions/official/{n}/overview/",
            **over,
        )

    def test_first_run_writes_items_sources_and_status(self):
        report = self.run_pipeline([spec("dacon", [self.raw_for(1), self.raw_for(2)])])
        self.assertTrue(report["updated"])
        doc = json.loads(self.out.read_text(encoding="utf-8"))
        self.assertEqual(doc["schemaVersion"], 2)
        self.assertEqual(doc["updatedAt"], NOW_ISO)
        self.assertEqual(len(doc["items"]), 2)
        src = doc["sources"][0]
        self.assertEqual((src["id"], src["status"], src["itemCount"], src["lastSuccessAt"]), ("dacon", "ok", 2, NOW_ISO))
        status = json.loads(self.status.read_text(encoding="utf-8"))
        self.assertEqual(set(status), {"lastAttemptAt", "sources"})
        self.assertEqual(status["sources"][0]["status"], "ok")
        self.assertEqual(list(self.dir.glob("*.tmp")), [])

    def test_all_fail_preserves_bytes_and_records_status(self):
        self.run_pipeline([spec("dacon", [self.raw_for(1)])])
        before = self.out.read_bytes()
        later = NOW + timedelta(days=1)
        report = self.run_pipeline([spec("dacon", error=SourceError("error", "HTTP 500"))], now=later)
        self.assertFalse(report["updated"])
        self.assertEqual(self.out.read_bytes(), before)
        status = json.loads(self.status.read_text(encoding="utf-8"))
        self.assertEqual(status["lastAttemptAt"], "2026-10-03T08:00:00Z")
        s = status["sources"][0]
        self.assertEqual((s["status"], s["lastSuccessAt"], s["message"]), ("error", NOW_ISO, "HTTP 500"))

    def test_all_fail_without_existing_file_creates_no_opportunities(self):
        report = self.run_pipeline([spec("dacon", error=SourceError("blocked", "robots"))])
        self.assertFalse(report["updated"])
        self.assertFalse(self.out.exists())
        self.assertEqual(json.loads(self.status.read_text(encoding="utf-8"))["sources"][0]["status"], "blocked")

    def test_partial_failure_preserves_failed_source_rows(self):
        self.run_pipeline([spec("dacon", [self.raw_for(1)]), spec("wevity", [self.raw_for(2)])])
        old = json.loads(self.out.read_text(encoding="utf-8"))
        old_wevity = [i for i in old["items"] if i["sourceId"] == "wevity"]
        later = NOW + timedelta(days=1)
        self.run_pipeline([spec("dacon", [self.raw_for(3)]), spec("wevity", error=SourceError("error", "down"))], now=later)
        doc = json.loads(self.out.read_text(encoding="utf-8"))
        self.assertEqual([i for i in doc["items"] if i["sourceId"] == "wevity"], old_wevity)
        dacon_titles = [i["title"] for i in doc["items"] if i["sourceId"] == "dacon"]
        self.assertIn("AI 해커톤 3", dacon_titles)
        srcs = {s["id"]: s for s in doc["sources"]}
        self.assertEqual(srcs["dacon"]["status"], "ok")
        self.assertEqual((srcs["wevity"]["status"], srcs["wevity"]["lastSuccessAt"]), ("error", NOW_ISO))
        self.assertEqual(srcs["wevity"]["itemCount"], 1)
        self.assertEqual(doc["updatedAt"], "2026-10-03T08:00:00Z")

    def test_missing_live_item_becomes_stale_with_old_verified_at(self):
        self.run_pipeline([spec("dacon", [self.raw_for(1, deadlineDate="2026-12-01", endDate="2026-12-10"), self.raw_for(2, deadlineDate="2026-12-01", endDate="2026-12-10")])])
        later = NOW + timedelta(days=1)
        self.run_pipeline([spec("dacon", [self.raw_for(2, deadlineDate="2026-12-01", endDate="2026-12-10")])], now=later)
        items = {i["title"]: i for i in json.loads(self.out.read_text(encoding="utf-8"))["items"]}
        self.assertTrue(items["AI 해커톤 1"]["stale"])
        self.assertEqual(items["AI 해커톤 1"]["verifiedAt"], NOW_ISO)
        self.assertFalse(items["AI 해커톤 2"]["stale"])
        self.assertEqual(items["AI 해커톤 2"]["verifiedAt"], "2026-10-03T08:00:00Z")

    def test_zero_results_is_ok_and_makes_old_items_stale(self):
        self.run_pipeline([spec("dacon", [self.raw_for(1, deadlineDate="2026-12-01", endDate="2026-12-10")])])
        self.run_pipeline([spec("dacon", [])], now=NOW + timedelta(days=1))
        doc = json.loads(self.out.read_text(encoding="utf-8"))
        self.assertEqual(doc["sources"][0]["status"], "ok")
        self.assertEqual(doc["sources"][0]["itemCount"], 1)
        self.assertTrue(doc["items"][0]["stale"])

    def test_archive_retention_90_days(self):
        old_kept = make_item(n=1, startDate="2026-06-20", endDate="2026-07-10", deadlineDate="2026-07-01")
        old_dropped = make_item(n=2, startDate="2026-05-01", endDate="2026-05-10", deadlineDate="2026-05-05")
        seed = {"schemaVersion": 2, "updatedAt": "2026-09-01T00:00:00Z", "lastAttemptAt": "2026-09-01T00:00:00Z",
                "sources": [], "items": [old_kept, old_dropped]}
        self.out.write_text(json.dumps(seed, ensure_ascii=False), encoding="utf-8")
        self.run_pipeline([spec("dacon", [self.raw_for(3, deadlineDate="2026-12-01", endDate="2026-12-10")])])
        items = {i["title"]: i for i in json.loads(self.out.read_text(encoding="utf-8"))["items"]}
        self.assertIn("AI 해커톤 1", items)
        self.assertNotIn("AI 해커톤 2", items)
        kept = items["AI 해커톤 1"]
        self.assertEqual({k: v for k, v in kept.items() if k != "stale"}, {k: v for k, v in old_kept.items() if k != "stale"})
        self.assertFalse(kept["stale"])

    def test_duplicate_urls_collapse_across_sources(self):
        a = self.raw_for(1)
        b = self.raw_for(1, sourceName="WEVITY")
        b["url"] = "https://dacon.io/competitions/official/1/overview?utm_source=x"
        b["sourceUrl"] = "https://www.wevity.com/?c=find&gub=1&gbn=view&ix=5"
        self.run_pipeline([spec("dacon", [a, a]), spec("wevity", [b])])
        doc = json.loads(self.out.read_text(encoding="utf-8"))
        self.assertEqual(len(doc["items"]), 1)
        self.assertEqual(doc["items"][0]["sourceId"], "dacon")

    def test_invalid_raw_rows_are_skipped_not_fatal(self):
        bad = self.raw_for(9, startDate="2026-02-30")
        self.run_pipeline([spec("dacon", [bad, self.raw_for(1)])])
        self.assertEqual(len(json.loads(self.out.read_text(encoding="utf-8"))["items"]), 1)

    def test_unexpected_exception_is_recorded_as_error(self):
        report = self.run_pipeline([spec("dacon", error=ValueError("boom")), spec("wevity", [self.raw_for(1)])])
        by_id = {s["id"]: s for s in report["sources"]}
        self.assertEqual(by_id["dacon"]["status"], "error")
        self.assertEqual(by_id["wevity"]["status"], "ok")

    def test_corrupt_existing_json_errors_and_is_untouched(self):
        for content in ("{not json", "", json.dumps({"schemaVersion": 1, "items": []})):
            self.out.write_text(content, encoding="utf-8")
            with self.assertRaises(ExistingDataError):
                self.run_pipeline([spec("dacon", [self.raw_for(1)])])
            self.assertEqual(self.out.read_text(encoding="utf-8"), content)
            self.assertFalse(self.status.exists())

    def test_idempotent_stable_payload(self):
        specs = lambda: [spec("dacon", [self.raw_for(2), self.raw_for(1)]), spec("wevity", [self.raw_for(3)])]
        self.run_pipeline(specs())
        first = self.out.read_bytes()
        self.run_pipeline(specs())
        self.assertEqual(self.out.read_bytes(), first)
        self.assertTrue(first.endswith(b"\n"))

    def test_dry_run_writes_nothing(self):
        report = self.run_pipeline([spec("dacon", [self.raw_for(1)])], dry_run=True)
        self.assertTrue(report["dryRun"])
        self.assertEqual(report["itemCount"], 1)
        self.assertFalse(self.out.exists())
        self.assertFalse(self.status.exists())

    def test_max_items_is_passed_to_sources(self):
        seen = []

        def collect(fetcher, now, max_items):
            seen.append(max_items)
            return CollectResult(items=[], message="ok")

        self.run_pipeline([SourceSpec(id="dacon", name="DACON", url="https://dacon.io/competitions", collect=collect)], max_items=5)
        self.assertEqual(seen, [5])

    def test_curated_items_merged_and_validated(self):
        item = make_item(source_id="curated", n=7)
        self.curated.write_text(json.dumps({"schemaVersion": 2, "items": [item]}, ensure_ascii=False), encoding="utf-8")
        self.run_pipeline([spec("dacon", [self.raw_for(1)])])
        doc = json.loads(self.out.read_text(encoding="utf-8"))
        self.assertIn(item["id"], [i["id"] for i in doc["items"]])
        broken = copy.deepcopy(item)
        broken["url"] = "http://insecure.example/"
        self.curated.write_text(json.dumps({"schemaVersion": 2, "items": [broken]}), encoding="utf-8")
        with self.assertRaises(ExistingDataError):
            self.run_pipeline([spec("dacon", [self.raw_for(1)])])


class ReviewFixesTest(unittest.TestCase):
    """Codex 교차 리뷰에서 확인된 7개 오류의 회귀 테스트."""

    # 1. redirect 단계마다 robots 확인
    def test_redirect_target_robots_checked_before_request(self):
        routes = {
            "https://dacon.io/robots.txt": OK_ROBOTS,
            "https://www.dacon.io/robots.txt": FakeResp(200, b"User-agent: *\nDisallow: /\n"),
            "https://dacon.io/a": FakeResp(302, b"", {"Location": "https://www.dacon.io/b"}),
            "https://www.dacon.io/b": FakeResp(200, b"secret"),
        }
        fetcher, session, _ = make_fetcher(routes)
        with self.assertRaises(FetchError) as cm:
            fetcher.get("https://dacon.io/a")
        self.assertEqual(cm.exception.status, "blocked")
        self.assertNotIn("https://www.dacon.io/b", session.calls)

    def test_intermediate_redirect_robots_checked_and_allowed_chain_followed(self):
        routes = {
            "https://dacon.io/robots.txt": FakeResp(200, b"User-agent: *\nDisallow: /b\n"),
            "https://dacon.io/a": FakeResp(302, b"", {"Location": "/b"}),
            "https://dacon.io/b": FakeResp(302, b"", {"Location": "/c"}),
            "https://dacon.io/c": FakeResp(200, b"done"),
            "https://dacon.io/x": FakeResp(302, b"", {"Location": "/y"}),
            "https://dacon.io/y": FakeResp(302, b"", {"Location": "/c"}),
        }
        fetcher, session, _ = make_fetcher(routes)
        with self.assertRaises(FetchError):
            fetcher.get("https://dacon.io/a")
        self.assertNotIn("https://dacon.io/b", session.calls)
        self.assertNotIn("https://dacon.io/c", session.calls)
        result = fetcher.get("https://dacon.io/x")
        self.assertEqual((result.text, result.url), ("done", "https://dacon.io/c"))

    # 2. 한국 참가 자격 판정
    def test_korea_allowed_exclusion_context_and_including(self):
        self.assertFalse(rules.korea_allowed("Eligible residents of Japan. South Korea is not eligible."))
        self.assertFalse(rules.korea_allowed("Residents of Japan; no participation from South Korea"))
        self.assertTrue(rules.korea_allowed("Worldwide, including South Korea; excluding North Korea"))

    def test_korea_allowed_unconfirmed_standard_exceptions_stay_rejected_with_other_lines(self):
        for t in (
            "Ages 18+ only; All countries/territories, excluding standard exceptions",
            "All countries/territories, excluding standard exceptions; Students only",
            "All countries/territories, excluding standard exceptions. Developers or professionals",
        ):
            self.assertFalse(rules.korea_allowed(t), t)
        self.assertTrue(rules.korea_allowed("Ages 18+ only; All countries/territories, excluding standard exceptions (Cuba, North Korea)"))

    def test_devpost_keeps_student_and_age_conditions(self):
        cand = {"title": "AI Student Hackathon", "organizer": "x", "themes": [], "period": "Oct 5 - 20, 2026", "prize": None, "url": "https://x.devpost.com/"}
        detail = {"eligibility_lines": ["Students only", "Ages 18+", "Residents of Japan, South Korea"],
                  "deadlineAt": "2026-10-20T17:00:00-04:00", "description": ""}
        raw = devpost.build_raw(cand, detail)
        self.assertIn("Students only", raw["eligibility"])
        self.assertIn("Ages 18+", raw["eligibility"])

    # 3. Devpost 기간 시작 연도
    def test_devpost_period_start_year(self):
        self.assertEqual(devpost._period_start("Dec 20 - Jan 10, 2027"), "2026-12-20")
        self.assertEqual(devpost._period_start("Dec 20, 2026 - Jan 10, 2027"), "2026-12-20")
        self.assertEqual(devpost._period_start("Sep 22 - Oct 26, 2026"), "2026-09-22")
        self.assertEqual(devpost._period_start("Oct 5 - 20, 2026"), "2026-10-05")
        self.assertEqual(devpost._period_start("Jan 5, 2026 - Feb 1, 2026"), "2026-01-05")

    # 4. 빈 userinfo
    def test_empty_userinfo_rejected(self):
        for bad in ("https://@dacon.io/x", "https://:@dacon.io/x", "https://user@dacon.io/x"):
            self.assertFalse(urlsafe.is_fetch_allowed(bad), bad)
            self.assertFalse(urlsafe.is_safe_https_url(bad), bad)
        self.assertTrue(urlsafe.is_fetch_allowed("https://dacon.io/x"))

    # 5. 중복 제거
    def _run(self, specs):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "opportunities.json"
            pipeline.run(out, status_path=Path(tmp) / "s.json", curated_path=None, fetcher=None, sources=specs, now=NOW)
            return json.loads(out.read_text(encoding="utf-8"))["items"]

    def test_same_detail_url_and_source_url_from_different_sources_collapses(self):
        a = make_raw(url="https://example.org/contest/1", sourceUrl="https://www.wevity.com/?ix=1")
        b = make_raw(title="AI 해커톤 테스트 (재게시)", url="https://example.org/contest/1/", sourceUrl="https://www.wevity.com/?ix=1")
        items = self._run([spec("dacon", [a]), spec("wevity", [b])])
        self.assertEqual(len(items), 1)

    def test_different_contests_sharing_organizer_root_are_kept(self):
        a = make_raw(title="AI 공모전 A", kind="contest", url="https://organizer.example.com/", sourceUrl="https://www.wevity.com/?ix=1")
        b = make_raw(title="AI 공모전 B", kind="contest", url="https://organizer.example.com/", sourceUrl="https://www.wevity.com/?ix=2")
        c = make_raw(title="AI 공모전 C", kind="contest", url="https://organizer.example.com", sourceUrl="https://dacon.io/competitions/official/3/overview/")
        items = self._run([spec("wevity", [a, b]), spec("dacon", [c])])
        self.assertEqual(sorted(i["title"] for i in items), ["AI 공모전 A", "AI 공모전 B", "AI 공모전 C"])

    # 6. 초대 전용 제외와 Devpost 유형
    def test_invite_only_titles_excluded_but_public_student_contests_kept(self):
        for title in ("AIC Internal Competition -2026 (Agentic AI)", "AI Private Hackathon", "AI Hackathon (Invite-only)"):
            self.assertIsNone(rules.normalize_item(make_raw(title=title), "devpost", NOW_ISO), title)
        for title in ("AI 대학생 경진대회", "Student AI Competition (Ages 18-25)"):
            self.assertIsNotNone(rules.normalize_item(make_raw(title=title, kind="contest"), "dacon", NOW_ISO), title)

    def test_devpost_kind_from_title(self):
        detail = {"eligibility_lines": ["Worldwide"], "deadlineAt": "2026-10-26T17:00:00-04:00", "description": ""}

        def kind(title):
            cand = {"title": title, "organizer": "x", "themes": [], "period": "Oct 5 - 20, 2026", "prize": None, "url": "https://x.devpost.com/"}
            return devpost.build_raw(cand, detail)["kind"]

        self.assertEqual(kind("Global AI Competition 2026"), "contest")
        self.assertEqual(kind("Agent Contest"), "contest")
        self.assertEqual(kind("AI Hackathon Competition"), "hackathon")
        self.assertEqual(kind("Build with AI"), "hackathon")

    # 6-b. 저장된 항목에도 같은 계약 적용
    def test_stored_items_failing_contract_are_dropped_on_merge(self):
        good = make_item(source_id="devpost", n=1, deadlineDate="2026-12-01", endDate="2026-12-10")
        bad = dict(make_item(source_id="devpost", n=2, deadlineDate="2026-12-01", endDate="2026-12-10"), title="AIC Internal Competition -2026 (Agentic AI)")
        bad_global = make_item(source_id="devpost", n=3, country="GLOBAL", mode="online", eligibilityVerified=True,
                               eligibility="All countries/territories, excluding standard exceptions",
                               deadlineDate="2026-12-01", endDate="2026-12-10")
        seed = {"schemaVersion": 2, "updatedAt": "2026-09-01T00:00:00Z", "lastAttemptAt": "2026-09-01T00:00:00Z",
                "sources": [], "items": [good, bad, bad_global]}
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "opportunities.json"
            out.write_text(json.dumps(seed, ensure_ascii=False), encoding="utf-8")
            fresh = make_raw(title="AI 해커톤 9", url="https://dacon.io/competitions/official/9/overview/",
                             sourceUrl="https://dacon.io/competitions/official/9/overview/")
            pipeline.run(out, status_path=Path(tmp) / "s.json", curated_path=None, fetcher=None, sources=[spec("devpost", [fresh])], now=NOW)
            titles = [i["title"] for i in json.loads(out.read_text(encoding="utf-8"))["items"]]
        self.assertIn("AI 해커톤 1", titles)
        self.assertIn("AI 해커톤 9", titles)
        self.assertNotIn("AIC Internal Competition -2026 (Agentic AI)", titles)
        self.assertNotIn("AI 해커톤 3", titles)


class CliTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        self.out = self.dir / "opportunities.json"

    def args(self, *extra):
        return ["--output", str(self.out), "--curated", str(self.dir / "curated.json"), *extra]

    def test_offline_validates_without_writing(self):
        self.assertEqual(cli.main(self.args("--offline")), 0)
        self.assertEqual(list(self.dir.iterdir()), [])

    def test_offline_corrupt_existing_returns_2(self):
        self.out.write_text("{bad", encoding="utf-8")
        self.assertEqual(cli.main(self.args("--offline")), 2)
        self.assertEqual(self.out.read_text(encoding="utf-8"), "{bad")

    def test_dry_run_with_injected_sources(self):
        code = cli.main(self.args("--dry-run", "--max-items", "4"), sources=[spec("dacon", [make_raw()])], fetcher=object())
        self.assertEqual(code, 0)
        self.assertEqual(list(self.dir.iterdir()), [])

    def test_exit_code_1_when_all_sources_fail(self):
        code = cli.main(self.args(), sources=[spec("dacon", error=SourceError("error", "x"))], fetcher=object())
        self.assertEqual(code, 1)
        self.assertTrue((self.dir / "ingest-status.json").exists())
        self.assertFalse(self.out.exists())

    def test_real_write_and_partial_success_exit_0(self):
        code = cli.main(self.args(), sources=[spec("dacon", [make_raw()]), spec("wevity", error=SourceError("error", "x"))], fetcher=object())
        self.assertEqual(code, 0)
        self.assertTrue(self.out.exists())


class RepoDataTest(unittest.TestCase):
    """저장소의 실제 data 파일이 계약을 지키는지 확인한다(없으면 건너뜀)."""

    def test_committed_documents_valid(self):
        path = ROOT / "data" / "opportunities.json"
        if not path.exists():
            self.skipTest("data/opportunities.json 없음")
        doc = json.loads(path.read_text(encoding="utf-8"))
        pipeline.validate_document(doc)
        status_path = ROOT / "data" / "ingest-status.json"
        if status_path.exists():
            status = json.loads(status_path.read_text(encoding="utf-8"))
            self.assertEqual(set(status), {"lastAttemptAt", "sources"})


if __name__ == "__main__":
    unittest.main()


class SecondReviewTest(unittest.TestCase):
    # 2. 표준 예외는 실제 국가 목록이 있을 때만 승인
    def test_standard_exceptions_need_real_country_list(self):
        for t in (
            "Worldwide, excluding standard exceptions (see rules)",
            "All countries/territories, excluding standard exceptions (see terms)",
            "All countries, excluding standard exceptions (TBD)",
            "All countries, excluding standard exceptions ()",
            "All countries, excluding standard exceptions (etc.)",
            "All countries, excluding (see rules)",
        ):
            self.assertFalse(rules.korea_allowed(t), t)
        self.assertTrue(rules.korea_allowed("All countries/territories, excluding standard exceptions (Brazil, Crimea, Cuba, Iran, North Korea, Quebec, Russia)"))
        self.assertTrue(rules.korea_allowed("All countries/territories, excluding (North Korea)"))

    # 3. curated/신선 결과에도 계약 검사
    def _curated_error(self, item):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "curated.json"
            path.write_text(json.dumps({"schemaVersion": 2, "items": [item]}, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(ExistingDataError):
                pipeline.load_curated(path)
            self.assertTrue(path.exists())

    def test_curated_rejects_contract_violations(self):
        ok = make_item(source_id="curated", n=1)
        self._curated_error(dict(ok, mode="offline", country="GLOBAL", eligibilityVerified=False))
        self._curated_error(dict(ok, title="요리 대회", tags=[], description="요리"))
        self._curated_error(dict(ok, title="AIC Internal Competition -2026 (Agentic AI)"))
        self._curated_error(dict(ok, mode="online", country="GLOBAL", eligibilityVerified=True, eligibility="Worldwide, excluding standard exceptions (see rules)"))

    def test_curated_missing_or_empty_is_ok(self):
        self.assertIsNone(pipeline.load_curated(None))
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(pipeline.load_curated(Path(tmp) / "none.json"))
            path = Path(tmp) / "curated.json"
            path.write_text('{"schemaVersion": 2, "items": []}', encoding="utf-8")
            self.assertEqual(pipeline.load_curated(path), [])

    def test_fresh_source_result_must_meet_contract(self):
        raw = make_raw(country="GLOBAL", mode="online", eligibilityVerified=True,
                       eligibility="Worldwide, excluding standard exceptions (see rules)")
        outcome, items = pipeline._collect_source(spec("devpost", [raw]), None, NOW, NOW_ISO, None)
        self.assertEqual(outcome["status"], "ok")
        self.assertEqual(items, [])
        self.assertIn("1건 제외", outcome["message"])


class WorkflowTest(unittest.TestCase):
    # 4. 전체 실패 상태 전달 + 손상 데이터 push 차단
    def setUp(self):
        self.text = (ROOT / ".github" / "workflows" / "update.yml").read_text(encoding="utf-8")

    def test_collector_failure_does_not_block_status_commit(self):
        self.assertIn("id: collect", self.text)
        self.assertIn("continue-on-error: true", self.text)
        self.assertLess(self.text.index("id: collect"), self.text.index("Run tests"))
        self.assertLess(self.text.index("Run tests"), self.text.index("Commit changes"))
        self.assertLess(self.text.index("Commit changes"), self.text.index("Fail if collector failed"))
        self.assertIn("steps.collect.outcome == 'failure'", self.text)

    def test_corrupt_data_exit_2_never_commits(self):
        self.assertIn("exit_code != '2'", self.text)

    def test_schedule_gate_unchanged(self):
        self.assertIn("vars.ENABLE_OPPORTUNITY_UPDATES == 'true'", self.text)
