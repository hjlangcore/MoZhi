"""Human Review Gate — 人工审核门控机制

参考 InkOS 的 HRG (Human Review Gate) 机制：
- 每N章自动暂停，等待人工审核
- 支持批量审核模式
- 提供审核建议和修改入口
- 确保内容方向符合创作者意图
"""
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from loguru import logger


class ReviewStatus(str, Enum):
    """审核状态"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"
    SKIPPED = "skipped"


class GateTrigger(str, Enum):
    """触发审核的原因"""
    CHAPTER_INTERVAL = "chapter_interval"
    QUALITY_DROP = "quality_drop"
    CRITICAL_PLOT = "critical_plot"
    CHARACTER_DEATH = "character_death"
    WORLD_CHANGE = "world_change"
    MANUAL = "manual"


@dataclass
class ReviewItem:
    """待审核项"""
    chapter_number: int
    trigger: GateTrigger
    status: ReviewStatus = ReviewStatus.PENDING
    content_preview: str = ""
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    reviewed_at: Optional[datetime] = None
    reviewer_notes: str = ""


@dataclass
class ReviewGateConfig:
    """审核门控配置"""
    enabled: bool = True
    interval_chapters: int = 10
    quality_threshold: float = 60.0
    auto_approve_minor: bool = False
    pause_on_critical: bool = True
    notify_on_gate: bool = True
    batch_size: int = 5


@dataclass
class GateReport:
    """门控报告"""
    total_chapters: int
    pending_reviews: int
    approved_count: int
    rejected_count: int
    next_gate_chapter: int
    is_paused: bool
    recent_reviews: List[ReviewItem]


class HumanReviewGate:
    """人工审核门控"""
    
    def __init__(self, config: Optional[ReviewGateConfig] = None):
        self.config = config or ReviewGateConfig()
        self.review_queue: List[ReviewItem] = []
        self.review_history: Dict[int, ReviewItem] = {}
        self.chapter_count = 0
        self.is_paused = False
        self.pause_reason = ""
        self._gate_callbacks: List[Callable] = []
    
    def should_pause(self, chapter_number: int, quality_score: float = 100.0) -> bool:
        """判断是否应该暂停等待审核"""
        if not self.config.enabled:
            return False
        
        self.chapter_count = chapter_number
        
        if self.is_paused:
            return True
        
        if chapter_number % self.config.interval_chapters == 0:
            self._create_review_item(chapter_number, GateTrigger.CHAPTER_INTERVAL)
            return self._handle_gate_trigger(chapter_number, "章节间隔触发")
        
        if quality_score < self.config.quality_threshold:
            self._create_review_item(chapter_number, GateTrigger.QUALITY_DROP)
            return self._handle_gate_trigger(chapter_number, "质量下降触发")
        
        return False
    
    def _create_review_item(self, chapter_number: int, trigger: GateTrigger) -> ReviewItem:
        """创建审核项"""
        item = ReviewItem(
            chapter_number=chapter_number,
            trigger=trigger,
            status=ReviewStatus.PENDING
        )
        self.review_queue.append(item)
        self.review_history[chapter_number] = item
        logger.info(f"Human Review Gate: 创建审核项 - 章节{chapter_number}, 触发原因: {trigger.value}")
        return item
    
    def _handle_gate_trigger(self, chapter_number: int, reason: str) -> bool:
        """处理门控触发"""
        if self.config.pause_on_critical:
            self.is_paused = True
            self.pause_reason = reason
            logger.warning(f"Human Review Gate: 暂停写作 - {reason}, 章节{chapter_number}")
            
            for callback in self._gate_callbacks:
                try:
                    callback(chapter_number, reason)
                except Exception as e:
                    logger.error(f"Gate callback error: {e}")
            
            return True
        return False
    
    def approve(self, chapter_number: int, notes: str = "") -> bool:
        """批准审核"""
        if chapter_number in self.review_history:
            item = self.review_history[chapter_number]
            item.status = ReviewStatus.APPROVED
            item.reviewed_at = datetime.now()
            item.reviewer_notes = notes
            
            self.review_queue = [r for r in self.review_queue if r.chapter_number != chapter_number]
            
            if len(self.review_queue) == 0:
                self.is_paused = False
                self.pause_reason = ""
                logger.info(f"Human Review Gate: 审核通过 - 章节{chapter_number}, 队列清空，恢复写作")
            
            return True
        return False
    
    def reject(self, chapter_number: int, issues: List[str], notes: str = "") -> bool:
        """拒绝审核"""
        if chapter_number in self.review_history:
            item = self.review_history[chapter_number]
            item.status = ReviewStatus.REJECTED
            item.reviewed_at = datetime.now()
            item.issues = issues
            item.reviewer_notes = notes
            
            self.review_queue = [r for r in self.review_queue if r.chapter_number != chapter_number]
            
            logger.warning(f"Human Review Gate: 审核拒绝 - 章节{chapter_number}, 问题: {issues}")
            return True
        return False
    
    def modify(self, chapter_number: int, modifications: str) -> bool:
        """修改后通过"""
        if chapter_number in self.review_history:
            item = self.review_history[chapter_number]
            item.status = ReviewStatus.MODIFIED
            item.reviewed_at = datetime.now()
            item.reviewer_notes = modifications
            
            self.review_queue = [r for r in self.review_queue if r.chapter_number != chapter_number]
            
            if len(self.review_queue) == 0:
                self.is_paused = False
                self.pause_reason = ""
            
            logger.info(f"Human Review Gate: 修改后通过 - 章节{chapter_number}")
            return True
        return False
    
    def skip_review(self, chapter_number: int) -> bool:
        """跳过审核"""
        if chapter_number in self.review_history:
            item = self.review_history[chapter_number]
            item.status = ReviewStatus.SKIPPED
            item.reviewed_at = datetime.now()
            
            self.review_queue = [r for r in self.review_queue if r.chapter_number != chapter_number]
            
            if len(self.review_queue) == 0:
                self.is_paused = False
                self.pause_reason = ""
            
            return True
        return False
    
    def batch_approve(self, chapter_numbers: List[int]) -> int:
        """批量批准"""
        approved = 0
        for ch in chapter_numbers:
            if self.approve(ch):
                approved += 1
        return approved
    
    def force_resume(self) -> bool:
        """强制恢复写作"""
        self.is_paused = False
        self.pause_reason = ""
        self.review_queue.clear()
        logger.warning("Human Review Gate: 强制恢复写作")
        return True
    
    def register_callback(self, callback: Callable) -> None:
        """注册门控回调函数"""
        self._gate_callbacks.append(callback)
    
    def get_report(self) -> GateReport:
        """获取门控报告"""
        approved = sum(1 for r in self.review_history.values() if r.status == ReviewStatus.APPROVED)
        rejected = sum(1 for r in self.review_history.values() if r.status == ReviewStatus.REJECTED)
        
        next_gate = ((self.chapter_count // self.config.interval_chapters) + 1) * self.config.interval_chapters
        
        recent = list(self.review_history.values())[-5:]
        
        return GateReport(
            total_chapters=self.chapter_count,
            pending_reviews=len(self.review_queue),
            approved_count=approved,
            rejected_count=rejected,
            next_gate_chapter=next_gate,
            is_paused=self.is_paused,
            recent_reviews=recent
        )
    
    def get_pending_reviews(self) -> List[ReviewItem]:
        """获取待审核列表"""
        return self.review_queue.copy()
    
    def get_status_text(self) -> str:
        """获取状态文本"""
        if not self.config.enabled:
            return "审核门控已禁用"
        
        if self.is_paused:
            return f"⏸️ 已暂停 - {self.pause_reason}，待审核章节: {[r.chapter_number for r in self.review_queue]}"
        
        return f"✅ 运行中 - 已完成 {self.chapter_count} 章，下次审核点: 第{((self.chapter_count // self.config.interval_chapters) + 1) * self.config.interval_chapters}章"


_human_review_gate: Optional[HumanReviewGate] = None


def get_human_review_gate(config: Optional[ReviewGateConfig] = None) -> HumanReviewGate:
    """获取 Human Review Gate 单例"""
    global _human_review_gate
    if _human_review_gate is None:
        _human_review_gate = HumanReviewGate(config)
    return _human_review_gate
