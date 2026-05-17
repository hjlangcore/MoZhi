"""文风分析器 — 参考 InkOS 的文风指纹提取功能

功能：
1. 分析参考文本，提取统计指纹（句长分布、词频特征、节奏模式）
2. 生成 LLM 风格指南
3. 支持文风仿写
4. 风格一致性检查
"""
import re
from typing import Dict, Any, List, Optional, Tuple
from collections import Counter
from dataclasses import dataclass, field
from loguru import logger
import json


@dataclass
class SentenceLengthDistribution:
    """句长分布统计"""
    avg_length: float
    min_length: int
    max_length: int
    std_dev: float
    short_ratio: float
    medium_ratio: float
    long_ratio: float
    distribution: List[int] = field(default_factory=list)


@dataclass
class WordFrequencyFeatures:
    """词频特征"""
    top_words: List[Tuple[str, int]]
    unique_ratio: float
    repetition_rate: float
    adjective_density: float
    verb_density: float
    noun_density: float


@dataclass
class RhythmPattern:
    """节奏模式"""
    avg_paragraph_length: float
    paragraph_variation: float
    dialogue_ratio: float
    description_ratio: float
    action_ratio: float
    psychological_ratio: float


@dataclass
class StyleFingerprint:
    """文风指纹"""
    sentence_length: SentenceLengthDistribution
    word_frequency: WordFrequencyFeatures
    rhythm: RhythmPattern
    style_tags: List[str]
    llm_style_guide: str
    sample_text: str = ""


@dataclass
class StyleComparison:
    """风格对比结果"""
    similarity_score: float
    differences: List[str]
    suggestions: List[str]


class StyleAnalyzer:
    """文风分析器"""
    
    def __init__(self):
        self.fingerprint_cache: Dict[str, StyleFingerprint] = {}
        self._stop_words = self._load_stop_words()
    
    def _load_stop_words(self) -> set:
        """加载停用词"""
        return {
            "的", "了", "是", "在", "我", "有", "和", "就", "不", "人",
            "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去",
            "你", "会", "着", "没有", "看", "好", "自己", "这", "那", "他",
            "她", "它", "们", "这个", "那个", "什么", "怎么", "为什么"
        }
    
    def analyze(self, text: str, name: str = "default") -> StyleFingerprint:
        """分析文本，提取文风指纹"""
        sentences = self._split_sentences(text)
        words = self._extract_words(text)
        paragraphs = self._split_paragraphs(text)
        
        sentence_length = self._analyze_sentence_length(sentences)
        word_frequency = self._analyze_word_frequency(words, text)
        rhythm = self._analyze_rhythm(paragraphs, text)
        style_tags = self._detect_style_tags(text, sentence_length, rhythm)
        llm_guide = self._generate_style_guide(sentence_length, word_frequency, rhythm, style_tags)
        
        fingerprint = StyleFingerprint(
            sentence_length=sentence_length,
            word_frequency=word_frequency,
            rhythm=rhythm,
            style_tags=style_tags,
            llm_style_guide=llm_guide,
            sample_text=text[:500] if len(text) > 500 else text
        )
        
        self.fingerprint_cache[name] = fingerprint
        logger.info(f"StyleAnalyzer: 完成文风分析 '{name}', 风格标签: {style_tags}")
        
        return fingerprint
    
    def _split_sentences(self, text: str) -> List[str]:
        """分割句子"""
        sentences = re.split(r'[。！？\n]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _extract_words(self, text: str) -> List[str]:
        """提取词汇"""
        words = []
        for match in re.finditer(r'[\u4e00-\u9fff]{2,4}', text):
            word = match.group()
            if word not in self._stop_words:
                words.append(word)
        return words
    
    def _split_paragraphs(self, text: str) -> List[str]:
        """分割段落"""
        paragraphs = re.split(r'\n{2,}', text)
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _analyze_sentence_length(self, sentences: List[str]) -> SentenceLengthDistribution:
        """分析句长分布"""
        lengths = [len(s) for s in sentences if len(s) > 0]
        
        if not lengths:
            return SentenceLengthDistribution(0, 0, 0, 0, 0, 0, 0)
        
        avg = sum(lengths) / len(lengths)
        min_len = min(lengths)
        max_len = max(lengths)
        
        variance = sum((l - avg) ** 2 for l in lengths) / len(lengths)
        std_dev = variance ** 0.5
        
        short = sum(1 for l in lengths if l < 15) / len(lengths)
        medium = sum(1 for l in lengths if 15 <= l < 30) / len(lengths)
        long = sum(1 for l in lengths if l >= 30) / len(lengths)
        
        return SentenceLengthDistribution(
            avg_length=round(avg, 1),
            min_length=min_len,
            max_length=max_len,
            std_dev=round(std_dev, 1),
            short_ratio=round(short, 3),
            medium_ratio=round(medium, 3),
            long_ratio=round(long, 3),
            distribution=lengths[:100]
        )
    
    def _analyze_word_frequency(self, words: List[str], text: str) -> WordFrequencyFeatures:
        """分析词频特征"""
        if not words:
            return WordFrequencyFeatures([], 0, 0, 0, 0, 0)
        
        word_counter = Counter(words)
        top_words = word_counter.most_common(20)
        
        unique_ratio = len(word_counter) / len(words)
        
        repeated = sum(1 for w, c in word_counter.items() if c >= 3)
        repetition_rate = repeated / len(word_counter)
        
        adj_count = len(re.findall(r'的[\u4e00-\u9fff]{1,2}', text))
        verb_count = len(re.findall(r'[\u4e00-\u9fff]{1,2}[了着过]', text))
        noun_count = len(re.findall(r'[\u4e00-\u9fff]{2,3}', text))
        
        total = len(text) / 10
        adjective_density = adj_count / max(total, 1)
        verb_density = verb_count / max(total, 1)
        noun_density = noun_count / max(total, 1)
        
        return WordFrequencyFeatures(
            top_words=top_words,
            unique_ratio=round(unique_ratio, 3),
            repetition_rate=round(repetition_rate, 3),
            adjective_density=round(adjective_density, 3),
            verb_density=round(verb_density, 3),
            noun_density=round(noun_density, 3)
        )
    
    def _analyze_rhythm(self, paragraphs: List[str], text: str) -> RhythmPattern:
        """分析节奏模式"""
        if not paragraphs:
            return RhythmPattern(0, 0, 0, 0, 0, 0)
        
        para_lengths = [len(p) for p in paragraphs]
        avg_length = sum(para_lengths) / len(para_lengths)
        
        if len(para_lengths) > 1:
            variation = sum(abs(para_lengths[i] - para_lengths[i-1]) for i in range(1, len(para_lengths))) / (len(para_lengths) - 1)
        else:
            variation = 0
        
        dialogue_count = len(re.findall(r'「[^」]+」', text))
        total_chars = len(text)
        
        dialogue_ratio = dialogue_count * 10 / max(total_chars, 1)
        description_ratio = len(re.findall(r'[的地得]', text)) / max(total_chars / 10, 1)
        action_ratio = len(re.findall(r'[着了过]', text)) / max(total_chars / 10, 1)
        psychological_ratio = len(re.findall(r'心想|觉得|感到|认为', text)) / max(total_chars / 100, 1)
        
        return RhythmPattern(
            avg_paragraph_length=round(avg_length, 1),
            paragraph_variation=round(variation, 1),
            dialogue_ratio=round(min(1, dialogue_ratio), 3),
            description_ratio=round(min(1, description_ratio), 3),
            action_ratio=round(min(1, action_ratio), 3),
            psychological_ratio=round(min(1, psychological_ratio), 3)
        )
    
    def _detect_style_tags(
        self, 
        text: str, 
        sentence_length: SentenceLengthDistribution,
        rhythm: RhythmPattern
    ) -> List[str]:
        """检测风格标签"""
        tags = []
        
        if sentence_length.avg_length < 20:
            tags.append("简洁明快")
        elif sentence_length.avg_length > 35:
            tags.append("华丽铺陈")
        else:
            tags.append("张弛有度")
        
        if rhythm.dialogue_ratio > 0.3:
            tags.append("对话主导")
        if rhythm.psychological_ratio > 0.2:
            tags.append("心理描写")
        if rhythm.action_ratio > 0.5:
            tags.append("动作密集")
        
        if sentence_length.std_dev > 15:
            tags.append("节奏多变")
        elif sentence_length.std_dev < 8:
            tags.append("节奏平稳")
        
        if "古风" in text or "江湖" in text or "侠" in text:
            tags.append("古典武侠")
        if "修仙" in text or "灵气" in text or "境界" in text:
            tags.append("仙侠玄幻")
        
        return tags[:5]
    
    def _generate_style_guide(
        self,
        sentence_length: SentenceLengthDistribution,
        word_frequency: WordFrequencyFeatures,
        rhythm: RhythmPattern,
        style_tags: List[str]
    ) -> str:
        """生成 LLM 风格指南"""
        guide_parts = []
        
        guide_parts.append(f"【句式风格】")
        guide_parts.append(f"- 平均句长: {sentence_length.avg_length}字")
        guide_parts.append(f"- 短句比例: {sentence_length.short_ratio*100:.1f}%")
        guide_parts.append(f"- 长句比例: {sentence_length.long_ratio*100:.1f}%")
        
        if sentence_length.short_ratio > 0.5:
            guide_parts.append(f"- 建议: 多用短句，节奏紧凑")
        elif sentence_length.long_ratio > 0.3:
            guide_parts.append(f"- 建议: 长句铺陈，细腻描写")
        
        guide_parts.append(f"\n【节奏特征】")
        guide_parts.append(f"- 对话占比: {rhythm.dialogue_ratio*100:.1f}%")
        guide_parts.append(f"- 动作占比: {rhythm.action_ratio*100:.1f}%")
        guide_parts.append(f"- 心理描写: {rhythm.psychological_ratio*100:.1f}%")
        
        guide_parts.append(f"\n【风格标签】")
        guide_parts.append(f"- {', '.join(style_tags)}")
        
        if word_frequency.top_words:
            guide_parts.append(f"\n【高频词汇】")
            top_5 = [f"{w}({c})" for w, c in word_frequency.top_words[:5]]
            guide_parts.append(f"- {', '.join(top_5)}")
        
        return "\n".join(guide_parts)
    
    def compare_styles(self, name1: str, name2: str) -> StyleComparison:
        """对比两种风格"""
        if name1 not in self.fingerprint_cache or name2 not in self.fingerprint_cache:
            return StyleComparison(0, ["未找到风格指纹"], [])
        
        fp1 = self.fingerprint_cache[name1]
        fp2 = self.fingerprint_cache[name2]
        
        differences = []
        suggestions = []
        
        len_diff = abs(fp1.sentence_length.avg_length - fp2.sentence_length.avg_length)
        if len_diff > 10:
            differences.append(f"句长差异较大: {fp1.sentence_length.avg_length} vs {fp2.sentence_length.avg_length}")
            suggestions.append(f"建议调整句长至 {(fp1.sentence_length.avg_length + fp2.sentence_length.avg_length) / 2:.0f} 字")
        
        rhythm_diff = abs(fp1.rhythm.dialogue_ratio - fp2.rhythm.dialogue_ratio)
        if rhythm_diff > 0.2:
            differences.append(f"对话比例差异: {fp1.rhythm.dialogue_ratio*100:.1f}% vs {fp2.rhythm.dialogue_ratio*100:.1f}%")
        
        tag_overlap = len(set(fp1.style_tags) & set(fp2.style_tags))
        tag_union = len(set(fp1.style_tags) | set(fp2.style_tags))
        similarity = tag_overlap / max(tag_union, 1) * 0.5 + (1 - len_diff / 50) * 0.5
        similarity = max(0, min(1, similarity))
        
        return StyleComparison(
            similarity_score=round(similarity, 3),
            differences=differences,
            suggestions=suggestions
        )
    
    def export_fingerprint(self, name: str) -> str:
        """导出风格指纹为 JSON"""
        if name not in self.fingerprint_cache:
            return "{}"
        
        fp = self.fingerprint_cache[name]
        data = {
            "sentence_length": {
                "avg": fp.sentence_length.avg_length,
                "std_dev": fp.sentence_length.std_dev,
                "short_ratio": fp.sentence_length.short_ratio,
                "long_ratio": fp.sentence_length.long_ratio
            },
            "rhythm": {
                "dialogue_ratio": fp.rhythm.dialogue_ratio,
                "action_ratio": fp.rhythm.action_ratio,
                "psychological_ratio": fp.rhythm.psychological_ratio
            },
            "style_tags": fp.style_tags,
            "llm_style_guide": fp.llm_style_guide
        }
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def import_fingerprint(self, name: str, json_data: str) -> bool:
        """从 JSON 导入风格指纹"""
        try:
            data = json.loads(json_data)
            sl = data.get("sentence_length", {})
            rh = data.get("rhythm", {})
            
            fingerprint = StyleFingerprint(
                sentence_length=SentenceLengthDistribution(
                    avg_length=sl.get("avg", 20),
                    min_length=5,
                    max_length=100,
                    std_dev=sl.get("std_dev", 10),
                    short_ratio=sl.get("short_ratio", 0.3),
                    medium_ratio=0.4,
                    long_ratio=sl.get("long_ratio", 0.3)
                ),
                word_frequency=WordFrequencyFeatures([], 0.5, 0.1, 0.1, 0.2, 0.3),
                rhythm=RhythmPattern(
                    avg_paragraph_length=100,
                    paragraph_variation=50,
                    dialogue_ratio=rh.get("dialogue_ratio", 0.2),
                    description_ratio=0.3,
                    action_ratio=rh.get("action_ratio", 0.3),
                    psychological_ratio=rh.get("psychological_ratio", 0.1)
                ),
                style_tags=data.get("style_tags", []),
                llm_style_guide=data.get("llm_style_guide", "")
            )
            
            self.fingerprint_cache[name] = fingerprint
            logger.info(f"StyleAnalyzer: 导入风格指纹 '{name}'")
            return True
        except Exception as e:
            logger.error(f"Import fingerprint failed: {e}")
            return False


_style_analyzer: Optional[StyleAnalyzer] = None


def get_style_analyzer() -> StyleAnalyzer:
    """获取文风分析器单例"""
    global _style_analyzer
    if _style_analyzer is None:
        _style_analyzer = StyleAnalyzer()
    return _style_analyzer
