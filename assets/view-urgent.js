// 필터 아래 접힌 details: 마감 임박 + 출처 상태
import { h, replaceChildrenOf } from './dom.js';
import { getStatus, getDeadline } from './status.mjs';
import { ddayLabel, formatDateShort, formatSeoulDateTime, SOURCE_STATUS_LABELS } from './format.mjs';
import { externalLink } from './item-parts.js';

const MAX_URGENT = 5;

export function urgentItems(items, now) {
  return items
    .filter((item) => getStatus(item, now) === 'open')
    .map((item) => ({ item, deadline: getDeadline(item, now) }))
    .filter(({ deadline }) => deadline.kind !== 'none')
    .sort((a, b) => a.deadline.ms - b.deadline.ms)
    .slice(0, MAX_URGENT);
}

export function renderUrgent(container, { items, now, onOpen }) {
  const list = urgentItems(items, now);
  replaceChildrenOf(container,
    h('summary', {}, h('span', {}, '마감 임박'), h('span', { class: 'rail-count' }, `${list.length}건`)),
    list.length
      ? h('ul', { class: 'urgent-list' }, list.map(({ item, deadline }) => h('li', {},
        h('button', { type: 'button', class: 'urgent-item', onclick: (e) => onOpen(item.id, e.currentTarget) },
          h('span', { class: 'urgent-title' }, item.title),
          h('span', { class: 'urgent-when' }, `${ddayLabel(deadline.daysLeft)} · ${formatDateShort(deadline.date)}`),
          deadline.needsTimeCheck ? h('span', { class: 'urgent-when date-note' }, '마감 시각 미확인') : null))))
      : h('p', { class: 'side-empty' }, '마감일이 확인된 모집중 기회가 없습니다.'));
}

function sourceRow(source) {
  const link = externalLink(source.url, '출처 열기');
  const success = source.lastSuccessAt ? `마지막 성공 확인 ${formatSeoulDateTime(source.lastSuccessAt)}` : '성공 확인 기록 없음';
  return h('li', {},
    h('p', { class: 'source-name' }, source.name || source.id),
    h('p', { class: 'source-meta' },
      h('span', { class: `source-state-${source.status}` }, SOURCE_STATUS_LABELS[source.status] || '상태 미확인'),
      ` · ${success}`),
    link);
}

export function renderSources(container, { data }) {
  const sources = data.sources || [];
  const note = data.updatedAt ? `마지막 갱신 ${formatSeoulDateTime(data.updatedAt)}` : '갱신 기록 없음';
  const missing = data.statusLoaded ? null : h('p', { class: 'side-empty' }, '최근 수집 상태를 불러오지 못했습니다. 저장된 출처 정보를 표시합니다.');
  replaceChildrenOf(container,
    h('summary', {}, h('span', {}, '출처 상태'), h('span', { class: 'source-summary-note' }, note)),
    missing,
    sources.length
      ? h('ul', { class: 'source-list' }, sources.map(sourceRow))
      : h('p', { class: 'side-empty' }, '등록된 출처 정보가 없습니다.'));
}
