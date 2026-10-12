import { test } from 'node:test';
import { readFileSync } from 'node:fs';
import assert from 'node:assert/strict';
import {
  DEFAULT_FILTERS, sanitizeFilters, applyFilters, sortItems, selectItems, facetCounts, activeFilterCount,
} from '../assets/filters.mjs';
import { NOW, makeItem, sampleItems } from './helpers.mjs';

const ids = (items) => items.map((i) => i.id);
const ctx = { now: NOW, savedIds: new Set() };
const run = (f, c = ctx) => ids(applyFilters(sampleItems(), { ...DEFAULT_FILTERS, ...f }, c));

test('기본 필터는 마감·종료 항목을 제외한다', () => {
  assert.deepEqual(run({}).sort(), ['a', 'c', 'd', 'f']);
});

test('상태 필터: 마감·종료는 closed+ended를 함께 보여준다', () => {
  assert.deepEqual(run({ status: 'closed' }).sort(), ['b', 'e']);
});

test('상태 필터: open / upcoming / ongoing / unknown', () => {
  assert.deepEqual(run({ status: 'open' }).sort(), ['a', 'f']); // f는 마감 10/5가 남아 open
  assert.deepEqual(run({ status: 'upcoming' }), ['c']);
  assert.deepEqual(run({ status: 'ongoing' }), []);
  assert.deepEqual(run({ status: 'unknown' }), ['d']);
});

test('유형·방식 필터', () => {
  assert.deepEqual(run({ kind: 'event' }).sort(), ['c', 'f']);
  assert.deepEqual(run({ mode: 'online' }).sort(), ['a', 'd']);
  assert.deepEqual(run({ kind: 'event', mode: 'offline' }), ['f']);
});

test('검색: 제목·주최·태그·설명을 대소문자 구분 없이 찾는다', () => {
  assert.deepEqual(run({ q: 'vision' }), ['a']);
  assert.deepEqual(run({ q: 'beta corp' }), ['c']);
  assert.deepEqual(run({ q: 'IMAGE MODELS' }), ['a']);
  assert.deepEqual(run({ q: '공모전', status: 'closed' }), ['b']);
});

test('검색: 여러 단어는 모두 포함해야 한다', () => {
  assert.deepEqual(run({ q: 'vision alpha' }), ['a']);
  assert.deepEqual(run({ q: 'vision beta' }), []);
});

test('저장 필터는 같은 조건에서 저장 id만 남긴다', () => {
  const c = { now: NOW, savedIds: new Set(['a', 'b', 'zzz']) };
  assert.deepEqual(run({ saved: true }, c), ['a']);
  assert.deepEqual(run({ saved: true, status: 'closed' }, c), ['b']);
});

test('facetCounts: 각 탭 수는 그 탭을 눌렀을 때의 결과 수와 같다', () => {
  const filters = { ...DEFAULT_FILTERS, q: 'a', mode: 'all' };
  const counts = facetCounts(sampleItems(), filters, ctx);
  for (const kind of ['all', 'event', 'contest', 'hackathon']) {
    const n = applyFilters(sampleItems(), { ...filters, kind }, ctx).length;
    assert.equal(counts.kind[kind], n, `kind=${kind}`);
  }
  for (const status of ['all', 'open', 'upcoming', 'ongoing', 'closed', 'unknown']) {
    const n = applyFilters(sampleItems(), { ...filters, status }, ctx).length;
    assert.equal(counts.status[status], n, `status=${status}`);
  }
  for (const mode of ['all', 'online', 'offline', 'hybrid']) {
    const n = applyFilters(sampleItems(), { ...filters, mode }, ctx).length;
    assert.equal(counts.mode[mode], n, `mode=${mode}`);
  }
});

test('sanitizeFilters: 잘못된 값은 기본값으로 되돌린다', () => {
  const f = sanitizeFilters({ kind: 'news', status: 5, mode: 'moon', sort: 'x', view: 'grid', saved: 'yes', q: 123 });
  assert.deepEqual(f, DEFAULT_FILTERS);
});

test('sanitizeFilters: 유효한 값은 유지하고 q는 다듬어 길이를 제한한다', () => {
  const f = sanitizeFilters({ kind: 'contest', status: 'closed', mode: 'hybrid', sort: 'start', view: 'calendar', saved: true, q: '  ' + 'x'.repeat(300) + ' ' });
  assert.equal(f.kind, 'contest');
  assert.equal(f.status, 'closed');
  assert.equal(f.sort, 'start');
  assert.equal(f.view, 'calendar');
  assert.equal(f.saved, true);
  assert.equal(f.q.length, 100);
});

test('sanitizeFilters: null/배열 입력도 안전하다', () => {
  assert.deepEqual(sanitizeFilters(null), DEFAULT_FILTERS);
  assert.deepEqual(sanitizeFilters([1, 2]), DEFAULT_FILTERS);
});

test('정렬 deadline: 남은 마감 임박순 → 지난 마감 최근순 → 미정 마지막', () => {
  const items = [
    makeItem({ id: 'unk' }),
    makeItem({ id: 'past', deadlineDate: '2026-09-20' }),
    makeItem({ id: 'far', deadlineAt: '2026-10-30T00:00:00Z' }),
    makeItem({ id: 'near', deadlineAt: '2026-10-03T00:00:00Z' }),
    makeItem({ id: 'today', deadlineDate: '2026-10-02' }),
    makeItem({ id: 'past2', deadlineDate: '2026-09-28' }),
  ];
  assert.deepEqual(ids(sortItems(items, 'deadline', NOW)), ['today', 'near', 'far', 'past2', 'past', 'unk']);
});

test('정렬 start: 개최일 빠른 순, 없으면 마지막', () => {
  const items = [
    makeItem({ id: 'x' }),
    makeItem({ id: 'late', startDate: '2026-12-01' }),
    makeItem({ id: 'early', startDate: '2026-10-05' }),
  ];
  assert.deepEqual(ids(sortItems(items, 'start', NOW)), ['early', 'late', 'x']);
});

test('정렬 verified: 최근 확인 순', () => {
  const sorted = sortItems(sampleItems(), 'verified', NOW);
  assert.deepEqual(ids(sorted).slice(0, 3), ['c', 'e', 'f']); // e,f는 기본 verifiedAt(10-02 00:00)으로 동률 → 입력 순서
  assert.equal(ids(sorted).at(-1), 'd');
});

test('정렬은 입력 배열을 바꾸지 않고, 같은 키는 입력 순서를 유지한다', () => {
  const items = [makeItem({ id: 'p' }), makeItem({ id: 'q' }), makeItem({ id: 'r' })];
  const before = ids(items);
  const out = sortItems(items, 'deadline', NOW);
  assert.deepEqual(ids(items), before);
  assert.deepEqual(ids(out), ['p', 'q', 'r']);
});

test('알 수 없는 정렬 키는 deadline으로 처리한다', () => {
  const a = ids(sortItems(sampleItems(), 'bogus', NOW));
  const b = ids(sortItems(sampleItems(), 'deadline', NOW));
  assert.deepEqual(a, b);
});

test('selectItems는 필터 후 정렬한다', () => {
  const out = selectItems(sampleItems(), { ...DEFAULT_FILTERS }, ctx);
  assert.deepEqual(ids(out), ['f', 'a', 'c', 'd']); // f(10/5 date-only) < a(10/10) < 미정 c,d (입력 순)
});

test('activeFilterCount는 기본값과 다른 상태·방식만 센다', () => {
  assert.equal(activeFilterCount(DEFAULT_FILTERS), 0);
  assert.equal(activeFilterCount({ ...DEFAULT_FILTERS, status: 'open', mode: 'online', kind: 'event', q: 'x' }), 2);
});

test('검색: 수집된 NVIDIA AI Day 항목을 한국어 표현으로 찾는다', () => {
  const doc = JSON.parse(readFileSync(new URL('../data/opportunities.json', import.meta.url), 'utf8'));
  const items = doc.items.filter((i) => i.sourceId === 'nvidia');
  assert.equal(items.length, 1);
  const f = { ...DEFAULT_FILTERS, kind: 'event', q: '엔비디아 AI 데이 서울 2026' };
  assert.deepEqual(ids(applyFilters(items, f, { now: '2026-10-12T00:00:00Z', savedIds: new Set() })), [items[0].id]);
});
