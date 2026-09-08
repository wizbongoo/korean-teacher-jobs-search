import os
import unittest
from unittest.mock import patch, MagicMock
from src.publisher import format_kboard_content, WordPressPublisher

class TestPublisher(unittest.TestCase):
    def setUp(self):
        self.sample_job = {
            "id": "test_job_123",
            "source": "국립국어원",
            "title": "테스트 한국어교원 채용 공고",
            "organization": "서울대학교 언어교육원",
            "location": "서울",
            "grade": "2급",
            "deadline": "2026-09-30",
            "url": "https://kteacher.korean.go.kr/jobsearch/123",
            "is_closed": False,
            "created_at": "2026-09-08"
        }

    def test_format_kboard_content(self):
        html = format_kboard_content(self.sample_job)
        self.assertIn("국립국어원", html)
        self.assertIn("서울대학교 언어교육원", html)
        self.assertIn("2026-09-30", html)
        self.assertIn("https://kteacher.korean.go.kr/jobsearch/123", html)
        self.assertIn("공고 원문 보러가기 ↗", html)

    @patch("src.publisher.post_job_opening")
    def test_wordpress_publisher_deduplication(self, mock_post):
        mock_post.return_value = {"status": "success", "kboard_uid": 999, "type": "kboard"}
        
        publisher = WordPressPublisher()
        # Ensure test id is clean
        if "test_job_123" in publisher.published_records:
            del publisher.published_records["test_job_123"]

        # First publish should succeed
        res = publisher.publish_single_job(self.sample_job)
        self.assertIsNotNone(res)
        self.assertTrue(publisher.is_published("test_job_123"))

        # Second publish should be skipped
        stats = publisher.publish_new_jobs([self.sample_job])
        self.assertEqual(stats["skipped"], 1)
        self.assertEqual(stats["published"], 0)

        # Cleanup
        if "test_job_123" in publisher.published_records:
            del publisher.published_records["test_job_123"]
            publisher._save_published_records()

if __name__ == "__main__":
    unittest.main()
