// 화면 상단 알림 목록 계산. 사용자에게는 출처·마지막 확인·수집 지연만 보여주고 기술 메시지는 쓰지 않는다.
import { datasetFreshness } from './data.mjs';
import { formatSeoulDateTime } from './format.mjs';

const MAX_NAMES = 3;

function failingSourcesText(sources) {
  const failing = sources.filter((s) => s.status !== 'ok');
  if (!failing.length) return null;
  const names = failing.slice(0, MAX_NAMES).map((s) => s.name || s.id).join(', ');
  const rest = failing.length - MAX_NAMES;
  const label = rest > 0 ? `${names} 외 ${rest}곳` : names;
  return `일부 출처(${label})를 갱신하지 못했어요. 해당 출처 항목은 이전에 확인한 시점 기준이에요.`;
}

export function buildNotices({ data, now, phase = 'ready', savedStatus, saveFailure, refreshFailed, orphanCount, savedView }) {
  const out = [];

  // 데이터 상태 알림은 읽기가 끝난 뒤에만 쓴다(로딩/오류 중 빈 데이터를 '미수집'이라 단정하지 않는다)
  if (phase === 'ready') {
    const freshness = datasetFreshness(data, now);
    if (freshness === 'none' && data.items.length === 0) {
      out.push({ id: 'no-data', tone: 'warn', text: '아직 수집된 기회가 없어요. 데이터가 갱신된 뒤 다시 확인해 주세요.' });
    } else if (freshness === 'stale') {
      const date = formatSeoulDateTime(data.updatedAt).slice(0, 10);
      out.push({ id: 'stale', tone: 'warn', text: `마지막 성공 갱신은 ${date}이에요. 수집이 지연되고 있어 마감·일정이 바뀌었을 수 있으니 출처에서 다시 확인해 주세요.` });
    }

    const sourcesText = failingSourcesText(data.sources || []);
    if (sourcesText) out.push({ id: 'sources', tone: 'warn', text: sourcesText });
  }

  if (refreshFailed) {
    out.push({ id: 'refresh-failed', tone: 'danger', text: '새로고침에 실패했어요. 이전에 불러온 데이터를 보여주고 있어요.' });
  }
  if (savedStatus === 'corrupt') {
    out.push({ id: 'saved-corrupt', tone: 'danger', text: '이 브라우저의 저장 목록 기록이 손상돼 불러오지 못했어요. 새로 저장하면 기록을 덮어써요.' });
  } else if (savedStatus === 'unavailable') {
    out.push({ id: 'saved-unavailable', tone: 'warn', text: '이 브라우저에서는 저장 기록을 쓸 수 없어요(사생활 보호 모드 등). 저장은 이 탭이 열려 있는 동안만 유지돼요.' });
  }
  if (saveFailure) {
    out.push({ id: 'save-failed', tone: 'warn', text: '저장 내용을 이 브라우저에 기록하지 못했어요. 이 탭을 닫거나 새로고침하면 사라져요.' });
  }
  if (savedView && orphanCount > 0) {
    out.push({ id: 'orphans', tone: 'info', text: `저장한 ${orphanCount}건은 현재 데이터에 없어요. 마감 후 목록에서 빠졌거나 출처에서 사라졌을 수 있어요. 저장 기록은 그대로 보관돼요.` });
  }
  if (data.dropped > 0) {
    out.push({ id: 'dropped', tone: 'info', text: `형식이 맞지 않는 ${data.dropped}건은 표시하지 않았어요.` });
  }
  return out;
}
