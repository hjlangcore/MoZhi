"""小说导出器 — 将生成的小说导出为可发布的 .txt 文件"""
from pathlib import Path
from datetime import datetime
from typing import Optional
from loguru import logger


class NovelExporter:
    def __init__(self, output_dir: str = "./novel_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_all(self, novel_state, target_dir: str = "") -> str:
        if not novel_state or not novel_state.chapters:
            return ""
        title = novel_state.setting.novel_title if novel_state.setting else "未命名"
        safe_title = "".join(c for c in title if c not in r'<>:"/\|?*')[:50]
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        if target_dir:
            novel_dir = Path(target_dir)
        else:
            novel_dir = self.output_dir / f"{safe_title}_{ts}"
        novel_dir.mkdir(parents=True, exist_ok=True)

        # 构建卷信息索引（章节号 → 卷标题）
        volume_map = {}  # chapter_number → volume info string
        if novel_state.setting and novel_state.setting.volume_threads:
            for vol in novel_state.setting.volume_threads:
                start, end = vol.chapter_range
                volume_map[start] = f"\n{'=' * 50}\n第{vol.volume_number}卷「{vol.title}」\n{'=' * 50}\n\n"

        # 每章单独文件
        for ch in novel_state.chapters:
            fname = "".join(c for c in f"第{ch.chapter_number:04d}章_{ch.title}.txt" if c not in r'<>:"/\|?*')
            with open(novel_dir / fname, "w", encoding="utf-8") as f:
                if ch.chapter_number in volume_map:
                    f.write(volume_map[ch.chapter_number])
                f.write(f"第{ch.chapter_number}章 {ch.title}\n\n{ch.content}\n")

        # 全集大文件
        full = novel_dir / f"{safe_title}_全集.txt"
        with open(full, "w", encoding="utf-8") as f:
            f.write(f"《{safe_title}》\n总字数：{novel_state.total_words:,}  章节：{len(novel_state.chapters)}\n")
            f.write(f"风格：{novel_state.setting.style_type if novel_state.setting else '未知'}\n")
            f.write("=" * 60 + "\n\n")
            for ch in novel_state.chapters:
                if ch.chapter_number in volume_map:
                    f.write(volume_map[ch.chapter_number])
                f.write(f"第{ch.chapter_number}章 {ch.title}\n\n{ch.content}\n\n")

        logger.info(f"Exported {len(novel_state.chapters)} chapters → {novel_dir}")
        return str(novel_dir)

    def export_chapter(self, chapter, title: str = "未命名") -> str:
        safe = "".join(c for c in title if c not in r'<>:"/\|?*')[:30]
        d = self.output_dir / safe
        d.mkdir(parents=True, exist_ok=True)
        fname = "".join(c for c in f"第{chapter.chapter_number:04d}章_{chapter.title}.txt" if c not in r'<>:"/\|?*')
        with open(d / fname, "w", encoding="utf-8") as f:
            f.write(f"第{chapter.chapter_number}章 {chapter.title}\n\n{chapter.content}\n")
        return str(d / fname)


_exporter: Optional[NovelExporter] = None


def get_exporter() -> NovelExporter:
    global _exporter
    if _exporter is None:
        _exporter = NovelExporter()
    return _exporter
