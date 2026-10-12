import { test } from 'node:test';
import assert from 'node:assert/strict';
import { formatRange, deadlineText, formatSeoulTime, KIND_LABELS, MODE_LABELS, SOURCE_STATUS_LABELS } from '../assets/format.mjs';
import { getDeadline } from '../assets/status.mjs';
import { NOW, makeItem } from './helpers.mjs';

test('formatRange: 같은 해 범위는 뒤쪽 연도를 생략한다', () => {
  assert.equal(formatRange('2026-11-03', '2026-11-05'), '2026.11.03 (화) – 11.05 (목)');
});

test('formatRange: 해가 다르면 둘 다 연도를 쓴다', () => {
  assert.equal(formatRange('2026-12-30', '2027-01-02'), '2026.12.30 (수) – 2027.01.02 (토)');
});

test('formatRange: 하루짜리/시작만/종료만/없음', () => {
  assert.equal(formatRange('2026-11-03', '2026-11-03'), '2026.11.03 (화)');
  assert.equal(formatRange('2026-11-03', null), '2026.11.03 (화)');
  assert.equal(formatRange(null, '2026-11-05'), '2026.11.05 (목) 종료');
  assert.equal(formatRange(null, null), null);
  assert.equal(formatRange('bad', 'worse'), null);
});

test('formatSeoulTime은 서울 HH:MM', () => {
  assert.equal(formatSeoulTime('2026-10-26T17:00:00-04:00'), '06:00');
  assert.equal(formatSeoulTime('2026-10-02T14:59:00Z'), '23:59');
});

test('deadlineText: 정확한 시각은 서울 날짜·시각과 기준 안내', () => {
  const d = getDeadline(makeItem({ deadlineAt: '2026-10-26T17:00:00-04:00' }), NOW);
  assert.deepEqual(deadlineText(d), { primary: '2026.10.27 (화) 06:00', note: '서울 시간 기준' });
});

test('deadlineText: 날짜만 있으면 시간 확인 필요를 붙인다', () => {
  const d = getDeadline(makeItem({ deadlineDate: '2026-10-05' }), NOW);
  assert.deepEqual(deadlineText(d), { primary: '2026.10.05 (월)', note: '마감 시각 미확인' });
});

test('deadlineText: 없으면 추측하지 않고 미확인이라고 쓴다', () => {
  const d = getDeadline(makeItem({}), NOW);
  assert.deepEqual(deadlineText(d), { primary: '마감일 미확인', note: null });
});

test('라벨 표는 모든 값을 덮는다', () => {
  assert.deepEqual(Object.keys(KIND_LABELS).sort(), ['contest', 'event', 'hackathon']);
  assert.deepEqual(Object.keys(MODE_LABELS).sort(), ['hybrid', 'offline', 'online', 'unknown']);
  assert.deepEqual(Object.keys(SOURCE_STATUS_LABELS).sort(), ['blocked', 'error', 'ok']);
});
