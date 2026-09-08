import json
import os
import unittest
from datetime import datetime
from src.utils import calculate_dday, extract_grade, extract_location, parse_date
from src.cleaner import JobDataCleaner

class TestPipeline(unittest.TestCase):
    def test_utils_grade_extraction(self):
        self.assertEqual(extract_grade("한국어교원 2급 이상 채용"), "2급")
        self.assertEqual(extract_grade("한국어 교원 1급 자격증 필수"), "1급")
        self.assertEqual(extract_grade("3급 교원 자격증 소지자"), "3급")
        self.assertEqual(extract_grade("한국어교원자격증 소지자 모집"), "자격소지자")
        self.assertEqual(extract_grade("다문화센터 프로그램 안내"), "무관/미지정")

    def test_utils_location_extraction(self):
        self.assertEqual(extract_location("서울 마포구 한국어학당"), "서울")
        self.assertEqual(extract_location("수원시 다문화가족지원센터"), "경기")
        self.assertEqual(extract_location("부산외국어대학교 한국어교육원"), "경남/부산/울산")
        self.assertEqual(extract_location("베트남 하노이 세종학당 교원 채용"), "해외")
        self.assertEqual(extract_location("기타 지역"), "전국/기타")

    def test_utils_date_and_dday(self):
        parsed = parse_date("2026.09.30")
        self.assertEqual(parsed, "2026-09-30")
        parsed2 = parse_date("2026년 10월 15일")
        self.assertEqual(parsed2, "2026-10-15")
        
        # Test D-day calculation
        label, days, is_closed = calculate_dday("상시채용")
        self.assertEqual(label, "상시")
        self.assertFalse(is_closed)

    def test_cleaner_noise_filtering(self):
        cleaner = JobDataCleaner()
        # Non-job items (results/interviews)
        self.assertTrue(cleaner.is_ended_or_result_notice("2026년도 제1차 면접심사 결과 공고 및 합격자 안내"))
        self.assertTrue(cleaner.is_ended_or_result_notice("서류전형 합격자 및 면접일정 공지"))
        self.assertTrue(cleaner.is_ended_or_result_notice("최종합격자 안내문"))
        
        # Valid teacher job items
        self.assertFalse(cleaner.is_ended_or_result_notice("[채용] 2026학년도 가을학기 한국어교원 모집 공고"))
        self.assertFalse(cleaner.is_ended_or_result_notice("한국어교육 강사 채용 공고"))

        # Irrelevant non-teacher jobs in multicultural centers
        self.assertFalse(cleaner.is_relevant_teacher_job("다문화가족지원센터 아이돌봄전담인력 채용 공고", "다누리"))
        self.assertFalse(cleaner.is_relevant_teacher_job("다문화센터 조리원 채용", "다누리"))
        self.assertTrue(cleaner.is_relevant_teacher_job("다문화가족지원센터 한국어집합교육 강사 채용", "다누리"))

    def test_jobs_json_schema(self):
        jobs_file = os.path.join(os.path.dirname(__file__), "..", "data", "jobs.json")
        self.assertTrue(os.path.exists(jobs_file), "data/jobs.json must exist")
        
        with open(jobs_file, "r", encoding="utf-8") as f:
            jobs = json.load(f)
            
        self.assertIsInstance(jobs, list)
        self.assertGreater(len(jobs), 0, "jobs.json should not be empty")

        required_keys = {
            "id", "source", "title", "organization", "location",
            "grade", "deadline", "url", "is_closed", "created_at"
        }

        for job in jobs:
            self.assertTrue(required_keys.issubset(job.keys()), f"Missing keys in {job}")
            self.assertTrue(job["title"].strip(), "Title must not be blank")
            self.assertTrue(job["url"].startswith("http"), f"Invalid url: {job['url']}")
            self.assertIn(job["source"], ["국립국어원", "한국어교육바다", "세종학당재단", "다누리", "워크넷"])

if __name__ == "__main__":
    unittest.main()
