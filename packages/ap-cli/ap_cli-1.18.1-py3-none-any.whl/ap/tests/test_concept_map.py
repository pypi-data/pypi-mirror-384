"""
ConceptMap 类的单元测试

测试多主题数据结构、数据迁移和向后兼容功能。
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from ap.core.concept_map import ConceptMap, slugify


class TestConceptMap(unittest.TestCase):
    """ConceptMap 类测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "test_concept_map.json"
    
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_empty_structure(self):
        """测试创建空数据结构"""
        concept_map = ConceptMap(str(self.test_file))
        
        self.assertIn("topics", concept_map.data)
        self.assertIn("metadata", concept_map.data)
        self.assertEqual(concept_map.data["metadata"]["version"], "2.0")
        self.assertEqual(concept_map.data["topics"], {})
        self.assertEqual(concept_map.data["metadata"]["active_topics"], [])
    
    def test_add_topic(self):
        """测试添加主题"""
        concept_map = ConceptMap(str(self.test_file))
        
        concept_map.add_topic("python", "Python Programming")
        
        self.assertTrue(concept_map.topic_exists("python"))
        topic = concept_map.get_topic("python")
        self.assertEqual(topic["name"], "Python Programming")
        self.assertIn("created_at", topic)
        self.assertEqual(topic["concepts"], {})
        self.assertIn("python", concept_map.data["metadata"]["active_topics"])
    
    def test_list_topics(self):
        """测试列出主题"""
        concept_map = ConceptMap(str(self.test_file))
        
        concept_map.add_topic("python", "Python Programming")
        concept_map.add_topic("javascript", "JavaScript Programming")
        
        topics = concept_map.list_topics()
        self.assertIn("python", topics)
        self.assertIn("javascript", topics)
        self.assertEqual(len(topics), 2)
    
    def test_remove_topic(self):
        """测试删除主题"""
        concept_map = ConceptMap(str(self.test_file))
        
        concept_map.add_topic("python", "Python Programming")
        self.assertTrue(concept_map.topic_exists("python"))
        
        result = concept_map.remove_topic("python")
        self.assertTrue(result)
        self.assertFalse(concept_map.topic_exists("python"))
        self.assertNotIn("python", concept_map.data["metadata"]["active_topics"])
        
        # 测试删除不存在的主题
        result = concept_map.remove_topic("nonexistent")
        self.assertFalse(result)
    
    def test_add_concept(self):
        """测试添加概念"""
        concept_map = ConceptMap(str(self.test_file))
        concept_map.add_topic("python", "Python Programming")
        
        concept_data = {
            "name": "Variables and Data Types",
            "children": [],
            "status": {"explained": False, "quiz_generated": False},
            "mastery": {"best_score_percent": -1}
        }
        
        concept_map.add_concept("python", "variables-and-data-types", concept_data)
        
        concept = concept_map.get_concept("python", "variables-and-data-types")
        self.assertIsNotNone(concept)
        self.assertEqual(concept["name"], "Variables and Data Types")
    
    def test_add_concept_to_nonexistent_topic(self):
        """测试向不存在的主题添加概念"""
        concept_map = ConceptMap(str(self.test_file))
        
        concept_data = {"name": "Test Concept"}
        
        with self.assertRaises(ValueError):
            concept_map.add_concept("nonexistent", "test-concept", concept_data)
    
    def test_update_status(self):
        """测试更新概念状态"""
        concept_map = ConceptMap(str(self.test_file))
        concept_map.add_topic("python", "Python Programming")
        
        concept_data = {
            "name": "Variables",
            "status": {"explained": False, "quiz_generated": False}
        }
        concept_map.add_concept("python", "variables", concept_data)
        
        concept_map.update_status("python", "variables", "explained", True)
        
        concept = concept_map.get_concept("python", "variables")
        self.assertTrue(concept["status"]["explained"])
    
    def test_update_mastery(self):
        """测试更新掌握程度"""
        concept_map = ConceptMap(str(self.test_file))
        concept_map.add_topic("python", "Python Programming")
        
        concept_data = {
            "name": "Variables",
            "mastery": {"best_score_percent": -1}
        }
        concept_map.add_concept("python", "variables", concept_data)
        
        # 第一次更新
        concept_map.update_mastery("python", "variables", 80.0)
        concept = concept_map.get_concept("python", "variables")
        self.assertEqual(concept["mastery"]["best_score_percent"], 80.0)
        
        # 更高分数应该更新
        concept_map.update_mastery("python", "variables", 90.0)
        concept = concept_map.get_concept("python", "variables")
        self.assertEqual(concept["mastery"]["best_score_percent"], 90.0)
        
        # 更低分数不应该更新
        concept_map.update_mastery("python", "variables", 70.0)
        concept = concept_map.get_concept("python", "variables")
        self.assertEqual(concept["mastery"]["best_score_percent"], 90.0)
    
    def test_save_and_load(self):
        """测试保存和加载"""
        concept_map = ConceptMap(str(self.test_file))
        concept_map.add_topic("python", "Python Programming")
        
        concept_data = {"name": "Variables", "children": []}
        concept_map.add_concept("python", "variables", concept_data)
        
        concept_map.save()
        
        # 创建新实例加载数据
        new_concept_map = ConceptMap(str(self.test_file))
        
        self.assertTrue(new_concept_map.topic_exists("python"))
        concept = new_concept_map.get_concept("python", "variables")
        self.assertIsNotNone(concept)
        self.assertEqual(concept["name"], "Variables")
    
    def test_old_format_detection(self):
        """测试旧格式检测"""
        concept_map = ConceptMap(str(self.test_file))
        
        # 新格式数据
        new_format_data = {
            "topics": {"python": {"name": "Python", "concepts": {}}},
            "metadata": {"version": "2.0"}
        }
        self.assertFalse(concept_map._is_old_format(new_format_data))
        
        # 旧格式数据
        old_format_data = {
            "python-basics": {
                "name": "Python Basics",
                "children": [],
                "status": {"explained": False}
            }
        }
        self.assertTrue(concept_map._is_old_format(old_format_data))
    
    @patch('typer.echo')
    def test_migration_from_old_format(self, mock_echo):
        """测试从旧格式迁移"""
        # 创建旧格式数据文件
        old_data = {
            "python-basics": {
                "name": "Python Basics",
                "children": ["variables", "functions"],
                "status": {"explained": True, "quiz_generated": False},
                "mastery": {"best_score_percent": 85.0}
            },
            "variables": {
                "name": "Variables",
                "children": [],
                "status": {"explained": True, "quiz_generated": True},
                "mastery": {"best_score_percent": 90.0}
            }
        }
        
        with open(self.test_file, 'w', encoding='utf-8') as f:
            json.dump(old_data, f)
        
        # 加载应该触发迁移
        concept_map = ConceptMap(str(self.test_file))
        
        # 验证迁移结果
        self.assertIn("topics", concept_map.data)
        self.assertIn("metadata", concept_map.data)
        self.assertEqual(concept_map.data["metadata"]["version"], "2.0")
        
        # 验证数据被迁移到 default 主题
        self.assertTrue(concept_map.topic_exists("default"))
        default_topic = concept_map.get_topic("default")
        self.assertEqual(default_topic["name"], "Default Topic")
        
        # 验证概念数据完整性
        python_basics = concept_map.get_concept("default", "python-basics")
        self.assertIsNotNone(python_basics)
        self.assertEqual(python_basics["name"], "Python Basics")
        self.assertTrue(python_basics["status"]["explained"])
        self.assertEqual(python_basics["mastery"]["best_score_percent"], 85.0)
        
        variables = concept_map.get_concept("default", "variables")
        self.assertIsNotNone(variables)
        self.assertEqual(variables["name"], "Variables")
        self.assertEqual(variables["mastery"]["best_score_percent"], 90.0)
        
        # 验证活跃主题列表
        self.assertIn("default", concept_map.data["metadata"]["active_topics"])
    
    def test_get_default_topic_id(self):
        """测试获取默认主题ID"""
        concept_map = ConceptMap(str(self.test_file))
        
        # 没有主题时返回 None
        self.assertIsNone(concept_map.get_default_topic_id())
        
        # 有 default 主题时返回 default
        concept_map.add_topic("default", "Default Topic")
        concept_map.add_topic("python", "Python Programming")
        self.assertEqual(concept_map.get_default_topic_id(), "default")
        
        # 没有 default 主题时返回第一个
        concept_map.remove_topic("default")
        self.assertEqual(concept_map.get_default_topic_id(), "python")
    
    def test_get_all_concepts_flat(self):
        """测试获取扁平化概念视图"""
        concept_map = ConceptMap(str(self.test_file))
        
        # 添加多个主题和概念
        concept_map.add_topic("python", "Python Programming")
        concept_map.add_topic("javascript", "JavaScript Programming")
        
        python_concept = {"name": "Python Variables", "children": []}
        js_concept = {"name": "JavaScript Variables", "children": []}
        
        concept_map.add_concept("python", "python-variables", python_concept)
        concept_map.add_concept("javascript", "js-variables", js_concept)
        
        # 获取扁平化视图
        flat_concepts = concept_map.get_all_concepts_flat()
        
        self.assertIn("python-variables", flat_concepts)
        self.assertIn("js-variables", flat_concepts)
        self.assertEqual(flat_concepts["python-variables"]["name"], "Python Variables")
        self.assertEqual(flat_concepts["js-variables"]["name"], "JavaScript Variables")


class TestSlugify(unittest.TestCase):
    """slugify 函数测试"""
    
    def test_basic_slugify(self):
        """测试基本 slugify 功能"""
        self.assertEqual(slugify("Python Programming"), "python-programming")
        self.assertEqual(slugify("JavaScript Basics"), "javascript-basics")
        self.assertEqual(slugify("Data Structures & Algorithms"), "data-structures-algorithms")
    
    def test_special_characters(self):
        """测试特殊字符处理"""
        self.assertEqual(slugify("C++ Programming"), "c-programming")
        self.assertEqual(slugify("Node.js Development"), "nodejs-development")
        self.assertEqual(slugify("API Design & Development"), "api-design-development")
    
    def test_multiple_spaces(self):
        """测试多个空格处理"""
        self.assertEqual(slugify("Python   Programming"), "python-programming")
        self.assertEqual(slugify("  JavaScript  Basics  "), "javascript-basics")
    
    def test_empty_and_edge_cases(self):
        """测试边界情况"""
        self.assertEqual(slugify(""), "")
        self.assertEqual(slugify("   "), "")
        self.assertEqual(slugify("A"), "a")
        self.assertEqual(slugify("123"), "123")


if __name__ == '__main__':
    unittest.main()