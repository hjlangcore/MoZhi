import re
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json


def count_chinese_characters(text: str) -> int:
    chinese_char_pattern = re.compile(r'[\u4e00-\u9fff]')
    return len(chinese_char_pattern.findall(text))


def count_words(text: str) -> int:
    chinese_chars = count_chinese_characters(text)
    english_words = len(re.findall(r'[a-zA-Z]+', text))
    return chinese_chars + english_words


def extract_keywords(text: str, top_n: int = 10) -> List[str]:
    chinese_chars = re.findall(r'[\u4e00-\u9fff]+', text)
    bigrams = []
    for chars in chinese_chars:
        for i in range(len(chars) - 1):
            bigrams.append(chars[i:i+2])

    from collections import Counter
    counter = Counter(bigrams)
    return [word for word, _ in counter.most_common(top_n)]


def calculate_text_similarity(text1: str, text2: str) -> float:
    if not text1 or not text2:
        return 0.0

    set1 = set(text1)
    set2 = set(text2)

    intersection = len(set1 & set2)
    union = len(set1 | set2)

    if union == 0:
        return 0.0
    return intersection / union


def find_duplicate_sentences(text: str, min_length: int = 20) -> List[Tuple[str, int]]:
    sentences = re.split(r'[。！？\n]', text)
    duplicates = []

    seen = {}
    for i, sentence in enumerate(sentences):
        sentence = sentence.strip()
        if len(sentence) < min_length:
            continue

        normalized = re.sub(r'\s+', '', sentence.lower())
        if normalized in seen:
            duplicates.append((sentence, seen[normalized], i))
        else:
            seen[normalized] = i

    return duplicates


def generate_text_hash(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    return dt.strftime(format_str)


def parse_datetime(date_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
    try:
        return datetime.strptime(date_str, format_str)
    except ValueError:
        return None


def clean_json_string(json_str: str) -> str:
    json_str = json_str.strip()
    json_str = re.sub(r'^```json\s*', '', json_str)
    json_str = re.sub(r'^```\s*', '', json_str)
    json_str = re.sub(r'\s*```$', '', json_str)
    return json_str


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    try:
        cleaned = clean_json_string(json_str)
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return default


def merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]

        if start > 0 and start + chunk_size < text_length:
            chunk = text[start - overlap:start] + chunk

        chunks.append(chunk)
        start = end - overlap

    return chunks


def extract_numbers(text: str) -> List[int]:
    return [int(n) for n in re.findall(r'\d+', text)]


def validate_chapter_title(title: str) -> bool:
    if not title or len(title) < 2 or len(title) > 50:
        return False
    return True


def sanitize_filename(filename: str) -> str:
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = filename.strip()
    return filename[:200]


def get_reading_time(word_count: int, words_per_minute: int = 500) -> int:
    return max(1, word_count // words_per_minute)
