from typing import Dict, Any, List, Set
from loguru import logger

from src.novel_agent.state import NovelState, NovelSettingModel


class CoherenceVerifier:
    def __init__(self):
        self.verification_rules = [
            "world_consistency",
            "power_system_consistency",
            "character_consistency",
            "plot_coherence",
            "timeline_consistency"
        ]

    def verify_novel_coherence(self, novel_state: NovelState) -> Dict[str, Any]:
        if not novel_state.setting:
            return {
                "coherent": False,
                "score": 0,
                "issues": ["Novel setting not initialized"],
                "verification_results": {}
            }

        results = {}
        total_score = 0
        all_issues = []

        results["world_consistency"] = self._verify_world_consistency(novel_state.setting)
        total_score += results["world_consistency"]["score"]
        all_issues.extend(results["world_consistency"].get("issues", []))

        results["power_system_consistency"] = self._verify_power_system(novel_state.setting)
        total_score += results["power_system_consistency"]["score"]
        all_issues.extend(results["power_system_consistency"].get("issues", []))

        results["character_consistency"] = self._verify_character_consistency(novel_state)
        total_score += results["character_consistency"]["score"]
        all_issues.extend(results["character_consistency"].get("issues", []))

        results["plot_coherence"] = self._verify_plot_coherence(novel_state)
        total_score += results["plot_coherence"]["score"]
        all_issues.extend(results["plot_coherence"].get("issues", []))

        avg_score = total_score / len(self.verification_rules)

        return {
            "coherent": avg_score >= 70 and len(all_issues) < 5,
            "score": avg_score,
            "issues": all_issues,
            "verification_results": results
        }

    def _verify_world_consistency(self, setting: NovelSettingModel) -> Dict[str, Any]:
        issues = []
        score = 100

        if not setting.world_framework or len(setting.world_framework) < 100:
            issues.append("世界观框架描述过于简略")
            score -= 30

        if not setting.major_factions or len(setting.major_factions) < 50:
            issues.append("主要势力描述不完整")
            score -= 20

        if not setting.power_system or len(setting.power_system) < 50:
            issues.append("修炼体系描述不完整")
            score -= 30

        power_keywords = ["练气", "筑基", "金丹", "元婴", "化神", "境界", "灵气", "修炼"]
        has_power_elements = any(kw in setting.power_system for kw in power_keywords)
        if not has_power_elements:
            issues.append("修炼体系缺少必要的元素")
            score -= 20

        return {
            "score": max(0, score),
            "issues": issues
        }

    def _verify_power_system(self, setting: NovelSettingModel) -> Dict[str, Any]:
        issues = []
        score = 100

        power_system = setting.power_system

        realm_names = ["练气", "筑基", "金丹", "元婴", "化神", "渡劫", "大乘", "飞升"]
        found_realms = [r for r in realm_names if r in power_system]

        if len(found_realms) < 3:
            issues.append(f"修炼境界划分不完整，仅找到{len(found_realms)}个境界")
            score -= 30

        power_elements = ["灵气", "真元", "法力", "灵力", "元气"]
        has_power_source = any(elem in power_system for elem in power_elements)
        if not has_power_source:
            issues.append("修炼体系缺少力量来源描述")
            score -= 20

        cultivation_methods = ["吸收", "炼化", "感悟", "突破", "修炼"]
        has_methods = any(m in power_system for m in cultivation_methods)
        if not has_methods:
            issues.append("修炼体系缺少修炼方式描述")
            score -= 20

        return {
            "score": max(0, score),
            "issues": issues
        }

    def _verify_character_consistency(self, novel_state: NovelState) -> Dict[str, Any]:
        issues = []
        score = 100

        if not novel_state.setting:
            return {"score": 0, "issues": ["No setting available"]}

        main_char = novel_state.setting.main_character
        if not main_char or not main_char.name or main_char.name == "待定":
            issues.append("主角设定不完整")
            score -= 40

        if main_char and main_char.description:
            if len(main_char.description) < 50:
                issues.append("主角描述过于简略")
                score -= 15

        supporting = novel_state.setting.supporting_characters
        if not supporting or len(supporting) == 0:
            issues.append("缺少配角设定")
            score -= 15

        antagonists = novel_state.setting.antagonists
        if not antagonists or len(antagonists) == 0:
            issues.append("缺少反派设定")
            score -= 20

        character_names = set()
        if main_char and main_char.name:
            character_names.add(main_char.name)

        for char in supporting:
            if char.name in character_names:
                issues.append(f"角色名称重复: {char.name}")
                score -= 10
            character_names.add(char.name)

        for char in antagonists:
            if char.name in character_names:
                issues.append(f"角色名称重复: {char.name}")
                score -= 10
            character_names.add(char.name)

        return {
            "score": max(0, score),
            "issues": issues
        }

    def _verify_plot_coherence(self, novel_state: NovelState) -> Dict[str, Any]:
        issues = []
        score = 100

        if not novel_state.setting:
            return {"score": 0, "issues": ["No setting available"]}

        if not novel_state.setting.main_plot_thread:
            issues.append("缺少主线剧情描述")
            score -= 40

        if not novel_state.setting.core_conflicts:
            issues.append("缺少核心冲突描述")
            score -= 30

        if novel_state.setting.main_plot_thread and len(novel_state.setting.main_plot_thread) < 50:
            issues.append("主线剧情描述过于简略")
            score -= 20

        unresolved_foreshadowing = [fs for fs in novel_state.foreshadowing_tracking if fs.status == "unresolved"]
        if len(unresolved_foreshadowing) > 50:
            issues.append(f"伏笔过多（{len(unresolved_foreshadowing)}个），可能难以全部回收")
            score -= 10

        return {
            "score": max(0, score),
            "issues": issues
        }
