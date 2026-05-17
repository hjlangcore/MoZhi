from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel, Field
import json
import re

from src.api.schemas import BaseResponse
from src.core.config import settings
from src.novel_agent.workflow import LLMClient
from src.novel_agent.style_analyzer import get_style_analyzer


router = APIRouter(prefix="/ai/generate", tags=["ai-generate"])


def get_llm_client() -> LLMClient:
    return LLMClient(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_MODEL,
        timeout=settings.OLLAMA_TIMEOUT,
        num_gpu=14,
    )


def _extract_json(text: str) -> dict:
    cleaned = text.strip()
    code_block = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', cleaned, re.DOTALL)
    if code_block:
        cleaned = code_block.group(1).strip()
    json_match = re.search(r'\{[\s\S]*\}', cleaned)
    if not json_match:
        raise ValueError("No JSON object found")
    json_str = json_match.group(0)
    json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
    json_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', json_str)
    return json.loads(json_str)


class WorldViewGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="世界观生成提示词")


class CharacterGenerateRequest(BaseModel):
    worldView: dict = Field(..., description="世界观数据")
    roleType: str = Field(default="protagonist", description="角色类型")


WORLDVIEW_PROMPT_TEMPLATE = """你是一个专业的小说世界观设计师。请根据以下提示，生成一个完整的小说世界观设定。

用户提示：{prompt}

请严格按照以下 JSON 格式输出（不要输出任何其他文本）：
{{
  "core_theme": "核心主题（一句话哲学/思想概括）",
  "historical_events": [
    "创世/起源事件",
    "黄金时代",
    "转折点/灾难",
    "当前局势"
  ],
  "social_structure": {{
    "dominant_forces": "主导势力",
    "class_divisions": "阶层划分",
    "core_conflicts": "核心冲突"
  }},
  "geography": {{
    "major_regions": "主要区域",
    "power_distribution": "势力分布",
    "key_locations": "关键地点"
  }},
  "physics_rules": {{
    "power_system": "力量体系（修炼/魔法系统）",
    "limitations": "限制条件",
    "cost_mechanism": "代价机制"
  }}
}}
"""


CHARACTER_PROMPT_TEMPLATE = """你是一个专业的小说角色设计师。请根据给定的世界观和角色类型，生成一个立体的小说角色。

世界观背景：
- 核心主题：{core_theme}
- 社会结构：{social_structure}
- 地理生态：{geography}
- 力量体系：{physics_rules}

角色类型：{role_type}

请严格按照以下 JSON 格式输出（不要输出任何其他文本）：
{{
  "name": "角色姓名",
  "age": 年龄数字,
  "gender": "性别（男/女）",
  "social_identity": "社会身份",
  "nickname": "外号/称号",
  "wants": "角色表面想要什么",
  "needs": "角色真正需要什么",
  "fears": "角色内心最害怕的事",
  "weakness": "角色的致命弱点",
  "speech_style": "说话方式",
  "habits": "行为习惯",
  "skills": "特殊技能",
  "fatal_flaw": "致命缺陷",
  "arc_start": "故事开始时的状态",
  "trigger_event": "改变命运的关键事件",
  "midpoint_change": "故事中段的重大转变",
  "final_form": "故事结束时的样子"
}}
"""


@router.post("/worldview", response_model=BaseResponse)
async def generate_worldview(data: WorldViewGenerateRequest):
    logger.info(f"Generating worldview for prompt: {data.prompt[:50]}...")

    try:
        llm = get_llm_client()
        prompt = WORLDVIEW_PROMPT_TEMPLATE.format(prompt=data.prompt)
        try:
            result = llm.generate_json(prompt, temperature=0.7)
        except Exception as json_err:
            logger.warning(f"generate_json failed, fallback to raw parse: {json_err}")
            raw = llm.generate(prompt, temperature=0.5)
            result = _extract_json(raw)

        logger.info(f"Worldview generated successfully")
        return BaseResponse(
            code=200,
            message="Worldview generated successfully",
            data=result,
        )
    except Exception as e:
        logger.error(f"Worldview generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")


@router.post("/character", response_model=BaseResponse)
async def generate_character(data: CharacterGenerateRequest):
    logger.info(f"Generating character with role type: {data.roleType}")

    try:
        llm = get_llm_client()

        world_view = data.worldView
        core_theme = world_view.get("core_theme", "未知")

        social = world_view.get("social_structure", {})
        social_str = f"主导势力:{social.get('dominant_forces','')}, 阶层划分:{social.get('class_divisions','')}"

        geo = world_view.get("geography", {})
        geo_str = f"主要区域:{geo.get('major_regions','')}, 势力分布:{geo.get('power_distribution','')}"

        physics = world_view.get("physics_rules", {})
        physics_str = physics.get("power_system", "未知力量体系")

        role_labels = {
            "protagonist": "核心主角",
            "mentor": "导师",
            "rival": "对手",
            "love_interest": "爱人",
            "antagonist": "反派",
            "ally": "盟友",
            "family": "亲人",
        }
        role_label = role_labels.get(data.roleType, data.roleType)

        prompt = CHARACTER_PROMPT_TEMPLATE.format(
            core_theme=core_theme,
            social_structure=social_str,
            geography=geo_str,
            physics_rules=physics_str,
            role_type=role_label,
        )
        try:
            result = llm.generate_json(prompt, temperature=0.7)
        except Exception as json_err:
            logger.warning(f"generate_json failed, fallback to raw parse: {json_err}")
            raw = llm.generate(prompt, temperature=0.5)
            result = _extract_json(raw)

        logger.info(f"Character generated successfully: {result.get('name', '?')}")
        return BaseResponse(
            code=200,
            message="Character generated successfully",
            data=result,
        )
    except Exception as e:
        logger.error(f"Character generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")


class StyleAnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=100, description="待分析的参考文本")


@router.post("/style/analyze", response_model=BaseResponse)
async def analyze_style(data: StyleAnalyzeRequest):
    logger.info(f"Analyzing style for text length: {len(data.text)}")

    try:
        analyzer = get_style_analyzer()
        fp = analyzer.analyze(data.text)

        result = {
            "sentence_length": {
                "avg": fp.sentence_length.avg_length,
                "std_dev": fp.sentence_length.std_dev,
                "short_ratio": fp.sentence_length.short_ratio,
                "long_ratio": fp.sentence_length.long_ratio,
            },
            "rhythm": {
                "dialogue_ratio": fp.rhythm.dialogue_ratio,
                "action_ratio": fp.rhythm.action_ratio,
                "psychological_ratio": fp.rhythm.psychological_ratio,
            },
            "style_tags": fp.style_tags,
            "llm_style_guide": fp.llm_style_guide,
        }

        logger.info(f"Style analysis completed, tags: {fp.style_tags}")
        return BaseResponse(
            code=200,
            message="Style analysis completed",
            data=result,
        )
    except Exception as e:
        logger.error(f"Style analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Style analysis failed: {str(e)}")
