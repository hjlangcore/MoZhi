import unittest
from datetime import datetime
from src.novel_agent.utils import (
    count_chinese_characters,
    count_words,
    extract_keywords,
    calculate_text_similarity,
    find_duplicate_sentences,
    generate_text_hash,
    truncate_text,
    format_datetime,
    parse_datetime,
    safe_json_loads,
    merge_dicts,
    chunk_text,
    extract_numbers,
    validate_chapter_title,
    sanitize_filename,
    get_reading_time
)


class TestUtils(unittest.TestCase):
    """工具函数单元测试"""

    def test_count_chinese_characters(self):
        """测试中文字符计数"""
        self.assertEqual(count_chinese_characters("Hello世界"), 2)
        self.assertEqual(count_chinese_characters("你好世界"), 4)
        self.assertEqual(count_chinese_characters("Hello"), 0)
        self.assertEqual(count_chinese_characters(""), 0)

    def test_count_words(self):
        """测试单词计数"""
        self.assertEqual(count_words("Hello世界"), 3)
        self.assertEqual(count_words("Hello World世界"), 4)
        self.assertEqual(count_words("你好世界"), 4)

    def test_extract_keywords(self):
        """测试关键词提取"""
        text = "这是一段测试文本，包含一些关键词"
        keywords = extract_keywords(text, top_n=5)
        self.assertIsInstance(keywords, list)
        self.assertEqual(len(keywords), min(5, len(keywords)))

    def test_calculate_text_similarity(self):
        """测试文本相似度计算"""
        self.assertEqual(calculate_text_similarity("", ""), 0.0)
        self.assertEqual(calculate_text_similarity("test", ""), 0.0)
        self.assertEqual(calculate_text_similarity("test", "test"), 1.0)
        self.assertTrue(0 < calculate_text_similarity("hello world", "hello there") < 1)

    def test_find_duplicate_sentences(self):
        """测试重复句子查找"""
        long_sentence = "这是一段超过二十个字符的测试句子，用于验证重复句子查找功能。"
        text = long_sentence + "。" + "这是第二段不同的内容，长度也超过二十个字符。" + "。" + long_sentence + "。"
        duplicates = find_duplicate_sentences(text)
        self.assertEqual(len(duplicates), 1)

    def test_generate_text_hash(self):
        """测试文本哈希生成"""
        text = "test"
        hash_val = generate_text_hash(text)
        self.assertEqual(len(hash_val), 64)
        self.assertEqual(generate_text_hash("test"), generate_text_hash("test"))

    def test_truncate_text(self):
        """测试文本截断"""
        text = "Hello World"
        self.assertEqual(truncate_text(text, 5), "He...")
        self.assertEqual(truncate_text(text, 20), "Hello World")

    def test_format_datetime(self):
        """测试日期时间格式化"""
        dt = datetime(2024, 1, 15, 10, 30, 0)
        self.assertEqual(format_datetime(dt), "2024-01-15 10:30:00")

    def test_parse_datetime(self):
        """测试日期时间解析"""
        date_str = "2024-01-15 10:30:00"
        dt = parse_datetime(date_str)
        self.assertEqual(dt.year, 2024)
        self.assertIsNone(parse_datetime("invalid"))

    def test_safe_json_loads(self):
        """测试安全JSON解析"""
        json_str = '{"key": "value"}'
        self.assertEqual(safe_json_loads(json_str), {"key": "value"})
        self.assertIsNone(safe_json_loads("invalid json"))

    def test_merge_dicts(self):
        """测试字典合并"""
        dict1 = {"a": 1, "b": {"c": 2}}
        dict2 = {"b": {"d": 3}, "e": 4}
        result = merge_dicts(dict1, dict2)
        self.assertEqual(result["a"], 1)
        self.assertEqual(result["b"]["c"], 2)
        self.assertEqual(result["b"]["d"], 3)
        self.assertEqual(result["e"], 4)

    def test_chunk_text(self):
        """测试文本分块"""
        text = "a" * 2500
        chunks = chunk_text(text, chunk_size=1000, overlap=100)
        self.assertEqual(len(chunks), 3)

    def test_extract_numbers(self):
        """测试数字提取"""
        text = "abc123def456"
        self.assertEqual(extract_numbers(text), [123, 456])

    def test_validate_chapter_title(self):
        """测试章节标题验证"""
        self.assertTrue(validate_chapter_title("第一章"))
        self.assertTrue(validate_chapter_title("第100章 大结局"))
        self.assertFalse(validate_chapter_title(""))
        self.assertFalse(validate_chapter_title("a"))
        self.assertFalse(validate_chapter_title("a" * 51))

    def test_sanitize_filename(self):
        """测试文件名清理"""
        filename = "test:file/path.txt"
        result = sanitize_filename(filename)
        self.assertNotIn(":", result)
        self.assertNotIn("/", result)

    def test_get_reading_time(self):
        """测试阅读时间计算"""
        self.assertEqual(get_reading_time(500), 1)
        self.assertEqual(get_reading_time(1500), 3)
        self.assertEqual(get_reading_time(0), 1)


if __name__ == "__main__":
    unittest.main()
