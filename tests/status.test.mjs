import { test } from 'node:test';
import assert from 'node:assert/strict';
import { getStatus, getDeadline } from '../assets/status.mjs';
import { NOW, makeItem } from './helpers.mjs';

const st = (o, now = NOW) => getStatus(makeItem(o), now);

test('① 종료일이 서울 오늘 이전이면 미래 마감이 있어도 ended', () => {
  assert.equal(st({ endDate: '2026-10-01', deadlineAt: '2026-10-30T00:00:00Z' }), 'ended');
});

test('종료일이 오늘이면 아직 ended가 아니다', () => {
  assert.equal(st({ startDate: '2026-10-01', endDate: '2026-10-02' }), 'ongoing');
});

test('② 출처가 명시 closed이면 미래 마감보다 우선한다', () => {
  assert.equal(st({ sourceStatus: 'closed', deadlineAt: '2026-10-30T00:00:00Z' }), 'closed');
});

test('③ 정확한 deadlineAt은 절대 시각으로 비교한다', () => {
  assert.equal(st({ deadlineAt: '2026-10-02T02:00:00Z' }), 'closed'); // 서울 11:00, 이미 지남
  assert.equal(st({ deadlineAt: '2026-10-02T10:00:00Z' }), 'open'); // 서울 19:00, 아직 남음
});

test('④ date-only 마감은 서울 당일 끝까지 open', () => {
  assert.equal(st({ deadlineDate: '2026-10-02' }), 'open');
  assert.equal(st({ deadlineDate: '2026-10-01' }), 'closed');
});

test('서울 기준: UTC로는 아직 10/01이어도 서울은 10/02이므로 10/01 마감은 closed', () => {
  const now = '2026-10-01T16:00:00Z'; // 서울 10/02 01:00
  assert.equal(st({ deadlineDate: '2026-10-01' }, now), 'closed');
  assert.equal(st({ deadlineDate: '2026-10-02' }, now), 'open');
});

test('deadlineAt이 있으면 deadlineDate보다 우선한다', () => {
  assert.equal(st({ deadlineAt: '2026-10-03T00:00:00Z', deadlineDate: '2026-10-01' }), 'open');
});

test('Devpost 10/26 17:00 EDT 마감은 서울 10/27 06:00까지 open', () => {
  const it = makeItem({ deadlineAt: '2026-10-26T17:00:00-04:00' });
  assert.equal(getStatus(it, '2026-10-27T05:59:00+09:00'), 'open');
  assert.equal(getStatus(it, '2026-10-27T06:01:00+09:00'), 'closed');
});

test('⑤ 접수 시작일이 미래면 upcoming (마감이 미래여도)', () => {
  assert.equal(st({ registrationStartDate: '2026-10-10', deadlineDate: '2026-10-30' }), 'upcoming');
});

test('접수 시작일이 오늘이거나 지났고 마감이 미래면 open', () => {
  assert.equal(st({ registrationStartDate: '2026-10-02', deadlineDate: '2026-10-30' }), 'open');
});

test('⑥ sourceStatus open이면 마감 정보가 없어도 open', () => {
  assert.equal(st({ sourceStatus: 'open' }), 'open');
});

test('⑧ 마감을 모르고 개최일만 미래면 open이 아니라 upcoming', () => {
  assert.equal(st({ kind: 'event', startDate: '2026-11-05' }), 'upcoming');
});

test('⑦ 개최 기간 중이고 마감 정보가 없으면 ongoing', () => {
  assert.equal(st({ startDate: '2026-10-01', endDate: '2026-10-03' }), 'ongoing');
});

test('마감이 아직 남은 개최 중 항목은 open (⑥이 ⑦보다 먼저)', () => {
  assert.equal(st({ startDate: '2026-10-01', endDate: '2026-10-03', deadlineDate: '2026-10-05' }), 'open');
});

test('⑨ 날짜가 전혀 없으면 unknown', () => {
  assert.equal(st({}), 'unknown');
});

test('종료일 없이 과거 시작일만 있으면 unknown (종료를 추측하지 않는다)', () => {
  assert.equal(st({ startDate: '2026-09-01' }), 'unknown');
});

test('getDeadline: 정확한 시각은 서울 날짜로 환산하고 D-day를 준다', () => {
  const d = getDeadline(makeItem({ deadlineAt: '2026-10-26T17:00:00-04:00' }), NOW);
  assert.equal(d.kind, 'exact');
  assert.equal(d.date, '2026-10-27');
  assert.equal(d.daysLeft, 25);
  assert.equal(d.needsTimeCheck, false);
});

test('getDeadline: date-only는 시간 확인 필요', () => {
  const d = getDeadline(makeItem({ deadlineDate: '2026-10-02' }), NOW);
  assert.equal(d.kind, 'dateOnly');
  assert.equal(d.daysLeft, 0);
  assert.equal(d.needsTimeCheck, true);
});

test('getDeadline: 없으면 none', () => {
  const d = getDeadline(makeItem({ startDate: '2026-11-01' }), NOW);
  assert.equal(d.kind, 'none');
  assert.equal(d.date, null);
});
