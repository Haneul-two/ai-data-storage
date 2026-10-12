"""AI 행사·공모전·해커톤 수집 진입점. 구현은 collectors/opportunities/ 에 있다.

사용: python collectors/collect_events.py [--dry-run] [--offline] [--output PATH] [--max-items N]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from collectors.opportunities.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
