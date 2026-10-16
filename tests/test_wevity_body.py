"""위비티 상세 본문에서 진행 방식·마감 시각·참가비를 읽는 규칙. 문구는 실제 위비티 본문(2026-10-16)에서 옮겼다."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from collectors.opportunities.sources import wevity_body as wb  # noqa: E402


class ModeTest(unittest.TestCase):
    def test_online_submission_channels(self):
        for text in ("■ 접수방법 : E-mail(nrc@nrc.re.kr)로 송부", "- 접수 방법 : 구글폼 지원", "주최측 홈페이지를 통한 온라인 접수",
                     "신청•예선•본선 온라인 진행", "③ 작품 제출(이메일)"):
            self.assertEqual(wb.infer_mode(text), "online", text)

    def test_offline_only(self):
        self.assertEqual(wb.infer_mode("- 방식 : 오프라인 집체교육"), "offline")

    def test_online_run_and_offline_is_hybrid(self):
        for text in ("- 온라인 앱 개발 : 10월 16일(금)까지\n- 오프라인 발표 및 시상 : 2026년 10월 17일(토)",
                     "1차 예선 : 10월 17일(토) 중 1일 온라인 진행\n해커톤 본선 : 2026년 11월 11일(수) (코엑스 오프라인 진행)",
                     "4. 라벨링 프로젝트 참여: 9/15(화) ~ 10/4(일) (20일간)/재택근무\n* 오프라인 OJT 선택 참여 가능"):
            self.assertEqual(wb.infer_mode(text), "hybrid", text)

    def test_online_application_for_offline_event_is_offline(self):
        text = "- 해커톤: 11. 6.(금) ~ 11. 7.(토) / 오프라인 진행\n- 구글 계정 로그인 → 신청서류 작성 → 구글폼 작성 및 신청서 등 제출"
        self.assertEqual(wb.infer_mode(text), "offline")

    def test_online_application_alone_does_not_make_hackathon_online(self):
        text = "- 해커톤: 11. 6.(금) ~ 11. 7.(토) 9:00 ~ 18:00 / 오프라인 비숙박\n- 구글폼 작성 및 신청서 등 제출"
        self.assertEqual(wb.infer_mode(text, "hackathon"), "unknown")
        self.assertEqual(wb.infer_mode("신청•예선•본선 온라인 진행", "hackathon"), "online")

    def test_contact_and_unrelated_lines_are_not_evidence(self):
        for text in ("- E-mail : wolfman911@btp.or.kr", "문의: 전화 043-225-9188 / 이메일 kyj07@cjculture.org",
                     "주최자가 관리하는 누리집 및 SNS 채널(유튜브, 블로그, 인스타그램, 페이스북 등), 오프라인 행사 등에 입상작을 활용하며 응모자는 이에 동의",
                     "- 충청북도 내 과학관 및 연구소 방문, 과학축제‧과학이벤트참여, 생태‧자연탐방 등 경험한 과학문화",
                     "실제 현장에서 적용되고 있는 사례", "- 시상: 11. 15.(일) / 오프라인", "- 비대면 진행", ""):
            self.assertEqual(wb.infer_mode(text), "unknown", text)


class DeadlineTimeTest(unittest.TestCase):
    def test_reads_time_right_after_deadline_date(self):
        cases = {
            "■ 접수기간: 2026. 9. 21.(월) ~ 10. 12.(월) 14:00까지": ("2026-10-12", "2026-10-12T14:00:00+09:00"),
            "■ 접수기간 : 2026. 9. 1.(화) ~ 9. 13.(일) / 23:59": ("2026-09-13", "2026-09-13T23:59:00+09:00"),
            "1. 참가자 모집: 8/28(금) ~ 9/8(화), 17:00 마감": ("2026-09-08", "2026-09-08T17:00:00+09:00"),
            "- 공모전 접수 : 2026년 9월 1일(화) ~ 9월 21일(월) 오후 11시 59분": ("2026-09-21", "2026-09-21T23:59:00+09:00"),
            "■ 접수기간 : 2026. 9. 7.(월) ∼ 10. 31.(토) 까지 23:59까지": ("2026-10-31", "2026-10-31T23:59:00+09:00"),
            "■ 접수 : 2026. 9. 21.(월) ~ 10. 13.(화) 18시": ("2026-10-13", "2026-10-13T18:00:00+09:00"),
            "■ 모집 기간\n2026년 9월 23일 ~ 10월 7일 23:59 (KST)": ("2026-10-07", "2026-10-07T23:59:00+09:00"),
            "■ 기간 및 일정\n\n- 26.8.20.(목) ~ 9.13.(일) 23:59까지": ("2026-09-13", "2026-09-13T23:59:00+09:00"),
            "■ 예선 접수 마감 : 2026.8.14(금) 23:59": ("2026-08-14", "2026-08-14T23:59:00+09:00"),
            "■ 접 수 : 2026.9.15~10.19.18:00": ("2026-10-19", "2026-10-19T18:00:00+09:00"),
        }
        for text, (date, expected) in cases.items():
            self.assertEqual(wb.deadline_at(text, date), expected, text)

    def test_end_of_day_24_stays_on_same_date(self):
        for text in ("■ 공모 접수 : 9.3.(목) 09:00 ~ 11.8.(일) 24:00 ※이메일로 신청 접수", "- 접수/제출 : 2026년 9월3일 0시 ~ 11월 8일 24시",
                     "■ 접수마감: 11월 8일(일) 밤 12시까지"):
            self.assertEqual(wb.deadline_at(text, "2026-11-08"), "2026-11-08T23:59:59+09:00", text)

    def test_start_time_and_other_dates_are_ignored(self):
        self.assertIsNone(wb.deadline_at("- 공고 및 참가신청 : 9.2. (수) 10:00 ~ 9.14. (월)", "2026-09-14"))
        self.assertIsNone(wb.deadline_at("■ 국민심사 : 2026. 9. 22.(화) ~ 9. 30.(수) / 23:59", "2026-09-13"))
        self.assertIsNone(wb.deadline_at("접수기간 2026-09-21 ~ 2026-10-12", "2026-10-12"))
        self.assertIsNone(wb.deadline_at("접수 ~ 10. 12.(월) 18:00", None))

    def test_conflicting_times_for_same_date_are_left_empty(self):
        text = "- 접수: ~ 10. 12.(월) 18:00\n- 서류 제출: ~ 10. 12.(월) 23:59"
        self.assertIsNone(wb.deadline_at(text, "2026-10-12"))

    def test_same_time_repeated_is_fine(self):
        text = "- 2026. 10. 1. ~ 2026. 10. 31. 18:00까지\n- 10. 31.(토) 18:00까지 이메일로 제출"
        self.assertEqual(wb.deadline_at(text, "2026-10-31"), "2026-10-31T18:00:00+09:00")

    def test_time_of_other_schedule_on_same_date_is_ignored(self):
        self.assertIsNone(wb.deadline_at("접수: 10.1 ~ 10.12\n결과 발표: 10.12. 14:00", "2026-10-12"))
        self.assertIsNone(wb.deadline_at("■ 국민심사 : 2026. 9. 22.(화) ~ 9. 30.(수) / 23:59", "2026-09-30"))

    def test_line_without_deadline_context_is_ignored(self):
        self.assertIsNone(wb.deadline_at("■ 운영 안내\n2026년 10월 12일 18:00", "2026-10-12"))

    def test_other_year_is_ignored(self):
        self.assertIsNone(wb.deadline_at("접수 마감: 2025.10.12. 18:00", "2026-10-12"))
        self.assertIsNone(wb.deadline_at("접수 마감: '25.10.12. 18:00", "2026-10-12"))
        self.assertEqual(wb.deadline_at("접수 마감: 2026.10.12. 18:00", "2026-10-12"), "2026-10-12T18:00:00+09:00")

    def test_time_range_or_alternatives_are_ambiguous(self):
        for text in ("접수: ~ 10.12. 18:00~20:00", "접수 마감: 10.12. 18:00 또는 23:59", "접수 마감: 10.12. 오후 6시 ~ 8시"):
            self.assertIsNone(wb.deadline_at(text, "2026-10-12"), text)

    def test_meridiem_edge_cases(self):
        cases = {"오전 12시": "00:00:00", "오후 12시": "12:00:00", "저녁 7시": "19:00:00", "오후 11시 59분": "23:59:00"}
        for clock, expected in cases.items():
            self.assertEqual(wb.deadline_at(f"접수 마감: 10월 12일 {clock}", "2026-10-12"), f"2026-10-12T{expected}+09:00", clock)

    def test_month_day_must_not_be_part_of_longer_number(self):
        self.assertIsNone(wb.deadline_at("- 10. 1.(목) 12:00 시작", "2026-10-12"))
        self.assertIsNone(wb.deadline_at("- 2026. 10. 12.(월) 18:00", "2026-10-02"))


class FeeTest(unittest.TestCase):
    def test_explicit_free(self):
        for text in ("- 참가비 무료", "- 참가비: 무료", "- 교육비 전액 무료", "참가비는 없음"):
            self.assertEqual(wb.fee(text), "무료", text)

    def test_explicit_amount(self):
        self.assertEqual(wb.fee("- 참가비 : 30,000원"), "30,000원")

    def test_unclear_fee_text_is_left_empty(self):
        for text in ("대학(원)생, 성인 등 / 무료", "무료 요금제 생성물은 출품할 수 없음", "유료 라이선스 계정을 통한", "",
                     "- 참가비: 30,000원\n- 교육비 무료", "- 참가비: 무료(학생만), 일반 30,000원"):
            self.assertIsNone(wb.fee(text), text)


if __name__ == "__main__":
    unittest.main()
