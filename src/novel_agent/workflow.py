import json
import re
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
from loguru import logger

from src.core.config import NovelConfig, settings
from src.core.exceptions import LLMConnectionError, LLMResponseError
from src.novel_agent.state import (
    NovelState, ChapterModel, NovelStatus, ChapterStatus,
    NovelSettingModel, ForeshadowingModel, VolumeModel
)
from src.novel_agent.prompts import (
    FRAMEWORK_GENERATION_PROMPT,
    CHAPTER_WRITING_PROMPT,
    GOLDEN_CHAPTER_1_PROMPT,
    GOLDEN_CHAPTER_2_PROMPT,
    GOLDEN_CHAPTER_3_PROMPT,
    CLIMAX_CHAPTER_PROMPT,
    POLISH_PROMPT,
    PROOFREAD_PROMPT,
    CONTINUITY_CHECK_PROMPT,
    GENRE_ENFORCEMENT_PROMPT,
    CHAPTER_TITLE_PROMPT,
    format_prompt
)
from src.novel_agent.coherence_verifier import CoherenceVerifier
from src.novel_agent.genre_enforcer import GenreEnforcer
from src.novel_agent.repetition_guard import RepetitionGuard
from src.novel_agent.foreshadowing import ForeshadowingManager
from src.novel_agent.style_anchor import StyleAnchor, get_style_anchor_manager
from src.novel_agent.rhythm_controller import get_rhythm_controller, ChapterType
from src.novel_agent.deai_processor import get_deai_processor
from src.novel_agent.card_system import CardManager, create_cards_from_setting, get_card_manager
from src.novel_agent.audit_pipeline import get_audit_pipeline
from src.novel_agent.coherence_manager import get_coherence_manager
from src.novel_agent.novel_exporter import get_exporter
from src.novel_agent.story_planner import get_story_planner_prompt, VOLUME_TEMPLATE_50W, StoryPlan
from src.novel_agent.knowledge_integrator import get_knowledge_integrator, KnowledgeIntegrator
from src.novel_agent.memory_weights import get_memory_weighter, DynamicMemoryWeighter, WeightTier
from src.novel_agent.reasoning_planner import get_reasoning_planner, ReasoningPlanner, ChapterPlan
from src.novel_agent.generation_gates import get_generation_gates, GenerationGates, GateResult
from src.novel_agent.enhanced_audit import get_enhanced_audit, EnhancedAuditPipeline
from src.novel_agent.state_writeback import get_state_writeback, StateWritebackPipeline
from src.novel_agent.agent_loop import AgentLoopExecutor, EditorAgent, get_editor_agent
from src.novel_agent.terminal_display import get_terminal_display, TerminalDisplay


class LLMClient:
    def __init__(self, base_url: str, model: str, timeout: int = 120, num_gpu: int = 20):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout
        self.num_gpu = num_gpu  # 20=4G显存安全值, 999=自动全部GPU

    def generate(self, prompt: str, temperature: float = 0.7) -> str:
        import requests

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "temperature": temperature,
                    "stream": False,
                    "options": {
                        "num_gpu": self.num_gpu,
                        "num_predict": 4096, # 最大输出4096 tokens (约2000-4000中文字)
                        "num_ctx": 32768,     # 上下文窗口
                    }
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except requests.exceptions.ConnectionError:
            raise LLMConnectionError(f"Failed to connect to LLM at {self.base_url}")
        except requests.exceptions.Timeout:
            raise LLMConnectionError(f"LLM request timed out after {self.timeout}s")
        except Exception as e:
            raise LLMResponseError(f"LLM generation failed: {str(e)}")

    def generate_stream(self, prompt: str, temperature: float = 0.7, on_token=None) -> str:
        """流式生成，逐 token 回调 on_token(token)，返回完整文本"""
        import requests
        from loguru import logger as _logger

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "temperature": temperature,
                    "stream": True,
                    "options": {
                        "num_gpu": self.num_gpu,
                        "num_predict": 4096,
                        "num_ctx": 32768,
                    }
                },
                timeout=self.timeout,
                stream=True
            )
            response.raise_for_status()

            full_text = ""
            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    token = data.get("response", "")
                    if token:
                        full_text += token
                        if on_token:
                            on_token(token)
                    if data.get("done", False):
                        break
                except json.JSONDecodeError:
                    continue
            return full_text
        except requests.exceptions.ConnectionError:
            raise LLMConnectionError(f"Failed to connect to LLM at {self.base_url}")
        except requests.exceptions.Timeout:
            raise LLMConnectionError(f"LLM request timed out after {self.timeout}s")
        except Exception as e:
            raise LLMResponseError(f"LLM streaming failed: {str(e)}")

    def generate_json(self, prompt: str, temperature: float = 0.3) -> Dict[str, Any]:
        response_text = self.generate(prompt, temperature)

        def _try_parse(text: str) -> dict:
            # 先尝试直接解析（可能是纯 JSON）
            try:
                result = json.loads(text.strip())
                if isinstance(result, dict):
                    return result
            except json.JSONDecodeError:
                pass

            # 正则提取最外层的 JSON 对象
            json_match = re.search(r'\{[\s\S]*\}', text)
            if not json_match:
                raise LLMResponseError("No JSON object found in LLM response")

            json_str = json_match.group()
            # 去除尾部多余逗号
            json_str = re.sub(r',\s*\}', '}', json_str)
            json_str = re.sub(r',\s*\]', ']', json_str)
            # 去除控制字符（保留换行用于字符串内部）
            json_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', json_str)

            result = json.loads(json_str)
            if not isinstance(result, dict):
                raise LLMResponseError(f"LLM returned non-object JSON: {type(result).__name__}")
            return result

        try:
            return _try_parse(response_text)
        except (json.JSONDecodeError, LLMResponseError):
            raise
        except Exception as e:
            logger.warning(f"JSON parse failed: {e}, retrying...")
            retry_prompt = prompt + "\n\n注意：必须输出有效的JSON，不要有任何额外文本，确保所有字符串用双引号包裹，不要在最后一个元素后加逗号。"
            retry_text = self.generate(retry_prompt, temperature=0.1)
            try:
                return _try_parse(retry_text)
            except (json.JSONDecodeError, Exception) as e2:
                logger.error(f"JSON retry also failed: {retry_text[:300]}")
                raise LLMResponseError(f"LLM returned invalid JSON after retry: {e2}")


class SettingAgent:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def generate_setting(self, config: NovelConfig) -> NovelSettingModel:
        logger.info("Generating comprehensive story plan (characters + volumes + ending)...")

        def _safe_str(value, default=""):
            """将 LLM 可能返回的 dict/list 值安全转为字符串"""
            if isinstance(value, str):
                return value
            if isinstance(value, (dict, list)):
                return json.dumps(value, ensure_ascii=False)
            return str(value) if value else default

        style_descriptions = {
            "凡人流": "贴近现实，修仙路艰难险阻，主角需要一步一个脚印地修炼",
            "热血": "激情澎湃，战斗场面宏大，主角成长迅速",
            "隐忍": "低调内敛，主角前期受尽屈辱，后期爆发",
            "宏大": "世界观庞大，涉及多界、多域，势力纷杂",
            "番茄模式": "快节奏爽文，开局即冲突，金手指明确，打脸频繁，适合下沉市场"
        }

        prompt = get_story_planner_prompt(
            theme=config.novel_theme,
            style=config.style_type,
            total_words=config.max_words
        )

        result = self.llm.generate_json(prompt)
        logger.info(f"Story plan generated: {result.get('novel_title', '?')}")

        from src.novel_agent.state import CharacterModel

        # 构建主角
        chars = result.get("characters", [])
        mc_data = chars[0] if len(chars) > 0 else {}
        main_character = CharacterModel(
            name=mc_data.get("name", "待定"),
            role="主角",
            description=f"{mc_data.get('appearance', '')} | {mc_data.get('personality', '')}",
            background=mc_data.get("background", ""),
            personality=mc_data.get("personality", ""),
            motivation=mc_data.get("motivation", ""),
            importance="main"
        )

        # 构建配角（女主/导师/盟友）
        supporting = []
        for char in chars[1:]:
            role = char.get("role", "配角")
            if role in ("女主", "导师", "盟友"):
                supporting.append(CharacterModel(
                    name=char.get("name", "待定"),
                    role=role,
                    description=f"{char.get('personality', '')} | {char.get('background', '')}",
                    background=char.get("background", ""),
                    personality=char.get("personality", ""),
                    motivation=char.get("fate_50w", ""),
                    importance="supporting"
                ))

        # 构建反派
        antagonists = []
        for char in chars:
            role = char.get("role", "")
            if "BOSS" in role or "反派" in role:
                antagonists.append(CharacterModel(
                    name=char.get("name", "待定"),
                    role=role,
                    description=f"{char.get('personality', '')} | {char.get('fate_50w', '')}",
                    background=char.get("background", ""),
                    importance="antagonist"
                ))

        # 构建完整主线剧情（包含人物+分卷+结局）
        main_plot_parts = [f"核心主题：{result.get('core_theme', '')}"]
        main_plot_parts.append(f"结局类型：{result.get('ending_type', '')}")
        main_plot_parts.append(f"结局概要：{result.get('ending_summary', '')}")
        main_plot_parts.append(f"续集钩子：{result.get('sequel_hook', '无')}")

        # 角色一览
        main_plot_parts.append("\n角色阵容：")
        for char in chars:
            main_plot_parts.append(
                f"【{char.get('role', '?')}】{char.get('name', '?')} "
                f"→ 实力：{char.get('power_start', '?')}→{char.get('power_peak', '?')} "
                f"→ 50万字结局：{char.get('fate_50w', '?')}"
            )

        # 分卷大纲 + 创建 VolumeModel（每卷章节数 = 预估总章数 / 卷数）
        total_estimated_chapters = config.max_words // config.chapter_words
        vols_count = len(VOLUME_TEMPLATE_50W)
        ch_per_vol = max(1, total_estimated_chapters // vols_count)
        volume_models = []
        main_plot_parts.append(f"\n{config.max_words}字{vols_count}卷结构（每卷约{ch_per_vol}章）：")
        for vol in VOLUME_TEMPLATE_50W:
            vn = vol['volume_number']
            start_ch = (vn - 1) * ch_per_vol + 1
            end_ch = vn * ch_per_vol if vn < vols_count else total_estimated_chapters
            main_plot_parts.append(
                f"第{vn}卷「{vol['title']}」({vol['word_range']}，第{start_ch}-{end_ch}章)："
                f"{vol['main_goal']} | 反派：{vol['antagonist']} | "
                f"卷末钩子：{vol['ending_hook']}"
            )
            volume_models.append(VolumeModel(
                volume_number=vn,
                title=vol['title'],
                core_conflict=vol['main_goal'],
                character_growth=vol.get('main_goal', ''),
                climax_type=vol.get('climax', ''),
                chapter_range=(start_ch, end_ch),
                total_words=config.max_words // vols_count,
            ))

        main_plot_thread = "\n".join(main_plot_parts)

        # 构建势力描述
        factions = []
        for char in chars:
            role = char.get("role", "")
            name = char.get("name", "")
            if "BOSS" in role:
                factions.append(f"{name}势力")

        setting = NovelSettingModel(
            novel_title=_safe_str(result.get("novel_title", ""), "待定"),
            world_framework=_safe_str(result.get("world_setting", "")),
            power_system=_safe_str(result.get("power_system", "")),
            major_factions="、".join(factions) if factions else "多方势力角逐",
            main_character=main_character,
            supporting_characters=supporting,
            antagonists=antagonists,
            main_plot_thread=main_plot_thread,
            core_conflicts=_safe_str(result.get("core_theme", "")),
            style_type=config.style_type,
            style_description=style_descriptions.get(config.style_type, ""),
            volume_threads=volume_models,
        )

        logger.info(f"Setting generated: {setting.novel_title} "
                     f"({len(supporting)} allies, {len(antagonists)} villains, {len(chars)} total)")
        return setting


class WriterAgent:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
        self.rhythm = get_rhythm_controller()

    def write_chapter(
        self,
        novel_state: NovelState,
        chapter_number: int,
        target_words: int,
        knowledge_context: str = "",
        reasoning_context: str = "",
        memory_context: str = "",
        volume_context: str = ""
    ) -> str:
        logger.info(f"Writing chapter {chapter_number}...")

        previous_summary = ""
        if chapter_number > 1 and len(novel_state.chapters) >= chapter_number - 1:
            prev_chapter = novel_state.chapters[chapter_number - 2]
            previous_summary = f"第{chapter_number - 1}章「{prev_chapter.title}」的结尾：{prev_chapter.content[-200:]}"

        foreshadowing_hints = ""
        unresolved = [fs for fs in novel_state.foreshadowing_tracking if fs.status == "unresolved"]
        if unresolved:
            foreshadowing_hints = "\n".join([f"- {fs.seed}" for fs in unresolved[:3]])

        rhythm_guidance = self.rhythm.get_chapter_guidance(
            chapter_number,
            novel_state.setting.style_type if novel_state.setting else "凡人流"
        )

        style_guide = novel_state.setting.style_description if novel_state.setting else ""
        novel_title = novel_state.setting.novel_title if novel_state.setting else "待定"

        # 使用节奏控制器选择专用 Prompt
        chapter_type = self.rhythm.get_chapter_type(chapter_number)

        if chapter_type == ChapterType.GOLDEN_OPENING and chapter_number == 1:
            prompt = format_prompt(
                GOLDEN_CHAPTER_1_PROMPT,
                novel_title=novel_title,
                style_guide=style_guide,
                target_words=target_words
            )
        elif chapter_type == ChapterType.GOLDEN_OPENING and chapter_number == 2:
            prompt = format_prompt(
                GOLDEN_CHAPTER_2_PROMPT,
                novel_title=novel_title,
                style_guide=style_guide,
                previous_summary=previous_summary,
                target_words=target_words
            )
        elif chapter_type == ChapterType.GOLDEN_OPENING and chapter_number == 3:
            prompt = format_prompt(
                GOLDEN_CHAPTER_3_PROMPT,
                novel_title=novel_title,
                style_guide=style_guide,
                previous_summary=previous_summary,
                target_words=target_words
            )
        elif chapter_type in (ChapterType.BIG_CLIMAX, ChapterType.SMALL_CLIMAX, ChapterType.VOLUME_CLIMAX):
            prompt = format_prompt(
                CLIMAX_CHAPTER_PROMPT,
                novel_title=novel_title,
                style_guide=style_guide,
                previous_summary=previous_summary,
                rhythm_guidance=rhythm_guidance,
                target_words=target_words
            )
        else:
            prompt = format_prompt(
                CHAPTER_WRITING_PROMPT,
                novel_title=novel_title,
                setting_summary=str(novel_state.setting.dict())[:2000] if novel_state.setting else "",
                style_guide=style_guide,
                chapter_idx=chapter_number,
                total_words=novel_state.total_words,
                target_words=target_words,
                previous_summary=previous_summary,
                foreshadowing_hints=foreshadowing_hints,
                rhythm_guidance=rhythm_guidance,
                volume_context=volume_context or "（无卷信息）",
            )

        # 注入卷上下文（黄金章节和高潮章也需要卷信息）
        if volume_context:
            prompt = prompt + "\n\n【当前卷信息】\n" + volume_context

        # 注入动态记忆上下文（优先，因为 token 预算有限）
        if memory_context:
            prompt = prompt + "\n\n【动态记忆 — 当前章节相关背景】\n" + memory_context
            logger.info(f"Injected dynamic memory into chapter {chapter_number} prompt")

        # 注入主编规划（思考-规划-写作的 Phase 1 产出）
        if reasoning_context:
            prompt = prompt + "\n" + reasoning_context
            logger.info(f"Injected reasoning plan into chapter {chapter_number} prompt")

        # 追加联网参考资料
        if knowledge_context:
            prompt = prompt + "\n" + knowledge_context
            logger.info(f"Injected web knowledge into chapter {chapter_number} prompt")

        content = self.llm.generate(prompt, temperature=0.8)

        # 字数不足时强制续写
        min_words = int(target_words * 0.7)
        chinese_chars = len([c for c in content if '一' <= c <= '鿿'])
        if chinese_chars < min_words:
            logger.warning(f"Chapter {chapter_number} too short ({chinese_chars}/{target_words} Chinese chars), extending...")
            extend_prompt = f"""上文是一章小说的前半部分，共{chinese_chars}字。请继续往下写，把这章补到至少{target_words}字。

【上文结尾】：
{content[-300:]}

【要求】：
- 接着上文继续写，不要重复
- 推进情节或展开描写
- 必须至少再写{target_words - chinese_chars}字
- 结尾留悬念钩子
- 直接输出续写内容"""

            try:
                extension = self.llm.generate(extend_prompt, temperature=0.8)
                content = content + "\n\n" + extension
                new_count = len([c for c in content if '一' <= c <= '鿿'])
                logger.info(f"Extended: {chinese_chars} -> {new_count} Chinese chars")
            except Exception as e:
                logger.warning(f"Extension failed: {e}")

        logger.info(f"Chapter {chapter_number} written ({chapter_type.value}), length: {len(content)} chars")
        return content

    def write_chapter_stream(self, novel_state, chapter_number: int, target_words: int, knowledge_context: str = "", reasoning_context: str = "", memory_context: str = "", volume_context: str = "", on_token=None) -> str:
        logger.info(f"Writing chapter {chapter_number} (streaming)...")
        previous_summary = ""
        prev_idx = chapter_number - 2
        if chapter_number > 1 and len(novel_state.chapters) > prev_idx:
            prev_chapter = novel_state.chapters[prev_idx]
            previous_summary = f"Ch{chapter_number-1} {prev_chapter.title}: {prev_chapter.content[-200:]}"
        foreshadowing_hints = ""
        unresolved = [fs for fs in novel_state.foreshadowing_tracking if fs.status == "unresolved"]
        if unresolved:
            foreshadowing_hints = "\n".join([f"- {fs.seed}" for fs in unresolved[:3]])
        rhythm_guidance = self.rhythm.get_chapter_guidance(chapter_number, novel_state.setting.style_type if novel_state.setting else "fanren")
        style_guide = novel_state.setting.style_description if novel_state.setting else ""
        novel_title_str = novel_state.setting.novel_title if novel_state.setting else "pending"
        chapter_type = self.rhythm.get_chapter_type(chapter_number)
        if chapter_type == ChapterType.GOLDEN_OPENING and chapter_number == 1:
            prompt = format_prompt(GOLDEN_CHAPTER_1_PROMPT, novel_title=novel_title_str, style_guide=style_guide, target_words=target_words)
        elif chapter_type == ChapterType.GOLDEN_OPENING and chapter_number == 2:
            prompt = format_prompt(GOLDEN_CHAPTER_2_PROMPT, novel_title=novel_title_str, style_guide=style_guide, previous_summary=previous_summary, target_words=target_words)
        elif chapter_type == ChapterType.GOLDEN_OPENING and chapter_number == 3:
            prompt = format_prompt(GOLDEN_CHAPTER_3_PROMPT, novel_title=novel_title_str, style_guide=style_guide, previous_summary=previous_summary, target_words=target_words)
        elif chapter_type in (ChapterType.BIG_CLIMAX, ChapterType.SMALL_CLIMAX, ChapterType.VOLUME_CLIMAX):
            prompt = format_prompt(CLIMAX_CHAPTER_PROMPT, novel_title=novel_title_str, style_guide=style_guide, previous_summary=previous_summary, rhythm_guidance=rhythm_guidance, target_words=target_words)
        else:
            setting_str = str(novel_state.setting.dict())[:2000] if novel_state.setting else ""
            prompt = format_prompt(CHAPTER_WRITING_PROMPT, novel_title=novel_title_str, setting_summary=setting_str, style_guide=style_guide, chapter_idx=chapter_number, total_words=novel_state.total_words, target_words=target_words, previous_summary=previous_summary, foreshadowing_hints=foreshadowing_hints, rhythm_guidance=rhythm_guidance, volume_context=volume_context or "（无卷信息）")
        if volume_context:
            prompt = prompt + "\n\n【当前卷信息】\n" + volume_context
        if memory_context:
            prompt = prompt + "\n\n[Dynamic Memory]\n" + memory_context
        if reasoning_context:
            prompt = prompt + "\n" + reasoning_context
        if knowledge_context:
            prompt = prompt + "\n" + knowledge_context
        content = self.llm.generate_stream(prompt, temperature=0.8, on_token=on_token)
        min_words = int(target_words * 0.7)
        chinese_chars = len([c for c in content if ord(c) > 0x4e00])
        if chinese_chars < min_words and len(content) < target_words:
            extend_prompt = f"Continue:\n{content[-300:]}"
            extra = self.llm.generate_stream(extend_prompt, temperature=0.7, on_token=on_token)
            content += extra
        return content

    def generate_title(self, novel_title: str, chapter_event: str, prev_ending: str, style_type: str, chapter_idx: int) -> str:
        prompt = format_prompt(
            CHAPTER_TITLE_PROMPT,
            novel_title=novel_title,
            chapter_event=chapter_event,
            prev_ending=prev_ending,
            style_type=style_type,
            chapter_idx=chapter_idx
        )

        title = self.llm.generate(prompt, temperature=0.3).strip()
        logger.info(f"Generated title for chapter {chapter_idx}: {title}")
        return title


class PolisherAgent:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def polish(self, content: str, style_guide: str) -> str:
        logger.info("Polishing content...")

        prompt = format_prompt(
            POLISH_PROMPT,
            chapter_content=content,
            style_guide=style_guide
        )

        polished = self.llm.generate(prompt, temperature=0.5)
        logger.info(f"Content polished, new length: {len(polished)} chars")
        return polished


class ProofreaderAgent:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def proofread(self, content: str) -> str:
        logger.info("Proofreading content...")

        prompt = format_prompt(
            PROOFREAD_PROMPT,
            chapter_content=content
        )

        proofread = self.llm.generate(prompt, temperature=0.2)
        logger.info(f"Proofreading complete")
        return proofread


class ContinuityChecker:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def check(
        self,
        chapter_idx: int,
        prev_ending: str,
        current_content: str,
        history_plot: str,
        character_states: str
    ) -> Dict[str, Any]:
        prompt = format_prompt(
            CONTINUITY_CHECK_PROMPT,
            chapter_idx=chapter_idx,
            prev_ending=prev_ending,
            current_content=current_content[:1000],
            history_plot=history_plot,
            character_states=character_states
        )

        result = self.llm.generate_json(prompt)
        return result


class NovelWorkflow:
    def __init__(self, config: NovelConfig, stop_event=None):
        self.config = config
        self._stop_event = stop_event  # threading.Event for immediate stop
        self.llm = LLMClient(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            timeout=settings.OLLAMA_TIMEOUT
        )

        self.setting_agent = SettingAgent(self.llm)
        self.writer_agent = WriterAgent(self.llm)
        self.polisher_agent = PolisherAgent(self.llm)
        self.proofreader_agent = ProofreaderAgent(self.llm)
        self.continuity_checker = ContinuityChecker(self.llm)

        self.coherence_verifier = CoherenceVerifier()
        self.genre_enforcer = GenreEnforcer()
        self.repetition_guard = RepetitionGuard()
        self.foreshadowing_mgr = ForeshadowingManager()
        self.style_anchor = get_style_anchor_manager()
        self.deai = get_deai_processor()
        self.rhythm = get_rhythm_controller()
        self.audit = get_audit_pipeline()
        self.card_manager: Optional[CardManager] = None
        self.coherence_mgr = get_coherence_manager()
        self.exporter = get_exporter()
        self.knowledge_integrator = get_knowledge_integrator()
        self.memory_weighter = get_memory_weighter()
        self.reasoning_planner = get_reasoning_planner()
        self.generation_gates = get_generation_gates()
        self.enhanced_audit = get_enhanced_audit()
        self.state_writeback = get_state_writeback()
        self.editor_agent = get_editor_agent()
        self.agent_loop = AgentLoopExecutor(self)
        self.display = get_terminal_display()

        self.state = NovelState()

    def initialize_novel(self) -> NovelState:
        logger.info("Initializing novel...")

        self.state.status = NovelStatus.WRITING
        self.state.setting = self.setting_agent.generate_setting(self.config)
        self.state.current_chapter = 0

        # 初始化卡片系统（创作真相来源）
        if self.state.novel_id and self.state.setting:
            self.card_manager = create_cards_from_setting(self.state.novel_id, self.state.setting)
            logger.info(f"Card system initialized: {len(self.card_manager.characters)} characters")

        coherence = self.coherence_verifier.verify_novel_coherence(self.state)
        if coherence["score"] < 60:
            logger.warning(f"Initial setting coherence score is low: {coherence['score']}")
            for issue in coherence.get("issues", [])[:5]:
                logger.warning(f"  - {issue}")

        genre_check = self.genre_enforcer.enforce_genre(self.state, self.config.style_type)
        if not genre_check["enforced"]:
            logger.warning(f"Genre enforcement warnings: {genre_check['missing_keywords'][:3]}")

        # 种子记忆：将核心设定注册到动态记忆系统
        s = self.state.setting
        self.memory_weighter.add_memory("outline_novel", f"《{s.novel_title}》核心主题：{s.core_conflicts}", "outline", 0.95, WeightTier.CRITICAL)
        self.memory_weighter.add_memory("world_framework", s.world_framework[:300], "world", 0.8, WeightTier.HIGH)
        self.memory_weighter.add_memory("power_system", s.power_system[:300], "world", 0.75, WeightTier.HIGH)
        self.memory_weighter.add_memory("factions", s.major_factions[:200], "world", 0.7, WeightTier.HIGH)
        self.memory_weighter.add_memory("main_plot", s.main_plot_thread[:500], "outline", 0.85, WeightTier.CRITICAL)
        self.memory_weighter.add_memory(f"char_mc", f"主角：{s.main_character.name}，{s.main_character.personality or ''}，{s.main_character.motivation or ''}", "character", 0.9, WeightTier.CRITICAL)
        for i, ant in enumerate(s.antagonists[:3]):
            self.memory_weighter.add_memory(f"char_ant{i}", f"反派：{ant.name}，{ant.role}，{ant.description[:100]}", "character", 0.6, WeightTier.HIGH)
        for i, sup in enumerate(s.supporting_characters[:3]):
            self.memory_weighter.add_memory(f"char_sup{i}", f"配角：{sup.name}，{sup.role}，{sup.personality or ''}", "character", 0.5, WeightTier.MEDIUM)
        for vol in s.volume_threads[:5]:
            self.memory_weighter.add_memory(f"vol_{vol.volume_number}", f"第{vol.volume_number}卷「{vol.title}」：{vol.core_conflict}", "plot", 0.7, WeightTier.HIGH)
        logger.info(f"Seeded {len(self.memory_weighter.memories)} core memories into dynamic weighter")

        # 终端流式展示：小说完整信息
        self.display.show_novel_header(self.state, self.config)

        logger.info(f"Novel initialized: {self.state.setting.novel_title}")
        return self.state

    def write_next_chapter(self, enable_quality_check: bool = True) -> ChapterModel:
        if not self.state.setting:
            raise ValueError("Novel not initialized")

        self.state.current_chapter += 1
        chapter_number = self.state.current_chapter

        logger.info(f"Writing chapter {chapter_number}...")
        setting = self.state.setting
        style_guide = self.style_anchor.get_style_guidance(self.config.style_type)
        if setting:
            setting.style_description = style_guide

        chapter_type = self.rhythm.get_chapter_type(chapter_number)
        # 终端展示：开始写本章
        self.display.show_chapter_start(chapter_number, self.config.estimated_chapters, chapter_type.value)

        # ================================================================
        # Phase 1: 收集上下文
        # ================================================================
        previous_ending = self.state.chapters[-1].content[-300:] if self.state.chapters else ""
        volume_goal = ""
        current_volume_info = ""
        if setting.volume_threads and chapter_number > 0:
            for vol in setting.volume_threads:
                start, end = vol.chapter_range
                if start <= chapter_number <= end:
                    vol_idx = vol.volume_number - 1
                    volume_goal = vol.core_conflict
                    current_volume_info = f"第{vol.volume_number}卷「{vol.title}」({start}-{end}章)"
                    break

        urgent_foreshadowing = [
            fs.seed for fs in self.state.foreshadowing_tracking
            if fs.status == "unresolved" and chapter_number - fs.chapter_introduced > 30
        ]

        # ================================================================
        # T1-1: 动态记忆权重
        # ================================================================
        memory_context = ""
        try:
            # 提取本章活跃角色
            active_chars = []
            if setting.main_character:
                active_chars.append(setting.main_character.name)
            if setting.antagonists and chapter_number % 5 == 0:
                for a in setting.antagonists[:2]:
                    active_chars.append(a.name)

            # 计算记忆权重并构建上下文
            sorted_mem = self.memory_weighter.compute_weights(
                current_chapter=chapter_number,
                active_characters=active_chars,
                volume_goal=volume_goal,
                urgent_foreshadowing=urgent_foreshadowing,
            )
            if sorted_mem:
                memory_context = self.memory_weighter.select_for_prompt(sorted_mem, max_tokens=1500)
        except Exception as e:
            logger.warning(f"Memory weighting skipped: {e}")

        # ================================================================
        # T1-2: 思考-规划 (Phase 1: REASONING)
        # ================================================================
        reasoning_context = ""
        if self.reasoning_planner.should_plan(chapter_number, chapter_type.value):
            try:
                # 构建角色状态摘要
                char_states = self.coherence_mgr.get_all_character_states(chapter_number)

                # 构建伏笔列表
                unresolved = [fs for fs in self.state.foreshadowing_tracking if fs.status == "unresolved"]
                foreshadowing_list = "\n".join(
                    [f"- [{fs.chapter_introduced}章埋] {fs.seed}" for fs in unresolved[:5]]
                ) if unresolved else ""

                rhythm_guidance = self.rhythm.get_chapter_guidance(
                    chapter_number, setting.style_type
                )

                plan = self.reasoning_planner.plan_chapter(
                    llm_generate=self.llm.generate,
                    chapter_number=chapter_number,
                    novel_title=setting.novel_title,
                    total_words=self.state.total_words,
                    style_guide=style_guide,
                    rhythm_guidance=rhythm_guidance,
                    previous_ending=previous_ending,
                    foreshadowing_list=foreshadowing_list,
                    volume_goal=volume_goal,
                    character_states=char_states,
                )
                reasoning_context = plan.to_prompt_context()
            except Exception as e:
                logger.warning(f"Reasoning planner skipped: {e}")

        # ================================================================
        # 联网知识注入（每5章或高潮章节）
        # ================================================================
        knowledge_context = ""
        if chapter_number % 5 == 0 or chapter_type in (
            ChapterType.BIG_CLIMAX, ChapterType.VOLUME_CLIMAX
        ):
            try:
                knowledge_context = self.knowledge_integrator.run_pipeline(
                    llm_generate=self.llm.generate,
                    novel_title=setting.novel_title,
                    world_setting=setting.world_framework,
                    power_system=setting.power_system,
                    chapter_number=chapter_number,
                    total_words=self.state.total_words,
                    last_ending=previous_ending,
                    volume_goal=volume_goal,
                )
            except Exception as e:
                logger.warning(f"Knowledge pipeline skipped: {e}")

        # ================================================================
        # Phase 2: WRITING（注入所有上下文）
        # ================================================================
        # 创建占位章节（前端轮询可立即看到）
        placeholder = ChapterModel(
            chapter_number=chapter_number,
            title="写作中...",
            content="",
            status=ChapterStatus.DRAFT,
            word_count=0
        )
        self.state.chapters.append(placeholder)

        # 终端流式输出
        print(f"\n--- 第{chapter_number}章正文 ---", flush=True)
        content = self.writer_agent.write_chapter_stream(
            self.state,
            chapter_number,
            self.config.chapter_words,
            knowledge_context=knowledge_context,
            reasoning_context=reasoning_context,
            memory_context=memory_context,
            volume_context=current_volume_info,
            on_token=lambda t: print(t, end="", flush=True)
        )
        print()  # 流式结束换行

        # ================================================================
        # T1-3: 生成门禁检查（不通过则自动修正重试）
        # ================================================================
        chapter_passed = False
        fix_attempt = 0
        while fix_attempt <= self.generation_gates.max_fix_retries:
            report = self.generation_gates.check_all(
                content=content,
                chapter_number=chapter_number,
                target_words=self.config.chapter_words,
                previous_content=self.state.chapters[-1].content if self.state.chapters else "",
                style_type=setting.style_type,
            )

            if report.passed:
                if report.overall == GateResult.WARN:
                    logger.info(f"Chapter {chapter_number} passed gates with warnings (avg={report.total_score:.0f})")
                else:
                    logger.info(f"Chapter {chapter_number} passed all gates (avg={report.total_score:.0f})")
                chapter_passed = True
                break
            else:
                logger.warning(f"Chapter {chapter_number} FAILED gates, fix attempt {fix_attempt + 1}")
                # 终端展示：门禁拒绝
                fail_reasons = [g.reason for g in report.gates if g.result.value == 'fail']
                self.display.show_chapter_rejected(chapter_number, "; ".join(fail_reasons[:2]))
                fix_prompt = self.generation_gates.build_fix_prompt(
                    content, report.get_fix_instructions(), self.config.chapter_words
                )
                try:
                    content = self.llm.generate(fix_prompt, temperature=0.7)
                    fix_attempt += 1
                    # 重新检查修正后的质量
                    recheck = self.generation_gates.check_all(
                        content=content, chapter_number=chapter_number,
                        target_words=self.config.chapter_words,
                    )
                    self.display.show_chapter_fixed(chapter_number, recheck.total_score)
                except Exception as e:
                    logger.error(f"Gate fix generation failed: {e}")
                    break

        if not chapter_passed:
            logger.warning(f"Chapter {chapter_number} accepted with gate failures after {fix_attempt} fix attempts")

        # ================================================================
        # 补充质量检查（轻量级，不阻塞）
        # ================================================================
        if enable_quality_check and content:
            rep_check = self.repetition_guard.check_repetition(
                content,
                self.state.chapters[-1].content if self.state.chapters else ""
            )
            if not rep_check["passed"]:
                logger.warning(f"Repetition issues in chapter {chapter_number}: {rep_check['issues']}")

            genre_chapter_check = self.genre_enforcer.validate_chapter_genre_consistency(
                content, setting
            )
            if not genre_chapter_check["consistent"]:
                logger.warning(f"Genre drift in chapter {chapter_number}: {genre_chapter_check['issues']}")

            ai_check = self.deai.detect_ai_traces(content)
            if ai_check["ai_score"] > 60:
                logger.warning(f"High AI traces in ch{chapter_number}, cleaning...")
                content = self.deai.clean_ai_traces(content)

        # ================================================================
        # 生成标题
        # ================================================================
        title = self.writer_agent.generate_title(
            setting.novel_title,
            content[:200],
            self.state.chapters[-2].content[-200:] if len(self.state.chapters) > 1 else "",
            setting.style_type,
            chapter_number
        )

        # 中断检查：如果在 LLM 生成期间收到停止信号，丢弃本章
        if self._stop_event and self._stop_event.is_set():
            logger.info(f"Chapter {chapter_number} aborted by stop signal")
            self.state.current_chapter -= 1  # 回退章节计数
            return None

        # 更新占位章节为最终状态
        chapter = self.state.chapters[-1]
        chapter.title = title
        chapter.status = ChapterStatus.WRITTEN
        chapter.content = content
        chapter.word_count = len(content)
        self.state.total_words += chapter.word_count

        # 更新记忆权重：标记本章引用了哪些记忆
        for mem_key in self.memory_weighter.memories:
            if any(kw in content for kw in mem_key.split("_")):
                self.memory_weighter.mark_referenced(mem_key, chapter_number)

        # 长篇连贯性：自动摘要 + 状态追踪
        summary = self.coherence_mgr.auto_summarize_chapter(chapter, self.llm)
        self.coherence_mgr.add_chapter_summary(chapter_number, summary)
        self.coherence_mgr.add_plot_event(chapter_number, f"第{chapter_number}章：{chapter.title}")

        if setting.main_character:
            mc_name = setting.main_character.name
            locations = ["宗门", "山谷", "城中", "洞府", "山巅", "秘境", "宫殿", "战场", "森林", "荒漠", "坊市", "遗迹"]
            found_loc = [loc for loc in locations if loc in content]
            state_desc = f"位置：{found_loc[0] if found_loc else '未知'}"
            self.coherence_mgr.update_character(mc_name, chapter_number, state_desc)

        if chapter_number % 5 == 0 and setting:
            try:
                self.foreshadowing_mgr.create_foreshadowing(
                    self.state,
                    seed=f"第{chapter_number}章暗示: {content[:100]}...",
                    chapter_introduced=chapter_number,
                    description=f"第{chapter_number}章自动生成的伏笔"
                )
            except ValueError:
                pass

        # 增强审计：每10章或门禁低分时触发LLM深度审计
        if chapter_number % 10 == 0 or chapter.quality_score < 70:
            try:
                audit_report = self.enhanced_audit.audit(
                    llm_generate=self.llm.generate,
                    chapter=chapter,
                    novel_state=self.state,
                    previous_content=self.state.chapters[-2].content if len(self.state.chapters) > 1 else "",
                    target_words=self.config.chapter_words,
                    run_deep=(chapter_number % 10 == 0),
                )
                chapter.quality_score = audit_report.overall_score
                chapter.gate_report = {
                    "overall": audit_report.gate_report.overall.value if audit_report.gate_report else "unknown",
                    "score": audit_report.overall_score,
                    "suggestions": audit_report.suggestions[:3],
                }
            except Exception as e:
                logger.warning(f"Enhanced audit skipped: {e}")

        # 状态回写 + 上下文压缩（T2管线）
        if chapter_number % 5 == 0:
            try:
                wb_result = self.state_writeback.run_pipeline(
                    llm_generate=self.llm.generate,
                    chapter=chapter,
                    novel_state=self.state,
                    compress=(chapter_number % 10 == 0),
                )
                logger.info(
                    f"T2 pipeline: {len(wb_result['changes'])} state changes, "
                    f"compressed={wb_result['compressed'] is not None}"
                )
            except Exception as e:
                logger.warning(f"State writeback skipped: {e}")

        # 终端展示：本章完成
        self.display.show_chapter_done(
            chapter_number=chapter.chapter_number,
            title=chapter.title,
            word_count=chapter.word_count,
            quality_score=chapter.quality_score,
            total_words=self.state.total_words,
            target_words=self.config.max_words,
        )

        # 实时保存章节到 novel_output/{小说名}/ 目录
        self.display.save_chapter(chapter.chapter_number, chapter.title, chapter.content, chapter.word_count)

        return chapter

    def write_chapter_with_agent_loop(self) -> ChapterModel:
        """Agent Loop 模式 — 主编动态调度整个章节创作流程

        相比固定流程 write_next_chapter，Agent Loop 会：
        - 动态决定是否需要润色/校对/修正
        - 质量不达标时自动迭代优化
        - 追踪决策历史
        """
        if not self.state.setting:
            raise ValueError("Novel not initialized")

        self.state.current_chapter += 1
        chapter_number = self.state.current_chapter

        logger.info(f"Agent Loop: starting chapter {chapter_number}...")

        # 中断检查
        if self._stop_event and self._stop_event.is_set():
            logger.info(f"Agent Loop chapter {chapter_number} aborted by stop signal")
            self.state.current_chapter -= 1
            return None

        # 先用标准流程写出初稿
        chapter = self.write_next_chapter(enable_quality_check=True)
        if chapter is None:
            return None  # 被中断

        # Agent Loop 动态优化
        loop_result = self.agent_loop.run_chapter_loop(chapter_number)

        # 更新章节的质量评分
        chapter.quality_score = loop_result.final_quality

        logger.info(
            f"Agent Loop ch{chapter_number} done: "
            f"quality={loop_result.final_quality:.0f}, "
            f"iterations={loop_result.iterations}, "
            f"efficiency={loop_result.efficiency_ratio:.2f}"
        )

        return chapter

    def polish_chapter(self, chapter_number: int) -> ChapterModel:
        chapter = self.state.chapters[chapter_number - 1]
        logger.info(f"Polishing chapter {chapter_number}...")

        polished_content = self.polisher_agent.polish(
            chapter.content,
            self.state.setting.style_description if self.state.setting else ""
        )

        chapter.content = polished_content
        chapter.status = ChapterStatus.POLISHED
        chapter.word_count = len(polished_content)

        return chapter

    def proofread_chapter(self, chapter_number: int) -> ChapterModel:
        chapter = self.state.chapters[chapter_number - 1]
        logger.info(f"Proofreading chapter {chapter_number}...")

        proofed_content = self.proofreader_agent.proofread(chapter.content)

        chapter.content = proofed_content
        chapter.status = ChapterStatus.PROOFREAD

        return chapter

    def run(self):
        logger.info(f"Starting novel workflow: {self.config.novel_theme}")
        logger.info(f"Target: {self.config.max_words // 10000}万字, {self.config.estimated_chapters}章")
        logger.info(f"LLM: {settings.OLLAMA_MODEL} @ {settings.OLLAMA_BASE_URL}")

        self.initialize_novel()

        while self.state.total_words < self.config.max_words:
            if self._stop_event and self._stop_event.is_set():
                logger.info("Writing stopped by user")
                self.state.status = NovelStatus.ABANDONED
                return self.state
            chapter = self.write_chapter_with_agent_loop()
            if chapter is None:
                self.state.status = NovelStatus.ABANDONED
                return self.state

            if self.state.current_chapter % 3 == 0:
                chapter = self.polish_chapter(chapter.chapter_number)
                chapter = self.proofread_chapter(chapter.chapter_number)
                # 润色校对后重新保存
                self.display.save_chapter(chapter.chapter_number, chapter.title, chapter.content, chapter.word_count)

            if self.state.current_chapter % 5 == 0:
                continuity_result = self.continuity_checker.check(
                    chapter_idx=chapter.chapter_number,
                    prev_ending=self.state.chapters[-2].content[-300:] if len(self.state.chapters) > 1 else "",
                    current_content=chapter.content,
                    history_plot=self.state.setting.main_plot_thread if self.state.setting else "",
                    character_states=str(self.state.setting.main_character.dict()) if self.state.setting and self.state.setting.main_character else ""
                )
                if continuity_result.get("score", 100) < 60:
                    logger.warning(f"Continuity check low score for ch{chapter.chapter_number}: {continuity_result.get('score')}")
                    for issue in continuity_result.get("issues", [])[:3]:
                        logger.warning(f"  - {issue}")

            if self.state.current_chapter % 10 == 0:
                coherence = self.coherence_verifier.verify_novel_coherence(self.state)
                logger.info(f"Coherence check at ch{chapter.chapter_number}: score={coherence['score']:.1f}")
                foreshadowing_status = self.foreshadowing_mgr.get_foreshadowing_summary(self.state)
                rate = foreshadowing_status.get("resolution_rate", 0)
                logger.info(f"Foreshadowing: {foreshadowing_status['resolved']}/{foreshadowing_status['total_foreshadowing']} resolved ({rate:.0%})")

                # 多维度审计（每10章）
                if chapter.status in (ChapterStatus.POLISHED, ChapterStatus.PROOFREAD, ChapterStatus.WRITTEN):
                    audit_result = self.audit.audit_chapter(chapter, self.state)
                    logger.info(
                        f"Audit ch{chapter.chapter_number}: score={audit_result['overall_score']:.0f} "
                        f"({audit_result['passed_count']}/{audit_result['total_dimensions']} passed)"
                    )
                    for dim in audit_result["dimensions"]:
                        if not dim["passed"] and dim["score"] < 50:
                            logger.warning(f"  Audit [{dim['dimension']}]: {dim['issues'][:2]}")

            # 每10章展示进度总结
            if self.state.current_chapter % 10 == 0:
                self.display.show_progress_summary(self.state, self.config)

            logger.info(
                f"Progress: {self.state.current_chapter}/{self.config.estimated_chapters} chapters, "
                f"{self.state.total_words}/{self.config.max_words} words"
            )

        self.state.status = NovelStatus.COMPLETED
        logger.info(f"Novel completed: {self.state.total_words} words total")

        # 自动导出
        export_path = ""
        try:
            target = str(self.display.novel_dir) if self.display.novel_dir else ""
            export_path = self.exporter.export_all(self.state, target_dir=target)
            logger.info(f"Novel exported to: {export_path}")
        except Exception as e:
            logger.error(f"Export failed: {e}")

        # 终端展示：小说完成
        self.display.show_novel_complete(self.state, export_path)

        # 连贯性总览
        coh_summary = self.coherence_mgr.get_global_summary()
        logger.info(f"Coherence: {coh_summary}")

        return self.state
