"""终端流式输出 — 小说创作全过程可视化 + 文件持久化

终端实时展示 + 同步写入 novel_output/{小说名}/ 目录：
  _小说信息.txt  — 书名/世界观/角色/分卷
  _创作日志.txt  — 每章进度/质量/门禁记录
"""
from typing import List, Optional
from datetime import datetime
from pathlib import Path
from loguru import logger

from src.novel_agent.state import NovelState, NovelSettingModel, CharacterModel, VolumeModel


SEP = "=" * 70
SEP_THIN = "-" * 70


class TerminalDisplay:
    """终端可视化 + 文件持久化"""

    def __init__(self, enabled: bool = True, output_base: str = "./novel_output"):
        self.enabled = enabled
        self.output_base = Path(output_base)
        self.start_time: Optional[datetime] = None
        self._last_chapter_displayed = 0
        self._novel_dir: Optional[Path] = None
        self._info_file: Optional[Path] = None
        self._log_file: Optional[Path] = None
        self._lines: List[str] = []  # 缓存所有输出行

    def _write(self, text: str):
        """同时写入终端和文件"""
        if self.enabled:
            print(text)
        self._lines.append(text)
        # 实时写入文件
        if self._log_file:
            try:
                with open(self._log_file, "a", encoding="utf-8") as f:
                    f.write(text + "\n")
            except Exception:
                pass

    def _init_novel_dir(self, novel_title: str):
        """创建小说专属输出目录"""
        safe_title = "".join(c for c in novel_title if c not in r'<>:"/\|?*')[:50]
        if not safe_title:
            safe_title = "未命名"
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._novel_dir = self.output_base / f"{safe_title}_{ts}"
        self._novel_dir.mkdir(parents=True, exist_ok=True)
        self._log_file = self._novel_dir / "_创作日志.txt"
        self._info_file = self._novel_dir / "_小说信息.txt"

    def _save_info_file(self, content: str):
        """保存小说信息到文件"""
        if self._info_file:
            try:
                with open(self._info_file, "w", encoding="utf-8") as f:
                    f.write(content)
            except Exception as e:
                logger.warning(f"Failed to save info file: {e}")

    # ================================================================
    # 小说初始化展示
    # ================================================================
    def show_novel_header(self, state: NovelState, config):
        """展示小说完整信息 + 创建输出目录 + 保存信息文件"""
        if not self.enabled:
            return

        self.start_time = datetime.now()
        setting = state.setting
        if not setting:
            return

        # 创建 novel_output/{小说名}/ 目录
        self._init_novel_dir(setting.novel_title)

        # 收集所有信息行
        info_lines = []
        log_lines = []

        header = f"\n{'=' * 70}\n{'《' + setting.novel_title + '》':^68}\n{'=' * 70}"
        info_lines.append(f"《{setting.novel_title}》创作信息")
        info_lines.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        info_lines.append("")

        self._write(header)

        # 基本信息
        basic = [
            f"  [书名] 《{setting.novel_title}》",
            f"  [文风] {config.style_type}",
            f"  [主题] {config.novel_theme}",
            f"  [目标] {config.max_words // 10000}万字 / 约{config.estimated_chapters}章 / 每章{config.chapter_words}字",
        ]
        for line in basic:
            self._write(line)
        info_lines.extend(basic)
        info_lines.append("")

        # 世界观
        world_lines = self._build_worldview(setting)
        for line in world_lines:
            self._write(line)
        info_lines.extend(world_lines)
        info_lines.append("")

        # 角色阵容
        char_lines = self._build_characters(setting)
        for line in char_lines:
            self._write(line)
        info_lines.extend(char_lines)
        info_lines.append("")

        # 分卷结构
        vol_lines = self._build_volumes(setting, config)
        for line in vol_lines:
            self._write(line)
        info_lines.extend(vol_lines)

        # 保存小说信息文件
        self._save_info_file("\n".join(info_lines))
        logger.info(f"Novel dir: {self._novel_dir}")

    def _build_worldview(self, setting: NovelSettingModel) -> List[str]:
        lines = [f"  {SEP_THIN}", "  [世界观]"]
        if setting.world_framework:
            lines.append(f"     {setting.world_framework[:400]}")
        if setting.power_system:
            lines.append(f"\n  [修炼体系]")
            lines.append(f"     {setting.power_system[:400]}")
        if setting.major_factions:
            lines.append(f"\n  [主要势力]")
            lines.append(f"     {setting.major_factions[:200]}")
        lines.append(f"  {SEP_THIN}")
        return lines

    def _build_characters(self, setting: NovelSettingModel) -> List[str]:
        lines = ["  [角色阵容]", f"  {SEP_THIN}"]
        mc = setting.main_character
        if mc and mc.name != "待定":
            lines.append(self._char_line("[男主]", mc))
        for char in setting.supporting_characters:
            if "女主" in char.role or "CP" in char.role:
                lines.append(self._char_line("[女主]", char))
                break
        for char in setting.supporting_characters:
            if "女主" not in char.role and "CP" not in char.role:
                label = "[导师]" if "导师" in char.role else "[配角]"
                lines.append(self._char_line(label, char))
        for char in setting.antagonists:
            lines.append(self._char_line("[反派]", char))
        total = 1 + len(setting.supporting_characters) + len(setting.antagonists)
        lines.append(f"\n  >> 共 {total} 个角色")
        return lines

    @staticmethod
    def _char_line(label: str, char: CharacterModel) -> str:
        desc = char.description[:80] if char.description else ""
        if char.personality and not desc:
            desc = char.personality[:50]
        return f"     {label:<8} {char.name:<10} {desc}"

    def _build_volumes(self, setting: NovelSettingModel, config) -> List[str]:
        volumes = setting.volume_threads
        if not volumes:
            return []
        lines = [f"\n  [分卷结构] 共{len(volumes)}卷", f"  {SEP_THIN}"]
        ch_per_vol = max(1, config.estimated_chapters // max(1, len(volumes)))
        for vol in volumes:
            start_ch = (vol.volume_number - 1) * ch_per_vol + 1
            end_ch = min(vol.volume_number * ch_per_vol, config.estimated_chapters)
            lines.append(f"     第{vol.volume_number}卷「{vol.title}」")
            lines.append(f"         ~第{start_ch}-{end_ch}章 | {vol.core_conflict[:60]}")
            if vol.climax_type:
                lines.append(f"         高潮: {vol.climax_type}")
            if vol.character_growth:
                lines.append(f"         成长: {vol.character_growth[:50]}")
        return lines

    # ================================================================
    # 章节写作进度
    # ================================================================
    def show_chapter_start(self, chapter_number: int, total_estimated: int, chapter_type: str = ""):
        type_label = {
            "golden_opening": "[黄金章]", "small_climax": "[爽点章]",
            "big_climax": "[高潮章]", "volume_climax": "[卷高潮]"
        }.get(chapter_type, "")
        self._write(f"\n  {type_label} 正在创作第{chapter_number}章...")

    def show_chapter_done(
        self, chapter_number: int, title: str, word_count: int,
        quality_score: float = 0, total_words: int = 0, target_words: int = 0,
    ):
        if quality_score >= 80:
            q = f"A({quality_score:.0f})"
        elif quality_score >= 60:
            q = f"B({quality_score:.0f})"
        elif quality_score > 0:
            q = f"C({quality_score:.0f})"
        else:
            q = "--"
        progress = ""
        if target_words > 0:
            pct = min(100, total_words * 100 // target_words)
            bar_len = 20
            filled = int(bar_len * pct / 100)
            progress = f" [{'#' * filled}{'-' * (bar_len - filled)}] {pct}%"
        self._write(f"     -> 第{chapter_number:>3}章「{title}」 {word_count}字 质量{q} 累计{total_words}字{progress}")
        self._last_chapter_displayed = chapter_number

    def show_chapter_rejected(self, chapter_number: int, reason: str = ""):
        self._write(f"     !! 第{chapter_number}章 未通过门禁: {reason[:80]}... 自动修正中...")

    def show_chapter_fixed(self, chapter_number: int, new_quality: float):
        self._write(f"     ~~ 第{chapter_number}章 修正完成，新质量: {new_quality:.0f}")

    # ================================================================
    # 进度总结
    # ================================================================
    def show_progress_summary(self, state: NovelState, config):
        chapters = state.chapters
        if not chapters:
            return
        self._write(f"\n  {SEP}")
        self._write(f"  [进度总结] 已完成 {len(chapters)} 章")
        self._write(f"  {SEP_THIN}")
        self._write("  最近章节：")
        for ch in chapters[-5:]:
            q = ch.quality_score
            q_str = f"A({q:.0f})" if q >= 80 else f"B({q:.0f})" if q >= 60 else f"C({q:.0f})" if q > 0 else "--"
            self._write(f"     Ch{ch.chapter_number:>3}「{ch.title}」 {ch.word_count}字 {q_str}")
        total = state.total_words
        target = config.max_words
        pct = min(100, int(total * 100 / target))
        elapsed = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        speed = int(total / elapsed * 60) if elapsed > 0 else 0
        self._write(f"\n  总进度: {total}/{target}字 ({pct}%)")
        if speed > 0:
            self._write(f"  平均速度: {speed}字/分钟")
            self._write(f"  预计剩余: { (target - total) // max(1, speed) }分钟")

    def show_novel_complete(self, state: NovelState, export_path: str = ""):
        elapsed = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        self._write(f"\n  {SEP}")
        self._write(f"  *** 小说创作完成! ***")
        self._write(f"  {SEP}")
        self._write(f"     总字数: {state.total_words:,}")
        self._write(f"     总章数: {state.current_chapter}")
        self._write(f"     总耗时: {hours}时{minutes}分")
        if export_path:
            self._write(f"     导出路径: {export_path}")
        if self._novel_dir:
            self._write(f"     信息目录: {self._novel_dir}")
        self._write(f"  {SEP}\n")

    def save_chapter(self, chapter_number: int, title: str, content: str, word_count: int = 0):
        """每章写完后立即保存到 novel_output 目录"""
        if not self._novel_dir:
            return
        safe_title = "".join(c for c in title if c not in r'<>:"/\|?*')[:40]
        fname = f"第{chapter_number:04d}章_{safe_title}.txt"
        try:
            path = self._novel_dir / fname
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"第{chapter_number}章 {title}\n")
                f.write(f"字数：{word_count}\n")
                f.write(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n\n")
                f.write(content)
            logger.debug(f"Chapter saved: {fname}")
        except Exception as e:
            logger.warning(f"Failed to save chapter file: {e}")

    @property
    def novel_dir(self) -> Optional[Path]:
        return self._novel_dir


_display: Optional[TerminalDisplay] = None


def get_terminal_display() -> TerminalDisplay:
    global _display
    if _display is None:
        _display = TerminalDisplay(enabled=True)
    return _display