// 테스트 전용 합성 데이터. 실제 행사 데이터가 아니다.
export const NOW = '2026-10-02T03:00:00Z'; // 서울 2026-10-02 12:00

export function makeItem(overrides = {}) {
  return {
    id: 't-1',
    kind: 'hackathon',
    title: 'Test Item',
    organizer: null,
    description: '',
    tags: [],
    mode: 'online',
    region: '해외 온라인',
    country: 'GLOBAL',
    startDate: null,
    endDate: null,
    registrationStartDate: null,
    deadlineDate: null,
    deadlineAt: null,
    eligibility: '확인 필요',
    eligibilityVerified: false,
    fee: '확인 필요',
    prize: null,
    url: 'https://example.com/a',
    sourceUrl: 'https://example.com/s',
    sourceId: 'src',
    sourceName: '테스트 출처',
    verifiedAt: '2026-10-02T00:00:00Z',
    dateNote: null,
    stale: false,
    ...overrides,
  };
}

// 필터·정렬 테스트용 6건 (NOW 기준 상태가 각각 다르다)
export function sampleItems() {
  return [
    makeItem({ id: 'a', kind: 'hackathon', mode: 'online', title: 'Vision Hack', organizer: 'Alpha Lab', tags: ['AI', 'Vision'], description: 'Build image models', deadlineAt: '2026-10-10T10:00:00Z', startDate: '2026-10-20', verifiedAt: '2026-10-01T00:00:00Z' }),
    makeItem({ id: 'b', kind: 'contest', mode: 'offline', title: '데이터 공모전', organizer: '한국원', deadlineDate: '2026-09-30', verifiedAt: '2026-09-29T00:00:00Z' }),
    makeItem({ id: 'c', kind: 'event', mode: 'hybrid', title: 'AI Summit', organizer: 'Beta Corp', startDate: '2026-11-05', endDate: '2026-11-06', verifiedAt: '2026-10-02T01:00:00Z' }),
    makeItem({ id: 'd', kind: 'contest', mode: 'online', title: '알 수 없는 대회', verifiedAt: '2026-08-01T00:00:00Z' }),
    makeItem({ id: 'e', kind: 'hackathon', mode: 'online', title: 'Old Hack', endDate: '2026-09-30', deadlineDate: '2026-09-01' }),
    makeItem({ id: 'f', kind: 'event', mode: 'offline', title: 'Meetup Now', startDate: '2026-10-01', endDate: '2026-10-03', deadlineDate: '2026-10-05' }),
  ];
}
