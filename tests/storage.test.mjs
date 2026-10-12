import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  getStorage, loadSavedIds, saveSavedIds, toggleSaved, orphanIds,
  loadFilters, saveFilters, resolveFilters, serializeFilters,
} from '../assets/storage.mjs';
import { DEFAULT_FILTERS } from '../assets/filters.mjs';

function fakeStorage(initial = {}, { failSet = null, failGet = null } = {}) {
  const map = new Map(Object.entries(initial));
  return {
    map,
    getItem(k) { if (failGet) throw failGet; return map.has(k) ? map.get(k) : null; },
    setItem(k, v) { if (failSet) throw failSet; map.set(k, String(v)); },
  };
}
const named = (name) => Object.assign(new Error(name), { name });

test('getStorage: 접근 자체가 예외여도 null (사생활 보호 모드 등)', () => {
  const win = { get localStorage() { throw named('SecurityError'); } };
  assert.equal(getStorage(win), null);
  assert.equal(getStorage({}), null);
});

test('loadSavedIds: 없으면 빈 목록, 정상 JSON이면 문자열 id만 중복 없이', () => {
  assert.deepEqual(loadSavedIds(fakeStorage()), { ids: [], status: 'ok' });
  const s = fakeStorage({ 'aob.saved.v1': JSON.stringify(['a', 'b', 'a', 3, null, '']) });
  assert.deepEqual(loadSavedIds(s), { ids: ['a', 'b'], status: 'ok' });
});

test('loadSavedIds: 손상된 JSON은 corrupt로 알리고 빈 목록', () => {
  const s = fakeStorage({ 'aob.saved.v1': '{not json' });
  assert.deepEqual(loadSavedIds(s), { ids: [], status: 'corrupt' });
});

test('loadSavedIds: 배열이 아닌 JSON도 corrupt', () => {
  const s = fakeStorage({ 'aob.saved.v1': '{"a":1}' });
  assert.equal(loadSavedIds(s).status, 'corrupt');
});

test('loadSavedIds: 저장소를 못 쓰면 unavailable', () => {
  assert.deepEqual(loadSavedIds(null), { ids: [], status: 'unavailable' });
  assert.equal(loadSavedIds(fakeStorage({}, { failGet: named('SecurityError') })).status, 'unavailable');
});

test('saveSavedIds: 성공하면 ok와 함께 실제로 기록한다', () => {
  const s = fakeStorage();
  assert.deepEqual(saveSavedIds(s, ['a', 'b']), { ok: true });
  assert.equal(s.map.get('aob.saved.v1'), '["a","b"]');
});

test('saveSavedIds: 용량 초과/접근 불가를 구분해 실패를 돌려준다', () => {
  const q = saveSavedIds(fakeStorage({}, { failSet: named('QuotaExceededError') }), ['a']);
  assert.deepEqual(q, { ok: false, reason: 'quota' });
  const u = saveSavedIds(fakeStorage({}, { failSet: named('SecurityError') }), ['a']);
  assert.deepEqual(u, { ok: false, reason: 'unavailable' });
  assert.deepEqual(saveSavedIds(null, ['a']), { ok: false, reason: 'unavailable' });
});

test('toggleSaved는 원본을 바꾸지 않고 추가/제거한다', () => {
  const base = ['a'];
  assert.deepEqual(toggleSaved(base, 'b'), ['a', 'b']);
  assert.deepEqual(toggleSaved(base, 'a'), []);
  assert.deepEqual(base, ['a']);
});

test('orphanIds: 데이터에서 사라진 저장 id를 찾되 id는 지우지 않는다', () => {
  const items = [{ id: 'a' }, { id: 'c' }];
  assert.deepEqual(orphanIds(['a', 'b', 'z'], items), ['b', 'z']);
  assert.deepEqual(orphanIds([], items), []);
});

test('serializeFilters: 기본값은 URL에서 생략한다', () => {
  assert.equal(serializeFilters(DEFAULT_FILTERS), '');
  const qs = serializeFilters({ ...DEFAULT_FILTERS, kind: 'event', status: 'open', q: 'LLM 해커톤', saved: true });
  const p = new URLSearchParams(qs);
  assert.equal(p.get('kind'), 'event');
  assert.equal(p.get('status'), 'open');
  assert.equal(p.get('q'), 'LLM 해커톤');
  assert.equal(p.get('saved'), '1');
  assert.equal(p.has('mode'), false);
});

test('resolveFilters: URL 값이 저장값보다 우선한다', () => {
  const stored = { ...DEFAULT_FILTERS, kind: 'contest', status: 'closed' };
  const f = resolveFilters('?kind=event', stored);
  assert.equal(f.kind, 'event');
  assert.equal(f.status, 'closed'); // URL에 없는 키는 저장값
});

test('resolveFilters: URL이 없으면 저장값, 둘 다 없으면 기본값', () => {
  assert.equal(resolveFilters('', { ...DEFAULT_FILTERS, mode: 'online' }).mode, 'online');
  assert.deepEqual(resolveFilters('', null), DEFAULT_FILTERS);
});

test('resolveFilters: URL의 잘못된 값은 저장값이 아니라 기본값으로 안전하게 되돌린다', () => {
  const f = resolveFilters('?status=bogus&kind=news&view=zzz', { ...DEFAULT_FILTERS, status: 'closed' });
  assert.equal(f.status, DEFAULT_FILTERS.status);
  assert.equal(f.kind, DEFAULT_FILTERS.kind);
  assert.equal(f.view, DEFAULT_FILTERS.view);
});

test('saveFilters/loadFilters 왕복: 검색어와 저장 보기는 저장하지 않는다', () => {
  const s = fakeStorage();
  const r = saveFilters(s, { ...DEFAULT_FILTERS, kind: 'event', mode: 'online', q: 'secret', saved: true, view: 'calendar' });
  assert.deepEqual(r, { ok: true });
  const f = loadFilters(s);
  assert.equal(f.kind, 'event');
  assert.equal(f.mode, 'online');
  assert.equal(f.view, 'calendar');
  assert.equal(f.q, '');
  assert.equal(f.saved, false);
});

test('loadFilters: 손상된 값은 null (기본값 사용)', () => {
  assert.equal(loadFilters(fakeStorage({ 'aob.filters.v1': '###' })), null);
  assert.equal(loadFilters(fakeStorage({ 'aob.filters.v1': '[1]' })), null);
  assert.equal(loadFilters(null), null);
  assert.equal(loadFilters(fakeStorage()), null);
});

test('saveFilters 실패는 예외 없이 ok:false', () => {
  const r = saveFilters(fakeStorage({}, { failSet: named('QuotaExceededError') }), DEFAULT_FILTERS);
  assert.equal(r.ok, false);
});
