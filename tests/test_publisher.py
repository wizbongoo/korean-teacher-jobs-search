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

    def test_format_kboard_title_and_no_dday(self):
        from src.poster import format_kboard_title, format_job_html, format_deadline_tag
        
        # Test deadline formatting in title
        self.assertEqual(format_deadline_tag("2026-08-31"), "[마감 26-08-31]")
        self.assertEqual(format_deadline_tag("상시채용"), "[상시채용]")
        
        title_res = format_kboard_title(self.sample_job)
        self.assertEqual(title_res, "[마감 26-09-30] 테스트 한국어교원 채용 공고")
        
        # Verify D-Day badge and (D-Day) text are excluded from post HTML
        card_html = format_job_html(self.sample_job)
        self.assertNotIn("D-", card_html)
        self.assertNotIn("오늘마감", card_html)
        self.assertIn("2026-09-30", card_html)

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

    @patch("src.poster.post_job_opening")
    @patch("src.poster.save_jobs_file")
    @patch("src.poster.load_jobs_file")
    def test_operator_approval_workflow(self, mock_load, mock_save, mock_post):
        mock_jobs = [
            {
                "id": "pending_1",
                "source": "국립국어원",
                "title": "대기 공고 1",
                "organization": "테스트기관",
                "location": "서울",
                "grade": "2급",
                "deadline": "2026-09-30",
                "url": "https://example.com/1",
                "is_closed": False,
                "created_at": "2026-09-08",
                "status": "pending",
                "kboard_uid": None,
                "reviewed_at": None
            }
        ]
        mock_load.return_value = mock_jobs
        mock_post.return_value = {"status": "success", "kboard_uid": 888}

        from src.poster import approve_and_publish_job, reject_job, restore_to_pending
        
        # 1. Test approve_and_publish_job
        res = approve_and_publish_job("pending_1")
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["kboard_uid"], 888)
        self.assertEqual(mock_jobs[0]["status"], "published")
        self.assertIsNotNone(mock_jobs[0]["reviewed_at"])

        # 2. Test reject_job
        rej_res = reject_job("pending_1")
        self.assertTrue(rej_res)
        self.assertEqual(mock_jobs[0]["status"], "rejected")

        # 3. Test restore_to_pending
        rst_res = restore_to_pending("pending_1")
        self.assertTrue(rst_res)
        self.assertEqual(mock_jobs[0]["status"], "pending")
        self.assertIsNone(mock_jobs[0]["reviewed_at"])

if __name__ == "__main__":
    unittest.main()

