import { test } from 'node:test';
import assert from 'node:assert/strict';
import { buildNotices } from '../assets/notices.mjs';
import { NOW } from './helpers.mjs';

const okSource = (o = {}) => ({ id: 's1', name: '출처1', status: 'ok', ...o });
const base = (o = {}) => ({
  data: { items: [{ id: 'a' }], sources: [okSource()], updatedAt: '2026-10-01T00:00:00Z', dropped: 0 },
  now: NOW,
  savedStatus: 'ok',
  saveFailure: null,
  refreshFailed: false,
  orphanCount: 0,
  savedView: false,
  ...o,
});
const idsOf = (args) => buildNotices(args).map((n) => n.id);

test('모든 것이 정상이면 알림이 없다', () => {
  assert.deepEqual(buildNotices(base()), []);
});

test('데이터가 오래되면 마지막 성공 날짜를 밝히고 지연 안내를 한다', () => {
  const n = buildNotices(base({ data: { ...base().data, updatedAt: '2026-09-20T00:00:00Z' } }));
  const stale = n.find((x) => x.id === 'stale');
  assert.ok(stale);
  assert.match(stale.text, /2026\.09\.20/);
  assert.match(stale.text, /수집이 지연/);
  assert.equal(stale.tone, 'warn');
});

test('수집된 데이터가 전혀 없으면 별도 안내', () => {
  const ids = idsOf(base({ data: { items: [], sources: [], updatedAt: null, dropped: 0 } }));
  assert.deepEqual(ids, ['no-data']);
});

test('실패한 출처 이름을 알리되 기술 메시지는 노출하지 않는다', () => {
  const sources = [okSource(), okSource({ id: 's2', name: '위비티', status: 'error', message: 'HTTP 500 traceback' }), okSource({ id: 's3', name: 'Devpost', status: 'blocked' })];
  const n = buildNotices(base({ data: { ...base().data, sources } })).find((x) => x.id === 'sources');
  assert.ok(n);
  assert.match(n.text, /위비티/);
  assert.match(n.text, /Devpost/);
  assert.doesNotMatch(n.text, /HTTP|traceback/);
});

test('출처가 많으면 3곳까지만 이름을 쓰고 나머지는 개수로', () => {
  const sources = ['a', 'b', 'c', 'd', 'e'].map((x) => okSource({ id: x, name: `S-${x}`, status: 'error' }));
  const n = buildNotices(base({ data: { ...base().data, sources } })).find((x) => x.id === 'sources');
  assert.match(n.text, /외 2곳/);
});

test('저장소 손상/사용 불가/쓰기 실패를 각각 알린다', () => {
  assert.ok(idsOf(base({ savedStatus: 'corrupt' })).includes('saved-corrupt'));
  assert.ok(idsOf(base({ savedStatus: 'unavailable' })).includes('saved-unavailable'));
  const n = buildNotices(base({ saveFailure: 'quota' })).find((x) => x.id === 'save-failed');
  assert.ok(n);
  assert.match(n.text, /기록하지 못했/);
});

test('새로고침 실패는 기존 데이터를 보여주는 중임을 알린다', () => {
  const n = buildNotices(base({ refreshFailed: true })).find((x) => x.id === 'refresh-failed');
  assert.equal(n.tone, 'danger');
  assert.match(n.text, /이전에 불러온/);
});

test('사라진 저장 항목 안내는 저장 보기에서만 건수와 함께 나온다', () => {
  assert.deepEqual(idsOf(base({ orphanCount: 2, savedView: false })), []);
  const n = buildNotices(base({ orphanCount: 2, savedView: true })).find((x) => x.id === 'orphans');
  assert.match(n.text, /2건/);
  assert.match(n.text, /보관/);
});

test('형식이 맞지 않아 제외한 항목 수를 알린다', () => {
  const n = buildNotices(base({ data: { ...base().data, dropped: 3 } })).find((x) => x.id === 'dropped');
  assert.match(n.text, /3건/);
});

const EMPTY = { items: [], sources: [], updatedAt: null, dropped: 0 };

test('로딩/오류 중에는 미수집·신선도·출처 알림을 쓰지 않는다', () => {
  for (const phase of ['loading', 'error']) {
    assert.deepEqual(idsOf(base({ phase, data: EMPTY })), [], phase);
    const stale = { ...base().data, updatedAt: '2026-09-01T00:00:00Z', sources: [okSource({ status: 'error' })] };
    assert.deepEqual(idsOf(base({ phase, data: stale })), [], phase);
  }
});

test('로딩/오류 중에도 브라우저 저장 경고는 유지한다', () => {
  for (const phase of ['loading', 'error']) {
    const ids = idsOf(base({ phase, data: EMPTY, savedStatus: 'corrupt', saveFailure: 'quota' }));
    assert.deepEqual(ids, ['saved-corrupt', 'save-failed'], phase);
  }
});

test('ready 빈 데이터에서만 미수집 안내가 나온다', () => {
  assert.deepEqual(idsOf(base({ phase: 'ready', data: EMPTY })), ['no-data']);
});
