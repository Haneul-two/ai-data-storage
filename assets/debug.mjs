// ?debug=empty|error|loading 와 ?now=ISO 는 localhost/127.0.0.1 에서만 작동한다.
const DEBUG_MODES = ['empty', 'error', 'loading'];

export function isLocalHost(hostname) {
  return hostname === 'localhost' || hostname === '127.0.0.1';
}

export function parseDebug(search, hostname) {
  const off = { enabled: false, mode: null, nowMs: null };
  if (!isLocalHost(hostname)) return off;
  const params = new URLSearchParams(search);
  const mode = DEBUG_MODES.includes(params.get('debug')) ? params.get('debug') : null;
  const nowRaw = params.get('now');
  const parsed = nowRaw ? Date.parse(nowRaw) : NaN;
  const nowMs = Number.isNaN(parsed) ? null : parsed;
  return { enabled: mode !== null || nowMs !== null, mode, nowMs };
}
