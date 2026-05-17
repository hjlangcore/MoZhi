import unittest
from src.novel_agent.duplicate_detector import DuplicateDetector, get_duplicate_detector


class TestDuplicateDetector(unittest.TestCase):
    """重复检测单元测试"""

    def setUp(self):
        self.detector = DuplicateDetector()

    def test_check_chapter_duplicates_empty(self):
        """测试空内容检测"""
        result = self.detector.check_chapter_duplicates("", "")
        self.assertFalse(result["has_duplicate"])
        self.assertEqual(result["similarity"], 0.0)
        self.assertEqual(result["duplicate_segments"], [])

    def test_check_chapter_duplicates_identical(self):
        """测试完全相同内容检测"""
        content = "这是一段测试内容，用于检测重复。" * 20
        result = self.detector.check_chapter_duplicates(content, content)
        self.assertTrue(result["has_duplicate"])

    def test_check_chapter_duplicates_different(self):
        """测试完全不同内容检测"""
        result = self.detector.check_chapter_duplicates(
            "这是第一段测试内容。",
            "这是完全不同的第二段内容。"
        )
        self.assertFalse(result["has_duplicate"])

    def test_check_within_chapter_duplicates(self):
        """测试章节内重复检测"""
        long_sentence = "1234567890" * 5 + "这是一段足够长的测试句子用于验证重复检测"
        content = long_sentence + "。" + long_sentence + "。" + long_sentence
        result = self.detector.check_within_chapter_duplicates(content)
        self.assertTrue(result["has_duplicates"])
        self.assertGreater(result["duplicate_count"], 0)

    def test_check_within_chapter_no_duplicates(self):
        """测试无重复章节"""
        content = "这是一段唯一的内容，没有重复。"
        result = self.detector.check_within_chapter_duplicates(content)
        self.assertFalse(result["has_duplicates"])
        self.assertEqual(result["duplicate_count"], 0)

    def test_check_character_dialogue_patterns(self):
        """测试角色对话模式检测"""
        content = '"张三说你好。"张三说。"张三说你好。"张三说。"张三说你好。"张三说。"张三说你好。"张三说。"张三说你好。"张三说。'
        result = self.detector.check_character_dialogue_patterns(content, ["张三"])
        self.assertTrue(result["has_pattern_issues"])

    def test_check_character_dialogue_no_patterns(self):
        """测试无重复对话模式"""
        content = '"你好。"张三说。"再见。"张三说。"明天见。"张三说。'
        result = self.detector.check_character_dialogue_patterns(content, ["张三"])
        self.assertFalse(result["has_pattern_issues"])

    def test_batch_check_chapters(self):
        """测试批量章节检测"""
        chapters = [
            "第一章内容...",
            "第二章内容...",
            "第三章内容..."
        ]
        results = self.detector.batch_check_chapters(chapters)
        self.assertEqual(len(results), 3)
        self.assertIsNone(results[0]["duplicates_with_previous"])
        self.assertIsNotNone(results[1]["duplicates_with_previous"])

    def test_get_duplicate_detector_singleton(self):
        """测试单例模式"""
        detector1 = get_duplicate_detector()
        detector2 = get_duplicate_detector()
        self.assertIs(detector1, detector2)


if __name__ == "__main__":
    unittest.main()
