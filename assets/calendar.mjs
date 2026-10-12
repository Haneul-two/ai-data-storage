// 월별 달력 격자와 마커 계산. 순수 함수.
import { seoulDate, isValidDateStr } from './time.mjs';
import { getDeadline } from './status.mjs';

const pad = (n) => String(n).padStart(2, '0');

export function monthOf(now) {
  const [y, m] = seoulDate(now).split('-');
  return { year: +y, month: +m };
}

export function shiftMonth({ year, month }, delta) {
  const idx = year * 12 + (month - 1) + delta;
  return { year: Math.floor(idx / 12), month: (idx % 12) + 1 };
}

// weekStart: 0=일요일 시작, 1=월요일 시작. 항상 7칸 x N주.
export function buildMonthGrid(year, month, weekStart = 0) {
  const first = new Date(Date.UTC(year, month - 1, 1));
  const lead = (first.getUTCDay() - weekStart + 7) % 7;
  const daysInMonth = new Date(Date.UTC(year, month, 0)).getUTCDate();
  const weeks = Math.ceil((lead + daysInMonth) / 7);
  const grid = [];
  for (let w = 0; w < weeks; w += 1) {
    const row = [];
    for (let d = 0; d < 7; d += 1) {
      const cell = new Date(Date.UTC(year, month - 1, 1 - lead + w * 7 + d));
      const date = `${cell.getUTCFullYear()}-${pad(cell.getUTCMonth() + 1)}-${pad(cell.getUTCDate())}`;
      row.push({ date, day: cell.getUTCDate(), inMonth: cell.getUTCMonth() === month - 1 });
    }
    grid.push(row);
  }
  return grid;
}

// 마감 마커와 개최 시작 마커를 분리해 날짜별로 모은다. 두 날짜가 모두 없으면 undated.
export function calendarEntries(items, now) {
  const byDate = new Map();
  const undated = [];
  const push = (date, entry) => {
    if (!byDate.has(date)) byDate.set(date, []);
    byDate.get(date).push(entry);
  };
  for (const item of items) {
    const deadline = getDeadline(item, now ?? Date.now());
    let dated = false;
    if (deadline.kind !== 'none') {
      push(deadline.date, { type: 'deadline', item });
      dated = true;
    }
    if (isValidDateStr(item.startDate)) {
      push(item.startDate, { type: 'start', item });
      dated = true;
    }
    if (!dated) undated.push(item);
  }
  return { byDate, undated };
}
