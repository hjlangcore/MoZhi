"""卡片系统 — 借鉴 WenShape (文枢) 的卡片设计，作为创作的唯一事实来源

包含三种核心卡片：
1. 角色卡 (CharacterCard) — 姓名/外观/性格/动机/关系网/当前状态
2. 世界卡 (WorldCard) — 地理/势力/境界体系/历史事件/当前局势
3. 文风卡 (StyleCard) — 语调/句式/禁用词/节奏偏好
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from loguru import logger


# ============================================================
# 角色卡
# ============================================================
class CharacterState(BaseModel):
    """角色当前状态 — 会随剧情推进而变化"""
    current_location: str = ""
    current_realm: str = ""             # 当前境界
    current_health: str = "正常"
    current_goal: str = ""              # 当前目标
    known_secrets: List[str] = Field(default_factory=list)
    active_relationships: Dict[str, str] = Field(default_factory=dict)  # 角色名 → 关系状态


class CharacterCard(BaseModel):
    """角色卡 — 创作时的唯一角色事实来源"""
    card_id: str
    name: str
    role: str                          # 主角/配角/反派/路人
    archetype: str = ""                # 角色原型简述
    appearance: str = ""               # 外貌描述
    personality: str = ""              # 性格
    background: str = ""               # 背景故事
    motivation: str = ""               # 核心动机
    weakness: str = ""                 # 弱点/缺陷
    growth_arc: str = ""               # 成长弧线
    signature_phrases: List[str] = Field(default_factory=list)  # 口头禅
    forbidden_actions: List[str] = Field(default_factory=list)  # 不能做的事（防OOC）
    power_abilities: List[str] = Field(default_factory=list)    # 能力列表
    state: CharacterState = Field(default_factory=CharacterState)
    updated_at: datetime = Field(default_factory=datetime.now)

    def update_state(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self.state, key):
                setattr(self.state, key, value)
        self.updated_at = datetime.now()

    def get_context_prompt(self) -> str:
        """生成给LLM的角色上下文提示"""
        lines = [
            f"【{self.name}】{self.role} | 原型：{self.archetype}",
            f"外貌：{self.appearance}",
            f"性格：{self.personality}",
            f"动机：{self.motivation}",
            f"弱点：{self.weakness}",
            f"当前境界：{self.state.current_realm}",
            f"当前位置：{self.state.current_location}",
            f"当前目标：{self.state.current_goal}",
        ]
        if self.signature_phrases:
            lines.append(f"口头禅：{'、'.join(self.signature_phrases)}")
        if self.forbidden_actions:
            lines.append(f"⚠️ 不能做的事：{'、'.join(self.forbidden_actions)}")
        return "\n".join(lines)


# ============================================================
# 世界卡
# ============================================================
class WorldState(BaseModel):
    """世界当前局势"""
    active_conflicts: List[str] = Field(default_factory=list)
    major_events: List[str] = Field(default_factory=list)
    power_balance: str = ""            # 势力平衡状态
    timeline_position: str = ""        # 当前时间线位置


class WorldCard(BaseModel):
    """世界卡 — 创作时的唯一世界观事实来源"""
    card_id: str
    world_name: str = ""
    geography: str = ""                # 地理概况
    factions: Dict[str, str] = Field(default_factory=dict)  # 势力名 → 简介
    power_system: str = ""             # 修炼/力量体系
    realms: List[str] = Field(default_factory=list)  # 境界列表
    history: str = ""                  # 历史背景
    rules: List[str] = Field(default_factory=list)   # 世界规则（不能违反的铁律）
    state: WorldState = Field(default_factory=WorldState)
    updated_at: datetime = Field(default_factory=datetime.now)

    def update_state(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self.state, key):
                setattr(self.state, key, value)
        self.updated_at = datetime.now()

    def get_context_prompt(self) -> str:
        lines = [
            f"【世界观】{self.world_name}",
            f"地理：{self.geography}",
            f"修炼体系：{self.power_system}",
            f"境界划分：{' → '.join(self.realms) if self.realms else '未设定'}",
            f"势力分布：",
        ]
        for name, desc in self.factions.items():
            lines.append(f"  - {name}：{desc}")
        if self.rules:
            lines.append(f"⚠️ 铁律：{'；'.join(self.rules)}")
        if self.state.active_conflicts:
            lines.append(f"当前冲突：{'、'.join(self.state.active_conflicts)}")
        return "\n".join(lines)


# ============================================================
# 文风卡
# ============================================================
class StyleCard(BaseModel):
    """文风卡 — 创作时的唯一风格事实来源"""
    card_id: str
    style_name: str                    # 凡人流/热血/隐忍/宏大
    tone: str = ""                     # 整体基调
    sentence_preference: str = ""      # 句式偏好（短句/长句/混合）
    narrative_distance: str = "close"  # 叙事距离：close(贴身)/mid(中等)/far(远观)
    forbidden_words: List[str] = Field(default_factory=list)  # 禁用词
    preferred_words: List[str] = Field(default_factory=list)  # 推荐词
    dialogue_style: str = ""           # 对话风格
    chapter_opening_style: str = ""    # 章节开头风格
    chapter_ending_style: str = ""     # 章节结尾风格
    updated_at: datetime = Field(default_factory=datetime.now)

    def get_context_prompt(self) -> str:
        lines = [
            f"【文风要求】{self.style_name}",
            f"基调：{self.tone}",
            f"句式：{self.sentence_preference}",
            f"叙事距离：{self.narrative_distance}",
            f"对话风格：{self.dialogue_style}",
            f"章节开头：{self.chapter_opening_style}",
            f"章节结尾：{self.chapter_ending_style}",
        ]
        if self.forbidden_words:
            lines.append(f"❌ 禁用词：{'、'.join(self.forbidden_words)}")
        if self.preferred_words:
            lines.append(f"✅ 推荐词：{'、'.join(self.preferred_words)}")
        return "\n".join(lines)


# ============================================================
# 卡片管理器
# ============================================================
class CardManager:
    """统一管理所有卡片，作为创作的唯一真相来源 (Single Source of Truth)"""

    def __init__(self, novel_id: str):
        self.novel_id = novel_id
        self.characters: Dict[str, CharacterCard] = {}
        self.world_card: Optional[WorldCard] = None
        self.style_card: Optional[StyleCard] = None

    # ---- 角色卡管理 ----
    def add_character(self, card: CharacterCard):
        self.characters[card.card_id] = card
        logger.info(f"Character card added: {card.name} ({card.role})")

    def get_character(self, card_id: str) -> Optional[CharacterCard]:
        return self.characters.get(card_id)

    def get_main_character(self) -> Optional[CharacterCard]:
        for c in self.characters.values():
            if c.role == "主角":
                return c
        return None

    def get_character_by_name(self, name: str) -> Optional[CharacterCard]:
        for c in self.characters.values():
            if c.name == name:
                return c
        return None

    def update_character_state(self, card_id: str, **kwargs):
        card = self.characters.get(card_id)
        if card:
            card.update_state(**kwargs)

    def get_all_character_context(self) -> str:
        if not self.characters:
            return "暂无角色设定"
        return "\n\n".join(c.get_context_prompt() for c in self.characters.values())

    # ---- 世界卡管理 ----
    def set_world_card(self, card: WorldCard):
        self.world_card = card
        logger.info(f"World card set: {card.world_name}")

    def get_world_context(self) -> str:
        if not self.world_card:
            return "暂无世界观设定"
        return self.world_card.get_context_prompt()

    # ---- 文风卡管理 ----
    def set_style_card(self, card: StyleCard):
        self.style_card = card
        logger.info(f"Style card set: {card.style_name}")

    def get_style_context(self) -> str:
        if not self.style_card:
            return "暂无文风设定"
        return self.style_card.get_context_prompt()

    # ---- 完整上下文 ----
    def get_full_context_prompt(self) -> str:
        """生成给LLM的完整创作上下文"""
        parts = []
        parts.append(self.get_world_context())
        parts.append(self.get_style_context())
        parts.append(self.get_all_character_context())
        return "\n\n---\n\n".join(parts)

    # ---- OOC检查 ----
    def check_ooc(self, character_name: str, action_description: str) -> Dict[str, Any]:
        """检查角色行为是否符合卡片设定（OOC检测）"""
        card = self.get_character_by_name(character_name)
        if not card:
            return {"ooc": False, "reason": "角色卡不存在，无法检查"}

        issues = []
        for forbidden in card.forbidden_actions:
            if forbidden in action_description:
                issues.append(f"OOC：{character_name}做了禁止行为「{forbidden}」")

        return {
            "ooc": len(issues) > 0,
            "issues": issues,
            "character": character_name
        }


# ============================================================
# 卡片工厂 — 从NovelSettingModel生成卡片
# ============================================================
def create_cards_from_setting(novel_id: str, setting) -> CardManager:
    """从已有的NovelSettingModel生成卡片系统"""
    manager = CardManager(novel_id)

    # 主角卡
    if setting.main_character:
        mc = setting.main_character
        manager.add_character(CharacterCard(
            card_id=f"{novel_id}_main",
            name=mc.name,
            role="主角",
            archetype=setting.main_character.description[:20] if setting.main_character and setting.main_character.description else "",
            personality=mc.personality or "",
            background=mc.background or "",
            motivation=mc.motivation or "",
            state=CharacterState(current_goal="活下去，变强")
        ))

    # 配角卡
    for char in setting.supporting_characters:
        manager.add_character(CharacterCard(
            card_id=f"{novel_id}_{char.name}",
            name=char.name,
            role=char.role or "配角",
            personality=char.personality or "",
            background=char.background or "",
            motivation=char.motivation or "",
            state=CharacterState()
        ))

    # 反派卡
    for char in setting.antagonists:
        manager.add_character(CharacterCard(
            card_id=f"{novel_id}_{char.name}",
            name=char.name,
            role="反派",
            personality=char.personality or "",
            background=char.background or "",
            motivation=char.motivation or "",
            state=CharacterState()
        ))

    # 世界卡
    manager.set_world_card(WorldCard(
        card_id=f"{novel_id}_world",
        world_name=setting.novel_title,
        geography=setting.world_framework,
        power_system=setting.power_system,
        factions={f.strip(): "" for f in setting.major_factions.split("、") if f.strip()},
        history="",
        rules=["修炼体系内部逻辑自洽", "境界提升须有代价和铺垫"]
    ))

    # 文风卡
    style_presets = {
        "凡人流": StyleCard(
            card_id=f"{novel_id}_style", style_name="凡人流",
            tone="沉稳内敛，以细节打动人",
            sentence_preference="长短句交错，紧张用短句", narrative_distance="close",
            dialogue_style="简洁有力，一语中的",
            chapter_opening_style="场景切入，不铺垫", chapter_ending_style="悬念钩子或余韵",
            forbidden_words=["现代网络用语", "英文缩写"],
            preferred_words=["修炼术语", "古风词汇"]
        ),
        "热血": StyleCard(
            card_id=f"{novel_id}_style", style_name="热血",
            tone="激情澎湃，燃点密集", sentence_preference="短句为主，节奏急促",
            narrative_distance="mid", dialogue_style="热血宣言，简短有力",
            chapter_opening_style="战斗切入或冲突开场",
            chapter_ending_style="高潮悬念或战力展示",
            forbidden_words=["消极词汇", "冗长心理描写"],
            preferred_words=["战斗描写", "气势恢宏的形容词"]
        ),
    }
    style_type = setting.style_type if setting.style_type else "凡人流"
    manager.set_style_card(style_presets.get(style_type, style_presets["凡人流"]))

    return manager


_card_managers: Dict[str, CardManager] = {}


def get_card_manager(novel_id: str) -> CardManager:
    if novel_id not in _card_managers:
        _card_managers[novel_id] = CardManager(novel_id)
    return _card_managers[novel_id]
