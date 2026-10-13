"""Verify the deployed recovery against a specific collection attempt."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import requests
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://haneul-two.github.io/ai-data-storage/"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-at", required=True)
    args = parser.parse_args()
    responses = [requests.get(BASE + path, timeout=30) for path in
                 ("data/ingest-status.json", "data/opportunities.json")]
    for response in responses:
        response.raise_for_status()
    status, data = (response.json() for response in responses)
    source = next(s for s in status["sources"] if s["id"] == "aiexpo")
    assert source["status"] == "ok", source
    assert source["checkedAt"] == source["lastSuccessAt"] == status["lastAttemptAt"] == args.expected_at
    items = [i for i in data["items"] if i["sourceId"] == "aiexpo"]
    assert len(items) == 1, items
    item = items[0]
    assert item["id"] == "aiexpo-119c9024b15a"
    assert item["sourceUrl"] in (
        "https://aiexpo.co.kr/%ec%a0%84%ec%8b%9c%ed%9a%8c-%ea%b0%9c%ec%9a%94/",
        "https://www.showala.com/ex/ex_detail.php?idx=4273",
    )
    assert item["verifiedAt"] == args.expected_at
    assert (item["startDate"], item["endDate"]) == ("2027-04-14", "2027-04-16")
    assert len(status["sources"]) == 10 and all(s["status"] == "ok" for s in status["sources"]), status
    checks, errors = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        for width in (1440, 390):
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(BASE, wait_until="networkidle")
            expect(page.locator("#content")).to_have_attribute("aria-busy", "false")
            assert page.locator("#notices").inner_text().strip() == ""
            assert page.locator(".opp").count() > 0
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            page.screenshot(path=str(ROOT / "docs/evidence" / f"aiexpo-public-{width}.png"))
            checks.append({"width": width, "noticesAbsent": True, "overflow": False})
            page.close()
        browser.close()
    assert not errors, errors
    evidence = {"checkedAt": datetime.now(timezone.utc).isoformat(), "expectedAttemptAt": args.expected_at,
                "source": source, "id": item["id"], "verifiedAt": item["verifiedAt"], "sourceUrl": item["sourceUrl"],
                "sourceStatuses": {s["id"]: s["status"] for s in status["sources"]},
                "checks": checks, "pageErrors": errors}
    (ROOT / "docs/evidence/aiexpo-production.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, ensure_ascii=True))


if __name__ == "__main__":
    main()
