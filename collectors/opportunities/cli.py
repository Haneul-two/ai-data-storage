"""명령행 진입점. 종료 코드: 0 성공(일부 실패 포함), 1 모든 소스 실패, 2 기존 데이터 손상."""
import argparse
import sys
from pathlib import Path

from . import pipeline
from .errors import ExistingDataError
from .http import Fetcher

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "data" / "opportunities.json"
DEFAULT_CURATED = ROOT / "data" / "curated.json"


def _parser():
    p = argparse.ArgumentParser(description="AI 행사·공모전·해커톤 수집")
    p.add_argument("--dry-run", action="store_true", help="실제 조회는 하되 어떤 데이터 파일도 쓰지 않는다")
    p.add_argument("--offline", action="store_true", help="네트워크 없이 기존 JSON과 curated.json 계약만 검증한다")
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="opportunities.json 경로(상태 파일은 같은 폴더의 ingest-status.json)")
    p.add_argument("--curated", type=Path, default=DEFAULT_CURATED, help="수동 입력 curated.json 경로")
    p.add_argument("--max-items", type=int, default=None, help="소스별 최대 항목 수(기본: 소스별 상한)")
    return p


def main(argv=None, sources=None, fetcher=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    args = _parser().parse_args(argv)
    try:
        if args.offline:
            existing = pipeline.load_existing(args.output)
            curated = pipeline.load_curated(args.curated)
            print(f"[offline] opportunities 항목 {len(existing['items']) if existing else '파일 없음'}, curated 항목 {len(curated) if curated is not None else '파일 없음'} — 계약 검증 통과")
            return 0
        report = pipeline.run(
            args.output, curated_path=args.curated, fetcher=fetcher or Fetcher(), sources=sources,
            dry_run=args.dry_run, max_items=args.max_items,
        )
    except ExistingDataError as exc:
        print(f"[오류] 기존 데이터 문제로 중단: {exc}", file=sys.stderr)
        return 2
    mode = "dry-run(파일 미수정)" if args.dry_run else "저장"
    print(f"[{mode}] 갱신={report['updated']} 항목={report['itemCount']} 시각={report['lastAttemptAt']}")
    for s in report["sources"]:
        print(f"  - {s['id']}: {s['status']} 항목 {s['itemCount']} · {s['message']}")
    return 0 if any(s["status"] == "ok" for s in report["sources"]) else 1
