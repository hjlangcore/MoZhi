"""去AI味处理器 — 检测并清除AI写作痕迹，提升文字自然度

参考 InkOS 的词汇监控机制，增强以下功能：
1. 词汇使用频率追踪器
2. 章节级别的词汇监控
3. 替换建议生成
4. 语言多样性保持
"""
import re
from typing import Dict, Any, List, Set, Optional, Tuple
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from loguru import logger


@dataclass
class VocabularyStats:
    """词汇统计数据结构"""
    word: str
    count: int
    positions: List[int] = field(default_factory=list)
    first_chapter: int = 0
    last_chapter: int = 0
    fatigue_level: str = "normal"


@dataclass
class ChapterVocabularyReport:
    """章节词汇报告"""
    chapter_number: int
    total_words: int
    unique_words: int
    fatigue_score: float
    repeated_words: Dict[str, int]
    ai_patterns: List[Dict[str, Any]]
    suggestions: List[str]
    diversity_index: float


# AI高频疲劳词（中文小说场景）- 扩展版
AI_FATIGUE_WORDS = {
    "总的来说", "总而言之", "综上所述", "不可否认", "值得注意的是",
    "此外", "另外", "与此同时", "在此过程中", "因此",
    "所以", "于是", "便", "随即", "紧接着",
    "然而", "不过", "却", "但是", "尽管如此",
    "显然", "毫无疑问", "可以想象", "毋庸置疑",
    "令人惊讶的是", "出乎意料的是", "没想到的是",
    "在这个世界里", "在这个时代", "在这个地方",
    "他的眼中", "他的心中", "他的脑海中",
    "一股", "一道", "一声", "一抹",
    "微微", "轻轻", "缓缓", "渐渐", "慢慢",
    "不禁", "不由", "忍不住", "下意识",
    "仿佛", "好像", "似乎", "宛如",
}

# 高频动词替换表
VERB_REPLACEMENTS = {
    "看向": ["望向", "瞥向", "注视", "凝视"],
    "说道": ["道", "开口", "沉声道", "轻声道"],
    "想到": ["想起", "忆起", "脑海中浮现"],
    "感到": ["感觉到", "察觉到", "体会到"],
    "看到": ["看见", "瞧见", "目睹", "望见"],
    "听到": ["听见", "闻声", "耳畔传来"],
    "转身": ["回身", "转过身", "旋身"],
    "走道": ["走向", "行至", "踱步"],
}

# 高频形容词替换表
ADJECTIVE_REPLACEMENTS = {
    "冰冷": ["寒凉", "森寒", "冷冽"],
    "温暖": ["温热", "和煦", "暖融融"],
    "黑暗": ["漆黑", "幽暗", "昏黑"],
    "明亮": ["明亮", "璀璨", "熠熠"],
    "巨大": ["庞大", "硕大", "宏伟"],
    "渺小": ["微小", "细小", "微末"],
}

# AI高频句式模式（正则）
AI_PATTERNS = [
    (r'他\s*心中\s*(?:不[禁由])?\s*(?:暗[暗自]?)?\s*(?:想[到着]|思[索考]|感叹|惊[叹讶])', 'AI心理描写'),
    (r'只\s*见\s*(?:一道|一股|一抹|一片)', 'AI视觉描写'),
    (r'(?:缓[缓慢]|慢[慢缓]|渐[渐缓]|徐[徐缓])\s*(?:地\s*)?(?:走|行|移|推|拉|升|降|转|变)', 'AI动作描写'),
    (r'(?:不[由禁]|忍不[住禁])\s*(?:地\s*)?(?:倒吸|深吸|感叹|赞叹|点头|摇头)', 'AI反应描写'),
    (r'(?:眼中|眸中|目光中|眼神中)\s*(?:闪过|掠过|浮现|透出|露出)\s*(?:一[丝抹股道片]|些许|几分)', 'AI眼神描写'),
    (r'(?:嘴角|唇边)\s*(?:微微)?\s*(?:上扬|勾起|泛起|浮现|露出)\s*(?:一[丝抹]\s*)?(?:笑[意容]|弧度)', 'AI微表情'),
    (r'(?:深吸|深呼|呼出)\s*[一口]?\s*(?:口\s*)?(?:气|浊气)', 'AI呼吸描写'),
]

# AI文章常见问题
AI_ISSUES = [
    "段落开头句式重复（连续3段以上用相同结构开头）",
    "形容词堆砌（一句话超过3个形容词修饰同一对象）",
    "情绪标签化（直接说「他很愤怒」而非通过行为展示）",
    "节奏过于平均（每段长度相似，缺乏长短错落）",
    "过度解释（角色做一件事后紧跟着解释为什么）",
    "对话过于正式（缺乏口语化、缩略、语气词）",
    "视角跳跃（同一段落内切换多人视角）",
]


class VocabularyMonitor:
    """词汇监控器 - 参考 InkOS 的词汇疲劳检测机制"""
    
    def __init__(self):
        self.word_history: Dict[str, VocabularyStats] = {}
        self.chapter_vocabulary: Dict[int, Set[str]] = defaultdict(set)
        self.total_chapters = 0
        self.fatigue_threshold = 3
        self.diversity_target = 0.7
    
    def track_chapter(self, content: str, chapter_number: int) -> ChapterVocabularyReport:
        """追踪章节词汇使用情况"""
        words = self._extract_words(content)
        word_counter = Counter(words)
        
        self.total_chapters = max(self.total_chapters, chapter_number)
        self.chapter_vocabulary[chapter_number] = set(words)
        
        repeated_words = {}
        for word, count in word_counter.most_common(50):
            if count >= self.fatigue_threshold:
                repeated_words[word] = count
                if word not in self.word_history:
                    self.word_history[word] = VocabularyStats(
                        word=word,
                        count=count,
                        first_chapter=chapter_number,
                        last_chapter=chapter_number
                    )
                else:
                    self.word_history[word].count += count
                    self.word_history[word].last_chapter = chapter_number
        
        diversity_index = self._calculate_diversity(words, word_counter)
        fatigue_score = self._calculate_fatigue_score(repeated_words, len(words))
        suggestions = self._generate_suggestions(repeated_words, diversity_index)
        
        return ChapterVocabularyReport(
            chapter_number=chapter_number,
            total_words=len(words),
            unique_words=len(word_counter),
            fatigue_score=fatigue_score,
            repeated_words=repeated_words,
            ai_patterns=[],
            suggestions=suggestions,
            diversity_index=diversity_index
        )
    
    def _extract_words(self, content: str) -> List[str]:
        """提取中文词汇（简化版分词）"""
        words = []
        for match in re.finditer(r'[\u4e00-\u9fff]{2,4}', content):
            words.append(match.group())
        return words
    
    def _calculate_diversity(self, words: List[str], word_counter: Counter) -> float:
        """计算词汇多样性指数"""
        if not words:
            return 1.0
        unique_ratio = len(word_counter) / len(words)
        top_10_ratio = sum(c for _, c in word_counter.most_common(10)) / len(words)
        diversity = unique_ratio * (1 - top_10_ratio * 0.5)
        return round(min(1.0, diversity), 3)
    
    def _calculate_fatigue_score(self, repeated_words: Dict[str, int], total: int) -> float:
        """计算疲劳得分"""
        if not repeated_words or total == 0:
            return 0.0
        fatigue_count = sum(repeated_words.values())
        return round(min(100, (fatigue_count / total) * 100), 1)
    
    def _generate_suggestions(self, repeated_words: Dict[str, int], diversity: float) -> List[str]:
        """生成替换建议"""
        suggestions = []
        
        for word, count in sorted(repeated_words.items(), key=lambda x: -x[1])[:5]:
            if word in VERB_REPLACEMENTS:
                alternatives = VERB_REPLACEMENTS[word]
                suggestions.append(f"「{word}」出现{count}次，可替换为：{', '.join(alternatives[:2])}")
            elif word in ADJECTIVE_REPLACEMENTS:
                alternatives = ADJECTIVE_REPLACEMENTS[word]
                suggestions.append(f"「{word}」出现{count}次，可替换为：{', '.join(alternatives[:2])}")
            elif word in AI_FATIGUE_WORDS:
                suggestions.append(f"「{word}」是AI高频词，出现{count}次，建议删除或替换")
        
        if diversity < 0.5:
            suggestions.append(f"词汇多样性指数{diversity}偏低，建议增加同义词变化")
        
        return suggestions
    
    def get_cross_chapter_fatigue(self) -> Dict[str, Any]:
        """获取跨章节词汇疲劳报告"""
        cross_chapter_words = {}
        for word, stats in self.word_history.items():
            if stats.last_chapter - stats.first_chapter >= 2:
                cross_chapter_words[word] = {
                    "count": stats.count,
                    "span": stats.last_chapter - stats.first_chapter + 1,
                    "density": stats.count / (stats.last_chapter - stats.first_chapter + 1)
                }
        
        return {
            "total_tracked": len(self.word_history),
            "cross_chapter_words": cross_chapter_words,
            "recommendation": "以下词汇在多章节重复出现，建议替换" if cross_chapter_words else "词汇使用良好"
        }


class DeAIProcessor:
    """检测并清除AI写作痕迹"""

    def __init__(self):
        self.fatigue_words: Set[str] = AI_FATIGUE_WORDS
        self.ai_patterns: List[tuple] = AI_PATTERNS
        self.issues: List[str] = AI_ISSUES
        self.vocabulary_monitor = VocabularyMonitor()

    def detect_ai_traces(self, content: str) -> Dict[str, Any]:
        """检测AI痕迹"""
        fatigue_hits: Dict[str, int] = {}
        for word in self.fatigue_words:
            count = content.count(word)
            if count > 0:
                fatigue_hits[word] = count

        pattern_hits: List[Dict[str, Any]] = []
        for pattern, label in self.ai_patterns:
            matches = re.findall(pattern, content)
            if matches:
                pattern_hits.append({
                    "pattern": pattern,
                    "label": label,
                    "count": len(matches)
                })

        # 计算AI味得分（0=完全人类，100=典型AI）
        fatigue_score = sum(fatigue_hits.values()) / max(len(content) / 100, 1) * 100
        fatigue_score = min(100, fatigue_score * 2)

        pattern_score = sum(p["count"] for p in pattern_hits) / max(len(content) / 200, 1) * 50
        pattern_score = min(100, pattern_score)

        # 检测段落开头句式重复
        sentences = re.split(r'[。！？\n]', content)
        sentence_starts = []
        for s in sentences:
            s = s.strip()
            if len(s) > 5:
                sentence_starts.append(s[:3])
        start_counter = Counter(sentence_starts)
        repeats = sum(1 for c in start_counter.values() if c >= 3)
        structure_score = min(30, repeats * 10)

        total_score = min(100, fatigue_score * 0.3 + pattern_score * 0.4 + structure_score * 0.3)

        level = "优秀"
        if total_score > 60:
            level = "明显AI痕迹"
        elif total_score > 30:
            level = "轻微AI痕迹"
        elif total_score > 15:
            level = "较自然"

        return {
            "ai_score": round(total_score, 1),
            "level": level,
            "fatigue_words": {k: v for k, v in fatigue_hits.items() if v >= 2},
            "pattern_hits": pattern_hits,
            "structure_issues": repeats > 0
        }

    def clean_ai_traces(self, content: str, llm_client=None) -> str:
        """清洗AI痕迹"""
        if llm_client:
            return self._llm_clean(content, llm_client)
        return self._rule_clean(content)

    def _rule_clean(self, content: str) -> str:
        """基于规则的AI痕迹清洗"""
        cleaned = content

        # 替换高频重复连接词
        replacements = {
            "总的来说": "",
            "总而言之": "",
            "综上所述": "",
            "不可否认": "",
            "值得注意的是": "注意",
            "令人惊讶的是": "",
            "出乎意料的是": "",
        }
        for word, replacement in replacements.items():
            if cleaned.count(word) >= 2:
                cleaned = cleaned.replace(word, replacement)

        # 限制「只见」「却是」等高频词
        for word in ["只见", "却是", "随即", "紧接着"]:
            count = cleaned.count(word)
            if count > 3:
                # 每3个保留1个
                parts = cleaned.split(word)
                keep_every = max(3, len(parts) // 3)
                new_parts = []
                for i, part in enumerate(parts):
                    new_parts.append(part)
                    if i < len(parts) - 1 and i % keep_every == 0:
                        new_parts.append(word)
                cleaned = "".join(new_parts)

        return cleaned

    def _llm_clean(self, content: str, llm_client) -> str:
        """使用LLM清洗AI痕迹"""
        prompt = f"""请对以下小说内容进行「去AI味」处理：

原文：
{content}

处理要求：
1. 删除或替换AI高频词汇（如「总的来说」「不可否认」「在这个世界里」）
2. 将过于工整的句式打散，增加长短句错落
3. 对话更口语化（加语气词、缩略、甚至不完整句）
4. 情绪描写改为行为展示（Show, don't tell）
5. 删除冗余的心理描写和过度解释
6. 保持故事内容和情节不变
7. 段落开头句式多样化

请直接输出去AI味后的内容，不要添加任何说明。"""

        try:
            cleaned = llm_client.generate(prompt, temperature=0.5)
            return cleaned
        except Exception as e:
            logger.error(f"LLM de-AI failed: {e}")
            return content

    def get_ai_free_writing_tips(self) -> str:
        """返回去AI味写作建议"""
        return """【去AI味写作建议】
1. 每段开头换花样 — 不要连续用「只见」「随即」「他...」
2. 对话要有人味儿 — 加语气词（呢、吧、啊、哈），允许说的不完整
3. 长短句错落 — 紧张用短句，抒情用长句，不要每句15-20字
4. 情绪靠行为表达 — 「他攥紧拳头」>「他很愤怒」
5. 少用副词 — 「他快速跑走」→「他冲了出去」
6. 删掉AI标签 — 去掉「总的来说」「值得注意的是」
7. 视角专一 — 同一段别在多人内心跳来跳去"""
    
    def analyze_chapter_vocabulary(self, content: str, chapter_number: int) -> ChapterVocabularyReport:
        """分析章节词汇使用情况"""
        report = self.vocabulary_monitor.track_chapter(content, chapter_number)
        ai_detection = self.detect_ai_traces(content)
        report.ai_patterns = ai_detection.get("pattern_hits", [])
        return report
    
    def get_vocabulary_suggestions(self, content: str) -> List[str]:
        """获取词汇替换建议"""
        words = self.vocabulary_monitor._extract_words(content)
        word_counter = Counter(words)
        suggestions = []
        
        for word, count in word_counter.most_common(20):
            if count >= 3:
                if word in VERB_REPLACEMENTS:
                    alternatives = VERB_REPLACEMENTS[word]
                    suggestions.append(f"「{word}」出现{count}次 → 建议替换为：{', '.join(alternatives)}")
                elif word in ADJECTIVE_REPLACEMENTS:
                    alternatives = ADJECTIVE_REPLACEMENTS[word]
                    suggestions.append(f"「{word}」出现{count}次 → 建议替换为：{', '.join(alternatives)}")
                elif word in AI_FATIGUE_WORDS:
                    suggestions.append(f"「{word}」是AI高频词，出现{count}次 → 建议删除")
        
        return suggestions[:10]
    
    def get_cross_chapter_report(self) -> Dict[str, Any]:
        """获取跨章节词汇疲劳报告"""
        return self.vocabulary_monitor.get_cross_chapter_fatigue()


_deai_processor: Optional[DeAIProcessor] = None


def get_deai_processor() -> DeAIProcessor:
    global _deai_processor
    if _deai_processor is None:
        _deai_processor = DeAIProcessor()
    return _deai_processor
