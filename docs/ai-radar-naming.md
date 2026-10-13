# AI Radar 이름 정리안

외부 적용 전 준비·독립 리뷰 완료. 실제 폴더·저장소 이름과 공개 주소는 아직 기존 상태다.

| 항목 | 현재 | 적용할 이름 |
|---|---|---|
| 활성 작업 폴더 | `C:/Users/caring/Projects/ai-data-storage-events` | `C:/Users/caring/Projects/ai-radar` |
| GitHub 저장소 | `Haneul-two/ai-data-storage` | `Haneul-two/ai-radar` |
| 공개 사이트 | `https://haneul-two.github.io/ai-data-storage/` | `https://haneul-two.github.io/ai-radar/` |
| 화면·브라우저 이름 | AI Radar | AI Radar |

README와 공개 검증 도구 두 개의 주소를 준비했다. 화면 파일은 상대 경로, 갱신 workflow는 `github.repository` 동적 참조를 사용하므로 이름 변경에 대응한다. Claude가 기존 파일을 편집했고 Codex가 diff를 독립 리뷰했다. 공개 검증 도구 구문과 현재 데이터 169건의 오프라인 계약 검증 통과. 외부 이름 변경이나 새 주소 배포 검증은 아직 하지 않았다.

적용 시 활성 프로젝트 폴더만 옮긴다. 별도 원본 `AI-DATA-STORAGE` checkout과 역사적 기록은 보존한다. Python 가상환경은 이동 시 실행기의 절대 경로가 달라지므로 기존 환경을 백업하고 새 폴더에 동일한 13개 설치 버전으로 복구한다. 삭제는 하지 않는다. Git remote·GitHub 저장소 설명·homepage를 새 이름에 맞추고 새 사이트의 데이터·PC/모바일 화면을 확인한다.

저장소 이름을 바꾸면 GitHub 저장소 링크는 새 이름으로 연결되지만, GitHub Pages의 기존 사이트 주소는 자동으로 연결되지 않는다. [GitHub 공식 안내](https://docs.github.com/en/repositories/creating-and-managing-repositories/renaming-a-repository). 사용자 확인 이후 실제 이름 변경을 적용한다.
