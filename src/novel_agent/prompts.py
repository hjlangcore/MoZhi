SETTING_GENERATION_PROMPT = """
你是一位资深的玄幻小说世界观架构师。请根据用户提供的主题，构建一个完整、严谨且富有想象力的小说设定框架。

主题要求：
{theme}

请按照以下结构输出JSON格式的设定文档：

{{
    "novel_title": "小说标题（必须2-10字）",
    "world_framework": "世界观框架描述（200-500字），包括世界的起源、地理环境、历史背景等",
    "power_system": "修炼体系描述（200-500字），包括境界划分、力量来源、修炼方式等",
    "major_factions": "主要势力介绍（200-500字），包括各大宗门、家族、帝国等",
    "main_character": "主角设定（200-500字），包括出身、性格、天赋、目标等",
    "supporting_characters": [
        {{"name": "角色名", "role": "角色定位", "description": "角色描述"}}
    ],
    "antagonists": [
        {{"name": "反派名", "role": "反派定位", "description": "反派描述"}}
    ],
    "main_plot_thread": "主线剧情概述（200-500字）",
    "core_conflicts": "核心冲突描述（100-300字）",
    "full_document": "完整设定文档（1000-2000字，包含上述所有内容的详细版）"
}}

注意事项：
1. 必须使用中文
2. 设定要符合玄幻修仙题材
3. 境界名称要符合传统玄幻设定（如练气、筑基、金丹等）
4. 输出必须是有效的JSON格式
"""

FRAMEWORK_GENERATION_PROMPT = """
你是一位资深的玄幻小说世界观架构师。请根据用户提供的主题，构建一个完整的小说设定框架。

## 核心要求
- 小说主题：{novel_theme}
- 预计字数：{max_words_wan}万字
- 文风类型：{style_type}
- 文风描述：{style_description}

## 输出格式（严格JSON，不要任何额外文本）

{{
    "novel_title": "2-10字小说标题",
    "world_framework": "200-400字世界观描述",
    "power_system": "100-200字修炼境界体系",
    "major_factions": "100-200字主要势力介绍",
    "main_character_name": "主角姓名",
    "main_character_desc": "主角的出身、性格、天赋、目标（200字）",
    "supporting_name": "重要配角姓名",
    "supporting_desc": "配角角色定位和特点（100字）",
    "antagonist_name": "主要反派姓名",
    "antagonist_desc": "反派的背景、实力、与主角冲突（200字）",
    "main_plot_thread": "200-300字主线剧情走向",
    "core_conflicts": "核心矛盾冲突描述"
}}

只输出JSON对象，不要添加任何解释文字。确保JSON中所有字符串用双引号包裹。"""

SETTING_UPDATE_PROMPT = """
你是一位资深的小说编辑。请根据当前故事发展，更新小说设定文档。

## 当前设定
{current_setting}

## 剧情发展
{history_summary}

## 更新要求
1. 根据已发生的剧情更新角色弧线
2. 更新卷脉络规划
3. 调整核心冲突
4. 保持设定的一致性

请输出更新后的设定JSON。
"""

CHAPTER_WRITING_PROMPT = """
你是一位资深的玄幻小说作家。请根据提供的设定和上下文，创作精彩的章节内容。

【小说标题】：{novel_title}

【当前设定】：
{setting_summary}

【文风要求】：
{style_guide}

【当前卷信息】：
{volume_context}

【创作上下文】：
- 当前章节：第{chapter_idx}章
- 已写总字数：{total_words}字
- 本章目标字数：{target_words}字
- 前情提要：{previous_summary}

【待收伏笔】：
{foreshadowing_hints}

【本章节奏指导】：
{rhythm_guidance}

【章节要求】：
1. 每章五步法：抛出矛盾 → 拉高仇恨/期待 → 主角出手 → 全场反应/震惊 → 结尾钩子
2. Show, don't tell：情绪通过行动展示（「他攥紧拳头」>「他很愤怒」）
3. 人物行为符合设定，不OOC
4. 战斗描写精彩，境界体现分明
5. 语言简洁有力，长短句错落
6. 结尾必须有钩子（悬念/新威胁/新目标/反转）
7. 对话自然口语化，避免正式书面语
8. 视角集中，同一段不跳多人视角

【字数铁律】：本章必须至少{target_words}字，这是硬性要求。请确保输出完整、足够长。
请直接输出章节内容，不要添加任何额外说明。
"""

# 黄金三章专用 Prompt（第1-3章）
GOLDEN_CHAPTER_1_PROMPT = """
你是一位资深的玄幻小说作家。现在创作小说的【第一章——黄金开篇】。

【小说标题】：{novel_title}
【文风要求】：{style_guide}

【黄金第一章·抓人】：
- 开局即冲突，前300字必须出事儿
- 禁止：世界观介绍、背景铺垫、风景描写、回忆
- 必须：直接切入冲突 — 被羞辱/被追杀/被退婚/修为被废
- 主角触底：让读者心疼、代入
- 结尾钩子：金手指即将出现

【Show, Don't Tell 铁律】：
- 「他很愤怒」→「指甲掐进肉里，牙齿咬得咯咯响」
- 「他非常害怕」→「脊背发凉，双腿不受控制地颤抖」
- 通过动作、生理反应、环境氛围展示情绪，不要直接说情绪

【字数铁律】：本章必须至少{target_words}字，写完整的故事场景，不要偷工减料。

请直接输出章节内容，不要添加任何说明。
"""

GOLDEN_CHAPTER_2_PROMPT = """
你是一位资深的玄幻小说作家。现在创作小说的【第二章——留人】。

【小说标题】：{novel_title}
【文风要求】：{style_guide}
【前情提要】：{previous_summary}

【黄金第二章·留人】：
- 金手指亮出来：让读者知道它能干啥，但别全开
- 解决一个小危机：第一次尝到甜头
- 反派继续施压：保持紧张感
- 与主角建立情感共鸣
- 结尾钩子：更大的麻烦正在逼近

【字数铁律】：本章必须至少{target_words}字，写完整，写详细。

请直接输出章节内容。
"""

GOLDEN_CHAPTER_3_PROMPT = """
你是一位资深的玄幻小说作家。现在创作小说的【第三章——锁人】。

【小说标题】：{novel_title}
【文风要求】：{style_guide}
【前情提要】：{previous_summary}

【黄金第三章·锁人】：
- 第一次爽点交付：必须让读者拍案
- 打脸/升级/让反派吃惊 — 实质性的
- 确立主线目标和世界观核心矛盾
- 结尾钩子：真正的大秘密/大威胁刚刚露头

【字数铁律】：本章必须至少{target_words}字，绝不少于这个数字。

请直接输出章节内容。
"""

# 爽点章节 Prompt
CLIMAX_CHAPTER_PROMPT = """
你是一位资深的玄幻小说作家。现在创作【高潮章节】。

【小说标题】：{novel_title}
【文风要求】：{style_guide}
【前情提要】：{previous_summary}

{rhythm_guidance}

【高潮章节要求】：
- 收掉前面章节的主要伏笔
- 主角实力/地位有实质性提升
- 多角度描写旁观者反应：不只是主角感受，还要写旁人的震惊/嫉妒/崇拜
- 场面宏大，情绪饱满
- 先抑后扬：小虐→爆发→大爽
- 结尾为下一阶段埋新伏笔

【字数铁律】：高潮章节必须至少{target_words}字，场面要展开写，不要一笔带过。

请直接输出章节内容。
"""

POLISH_PROMPT = """
你是一位专业的小说润色师。请对以下章节内容进行润色，提升文字质量。

【原文】：
{chapter_content}

【文风要求】：
{style_guide}

【润色要求】：
1. 保持原意不变
2. 提升语言表现力
3. 增强画面感和感染力
4. 修正语法和用词不当
5. 优化句子结构
6. 删除冗余内容

请直接输出润色后的内容。
"""

PROOFREAD_PROMPT = """
你是一位专业的文字校对员。请检查以下章节内容，找出并修正错误。

【内容】：
{chapter_content}

【校对要求】：
1. 检查错别字
2. 检查标点符号错误
3. 检查语法错误
4. 检查逻辑矛盾
5. 保持原意不变

请直接输出校对后的内容。
"""

STYLE_ANCHOR_EXTRACTION_PROMPT = """
分析以下文本的文风特征，提取文风指纹。

【样本文本】：
{sample_text}

请输出JSON格式的分析结果：
{{
    "tone_description": "语气描述",
    "sentence_rhythm": "句式节奏特征",
    "typical_openings": ["常见开头方式1", "常见开头方式2"],
    "typical_endings": ["常见结尾方式1", "常见结尾方式2"],
    "forbidden_patterns": ["应避免的表达模式"],
    "vocabulary_preferences": ["偏好使用的词汇类型"]
}}
"""

CONTINUITY_CHECK_PROMPT = """
你是一位专业的小说编辑，请分析以下章节内容的连贯性。

【章节信息】：
- 当前章节：第{chapter_idx}章

【前一章结尾】：
{prev_ending}

【当前章节内容】：
{current_content}

【前文剧情脉络】：
{history_plot}

【角色状态】：
{character_states}

请从以下维度分析连贯性：
1. 人物状态连贯性（角色在上一章的状态与本章是否一致）
2. 时间线连贯性（时间流逝是否合理）
3. 地点场景连贯性（场景转换是否合理）
4. 情节逻辑连贯性（情节发展是否合理）

输出JSON格式结果：
{{
    "passed": true/false,
    "score": 0-100,
    "issues": ["问题描述1", "问题描述2"],
    "suggestions": ["修改建议1", "修改建议2"]
}}

评分标准：
- 100-80：优秀，无需修改
- 79-60：良好，建议微调
- 59-40：一般，需要修改
- 39以下：较差，强烈建议重写
"""

GENRE_ENFORCEMENT_PROMPT = """
检查以下内容是否符合玄幻修仙题材要求：

【内容】：
{content}

【要求】：
- 必须包含玄幻元素（修炼、境界、法器、丹药等）
- 避免现代词汇
- 保持古风语言风格

输出JSON格式：
{{
    "compliant": true/false,
    "issues": ["问题描述"],
    "suggestions": ["修改建议"]
}}
"""

DUPLICATE_CHECK_PROMPT = """
检查以下新内容是否与已有内容重复或高度相似：

【新内容】：
{new_content}

【已有内容】：
{existing_content}

输出JSON格式：
{{
    "duplicate": true/false,
    "similarity_score": 0-100,
    "duplicate_sections": ["重复片段描述"]
}}
"""

CHAPTER_TITLE_PROMPT = """
为第{chapter_idx}章生成一个合适的标题。

【小说标题】：{novel_title}

【本章内容概括】：
{chapter_event}

【上一章结尾】：
{prev_ending}

【文风类型】：{style_type}

请输出2-10字的章节标题，不要添加任何额外内容。
"""

VOLUME_TITLE_PROMPT = """
为第{volume_idx}卷生成一个合适的标题。

【卷核心内容】：
{volume_core}

【最近章节内容】：
{chapter_summaries}

【文风类型】：{style_type}

请输出卷标题，不要添加任何额外内容。
"""


def format_prompt(template: str, **kwargs) -> str:
    return template.format(**kwargs)