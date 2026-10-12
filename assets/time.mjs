// 서울(UTC+9, DST 없음) 기준 날짜 계산. 모든 함수는 now/입력을 인자로 받아 순수하게 동작한다.
const KST_OFFSET_MS = 9 * 60 * 60 * 1000;
const DAY_MS = 24 * 60 * 60 * 1000;
const DATE_RE = /^(\d{4})-(\d{2})-(\d{2})$/;

export function toMs(input) {
  if (input instanceof Date) return input.getTime();
  if (typeof input === 'number') return Number.isFinite(input) ? input : null;
  if (typeof input === 'string' && input) {
    const ms = Date.parse(input);
    return Number.isNaN(ms) ? null : ms;
  }
  return null;
}

export function seoulDate(input) {
  const ms = toMs(input);
  if (ms === null) return null;
  return new Date(ms + KST_OFFSET_MS).toISOString().slice(0, 10);
}

export function isValidDateStr(s) {
  if (typeof s !== 'string') return false;
  const m = DATE_RE.exec(s);
  if (!m) return false;
  const d = new Date(Date.UTC(+m[1], +m[2] - 1, +m[3]));
  return d.toISOString().slice(0, 10) === s;
}

function dayNumber(s) {
  const m = DATE_RE.exec(s);
  return Date.UTC(+m[1], +m[2] - 1, +m[3]) / DAY_MS;
}

export function daysBetween(from, to) {
  return dayNumber(to) - dayNumber(from);
}

// 서울 날짜 당일의 마지막 순간(ms)
export function endOfSeoulDateMs(dateStr) {
  return Date.parse(`${dateStr}T23:59:59.999+09:00`);
}

export function weekdayOf(dateStr) {
  const m = DATE_RE.exec(dateStr);
  return new Date(Date.UTC(+m[1], +m[2] - 1, +m[3])).getUTCDay();
}
