// 비교 목록 행 렌더링. 외부 문자열은 h()의 text node로만 들어간다.
import { h, replaceChildrenOf } from './dom.js';
import { getDeadline } from './status.mjs';
import { deadlineText, formatRange, formatSeoulDateTime } from './format.mjs';
import { kindPill, statusBadge, ddayBadge, flagBadges, modeLine, saveButton } from './item-parts.js';

function cell(modifier, label, ...lines) {
  return h('dl', { class: `opp-cell ${modifier}` }, h('div', {}, h('dt', {}, label), h('dd', {}, ...lines)));
}

function deadlineCell(item, ctx) {
  const raw = getDeadline(item, ctx.now);
  if (raw.kind === 'none') return cell('is-deadline', '마감', h('span', { class: 'date-unknown' }, '미확인'));
  const text = deadlineText(raw);
  return cell('is-deadline', '마감',
    h('span', {}, ddayBadge(item, ctx.now), ' ', text.primary),
    text.note ? h('span', { class: 'date-note' }, text.note) : null);
}

function termsCell(item) {
  const checked = item.eligibilityVerified === true && item.eligibility;
  return cell('is-terms', '참가·상금',
    h('span', {}, modeLine(item)),
    h('span', { class: 'line-muted' }, checked ? item.eligibility : '참가 자격 확인 필요'),
    item.prize ? h('span', {}, `상금 ${item.prize}`) : null);
}

function buildRow(item, ctx) {
  const range = formatRange(item.startDate, item.endDate);
  const verified = formatSeoulDateTime(item.verifiedAt);
  const flags = flagBadges(item, ctx.sources, ctx.now, { skipEligibility: true });

  const article = h('article', { class: 'opp', 'data-id': item.id },
    h('div', { class: 'opp-title-cell' },
      h('h3', { class: 'opp-title' },
        h('button', {
          type: 'button',
          class: 'opp-open',
          'data-open-id': item.id,
          'aria-label': `${item.title} 상세 보기`,
          onclick: (e) => ctx.onOpen(item.id, e.currentTarget),
        }, item.title)),
      item.organizer ? h('p', { class: 'opp-org' }, item.organizer) : null,
      h('p', { class: 'opp-src' },
        kindPill(item),
        statusBadge(item, ctx.now),
        item.sourceName ? h('span', {}, item.sourceName) : null,
        verified ? h('span', {}, `확인 ${verified.slice(5)}`) : null,
        flags)),
    deadlineCell(item, ctx),
    cell('is-when', '개최', range ? h('span', {}, range) : h('span', { class: 'date-unknown' }, '미확인')),
    termsCell(item),
    h('div', { class: 'opp-save' }, saveButton(item, ctx.savedSet.has(item.id), ctx.onToggleSave)));

  // 행의 빈 곳을 눌러도 상세가 열린다 (키보드는 제목 버튼)
  article.addEventListener('click', (e) => {
    if (e.target.closest('button, a')) return;
    ctx.onOpen(item.id, article.querySelector('[data-open-id]'));
  });
  return h('li', {}, article);
}

export function renderRows(container, items, ctx) {
  replaceChildrenOf(container, h('div', { class: 'opp-board' },
    h('div', { class: 'opp-head', 'aria-hidden': 'true' },
      h('span', {}, '제목 · 주최'), h('span', {}, '마감'), h('span', {}, '개최'), h('span', {}, '참가 · 상금'), h('span', {})),
    h('ul', { class: 'opp-list' }, items.map((item) => buildRow(item, ctx)))));
}
