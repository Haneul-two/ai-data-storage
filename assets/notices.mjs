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
  return `일부 출처(${label}) 갱신에 실패했습니다. 해당 출처 항목은 마지막 확인 시점 기준입니다.`;
}

export function buildNotices({ data, now, phase = 'ready', savedStatus, saveFailure, refreshFailed, orphanCount, savedView, expiredTitle }) {
  const out = [];

  // 데이터 상태 알림은 읽기가 끝난 뒤에만 쓴다(로딩/오류 중 빈 데이터를 '미수집'이라 단정하지 않는다)
  if (phase === 'ready') {
    const freshness = datasetFreshness(data, now);
    if (freshness === 'none' && data.items.length === 0) {
      out.push({ id: 'no-data', tone: 'warn', text: '수집된 기회가 아직 없습니다. 데이터가 갱신된 뒤 다시 확인하세요.' });
    } else if (freshness === 'stale') {
      const date = formatSeoulDateTime(data.updatedAt).slice(0, 10);
      out.push({ id: 'stale', tone: 'warn', text: `마지막 성공 갱신은 ${date}입니다. 수집이 지연되어 마감·일정이 달라졌을 수 있으니 출처에서 확인하세요.` });
    }

    const sourcesText = failingSourcesText(data.sources || []);
    if (sourcesText) out.push({ id: 'sources', tone: 'warn', text: sourcesText });
  }

  if (refreshFailed) {
    out.push({ id: 'refresh-failed', tone: 'danger', text: '새로고침에 실패했습니다. 이전에 불러온 데이터를 표시합니다.' });
  }
  if (savedStatus === 'corrupt') {
    out.push({ id: 'saved-corrupt', tone: 'danger', text: '이 브라우저의 저장 기록이 손상되어 불러오지 못했습니다. 새로 저장하면 기록을 덮어씁니다.' });
  } else if (savedStatus === 'unavailable') {
    out.push({ id: 'saved-unavailable', tone: 'warn', text: '이 브라우저에서는 저장 기록을 쓸 수 없습니다(사생활 보호 모드 등). 저장은 이 탭이 열려 있는 동안만 유지됩니다.' });
  }
  if (saveFailure) {
    out.push({ id: 'save-failed', tone: 'warn', text: '저장 내용을 이 브라우저에 기록하지 못했습니다. 탭을 닫거나 새로고침하면 사라집니다.' });
  }
  if (savedView && orphanCount > 0) {
    out.push({ id: 'orphans', tone: 'info', text: `저장한 ${orphanCount}건은 신청이 마감됐거나 현재 데이터에 없어 목록에 표시하지 않습니다. 저장 기록은 보관됩니다.` });
  }
  if (expiredTitle) {
    out.push({ id: 'detail-expired', tone: 'info', text: `'${expiredTitle}' 신청이 마감되어 목록에서 제외했습니다.` });
  }
  if (data.dropped > 0) {
    out.push({ id: 'dropped', tone: 'info', text: `형식이 맞지 않는 ${data.dropped}건은 표시하지 않았습니다.` });
  }
  return out;
}
