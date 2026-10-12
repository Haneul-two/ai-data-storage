"""수집 실행·병합·검증·원자적 저장. 원격 실패가 기존 데이터를 훼손하지 않도록 설계한다."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from . import rules
from .errors import ExistingDataError, SourceError
from .urlsafe import canonical_url

SCHEMA_VERSION = 2
SOURCE_KEYS = {"id", "name", "url", "status", "checkedAt", "lastSuccessAt", "itemCount", "message"}
DOC_KEYS = {"schemaVersion", "updatedAt", "lastAttemptAt", "sources", "items"}
CURATED_ID = "curated"


def _iso(moment):
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def validate_source(source):
    if not isinstance(source, dict) or set(source) != SOURCE_KEYS:
        raise ExistingDataError(f"sources 항목 키가 계약과 다름: {source!r}")
    if source["status"] not in ("ok", "error", "blocked"):
        raise ExistingDataError(f"source status 값 오류: {source['status']!r}")
    if not isinstance(source["itemCount"], int) or isinstance(source["itemCount"], bool):
        raise ExistingDataError("source itemCount는 정수여야 함")
    for key in ("checkedAt", "lastSuccessAt"):
        value = source[key]
        if value is not None and rules.parse_iso_datetime(value) is None:
            raise ExistingDataError(f"source {key} 형식 오류")


def validate_document(doc):
    if not isinstance(doc, dict) or set(doc) != DOC_KEYS:
        raise ExistingDataError("opportunities 문서 키가 계약과 다름")
    if doc["schemaVersion"] != SCHEMA_VERSION:
        raise ExistingDataError(f"schemaVersion {doc['schemaVersion']!r}는 지원하지 않음")
    if doc["updatedAt"] is not None and rules.parse_iso_datetime(doc["updatedAt"]) is None:
        raise ExistingDataError("updatedAt 형식 오류")
    if rules.parse_iso_datetime(doc["lastAttemptAt"]) is None:
        raise ExistingDataError("lastAttemptAt 형식 오류")
    if not isinstance(doc["sources"], list) or not isinstance(doc["items"], list):
        raise ExistingDataError("sources/items는 배열이어야 함")
    for source in doc["sources"]:
        validate_source(source)
    seen = set()
    for item in doc["items"]:
        try:
            rules.validate_item(item)
        except ValueError as exc:
            raise ExistingDataError(f"항목 검증 실패: {exc}") from exc
        if item["id"] in seen:
            raise ExistingDataError(f"중복 id: {item['id']}")
        seen.add(item["id"])


def load_existing(path):
    path = Path(path)
    if not path.exists():
        return None
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise ExistingDataError(f"{path} 읽기/파싱 실패: {exc}") from exc
    validate_document(doc)
    return doc


def load_curated(path):
    if path is None or not Path(path).exists():
        return None
    try:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise ExistingDataError(f"{path} 읽기/파싱 실패: {exc}") from exc
    if not isinstance(doc, dict) or doc.get("schemaVersion") != SCHEMA_VERSION or not isinstance(doc.get("items"), list):
        raise ExistingDataError("curated.json은 {schemaVersion: 2, items: []} 형식이어야 함")
    for item in doc["items"]:
        try:
            rules.validate_item(item)
        except ValueError as exc:
            raise ExistingDataError(f"curated 항목 검증 실패: {exc}") from exc
        if not rules.meets_contract(item):
            raise ExistingDataError(f"curated 항목이 관련성·지역·자격·초대 전용 계약을 어김: {item['id']}")
    return doc["items"]


def atomic_write_json(path, doc):
    path = Path(path)
    text = json.dumps(doc, ensure_ascii=False, indent=2) + "\n"
    json.loads(text)  # 직렬화 결과가 다시 읽히는지 확인한 뒤에만 교체한다
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(text.encode("utf-8"))
    os.replace(tmp, path)


def _collect_source(spec, fetcher, now, now_iso, max_items):
    """(source_status 일부, 정규화된 항목 목록). 실패해도 예외를 밖으로 내보내지 않는다."""
    try:
        result = spec.collect(fetcher, now, max_items)
    except SourceError as exc:
        return {"status": exc.status, "message": str(exc)}, None
    except Exception as exc:  # 어댑터 버그가 다른 소스 수집을 막지 않게 한다
        return {"status": "error", "message": f"예상치 못한 오류({type(exc).__name__}): {exc}"}, None
    items, seen, skipped = [], set(), 0
    for raw in result.items:
        item = rules.normalize_item(raw, spec.id, now_iso)
        if item is None or not rules.meets_contract(item):
            skipped += 1
        elif item["id"] not in seen:
            seen.add(item["id"])
            items.append(item)
    message = result.message + (f" (계약 위반으로 {skipped}건 제외)" if skipped else "")
    return {"status": "ok", "message": message}, items


def _same_opportunity(owner, item, url_key):
    """같은 canonical url을 쓰는 다른 출처 항목이 같은 기회인가. 주최 홈페이지(root)는 여러 공모전이 공유하므로
    상세 주소이거나, 안내 주소(sourceUrl)나 제목이 같다는 증거가 있을 때만 같은 기회로 본다."""
    if urlsplit(url_key).path != "/":
        return True
    if canonical_url(owner["sourceUrl"]) == canonical_url(item["sourceUrl"]):
        return True
    return owner["title"].casefold() == item["title"].casefold()


def _dedupe(items, order):
    ranked = sorted(items, key=lambda i: (order.get(i["sourceId"], len(order)), i["id"]))
    kept, by_id, by_url = [], set(), {}
    for item in ranked:
        key = canonical_url(item["url"])
        owner = by_url.get(key)
        if item["id"] in by_id or (owner is not None and owner["sourceId"] != item["sourceId"] and _same_opportunity(owner, item, key)):
            continue
        by_id.add(item["id"])
        by_url.setdefault(key, item)
        kept.append(item)
    return kept


def run(output_path, status_path=None, curated_path=None, fetcher=None, sources=None, now=None, dry_run=False, max_items=None):
    from .sources import default_sources

    output_path = Path(output_path)
    status_path = Path(status_path) if status_path else output_path.with_name("ingest-status.json")
    now = now or datetime.now(timezone.utc)
    now_iso = _iso(now)
    today = now.astimezone(rules.SEOUL).date()
    specs = default_sources() if sources is None else sources

    existing = load_existing(output_path)  # 손상된 파일은 여기서 예외로 중단한다
    curated = load_curated(curated_path)
    old_items = existing["items"] if existing else []
    old_sources = {s["id"]: s for s in (existing["sources"] if existing else [])}

    statuses, fresh = [], {}
    for spec in specs:
        outcome, items = _collect_source(spec, fetcher, now, now_iso, max_items)
        statuses.append({
            "id": spec.id, "name": spec.name, "url": spec.url, "status": outcome["status"], "checkedAt": now_iso,
            "lastSuccessAt": now_iso if items is not None else (old_sources.get(spec.id) or {}).get("lastSuccessAt"),
            "itemCount": 0, "message": outcome["message"],
        })
        if items is not None:
            fresh[spec.id] = items
    if curated is not None:
        fresh[CURATED_ID] = curated

    updated = bool(fresh) and any(s["status"] == "ok" for s in statuses)
    items_out = old_items
    if updated:
        merged = []
        new_ids = {i["id"] for items in fresh.values() for i in items}
        for item in old_items:
            if item["id"] in new_ids:
                continue  # 새 결과로 교체
            if rules.is_expired_archive(item, today) or not rules.meets_contract(item):
                continue  # 만료됐거나 지금의 계약(관련성·지역·자격·초대 전용)을 어기는 stale 항목은 출력에서 뺀다
            if item["sourceId"] in fresh and not rules.is_archived(item, today):
                item = dict(item, stale=True)  # 성공 소스에서 사라진 활성 항목: verifiedAt은 그대로 둔다
            merged.append(item)
        for items in fresh.values():
            merged.extend(i for i in items if not rules.is_expired_archive(i, today))
        order = {spec.id: n for n, spec in enumerate(specs)}
        order.setdefault(CURATED_ID, len(order))
        items_out = _dedupe(merged, order)
    counts = {}
    for item in items_out:
        counts[item["sourceId"]] = counts.get(item["sourceId"], 0) + 1
    for status in statuses:
        status["itemCount"] = counts.get(status["id"], 0)

    report = {"updated": updated, "dryRun": dry_run, "lastAttemptAt": now_iso, "sources": statuses,
              "itemCount": len(items_out), "written": []}
    if updated:
        doc = {"schemaVersion": SCHEMA_VERSION, "updatedAt": now_iso, "lastAttemptAt": now_iso, "sources": statuses, "items": items_out}
        validate_document(doc)
        report["document"] = doc
        if not dry_run:
            atomic_write_json(output_path, doc)
            report["written"].append(str(output_path))
    if not dry_run:
        atomic_write_json(status_path, {"lastAttemptAt": now_iso, "sources": statuses})
        report["written"].append(str(status_path))
    return report
