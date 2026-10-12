// 목록 행 렌더링. 외부 문자열은 h()의 text node로만 들어간다.
import { h, replaceChildrenOf } from './dom.js';
import { icon } from './icons.js';
import { getDeadline } from './status.mjs';
import { deadlineText, formatRange } from './format.mjs';
import { kindPill, statusBadge, ddayBadge, flagBadges, modeLine, saveButton } from './item-parts.js';

function dateField(label, primary, note) {
  const dd = primary
    ? h('dd', {}, primary, note ? h('span', { class: 'date-note' }, note) : null)
    : h('dd', { class: 'date-unknown' }, '미확인');
  return h('div', {}, h('dt', {}, label), dd);
}

function buildRow(item, ctx) {
  const rawDeadline = getDeadline(item, ctx.now);
  const deadline = deadlineText(rawDeadline);
  const range = formatRange(item.startDate, item.endDate);
  const tags = Array.isArray(item.tags) ? item.tags.filter((t) => typeof t === 'string' && t) : [];

  return h('li', {},
    h('article', { class: 'opp', 'data-id': item.id },
      h('div', { class: 'opp-main' },
        h('div', { class: 'opp-badges' },
          kindPill(item),
          statusBadge(item, ctx.now),
          ddayBadge(item, ctx.now),
          flagBadges(item, ctx.sources, ctx.now)),
        h('h3', { class: 'opp-title' }, item.title),
        item.organizer ? h('p', { class: 'opp-org' }, item.organizer) : null,
        h('dl', { class: 'opp-dates' },
          dateField('마감', rawDeadline.kind === 'none' ? null : deadline.primary, deadline.note),
          dateField('개최 일정', range, null)),
        h('p', { class: 'opp-meta' }, modeLine(item)),
        tags.length ? h('ul', { class: 'tags', 'aria-label': '태그' }, tags.map((t) => h('li', { class: 'tag' }, t))) : null),
      h('div', { class: 'opp-actions' },
        h('button', {
          type: 'button',
          class: 'btn btn-primary',
          'data-open-id': item.id,
          'aria-label': `${item.title} 상세 보기`,
          onclick: (e) => ctx.onOpen(item.id, e.currentTarget),
        }, '상세 보기', icon('arrowRight')),
        saveButton(item, ctx.savedSet.has(item.id), ctx.onToggleSave))));
}

export function renderRows(container, items, ctx) {
  replaceChildrenOf(container, h('ul', { class: 'opp-list' }, items.map((item) => buildRow(item, ctx))));
}
