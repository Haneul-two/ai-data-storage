import { test } from 'node:test';
import assert from 'node:assert/strict';
import { seoulDate, daysBetween, isValidDateStr, endOfSeoulDateMs } from '../assets/time.mjs';
import { formatDateKo, ddayLabel } from '../assets/format.mjs';

test('서울 날짜는 UTC 날짜와 다를 수 있다 (UTC+9)', () => {
  assert.equal(seoulDate('2026-10-01T14:59:59Z'), '2026-10-01');
  assert.equal(seoulDate('2026-10-01T15:00:00Z'), '2026-10-02');
  assert.equal(seoulDate('2026-10-02T14:59:59Z'), '2026-10-02');
  assert.equal(seoulDate('2026-10-02T15:00:00Z'), '2026-10-03');
});

test('Devpost 마감 10/26 17:00 EDT는 서울 10/27이다', () => {
  assert.equal(seoulDate('2026-10-26T17:00:00-04:00'), '2026-10-27');
});

test('Date 객체와 epoch ms도 받는다', () => {
  assert.equal(seoulDate(new Date('2026-12-31T15:30:00Z')), '2027-01-01');
  assert.equal(seoulDate(Date.parse('2026-12-31T14:00:00Z')), '2026-12-31');
});

test('잘못된 시각은 null', () => {
  assert.equal(seoulDate('not-a-date'), null);
  assert.equal(seoulDate(null), null);
});

test('daysBetween은 월 경계를 넘어 정수 일수를 준다', () => {
  assert.equal(daysBetween('2026-10-02', '2026-10-05'), 3);
  assert.equal(daysBetween('2026-09-30', '2026-10-02'), 2);
  assert.equal(daysBetween('2026-10-05', '2026-10-02'), -3);
  assert.equal(daysBetween('2026-10-02', '2026-10-27'), 25);
});

test('isValidDateStr은 존재하지 않는 날짜를 거부한다', () => {
  assert.equal(isValidDateStr('2026-02-28'), true);
  assert.equal(isValidDateStr('2026-02-30'), false);
  assert.equal(isValidDateStr('2026-2-3'), false);
  assert.equal(isValidDateStr(null), false);
});

test('endOfSeoulDateMs는 서울 당일 23:59:59.999', () => {
  assert.equal(endOfSeoulDateMs('2026-10-02'), Date.parse('2026-10-02T14:59:59.999Z'));
});

test('formatDateKo는 요일을 붙인다', () => {
  assert.equal(formatDateKo('2026-10-27'), '2026.10.27 (화)');
  assert.equal(formatDateKo('2026-10-02'), '2026.10.02 (금)');
  assert.equal(formatDateKo(null), '');
});

test('ddayLabel', () => {
  assert.equal(ddayLabel(3), 'D-3');
  assert.equal(ddayLabel(0), 'D-day');
  assert.equal(ddayLabel(-2), '');
  assert.equal(ddayLabel(null), '');
});
