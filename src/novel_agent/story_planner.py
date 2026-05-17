"""故事规划器 — 原创角色体系 + 50万字结构 + 结局大纲"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from loguru import logger


class CharacterProfile(BaseModel):
    """完整角色档案 — 原创命名，避免套路化"""
    name: str = ""
    name_meaning: str = ""                  # 名字寓意
    role: str = ""                          # 核心主角/核心配角/辅助角色/背景角色
    archetype: str = ""                     # 原型简述
    age: str = ""
    appearance: str = ""                    # 外貌特征
    personality: str = ""                   # 性格（核心+表面+隐藏）
    background: str = ""                    # 出身背景故事
    motivation: str = ""                    # 核心动机/执念
    weakness: str = ""                      # 致命弱点
    growth_arc: str = ""                    # 成长弧线（50万字内如何变化）
    power_start: str = ""                   # 出场实力
    power_peak: str = ""                    # 巅峰实力（50万字结尾时）
    signature_skills: List[str] = Field(default_factory=list)
    signature_quote: str = ""               # 口头禅/标志台词
    relationships: Dict[str, str] = Field(default_factory=dict)
    fate_50w: str = ""                      # 50万字时的结局


class VolumePlan(BaseModel):
    """分卷规划 — 50万字拆为5卷，每卷10万字"""
    volume_number: int
    title: str
    word_range: str                         # e.g. "1-50章, 10万字"
    main_goal: str                          # 本卷目标
    antagonist: str                         # 本卷反派
    key_events: List[str] = Field(default_factory=list)
    foreshadowing_planted: List[str] = Field(default_factory=list)
    foreshadowing_resolved: List[str] = Field(default_factory=list)
    climax: str = ""                        # 本卷高潮
    ending_hook: str = ""                   # 卷末钩子


class StoryPlan(BaseModel):
    """完整故事规划

    50万字小说角色数量建议：
    - 核心主角：1-3人（贯穿全书，完整弧线）
    - 核心配角：5-8人（每部有独立故事线）
    - 辅助角色：20-30人（服务于特定情节）
    - 背景角色：50+（一笔带过或群体描写）
    """
    novel_title: str = ""
    core_theme: str = ""                    # 核心主题（一句话）

    # 人物体系
    characters: List[CharacterProfile] = Field(default_factory=list)

    # 世界观
    world_setting: str = ""
    power_system: str = ""
    realm_ladder: List[str] = Field(default_factory=list)

    # 50万字结构（5卷 × 10万字）
    volumes: List[VolumePlan] = Field(default_factory=list)

    # 结局规划
    ending_type: str = ""                   # 飞升/归隐/牺牲/系列化
    ending_summary: str = ""
    final_chapter_tone: str = ""
    sequel_hook: str = ""                   # 续集钩子（可选）

    created_at: datetime = Field(default_factory=datetime.now)


# 角色数量指南（嵌入 prompt 使用）
CHARACTER_COUNT_GUIDE = """
【角色数量配置 — 50万字小说】
┌────────────┬──────────┬──────────────────────────────┐
│ 角色类型   │ 数量     │ 说明                         │
├────────────┼──────────┼──────────────────────────────┤
│ 核心主角   │ 1-3人    │ 贯穿全书，完整成长弧线       │
│ 核心配角   │ 5-8人    │ 每个有独立故事线，与主角紧密 │
│ 辅助角色   │ 20-30人  │ 服务于特定情节，阶段性出场   │
│ 背景角色   │ 50+      │ 一笔带过或群体描写           │
└────────────┴──────────┴──────────────────────────────┘
"""


# 50万字分卷模板
VOLUME_TEMPLATE_50W = [
    {
        "volume_number": 1,
        "title": "觉醒启程卷",
        "word_range": "1-50章, 约10万字",
        "main_goal": "主角从平凡中觉醒，获得独特能力或机遇，迈出改变命运的第一步",
        "antagonist": "初期对立势力/竞争对手",
        "key_events": [
            "第1-3章：开场建立主角处境与核心冲突，引发读者共鸣",
            "第4-10章：转折事件发生，主角获得契机",
            "第11-20章：初步展现实力提升，建立自信",
            "第21-30章：结识第一个重要盟友或引路人",
            "第31-40章：卷入更大的事件，世界观逐步展开",
            "第41-50章：卷末高潮，完成第一次重大挑战，获得进入更广阔世界的资格"
        ],
        "ending_hook": "主角离开原点/进入新环境，更大的世界和未知的挑战在前面等待"
    },
    {
        "volume_number": 2,
        "title": "立足扎根卷",
        "word_range": "51-100章, 约10万字",
        "main_goal": "在新环境中站稳脚跟，实力稳步提升，建立自己的关系网络",
        "antagonist": "新环境中的敌对势力/利益冲突者",
        "key_events": [
            "第51-60章：进入新环境，面临质疑与考验",
            "第61-70章：通过关键事件证明自己，获得认可",
            "第71-80章：获得重要机缘或传承，实力大幅提升",
            "第81-90章：发现更大格局的线索",
            "第91-100章：卷末之战，击败当前主要对手，地位稳固"
        ],
        "ending_hook": "揭露隐藏的真相或更深的势力版图，故事进入更深层次"
    },
    {
        "volume_number": 3,
        "title": "风云际会卷",
        "word_range": "101-150章, 约10万字",
        "main_goal": "参与更大范围的博弈，面对真正的强敌，建立声望",
        "antagonist": "区域级强敌/势力首领",
        "key_events": [
            "第101-110章：卷入更大格局的冲突，各方势力登场",
            "第111-120章：首次面对强敌，遭遇挫折但未被打倒",
            "第121-130章：卧薪尝胆，获得突破性机缘",
            "第131-140章：卷土重来，首次正面击败强敌",
            "第141-150章：发现强敌背后的更大阴影，前期伏笔开始回收"
        ],
        "ending_hook": "真正的威胁逐渐浮现，危机即将降临"
    },
    {
        "volume_number": 4,
        "title": "生死考验卷",
        "word_range": "151-200章, 约10万字",
        "main_goal": "面对最大威胁，集结力量，经历生死考验",
        "antagonist": "最终反派/最大威胁",
        "key_events": [
            "第151-160章：最大威胁正式登场，展示碾压级实力",
            "第161-170章：主角集结力量，寻找破局之法",
            "第171-180章：关键战役，重要角色可能面临牺牲",
            "第181-190章：主角突破至最强状态",
            "第191-200章：与最大反派的决战（首轮），胜利但付出代价"
        ],
        "ending_hook": "击败强敌后，发现真正的根源还未解决，或隐藏的真相浮出水面"
    },
    {
        "volume_number": 5,
        "title": "收官收束卷",
        "word_range": "201-250章, 约10万字",
        "main_goal": "收束所有伏笔与线索，角色命运交代，主角做出最终选择",
        "antagonist": "幕后根源/内心考验/命运之力",
        "key_events": [
            "第201-210章：回收之前埋下的所有伏笔",
            "第211-220章：各角色命运交代，关系线收束",
            "第221-230章：主角面对最终选择",
            "第231-240章：最后一战/最后考验",
            "第241-250章：结局章，完成所有人物命运交代，全书收束"
        ],
        "climax": "主角完成蜕变，做出最终选择，所有线索在此收束",
        "ending_hook": "可选：留下微小的暗示指向更广阔的世界（但不影响本作完整性）"
    },
]


def get_story_planner_prompt(theme: str, style: str, total_words: int) -> str:
    """生成故事规划Prompt"""
    chapters = total_words // 2200
    return f"""你是一位资深的原创小说架构师。请为以下小说制定完整的故事规划。

【核心原则】
- 角色命名必须原创，严禁使用任何知名网文角色名（如叶凡、萧炎、韩立、林动、石昊、方平、
  宁缺、陈平安、秦牧、许七安、苏凛夜、顾清寒、龙傲天、阎无道、药老 等）
- 名字应与角色性格、出身、命运相关，有独特寓意，而非套用流行格式
- 避免"废柴逆袭""退婚流""系统流"等高度套路化的设定
- 世界观和修炼体系要有自己的创意，不要照搬现有作品的设定

{CHARACTER_COUNT_GUIDE}

【小说主题】{theme}
【文风类型】{style}
【总字数】{total_words}字（约{chapters}章）

请严格按照以下JSON格式输出（确保JSON有效）：

{{
    "novel_title": "2-10字原创小说标题，避免常见网文标题格式",
    "core_theme": "核心主题（一句话概括{total_words}字要讲什么）",

    "characters": [
        {{
            "name": "主角名（原创命名，2-3字，与角色性格/命运相关，有独特寓意）",
            "name_meaning": "名字寓意",
            "role": "核心主角",
            "archetype": "角色原型简述",
            "age": "年龄段",
            "appearance": "外貌描述（50字）",
            "personality": "性格：核心特质/表面表现/隐藏面（80字）",
            "background": "出身背景故事（100字）",
            "motivation": "核心执念/目标（50字）",
            "weakness": "致命弱点/缺陷",
            "growth_arc": "{total_words}字成长弧线（从什么变成什么）",
            "power_start": "出场实力",
            "power_peak": "{total_words}字结尾实力",
            "signature_skills": ["绝招1", "绝招2", "绝招3"],
            "signature_quote": "标志性台词",
            "fate_50w": "{total_words}字时结局"
        }},
        {{
            "name": "核心主角2（或核心配角，如有的话）",
            "role": "核心主角/核心配角",
            "personality": "性格（80字）",
            "background": "背景（80字）",
            "fate_50w": "结局"
        }},
        {{
            "name": "核心配角1（引路人/导师型角色，原创命名）",
            "role": "核心配角",
            "personality": "性格（60字）",
            "relationship": "与主角的关系",
            "fate_50w": "结局"
        }},
        {{
            "name": "核心配角2（盟友/伙伴型角色，原创命名）",
            "role": "核心配角",
            "personality": "性格（60字）",
            "fate_50w": "结局"
        }},
        {{
            "name": "核心配角3（盟友/伙伴型角色，原创命名）",
            "role": "核心配角",
            "personality": "性格（60字）",
            "fate_50w": "结局"
        }},
        {{
            "name": "核心配角4（主要对立面，原创命名，非套路化绰号）",
            "role": "核心配角（对立）",
            "personality": "性格/动机（80字，要有深度，不是单纯的恶）",
            "fate_50w": "结局"
        }},
        {{
            "name": "核心配角5（核心对立面/最终对手，原创命名）",
            "role": "核心配角（对立）",
            "personality": "性格/动机（80字，有说服力的反派动机）",
            "fate_50w": "最终结局"
        }}
    ],

    "power_system": "修炼体系/能力体系（100字，要有原创性，不照搬金丹元婴等常见体系）",
    "realm_ladder": ["境界1", "境界2", "境界3", "境界4", "境界5", "境界6", "境界7"],

    "world_setting": "世界观（100字，有独特设定，不套用模板）",

    "ending_type": "结局类型",
    "ending_summary": "最后一卷如何收束（150字，包含所有人物命运）",
    "final_chapter_tone": "最后一章的基调",
    "sequel_hook": "续集钩子（可选，如留了续集暗示就写，否则写无）"
}}

只输出JSON，不要任何其他文本。角色命名必须原创独特，严禁使用知名网文角色名。"""
