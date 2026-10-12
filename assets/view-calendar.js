// 월별 달력. 칸의 마커(데스크톱)와 월 일정 목록(좁은 화면)은 같은 상세 열기 핸들러를 쓴다.
import { h, replaceChildrenOf } from './dom.js';
import { icon } from './icons.js';
import { buildMonthGrid, calendarEntries } from './calendar.mjs';
import { seoulDate } from './time.mjs';
import { WEEKDAYS_KO, formatDateShort } from './format.mjs';

const WEEK_START = 0; // 일요일 시작 (요일 머리글에 그대로 표시)
const TYPE_LABEL = { deadline: '마감', start: '개최' };

const shape = (type) => h('span', { class: type === 'deadline' ? 'mk-deadline-shape' : 'mk-start-shape', 'aria-hidden': 'true' });

function marker(entry, onOpen) {
  return h('button', {
    type: 'button',
    class: 'mk',
    'aria-label': `${TYPE_LABEL[entry.type]}: ${entry.item.title}`,
    onclick: (e) => onOpen(entry.item.id, e.currentTarget),
  }, shape(entry.type), h('span', { class: 'mk-text' }, `${TYPE_LABEL[entry.type]} ${entry.item.title}`));
}

function cell(day, entries, today, onOpen) {
  const cls = ['cal-cell', day.inMonth ? '' : 'is-outside', day.date === today ? 'is-today' : ''].join(' ').trim();
  return h('div', { class: cls },
    h('span', { class: 'cal-day', 'aria-label': day.date === today ? `${day.day}일 오늘` : `${day.day}일` }, String(day.day)),
    entries.map((e) => marker(e, onOpen)),
    entries.length ? h('div', { class: 'cal-dots', 'aria-hidden': 'true' }, entries.map((e) => shape(e.type))) : null);
}

function agenda(month, byDate, onOpen) {
  const prefix = `${month.year}-${String(month.month).padStart(2, '0')}-`;
  const dates = [...byDate.keys()].filter((d) => d.startsWith(prefix)).sort();
  if (!dates.length) return null;
  return h('section', { class: 'agenda', 'aria-label': '이번 달 일정 목록' },
    h('h3', {}, '이번 달 일정'),
    dates.map((date) => h('div', { class: 'agenda-day' },
      h('p', { class: 'agenda-date' }, formatDateShort(date)),
      byDate.get(date).map((e) => h('button', {
        type: 'button',
        class: 'agenda-item',
        onclick: (ev) => onOpen(e.item.id, ev.currentTarget),
      }, shape(e.type), h('span', { class: 'agenda-kind' }, TYPE_LABEL[e.type]), h('span', { class: 'agenda-text' }, e.item.title)))
    )));
}

export function renderCalendar(container, { items, now, month, onMonth, onOpen, onShowList }) {
  const { byDate, undated } = calendarEntries(items, now);
  const today = seoulDate(now);
  const grid = buildMonthGrid(month.year, month.month, WEEK_START);
  const prefix = `${month.year}-${String(month.month).padStart(2, '0')}-`;
  const monthHasEntries = [...byDate.keys()].some((d) => d.startsWith(prefix));

  replaceChildrenOf(container, h('div', { class: 'cal' },
    h('div', { class: 'cal-head' },
      h('h3', { class: 'cal-title', 'aria-live': 'polite' }, `${month.year}년 ${month.month}월`),
      h('button', { type: 'button', class: 'btn', 'aria-label': '이전 달', onclick: () => onMonth(-1) }, icon('chevronLeft')),
      h('button', { type: 'button', class: 'btn', onclick: () => onMonth('today') }, '오늘'),
      h('button', { type: 'button', class: 'btn', 'aria-label': '다음 달', onclick: () => onMonth(1) }, icon('chevronRight'))),
    h('div', { class: 'cal-legend' },
      h('span', {}, shape('deadline'), '마감'),
      h('span', {}, shape('start'), '개최 시작'),
      h('span', {}, '일요일 시작')),
    h('div', { class: 'cal-grid', role: 'group', 'aria-label': `${month.year}년 ${month.month}월 달력` },
      WEEKDAYS_KO.map((d) => h('div', { class: 'cal-dow' }, d)),
      grid.flat().map((day) => cell(day, byDate.get(day.date) || [], today, onOpen))),
    monthHasEntries ? null : h('p', { class: 'cal-empty' }, '이 달에는 표시할 일정이 없어요. 다른 달을 확인해 보세요.'),
    undated.length
      ? h('div', { class: 'cal-undated' },
        h('span', {}, `일정 미정 ${undated.length}건은 달력에 표시되지 않아요.`),
        h('button', { type: 'button', class: 'btn', onclick: onShowList }, '목록에서 보기'))
      : null,
    agenda(month, byDate, onOpen)));
}
