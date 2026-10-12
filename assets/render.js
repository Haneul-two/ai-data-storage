// 상태(state) → 화면. 선택 그룹·헤더 버튼처럼 포커스를 가진 요소는 한 번 만들고 값만 갱신한다.
import { h, replaceChildrenOf } from './dom.js';
import { icon } from './icons.js';
import { applyFilters, selectItems, facetCounts, activeFilterCount, DEFAULT_FILTERS } from './filters.mjs';
import { orphanIds } from './storage.mjs';
import { buildNotices } from './notices.mjs';
import { seoulDate } from './time.mjs';
import { formatDateKo } from './format.mjs';
import { createChoiceGroup } from './view-controls.js';
import { renderRows } from './view-list.js';
import { renderCalendar } from './view-calendar.js';
import { renderUrgent, renderSources } from './view-urgent.js';

const KIND_OPTIONS = [
  { value: 'all', label: '전체' },
  { value: 'event', label: '행사' },
  { value: 'contest', label: '공모전' },
  { value: 'hackathon', label: '해커톤' },
];
const STATUS_OPTIONS = [
  { value: 'all', label: '전체 (종료 제외)' },
  { value: 'open', label: '모집중' },
  { value: 'upcoming', label: '예정' },
  { value: 'ongoing', label: '진행중' },
  { value: 'closed', label: '마감·종료' },
  { value: 'unknown', label: '일정 미정' },
];
const MODE_OPTIONS = [
  { value: 'all', label: '전체' },
  { value: 'online', label: '온라인' },
  { value: 'offline', label: '오프라인' },
  { value: 'hybrid', label: '혼합' },
];

function stateCard(title, text, action) {
  return h('div', { class: 'state' },
    h('h3', {}, title),
    text ? h('p', {}, text) : null,
    action ? h('button', { type: 'button', class: 'btn btn-primary', onclick: action.onClick }, action.label) : null);
}

export function createRenderer(els, actions) {
  const tabs = createChoiceGroup(els.kindTabs, { options: KIND_OPTIONS, buttonClass: 'tab', countClass: 'tab-count', onSelect: (v) => actions.setFilters({ kind: v }) });
  const statusGroup = createChoiceGroup(els.statusOptions, { options: STATUS_OPTIONS, buttonClass: 'option', countClass: 'option-count', onSelect: (v) => actions.setFilters({ status: v }) });
  const modeGroup = createChoiceGroup(els.modeOptions, { options: MODE_OPTIONS, buttonClass: 'option', countClass: 'option-count', onSelect: (v) => actions.setFilters({ mode: v }) });

  const viewButtons = {
    list: h('button', { type: 'button', class: 'btn', 'aria-pressed': 'false', onclick: () => actions.setFilters({ view: 'list' }) }, icon('list'), '목록'),
    calendar: h('button', { type: 'button', class: 'btn', 'aria-pressed': 'false', onclick: () => actions.setFilters({ view: 'calendar' }) }, icon('calendar'), '달력'),
  };
  els.viewSwitch.append(viewButtons.list, viewButtons.calendar);

  const savedCount = h('span', { class: 'btn-count' }, '0');
  els.savedToggle.append(icon('bookmark'), h('span', { class: 'btn-text' }, '내 저장'), savedCount);
  els.savedToggle.addEventListener('click', () => actions.setFilters({ saved: !els.savedToggle.matches('[aria-pressed="true"]') }));

  const refreshIcon = icon('refresh');
  const refreshLabel = h('span', { class: 'btn-text' }, '새로고침');
  els.refresh.append(refreshIcon, refreshLabel);
  els.refresh.addEventListener('click', () => actions.refresh());

  const railLabel = h('span', { class: 'rail-toggle-label' }, '필터');
  els.railToggle.append(icon('sliders'), railLabel);
  els.railToggle.addEventListener('click', () => {
    const open = !els.rail.classList.contains('is-open');
    els.rail.classList.toggle('is-open', open);
    els.railToggle.setAttribute('aria-expanded', String(open));
  });
  els.resetFilters.addEventListener('click', () => actions.resetFilters());
  els.sort.addEventListener('change', () => actions.setFilters({ sort: els.sort.value }));

  let noticeSignature = '';
  let sideKey = null;
  let lastSideData = null;

  function renderNotices(state, orphanCount) {
    const notices = buildNotices({
      data: state.data || { items: [], sources: [], updatedAt: null, dropped: 0 },
      now: state.now(),
      phase: state.phase,
      savedStatus: state.savedStatus,
      saveFailure: state.saveFailure,
      refreshFailed: state.refreshFailed,
      orphanCount,
      savedView: state.filters.saved,
    });
    const signature = JSON.stringify(notices);
    if (signature === noticeSignature) return;
    noticeSignature = signature;
    replaceChildrenOf(els.notices, notices.map((n) => h('div', { class: `notice notice-${n.tone}` }, icon('alert'), h('span', {}, n.text))));
  }

  function renderContent(state, selected, items, ctx) {
    const { filters } = state;
    els.content.setAttribute('aria-busy', state.phase === 'loading' ? 'true' : 'false');
    if (state.phase === 'loading') {
      replaceChildrenOf(els.content, h('div', { class: 'skeleton', role: 'status' },
        h('span', { class: 'visually-hidden' }, '기회 목록을 불러오는 중이에요'),
        [1, 2, 3].map(() => h('div', { class: 'skeleton-row', 'aria-hidden': 'true' }))));
      return;
    }
    if (state.phase === 'error') {
      replaceChildrenOf(els.content, stateCard('데이터를 불러오지 못했어요', '네트워크 상태를 확인한 뒤 다시 시도해 주세요. 이전에 저장한 항목은 그대로 남아 있어요.', { label: '다시 시도', onClick: () => actions.retry() }));
      return;
    }
    if (items.length === 0) {
      replaceChildrenOf(els.content, stateCard('아직 표시할 기회가 없어요', '수집된 AI 행사·공모전·해커톤이 생기면 이곳에 나타나요.', null));
      return;
    }
    if (selected.length === 0) {
      if (filters.saved && state.savedIds.length === 0) {
        replaceChildrenOf(els.content, stateCard('아직 저장한 기회가 없어요', '목록에서 저장 버튼을 누르면 이곳에 모여요.', { label: '전체 목록 보기', onClick: () => actions.setFilters({ saved: false }) }));
      } else {
        replaceChildrenOf(els.content, stateCard('조건에 맞는 기회가 없어요', '검색어나 필터를 바꾸거나 초기화해 보세요.', { label: '필터 초기화', onClick: () => actions.resetFilters() }));
      }
      return;
    }
    if (filters.view === 'calendar') {
      renderCalendar(els.content, {
        items: selected,
        now: state.now(),
        month: state.month,
        onMonth: actions.changeMonth,
        onOpen: actions.openDetail,
        onShowList: () => actions.setFilters({ view: 'list' }),
      });
    } else {
      renderRows(els.content, selected, ctx);
    }
  }

  // 저장 토글처럼 목록을 다시 그리지 않아야 하는 갱신(포커스 유지): 저장 개수와 알림만 바꾼다
  function renderSaveChrome(state) {
    const items = state.data ? state.data.items : [];
    const orphans = state.phase === 'ready' ? orphanIds(state.savedIds, items) : [];
    savedCount.textContent = String(state.savedIds.length - orphans.length);
    renderNotices(state, orphans.length);
  }

  function render(state) {
    const now = state.now();
    const { filters } = state;
    const items = state.data ? state.data.items : [];
    const savedSet = new Set(state.savedIds);
    const ctx = {
      now,
      sources: state.data ? state.data.sources : [],
      savedSet,
      onOpen: actions.openDetail,
      onToggleSave: actions.toggleSave,
    };
    const filterCtx = { now, savedIds: savedSet };
    const ready = state.phase === 'ready';

    const selected = ready ? selectItems(items, filters, filterCtx) : [];
    const counts = facetCounts(ready ? items : [], filters, filterCtx);
    const activeTotal = ready ? applyFilters(items, { ...DEFAULT_FILTERS }, filterCtx).length : 0;

    els.today.textContent = `${formatDateKo(seoulDate(now))} · 서울 기준`;
    els.introCount.textContent = ready ? `· 진행 중인 기회 ${activeTotal}건` : '';
    els.savedToggle.setAttribute('aria-pressed', String(filters.saved));
    els.savedToggle.setAttribute('aria-label', filters.saved ? '내 저장 목록 보기 끄기' : '내 저장 목록만 보기');

    refreshLabel.textContent = state.refreshing ? '불러오는 중' : '새로고침';
    els.refresh.disabled = state.refreshing;
    els.refresh.setAttribute('aria-busy', String(state.refreshing));

    tabs.update(filters.kind, counts.kind);
    statusGroup.update(filters.status, counts.status);
    modeGroup.update(filters.mode, counts.mode);
    const active = activeFilterCount(filters);
    railLabel.textContent = active ? `필터 · ${active}개 적용` : '필터';

    els.sort.value = filters.sort;
    els.sort.hidden = filters.view === 'calendar';
    viewButtons.list.setAttribute('aria-pressed', String(filters.view === 'list'));
    viewButtons.calendar.setAttribute('aria-pressed', String(filters.view === 'calendar'));

    if (state.phase === 'loading') els.resultCount.textContent = '불러오는 중…';
    else if (state.phase === 'error') els.resultCount.textContent = '';
    else els.resultCount.textContent = `${filters.saved ? '내 저장 ' : '조건에 맞는 기회 '}${selected.length}건`;

    renderSaveChrome(state);
    renderContent(state, selected, items, ctx);

    const key = `${state.data ? state.data.updatedAt : 'none'}|${state.data ? state.data.items.length : 0}|${seoulDate(now)}|${state.phase}`;
    if (key !== sideKey || state.data !== lastSideData) {
      sideKey = key;
      lastSideData = state.data;
      renderUrgent(els.urgent, { items: ready ? items : [], now, onOpen: actions.openDetail });
      if (state.data) renderSources(els.sources, { data: state.data });
      else replaceChildrenOf(els.sources, h('summary', { class: 'source-summary' }, '출처 상태'));
    }
  }

  return { render, renderSaveChrome };
}
