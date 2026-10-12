import { test } from 'node:test';
import assert from 'node:assert/strict';
import { buildMonthGrid, shiftMonth, monthOf, calendarEntries } from '../assets/calendar.mjs';
import { NOW, makeItem } from './helpers.mjs';

const flat = (grid) => grid.flat().map((c) => c.date);

test('2026년 10월 일요일 시작 격자: 5주, 9/27 ~ 10/31', () => {
  const grid = buildMonthGrid(2026, 10, 0);
  assert.equal(grid.length, 5);
  assert.ok(grid.every((w) => w.length === 7));
  assert.equal(flat(grid)[0], '2026-09-27');
  assert.equal(flat(grid).at(-1), '2026-10-31');
  assert.equal(grid[0][0].inMonth, false);
  assert.equal(grid[0][4].date, '2026-10-01');
  assert.equal(grid[0][4].inMonth, true);
});

test('월요일 시작 격자: 9/28 ~ 11/1', () => {
  const grid = buildMonthGrid(2026, 10, 1);
  assert.equal(flat(grid)[0], '2026-09-28');
  assert.equal(flat(grid).at(-1), '2026-11-01');
});

test('이번 달 날짜 수가 정확하다 (2월 윤년 아님/있음)', () => {
  const inMonth = (y, m) => buildMonthGrid(y, m, 0).flat().filter((c) => c.inMonth).length;
  assert.equal(inMonth(2026, 2), 28);
  assert.equal(inMonth(2028, 2), 29);
  assert.equal(inMonth(2026, 12), 31);
});

test('shiftMonth는 연도를 넘어간다', () => {
  assert.deepEqual(shiftMonth({ year: 2026, month: 12 }, 1), { year: 2027, month: 1 });
  assert.deepEqual(shiftMonth({ year: 2026, month: 1 }, -1), { year: 2025, month: 12 });
  assert.deepEqual(shiftMonth({ year: 2026, month: 10 }, 0), { year: 2026, month: 10 });
});

test('monthOf는 서울 오늘 기준 연·월', () => {
  assert.deepEqual(monthOf('2026-09-30T16:00:00Z'), { year: 2026, month: 10 }); // 서울 10/01
});

test('calendarEntries: 마감과 개최 시작이 서로 다른 마커로 들어간다', () => {
  const it = makeItem({ id: 'x', deadlineAt: '2026-10-26T17:00:00-04:00', startDate: '2026-11-03' });
  const { byDate, undated } = calendarEntries([it]);
  assert.deepEqual(byDate.get('2026-10-27').map((e) => e.type), ['deadline']); // 서울 날짜
  assert.deepEqual(byDate.get('2026-11-03').map((e) => e.type), ['start']);
  assert.equal(byDate.get('2026-10-27')[0].item, it);
  assert.equal(undated.length, 0);
});

test('calendarEntries: date-only 마감도 마커가 된다', () => {
  const it = makeItem({ id: 'y', deadlineDate: '2026-10-05' });
  assert.deepEqual(calendarEntries([it]).byDate.get('2026-10-05').map((e) => e.type), ['deadline']);
});

test('calendarEntries: 날짜가 하나도 없으면 일정 미정으로 센다', () => {
  const a = makeItem({ id: 'a' });
  const b = makeItem({ id: 'b', endDate: '2026-12-01' }); // 종료일만으로는 마커를 만들지 않는다
  const c = makeItem({ id: 'c', startDate: '2026-10-09' });
  const { byDate, undated } = calendarEntries([a, b, c]);
  assert.deepEqual(undated.map((i) => i.id), ['a', 'b']);
  assert.equal(byDate.size, 1);
});

test('calendarEntries: 같은 날 마감과 개최가 겹쳐도 둘 다 유지한다', () => {
  const it = makeItem({ id: 'z', deadlineDate: '2026-10-09', startDate: '2026-10-09' });
  assert.deepEqual(calendarEntries([it]).byDate.get('2026-10-09').map((e) => e.type), ['deadline', 'start']);
});

test('NOW 상수는 서울 10월 2일', () => {
  assert.deepEqual(monthOf(NOW), { year: 2026, month: 10 });
});
