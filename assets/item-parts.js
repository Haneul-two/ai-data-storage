// 목록 행·상세·사이드에서 공유하는 작은 조각들
import { h } from './dom.js';
import { icon } from './icons.js';
import { getStatus, getDeadline, STATUS_LABELS } from './status.mjs';
import { KIND_LABELS, MODE_LABELS, ddayLabel } from './format.mjs';
import { itemFlags } from './data.mjs';
import { safeHttpsUrl } from './safe-url.mjs';

const SOON_DAYS = 7;

export function kindPill(item) {
  return h('span', { class: 'kind' }, KIND_LABELS[item.kind]);
}

export function statusBadge(item, now) {
  const status = getStatus(item, now);
  return h('span', { class: `status status-${status}` }, STATUS_LABELS[status]);
}

export function ddayBadge(item, now) {
  if (getStatus(item, now) !== 'open') return null;
  const { daysLeft } = getDeadline(item, now);
  const label = ddayLabel(daysLeft);
  return label ? h('span', { class: daysLeft <= SOON_DAYS ? 'dday is-soon' : 'dday' }, label) : null;
}

// '출처 재확인 필요' · '수집 지연' · '참가 조건 확인 필요'. 행에서는 참가 열이 자격을 직접 보여주므로 skipEligibility로 뺀다
export function flagBadges(item, sources, now, { skipEligibility = false } = {}) {
  const f = itemFlags(item, sources, now);
  const flags = [];
  if (f.recheck) flags.push('출처 재확인 필요');
  else if (f.sourceDelayed) flags.push('수집 지연');
  if (f.eligibilityCheck && !skipEligibility) flags.push('참가 조건 확인 필요');
  return flags.map((text) => h('span', { class: 'flag' }, text));
}

export function modeLine(item) {
  const mode = MODE_LABELS[item.mode] || MODE_LABELS.unknown;
  const hasRegion = item.region && !(item.mode === 'unknown' && item.region === '미정');
  return hasRegion ? `${mode} · ${item.region}` : mode;
}

// 저장 버튼. 표시 문구만 바뀌고 접근 가능한 이름은 고정(상태는 aria-pressed)
export function saveButton(item, saved, onToggle, extraClass = '') {
  const btn = h('button', {
    type: 'button',
    class: `btn ${extraClass}`.trim(),
    'data-save-id': item.id,
    'aria-label': `${item.title} 저장`,
    'aria-pressed': saved ? 'true' : 'false',
    onclick: () => onToggle(item.id),
  }, icon('bookmark'), h('span', { class: 'save-label' }, saved ? '저장됨' : '저장'));
  return btn;
}

export function syncSaveButton(btn, saved) {
  btn.setAttribute('aria-pressed', saved ? 'true' : 'false');
  const label = btn.querySelector('.save-label');
  if (label) label.textContent = saved ? '저장됨' : '저장';
}

// 안전한 https 링크만 만든다. 안전하지 않으면 null
export function externalLink(href, text, className = '') {
  const safe = safeHttpsUrl(href);
  if (!safe) return null;
  return h('a', { href: safe, target: '_blank', rel: 'noopener noreferrer', class: className }, text);
}
