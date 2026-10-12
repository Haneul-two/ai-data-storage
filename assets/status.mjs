// 기회 상태 판정 (docs/spec.md §3). 첫 일치 규칙, now는 항상 인자로 받는다.
import { seoulDate, toMs, daysBetween, endOfSeoulDateMs, isValidDateStr } from './time.mjs';

export const STATUS_LABELS = {
  open: '모집중',
  upcoming: '예정',
  ongoing: '진행중',
  closed: '마감',
  ended: '종료',
  unknown: '일정 미정',
};

// 마감 정보: exact(절대 시각) > dateOnly(날짜만, 당일 끝까지 유효) > none
export function getDeadline(item, now) {
  const today = seoulDate(now);
  if (item.deadlineAt) {
    const ms = toMs(item.deadlineAt);
    if (ms !== null) {
      const date = seoulDate(ms);
      return { kind: 'exact', date, ms, daysLeft: daysBetween(today, date), needsTimeCheck: false };
    }
  }
  if (isValidDateStr(item.deadlineDate)) {
    return {
      kind: 'dateOnly',
      date: item.deadlineDate,
      ms: endOfSeoulDateMs(item.deadlineDate),
      daysLeft: daysBetween(today, item.deadlineDate),
      needsTimeCheck: true,
    };
  }
  return { kind: 'none', date: null, ms: null, daysLeft: null, needsTimeCheck: false };
}

export function getStatus(item, now) {
  const nowMs = toMs(now);
  const today = seoulDate(now);
  const deadline = getDeadline(item, now);
  const knownDeadlinePassed = deadline.kind !== 'none' && deadline.ms < nowMs;

  if (isValidDateStr(item.endDate) && item.endDate < today) return 'ended';
  if (item.sourceStatus === 'closed') return 'closed';
  if (knownDeadlinePassed) return 'closed';
  if (isValidDateStr(item.registrationStartDate) && item.registrationStartDate > today) return 'upcoming';
  if (item.sourceStatus === 'open' || deadline.kind !== 'none') return 'open';

  const start = isValidDateStr(item.startDate) ? item.startDate : null;
  const end = isValidDateStr(item.endDate) ? item.endDate : start;
  if (start && start <= today && end >= today) return 'ongoing';
  if (start && start > today) return 'upcoming';
  return 'unknown';
}
