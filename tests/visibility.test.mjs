import { test } from 'node:test';
import assert from 'node:assert/strict';
import { isListed, listedItems, listedSavedCount, hiddenSavedIds } from '../assets/visibility.mjs';
import { DEFAULT_FILTERS, sanitizeFilters, applyFilters, selectItems, facetCounts, STATUS_FILTERS } from '../assets/filters.mjs';
import { resolveFilters } from '../assets/storage.mjs';
import { calendarEntries } from '../assets/calendar.mjs';
import { getStatus } from '../assets/status.mjs';
import { urgentItems } from '../assets/view-urgent.js';
import { makeItem } from './helpers.mjs';

const DEADLINE = '2026-10-10T10:00:00Z';
const exact = makeItem({ id: 'exact', deadlineAt: DEADLINE });
const at = (ms) => new Date(Date.parse(DEADLINE) + ms);

test('exact 마감: 직전·정각은 노출, 1ms 뒤부터 제외', () => {
  assert.equal(isListed(exact, at(-1)), true);
  assert.equal(isListed(exact, at(0)), true);
  assert.equal(isListed(exact, at(1)), false);
});

test('dateOnly 마감: 한국 당일 23:59:59.999까지 노출, 다음 날 00:00부터 제외', () => {
  const item = makeItem({ id: 'd', deadlineDate: '2026-10-10' });
  assert.equal(isListed(item, '2026-10-10T14:59:59.999Z'), true); // KST 10/10 23:59:59.999
  assert.equal(isListed(item, '2026-10-10T15:00:00.000Z'), false); // KST 10/11 00:00
  assert.equal(isListed(item, '2026-10-09T15:00:00.000Z'), true); // KST 10/10 00:00
});

test('마감 미확정 미래 행사는 계속 노출하고, 명시 closed·종료는 제외한다', () => {
  const now = '2026-10-02T03:00:00Z';
  assert.equal(isListed(makeItem({ kind: 'event', startDate: '2026-11-05' }), now), true);
  assert.equal(isListed(makeItem({}), now), true);
  assert.equal(isListed(makeItem({ sourceStatus: 'closed' }), now), false);
  assert.equal(isListed(makeItem({ endDate: '2026-10-01' }), now), false);
});

test('원래 getStatus 계약은 그대로 closed를 돌려준다', () => {
  assert.equal(getStatus(exact, at(1)), 'closed');
  assert.equal(getStatus(makeItem({ endDate: '2026-10-01' }), '2026-10-02T03:00:00Z'), 'ended');
});

test('status 선택지에 closed가 없고, 예전 closed 값(URL·저장)은 all로 바뀐다', () => {
  assert.equal(STATUS_FILTERS.includes('closed'), false);
  assert.equal(sanitizeFilters({ status: 'closed' }).status, 'all');
  assert.equal(resolveFilters('?status=closed', null).status, 'all');
  assert.equal(resolveFilters('', { ...DEFAULT_FILTERS, status: 'closed' }).status, 'all');
});

const pool = () => [
  makeItem({ id: 'live', kind: 'hackathon', deadlineAt: DEADLINE, startDate: '2026-10-20' }),
  makeItem({ id: 'dead', kind: 'hackathon', deadlineAt: '2026-10-01T00:00:00Z', startDate: '2026-10-05' }),
  makeItem({ id: 'over', kind: 'event', endDate: '2026-09-01' }),
  makeItem({ id: 'src', kind: 'contest', sourceStatus: 'closed' }),
  makeItem({ id: 'tbd', kind: 'event', startDate: '2026-12-01' }),
];
const ctx = (savedIds = []) => ({ now: at(-1), savedIds: new Set(savedIds) });
const ids = (xs) => xs.map((i) => i.id);

test('검색·저장·유형·정렬 모든 탐색에서 마감 항목이 빠진다', () => {
  assert.deepEqual(ids(listedItems(pool(), at(-1))), ['live', 'tbd']);
  assert.deepEqual(ids(selectItems(pool(), DEFAULT_FILTERS, ctx())).sort(), ['live', 'tbd']);
  assert.deepEqual(ids(applyFilters(pool(), { ...DEFAULT_FILTERS, q: 'Test' }, ctx())).sort(), ['live', 'tbd']);
  assert.deepEqual(ids(applyFilters(pool(), { ...DEFAULT_FILTERS, saved: true }, ctx(['live', 'dead', 'over']))), ['live']);
  for (const sort of ['deadline', 'start', 'verified']) {
    assert.equal(ids(selectItems(pool(), { ...DEFAULT_FILTERS, sort }, ctx())).includes('dead'), false, sort);
  }
});

test('facetCounts는 skip 차원에서도 마감 항목을 세지 않고 목록 건수와 같다', () => {
  const counts = facetCounts(pool(), DEFAULT_FILTERS, ctx());
  assert.equal(counts.kind.all, 2);
  assert.equal(counts.kind.hackathon, 1);
  assert.equal(counts.kind.contest, 0);
  assert.equal(counts.status.all, 2);
  assert.equal(counts.mode.all, 2);
  assert.equal(counts.status.closed, undefined);
  for (const status of STATUS_FILTERS) {
    assert.equal(counts.status[status], applyFilters(pool(), { ...DEFAULT_FILTERS, status }, ctx()).length, status);
  }
});

test('저장 건수·숨겨진 저장 id: 마감된 저장은 세지 않되 기록은 지우지 않는다', () => {
  const saved = ['live', 'dead', 'gone'];
  assert.equal(listedSavedCount(saved, pool(), at(-1)), 1);
  assert.deepEqual(hiddenSavedIds(saved, pool(), at(-1)), ['dead', 'gone']);
  assert.deepEqual(saved, ['live', 'dead', 'gone']);
});

test('달력·임박 목록·상세 진입은 같은 노출 판정을 따른다', () => {
  const shown = selectItems(pool(), DEFAULT_FILTERS, ctx());
  const { byDate, undated } = calendarEntries(shown, at(-1));
  const calIds = new Set([...byDate.values()].flat().map((e) => e.item.id).concat(ids(undated)));
  assert.deepEqual([...calIds].sort(), ['live', 'tbd']);
  assert.deepEqual(urgentItems(pool(), at(-1)).map((r) => r.item.id), ['live']);
  assert.equal(isListed(pool()[1], at(-1)), false); // 상세 진입 가드
});

test('시간이 흘러 마감 시각이 지나면 같은 항목이 목록에서 사라진다', () => {
  assert.equal(ids(selectItems(pool(), DEFAULT_FILTERS, ctx())).includes('live'), true);
  assert.equal(ids(selectItems(pool(), DEFAULT_FILTERS, { now: at(1), savedIds: new Set() })).includes('live'), false);
});
