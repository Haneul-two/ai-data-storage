// 화면 표시용 문자열 포맷과 라벨 표. 순수 함수.
import { isValidDateStr, weekdayOf, toMs } from './time.mjs';

export const WEEKDAYS_KO = ['일', '월', '화', '수', '목', '금', '토'];

export const KIND_LABELS = { event: '행사', contest: '공모전', hackathon: '해커톤' };
export const MODE_LABELS = { online: '온라인', offline: '오프라인', hybrid: '혼합', unknown: '방식 미정' };
export const SOURCE_STATUS_LABELS = { ok: '정상', error: '확인 실패', blocked: '접근 제한' };

export function formatDateKo(dateStr) {
  if (!isValidDateStr(dateStr)) return '';
  return `${dateStr.replace(/-/g, '.')} (${WEEKDAYS_KO[weekdayOf(dateStr)]})`;
}

export function formatDateShort(dateStr) {
  if (!isValidDateStr(dateStr)) return '';
  const [, m, d] = dateStr.split('-');
  return `${+m}월 ${+d}일 (${WEEKDAYS_KO[weekdayOf(dateStr)]})`;
}

export function ddayLabel(daysLeft) {
  if (typeof daysLeft !== 'number' || daysLeft < 0) return '';
  return daysLeft === 0 ? 'D-day' : `D-${daysLeft}`;
}

const seoulIso = (input) => {
  const ms = toMs(input);
  return ms === null ? null : new Date(ms + 9 * 3600 * 1000).toISOString();
};

export function formatSeoulTime(input) {
  const iso = seoulIso(input);
  return iso ? iso.slice(11, 16) : '';
}

// 서울 기준 'YYYY.MM.DD HH:MM'
export function formatSeoulDateTime(input) {
  const iso = seoulIso(input);
  return iso ? `${iso.slice(0, 10).replace(/-/g, '.')} ${iso.slice(11, 16)}` : '';
}

// 개최 기간 표시. 둘 다 없으면 null
export function formatRange(start, end) {
  const s = isValidDateStr(start) ? start : null;
  const e = isValidDateStr(end) ? end : null;
  if (!s && !e) return null;
  if (!s) return `${formatDateKo(e)} 종료`;
  if (!e || e === s) return formatDateKo(s);
  const endText = s.slice(0, 4) === e.slice(0, 4) ? formatDateKo(e).slice(5) : formatDateKo(e);
  return `${formatDateKo(s)} – ${endText}`;
}

// getDeadline() 결과를 화면 문구로. 없는 정보는 추측하지 않는다.
export function deadlineText(deadline) {
  if (deadline.kind === 'exact') {
    return { primary: `${formatDateKo(deadline.date)} ${formatSeoulTime(deadline.ms)}`, note: '서울 시간 기준' };
  }
  if (deadline.kind === 'dateOnly') {
    return { primary: formatDateKo(deadline.date), note: '마감 시간 확인 필요' };
  }
  return { primary: '마감일 미확인', note: null };
}
