// 상세 패널: 네이티브 <dialog>.showModal() — 포커스 가둠·Esc·배경 비활성화는 브라우저가 처리하고,
// 초기 포커스(닫기 버튼)와 닫힌 뒤 포커스 복귀는 여기서 보장한다.
import { h, replaceChildrenOf } from './dom.js';
import { icon } from './icons.js';
import { getDeadline } from './status.mjs';
import { deadlineText, formatDateKo, formatRange, formatSeoulDateTime } from './format.mjs';
import { kindPill, statusBadge, ddayBadge, flagBadges, modeLine, saveButton, externalLink } from './item-parts.js';

function fact(label, ...value) {
  return h('div', { class: 'detail-fact' }, h('dt', {}, label), h('dd', {}, ...value));
}

function buildFacts(item, ctx) {
  const deadline = deadlineText(getDeadline(item, ctx.now));
  const source = externalLink(item.sourceUrl, '출처 확인');
  const rows = [
    fact('마감', deadline.primary, deadline.note ? h('span', { class: 'date-note' }, deadline.note) : null),
    item.registrationStartDate ? fact('접수 시작', formatDateKo(item.registrationStartDate)) : null,
    fact('개최 일정', formatRange(item.startDate, item.endDate) || '미확인'),
    item.dateNote ? fact('일정 안내', item.dateNote) : null,
    fact('방식·장소', modeLine(item)),
    fact('참가 자격', item.eligibility || '확인 필요'),
    fact('참가비', item.fee || '확인 필요'),
    fact('상금', item.prize || '확인된 정보 없음'),
    fact('마지막 확인', formatSeoulDateTime(item.verifiedAt) || '확인 기록 없음', item.stale ? h('span', { class: 'date-note' }, '출처 재확인 필요') : null),
    fact('출처', item.sourceName || '출처 미상', source ? ' · ' : null, source),
  ];
  return h('dl', { class: 'detail-facts' }, rows);
}

export function createDetail({ getContext, onToggleSave, onClosed }) {
  const dialog = h('dialog', { class: 'detail', 'aria-labelledby': 'detail-title' });
  document.body.appendChild(dialog);
  let opener = null;
  let currentId = null;

  dialog.addEventListener('click', (e) => {
    if (e.target === dialog) dialog.close();
  });
  dialog.addEventListener('close', () => {
    const id = currentId;
    currentId = null;
    onClosed(id, opener);
    opener = null;
  });

  function open(item, openerEl) {
    const ctx = getContext();
    opener = openerEl || document.activeElement;
    currentId = item.id;
    const link = externalLink(item.url, '안내 페이지 열기', 'btn btn-primary');
    if (link) link.appendChild(icon('external'));
    replaceChildrenOf(dialog,
      h('div', { class: 'detail-bar' },
        h('span', { class: 'detail-bar-title' }, '상세 정보'),
        h('button', { type: 'button', class: 'icon-btn', autofocus: true, 'aria-label': '상세 정보 닫기', onclick: () => dialog.close() }, icon('close'))),
      h('div', { class: 'detail-body' },
        h('div', { class: 'opp-badges' }, kindPill(item), statusBadge(item, ctx.now), ddayBadge(item, ctx.now), flagBadges(item, ctx.sources, ctx.now)),
        h('h2', { class: 'detail-title', id: 'detail-title' }, item.title),
        item.organizer ? h('p', { class: 'detail-org' }, item.organizer) : null,
        item.description ? h('p', { class: 'detail-desc' }, item.description) : null,
        buildFacts(item, ctx),
        h('div', { class: 'detail-actions' },
          link,
          saveButton(item, ctx.savedSet.has(item.id), onToggleSave)),
        link ? null : h('p', { class: 'side-empty' }, '안전하게 열 수 있는 안내 링크가 없어요. 출처 확인 링크를 이용해 주세요.')));
    dialog.showModal();
  }

  return {
    open,
    isOpen: () => dialog.open,
    close: () => dialog.close(),
    currentId: () => currentId,
  };
}
