import unittest
from datetime import datetime
from src.novel_agent.continuity_checker import ContinuityChecker, get_continuity_checker
from src.novel_agent.state import (
    NovelState, NovelSettingModel, CharacterModel, ChapterModel, ForeshadowingModel
)


class TestContinuityChecker(unittest.TestCase):
    """连贯性检查单元测试"""

    def setUp(self):
        self.checker = ContinuityChecker()
        self.novel_state = NovelState(
            setting=NovelSettingModel(
                novel_title="测试小说",
                world_framework="玄幻世界",
                power_system="修炼体系",
                major_factions="正道、魔道",
                main_character=CharacterModel(
                    name="李明",
                    role="主角",
                    description="年轻修士",
                    importance="main"
                ),
                supporting_characters=[],
                antagonists=[],
                main_plot_thread="主角成长之路",
                core_conflicts="正邪对立",
                style_type="凡人流",
                style_description="平凡少年逆袭"
            ),
            chapters=[
                ChapterModel(
                    chapter_number=1,
                    title="第一章 初入宗门",
                    content="李明来到了青云宗，开始了他的修炼之路。宗门里人来人往，热闹非凡。"
                ),
                ChapterModel(
                    chapter_number=2,
                    title="第二章 修炼开始",
                    content="李明开始修炼基础功法，每天勤奋刻苦。山谷中的灵气浓郁，非常适合修炼。"
                ),
                ChapterModel(
                    chapter_number=3,
                    title="第三章 遭遇挑战",
                    content="王强向李明发起挑战，两人在演武场展开对决。"
                )
            ]
        )

    def test_check_chapter_continuity_first_chapter(self):
        """测试第一章连贯性检查"""
        result = self.checker.check_chapter_continuity(self.novel_state, 1)
        self.assertTrue(result["passed"])
        self.assertEqual(result["score"], 100)

    def test_check_chapter_continuity_normal(self):
        """测试正常章节连贯性检查"""
        result = self.checker.check_chapter_continuity(self.novel_state, 2)
        self.assertTrue(result["passed"])

    def test_check_chapter_continuity_location_jump(self):
        """测试场景跳跃检测"""
        self.novel_state.chapters[1].content = "李明在宗门修炼，每天勤奋刻苦，希望能够早日突破境界。宗门内高手如云，李明感到压力很大。他每天早起晚睡，努力修炼基础功法。"
        self.novel_state.chapters[2].content = "李明来到了城中，开始逛街。城中热闹非凡，各种商铺琳琅满目，人来人往络绎不绝。他走进一家兵器铺，想要购买一把趁手的武器。"
        result = self.checker.check_chapter_continuity(self.novel_state, 3)
        self.assertIn("场景可能跳跃", str(result["issues"]))

    def test_check_character_continuity(self):
        """测试角色连贯性"""
        result = self.checker._check_character_continuity(
            self.novel_state.chapters[0],
            self.novel_state.chapters[1],
            self.novel_state
        )
        self.assertEqual(len(result), 0)

    def test_check_character_disappearance(self):
        """测试角色消失检测"""
        self.novel_state.chapters[1].content = "王强开始修炼。"
        result = self.checker._check_character_continuity(
            self.novel_state.chapters[0],
            self.novel_state.chapters[1],
            self.novel_state
        )
        self.assertIn("李明的状态可能不一致", str(result))

    def test_check_timeline_continuity(self):
        """测试时间线连贯性"""
        result = self.checker._check_timeline_continuity(
            self.novel_state.chapters[0],
            self.novel_state.chapters[1]
        )
        self.assertEqual(len(result), 0)

    def test_check_location_continuity(self):
        """测试地点连贯性"""
        result = self.checker._check_location_continuity(
            self.novel_state.chapters[0],
            self.novel_state.chapters[1]
        )
        self.assertEqual(len(result), 0)

    def test_check_plot_continuity(self):
        """测试剧情连贯性"""
        result = self.checker._check_plot_continuity(self.novel_state, 2)
        self.assertEqual(len(result), 0)

    def test_validate_character_consistency(self):
        """测试角色一致性验证"""
        result = self.checker.validate_character_consistency(self.novel_state, 1)
        self.assertTrue(result["consistent"])

    def test_validate_character_disappearance(self):
        """测试角色消失验证"""
        self.novel_state.chapters[1].content = "王强修炼。"
        result = self.checker.validate_character_consistency(self.novel_state, 2)
        self.assertFalse(result["consistent"])
        self.assertIn("李明", str(result["issues"]))

    def test_get_continuity_checker_singleton(self):
        """测试单例模式"""
        checker1 = get_continuity_checker()
        checker2 = get_continuity_checker()
        self.assertIs(checker1, checker2)


if __name__ == "__main__":
    unittest.main()
