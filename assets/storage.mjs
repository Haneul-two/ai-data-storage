// localStorage(저장 목록·필터)와 URL query 처리. storage 객체를 인자로 받아 테스트 가능하게 한다.
import { DEFAULT_FILTERS, sanitizeFilters } from './filters.mjs';

const SAVED_KEY = 'aob.saved.v1';
const FILTERS_KEY = 'aob.filters.v1';
const URL_KEYS = ['q', 'kind', 'status', 'mode', 'sort', 'view'];

// localStorage 접근 자체가 예외일 수 있다(사생활 보호 모드, 쿠키 차단)
export function getStorage(win) {
  try {
    return win && win.localStorage ? win.localStorage : null;
  } catch {
    return null;
  }
}

function failReason(err) {
  const name = err && err.name;
  return name === 'QuotaExceededError' || name === 'NS_ERROR_DOM_QUOTA_REACHED' ? 'quota' : 'unavailable';
}

function writeJson(storage, key, value) {
  if (!storage) return { ok: false, reason: 'unavailable' };
  try {
    storage.setItem(key, JSON.stringify(value));
    return { ok: true };
  } catch (err) {
    return { ok: false, reason: failReason(err) };
  }
}

// status: 'ok' | 'corrupt' | 'unavailable'
export function loadSavedIds(storage) {
  if (!storage) return { ids: [], status: 'unavailable' };
  let raw;
  try {
    raw = storage.getItem(SAVED_KEY);
  } catch {
    return { ids: [], status: 'unavailable' };
  }
  if (raw === null) return { ids: [], status: 'ok' };
  try {
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return { ids: [], status: 'corrupt' };
    const ids = [...new Set(parsed.filter((v) => typeof v === 'string' && v))];
    return { ids, status: 'ok' };
  } catch {
    return { ids: [], status: 'corrupt' };
  }
}

export function saveSavedIds(storage, ids) {
  return writeJson(storage, SAVED_KEY, ids);
}

export function toggleSaved(ids, id) {
  return ids.includes(id) ? ids.filter((x) => x !== id) : [...ids, id];
}

export function orphanIds(savedIds, items) {
  const known = new Set(items.map((i) => i.id));
  return savedIds.filter((id) => !known.has(id));
}

// 검색어와 저장 보기는 일시적 상태라 저장하지 않는다(URL로만 공유)
export function saveFilters(storage, filters) {
  const { q, saved, ...persisted } = filters;
  return writeJson(storage, FILTERS_KEY, persisted);
}

export function loadFilters(storage) {
  if (!storage) return null;
  try {
    const raw = storage.getItem(FILTERS_KEY);
    if (raw === null) return null;
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) return null;
    return sanitizeFilters(parsed);
  } catch {
    return null;
  }
}

// URL에 있는 키는 URL 값(잘못되면 기본값), 없는 키는 저장값, 둘 다 없으면 기본값
export function resolveFilters(search, stored) {
  const params = new URLSearchParams(search);
  const base = stored ? sanitizeFilters(stored) : { ...DEFAULT_FILTERS };
  const fromUrl = {};
  for (const key of URL_KEYS) {
    if (params.has(key)) fromUrl[key] = params.get(key);
  }
  if (params.has('saved')) fromUrl.saved = params.get('saved') === '1';
  const defaults = { ...DEFAULT_FILTERS };
  // 잘못된 URL 값은 저장값이 아니라 기본값으로: 먼저 URL 키만 검증해 기본값으로 채운다
  const checked = sanitizeFilters({ ...defaults, ...fromUrl });
  const out = { ...base };
  for (const key of Object.keys(fromUrl)) out[key] = checked[key];
  return out;
}

export function serializeFilters(filters) {
  const params = new URLSearchParams();
  for (const key of URL_KEYS) {
    if (filters[key] !== DEFAULT_FILTERS[key]) params.set(key, filters[key]);
  }
  if (filters.saved) params.set('saved', '1');
  return params.toString();
}
