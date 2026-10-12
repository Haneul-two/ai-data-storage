"""Verify AI Summit's deployed data and its failure notice in Edge."""
import json
from datetime import datetime, timezone
from pathlib import Path

import requests
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://haneul-two.github.io/ai-data-storage/"


def main():
    status_response = requests.get(BASE + "data/ingest-status.json", timeout=30)
    data_response = requests.get(BASE + "data/opportunities.json", timeout=30)
    status_response.raise_for_status()
    data_response.raise_for_status()
    status, data = status_response.json(), data_response.json()
    source = next(s for s in status["sources"] if s["id"] == "aisummit")
    item = next(i for i in data["items"] if i["id"] == "aisummit-57beffb6a815")
    assert source["status"] == "ok", source
    assert source["checkedAt"] == source["lastSuccessAt"] == status["lastAttemptAt"]
    assert item["verifiedAt"] == source["lastSuccessAt"]
    assert item["startDate"] == "2027-08-11" and item["endDate"] == "2027-08-13"
    checks, errors = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        for width in (1440, 390):
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(BASE, wait_until="networkidle")
            expect(page.locator("#content")).to_have_attribute("aria-busy", "false")
            assert "AI Summit Seoul" not in page.locator("#notices").inner_text()
            assert page.locator(".opp").count() > 0
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            page.screenshot(path=str(ROOT / "docs/evidence" / f"aisummit-public-{width}.png"))
            checks.append({"width": width, "sourceFailureNoticeAbsent": True, "overflow": False})
            page.close()
        browser.close()
    assert not errors, errors
    evidence = {
        "checkedAt": datetime.now(timezone.utc).isoformat(), "source": source,
        "id": item["id"], "verifiedAt": item["verifiedAt"],
        "sourceStatuses": {s["id"]: s["status"] for s in status["sources"]},
        "checks": checks, "pageErrors": errors,
    }
    (ROOT / "docs/evidence/aisummit-production.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, ensure_ascii=True))


if __name__ == "__main__":
    main()
