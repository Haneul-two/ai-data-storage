"""위비티 상세 본문(#viewContents)에서 진행 방식·마감 시각·참가비를 읽는다. 근거 문구가 애매하면 None/unknown으로 둔다."""
import re

_ONLINE = r"온라인|이메일|e-?mail|구글\s*폼|google\s*form|홈페이지"
_APPLY = r"접수|제출|신청|송부|지원"
_RUN = r"진행|예선|본선|개발"
_OFFLINE = r"오프라인|방문\s*접수|우편|(?<!비)대면|집체|현장\s*(?:접수|발표|심사|평가|참가|참여)"
_OFFLINE_ACTION = r"접수|제출|신청|진행|참가|참여|교육|발표|심사|평가|본선|예선|OJT"
_DEADLINE_LINE = re.compile(r"접\s*수|마\s*감|제출|신청|모집|공모|응모|기간")
_OTHER_SCHEDULE = re.compile(r"발표|심사|시상|투표|오리엔테이션|\bOT\b|행사|교육|멘토링")
_GAP = r"(?:\s*\([^)\n]{1,3}\))?[\s,/]*(?:까지[\s,/]*)?"
_TIME = r"(오전|오후|저녁|밤)?\s*(\d{1,2})\s*(?::\s*(\d{2})|시(?:\s*(\d{1,2})\s*분)?)(?!\d)"
_MORE_TIME = re.compile(r"\s*(?:[~∼-]|부터|또는|혹은|/)\s*(?:오전|오후|저녁|밤)?\s*\d{1,2}\s*[:시]")
_YEAR_BEFORE = re.compile(r"(?<!\d)'?(\d{4}|\d{2})\s*(?:[./-]|년)\s*$")
_FREE = re.compile(r"(?:참가비|참가\s*비용|참가료|교육비)\s*(?:[:：]|은|는)?\s*(?:전액\s*)?(?:무료|없음)")
_AMOUNT = re.compile(r"(?:참가비|참가료)\s*[:：]?\s*(\d[\d,]*\s*(?:만\s*)?원)")
_ANY_AMOUNT = re.compile(r"\d[\d,]*\s*(?:만\s*)?원")


def _near(word, action, line):
    """단어와 행동이 15자 안에 있어야 근거로 본다(활용 안내·주제 설명 문장의 우연한 동시 등장 제외)."""
    return re.search(rf"(?:{word}).{{0,15}}(?:{action})|(?:{action}).{{0,15}}(?:{word})", line, re.I) is not None


def infer_mode(text, kind="contest"):
    """접수·진행 문장의 온라인/오프라인 단서로 판단한다. 문의처 줄은 근거로 쓰지 않는다.
    온라인 접수만 있고 행사가 오프라인이면 오프라인(신청 방법은 진행 방식이 아니다), 온라인 진행·재택까지 있으면 혼합.
    온라인 접수·제출만으로 온라인이라 보는 건 작품 제출이 곧 참가인 공모전뿐이다(해커톤·행사는 신청만 온라인일 수 있다)."""
    applied = run = offline = False
    for line in (text or "").splitlines():
        if "문의" in line:
            continue
        applied = applied or _near(_ONLINE, _APPLY, line)
        run = run or _near("온라인", _RUN, line) or "재택" in line
        offline = offline or _near(_OFFLINE, _OFFLINE_ACTION, line)
    if offline:
        return "hybrid" if run else "offline"
    return "online" if run or (applied and kind == "contest") else "unknown"


def deadline_at(text, deadline_date):
    """접수·마감 줄에서 마감 날짜 바로 뒤에 붙은 시각만 읽는다.
    다른 연도, 발표·심사 같은 다른 일정, 시간 범위·복수 후보, 같은 날짜의 서로 다른 시각은 고르지 않는다."""
    if not deadline_date or not text:
        return None
    year, month, day = (int(p) for p in deadline_date.split("-"))
    dates = (rf"(?<!\d)0?{month}\s*[./-]\s*0?{day}(?!\d)\.?", rf"(?<!\d)0?{month}\s*월\s*0?{day}\s*일")
    times, header = set(), ""
    for line in text.splitlines():
        if not line.strip():
            continue
        context, header = header + "\n" + line, line  # 바로 위 줄('■ 접수기간' 같은 제목)까지 문맥으로 본다
        if not _DEADLINE_LINE.search(context) or (_OTHER_SCHEDULE.search(line) and not re.search(r"접수|마감", line)):
            continue
        for date in dates:
            for m in re.finditer(date + _GAP + _TIME, line):
                y = _YEAR_BEFORE.search(line[:m.start()])
                if y and int(y[1]) not in (year, year % 100):
                    continue
                clock = None if _MORE_TIME.match(line, m.end()) else _clock(*m.groups())
                times.add(clock)  # 애매하면 None을 넣어 아래에서 전체를 버린다
    if len(times) != 1 or None in times:
        return None
    return f"{year:04d}-{month:02d}-{day:02d}T{times.pop()}+09:00"


def _clock(meridiem, hour, minute_colon, minute_korean):
    hour, minute = int(hour), int(minute_colon or minute_korean or 0)
    if meridiem == "오전" and hour == 12:
        hour = 0
    elif meridiem in ("오후", "저녁", "밤") and hour < 12:
        hour += 12
    elif meridiem == "밤" and hour == 12:
        hour = 24
    if hour == 24 and minute == 0:
        return "23:59:59"  # 24:00·밤 12시는 그날 끝. 다음 날로 넘기면 마감 날짜가 바뀐다
    if hour > 23 or minute > 59:
        return None
    return f"{hour:02d}:{minute:02d}:00"


def fee(text):
    """참가비를 명시한 문구만 읽는다. 무료와 금액이 함께 있거나 조건이 붙으면 None(화면에는 '확인 필요')."""
    text = text or ""
    free = [m for m in _FREE.finditer(text)]
    amount = _AMOUNT.search(text)
    if free and amount:
        return None
    for m in free:
        line = text[text.rfind("\n", 0, m.start()) + 1:].split("\n", 1)[0]
        if _ANY_AMOUNT.search(line) or re.match(r"\s*\(", text[m.end():]):
            return None
    if free:
        return "무료"
    return re.sub(r"\s+", "", amount[1]) if amount else None
