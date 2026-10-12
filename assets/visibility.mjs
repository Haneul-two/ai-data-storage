// 노출 판정의 단일 출처. 신청이 끝난 항목(closed/ended)은 목록·검색·건수·저장·달력·임박·상세 진입 어디에도 나오지 않는다.
// getStatus 계약은 그대로 두고, 여기서만 "보여줄지"를 정한다. now는 항상 인자로 받는다.
import { getStatus } from './status.mjs';

export function isListed(item, now) {
  const status = getStatus(item, now);
  return status !== 'closed' && status !== 'ended';
}

export function listedItems(items, now) {
  return items.filter((item) => isListed(item, now));
}

const listedIdSet = (items, now) => new Set(listedItems(items, now).map((i) => i.id));

export function listedSavedCount(savedIds, items, now) {
  const listed = listedIdSet(items, now);
  return savedIds.filter((id) => listed.has(id)).length;
}

// 마감됐거나 데이터에서 사라져 목록에 못 나오는 저장 id. 저장 기록 자체는 지우지 않는다.
export function hiddenSavedIds(savedIds, items, now) {
  const listed = listedIdSet(items, now);
  return savedIds.filter((id) => !listed.has(id));
}
