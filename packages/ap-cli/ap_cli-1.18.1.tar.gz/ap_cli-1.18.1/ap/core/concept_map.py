"""
ConceptMap 多主题数据结构管理类

支持多主题学习系统的核心数据管理，包含数据迁移和向后兼容功能。
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import typer


class ConceptMap:
    """多主题概念地图管理类"""

    def __init__(self, file_path: Optional[str] = None):
        """
        初始化概念地图管理器

        Args:
            file_path: 概念地图文件路径，默认为 workspace/concept_map.json
        """
        if file_path is None:
            file_path = Path("workspace") / "concept_map.json"
        self.file_path = Path(file_path)
        self.data = self._load_or_migrate()

    def _load_or_migrate(self) -> Dict[str, Any]:
        """加载数据或执行迁移"""
        if not self.file_path.exists():
            return self._create_empty_structure()

        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 检查是否为旧格式
            if self._is_old_format(data):
                typer.echo("检测到旧格式数据，正在自动迁移...")
                data = self._migrate_from_old_format(data)
                self._backup_old_data()
                typer.echo("✅ 数据迁移完成")

            return data

        except (json.JSONDecodeError, IOError) as e:
            typer.echo(f"警告：无法读取概念地图文件 {self.file_path}: {e}", err=True)
            return self._create_empty_structure()

    def _create_empty_structure(self) -> Dict[str, Any]:
        """创建空的数据结构"""
        return {
            "metadata": {
                "version": "3.0",
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            },
            "topics": {},
            "graph": {
                "relationships": {},  # 概念间关系
                "layout": {},         # 图谱布局信息
                "styles": {}          # 节点和边的样式
            }
        }

    def _is_old_format(self, data: Dict[str, Any]) -> bool:
        """检测是否为旧格式数据"""
        # 新格式必须包含 topics 和 metadata
        if "topics" in data and "metadata" in data:
            return False

        # 旧格式：直接包含概念数据，没有 topics 层级
        return any(
            isinstance(v, dict) and "name" in v for v in data.values()
        )

    def _migrate_from_old_format(
        self, old_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """从旧格式迁移到新格式"""
        new_data = self._create_empty_structure()

        # 将所有旧数据迁移到 "default" 主题下
        if old_data:
            new_data["topics"]["default"] = {
                "name": "Default Topic",
                "created_at": datetime.now().isoformat(),
                "concepts": old_data
            }
            new_data["metadata"]["active_topics"] = ["default"]

        return new_data

    def _backup_old_data(self) -> None:
        """备份旧数据"""
        backup_path = self.file_path.with_suffix('.json.backup')
        if self.file_path.exists():
            import shutil
            shutil.copy2(self.file_path, backup_path)
            typer.echo(f"📦 旧数据已备份到: {backup_path}")

    def save(self) -> None:
        """保存概念地图到文件"""
        # 更新时间戳
        self.data["metadata"]["last_updated"] = datetime.now().isoformat()

        # 确保目录存在
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            typer.echo(f"错误：无法保存概念地图文件 {self.file_path}: {e}", err=True)
            raise typer.Exit(1)

    # 主题管理方法
    def add_topic(self, topic_id: str, topic_name: str) -> None:
        """
        添加主题

        Args:
            topic_id: 主题ID
            topic_name: 主题名称
        """
        if topic_id in self.data["topics"]:
            typer.echo(f"主题 '{topic_name}' 已存在")
            # 确保现有主题具有modules和graph字段（向后兼容）
            if "modules" not in self.data["topics"][topic_id]:
                self.data["topics"][topic_id]["modules"] = {}
            if "graph" not in self.data["topics"][topic_id]:
                self.data["topics"][topic_id]["graph"] = {
                    "relationships": {}
                }
            return

        self.data["topics"][topic_id] = {
            "name": topic_name,
            "created_at": datetime.now().isoformat(),
            "modules": {},  # 新增：学习模块
            "concepts": {},  # 保持向后兼容
            "graph": {  # 新增：知识图谱数据
                "relationships": {}  # 概念间关系
            }
        }

    def get_topic(self, topic_id: str) -> Optional[Dict[str, Any]]:
        """
        获取主题信息

        Args:
            topic_id: 主题ID

        Returns:
            主题数据字典，如果不存在返回 None
        """
        return self.data["topics"].get(topic_id)

    def list_topics(self) -> List[str]:
        """
        列出所有主题ID

        Returns:
            主题ID列表
        """
        return list(self.data["topics"].keys())

    def topic_exists(self, topic_id: str) -> bool:
        """
        检查主题是否存在

        Args:
            topic_id: 主题ID

        Returns:
            是否存在
        """
        return topic_id in self.data["topics"]

    def remove_topic(self, topic_id: str) -> bool:
        """
        删除主题

        Args:
            topic_id: 主题ID

        Returns:
            是否成功删除
        """
        if topic_id in self.data["topics"]:
            del self.data["topics"][topic_id]
            if topic_id in self.data["metadata"]["active_topics"]:
                self.data["metadata"]["active_topics"].remove(topic_id)
            return True
        return False

    # 模块管理方法
    def add_module(self, topic_id: str, module_id: str, module_data: Dict[str, Any]) -> None:
        """
        添加学习模块到指定主题

        Args:
            topic_id: 主题ID
            module_id: 模块ID
            module_data: 模块数据
        """
        if topic_id not in self.data["topics"]:
            raise ValueError(f"主题 '{topic_id}' 不存在")

        self.data["topics"][topic_id]["modules"][module_id] = module_data

    def get_module(self, topic_id: str, module_id: str) -> Optional[Dict[str, Any]]:
        """
        获取指定模块

        Args:
            topic_id: 主题ID
            module_id: 模块ID

        Returns:
            模块数据，如果不存在返回 None
        """
        topic = self.get_topic(topic_id)
        if topic and "modules" in topic:
            return topic["modules"].get(module_id)
        return None

    def add_concept_to_module(
        self, topic_id: str, module_id: str, concept_id: str, concept_data: Dict[str, Any]
    ) -> None:
        """向指定模块添加概念"""
        if not self.topic_exists(topic_id):
            raise ValueError(f"主题 '{topic_id}' 不存在")
        
        module = self.get_module(topic_id, module_id)
        if module is None:
            raise ValueError(f"模块 '{module_id}' 在主题 '{topic_id}' 中不存在")
        
        # 确保概念数据包含必要字段
        concept_data.setdefault("children", [])
        concept_data.setdefault("status", {})
        concept_data.setdefault("mastery", {"best_score_percent": 0})
        concept_data.setdefault("module_id", module_id)
        
        # 知识图谱相关字段
        concept_data.setdefault("relationships", {
            "prerequisites": [],    # 前置概念
            "dependencies": [],     # 依赖概念
            "related": [],          # 相关概念
            "enables": []           # 启用的概念
        })
        concept_data.setdefault("graph_metadata", {
            "difficulty": 1,                # 难度等级 1-5
            "importance": 1,                # 重要性 1-5
            "tags": []                      # 标签
        })
        
        # 添加到模块
        module["concepts"][concept_id] = concept_data
        
        # 同时添加到扁平化结构（向后兼容）
        self.data["topics"][topic_id]["concepts"][concept_id] = concept_data

    # 概念管理方法
    def add_concept(
        self, topic_id: str, concept_id: str, concept_data: Dict[str, Any]
    ) -> None:
        """向主题添加概念（扁平化存储，向后兼容）"""
        if not self.topic_exists(topic_id):
            raise ValueError(f"主题 '{topic_id}' 不存在")

        # 确保概念数据包含必要字段
        concept_data.setdefault("children", [])
        concept_data.setdefault("status", {})
        concept_data.setdefault("mastery", {"best_score_percent": 0})
        
        # 知识图谱相关字段
        concept_data.setdefault("relationships", {
            "prerequisites": [],    # 前置概念
            "dependencies": [],     # 依赖概念
            "related": [],          # 相关概念
            "enables": []           # 启用的概念
        })
        concept_data.setdefault("graph_metadata", {
            "difficulty": 1,                # 难度等级 1-5
            "importance": 1,                # 重要性 1-5
            "tags": []                      # 标签
        })

        self.data["topics"][topic_id]["concepts"][concept_id] = concept_data

    def get_concept(
        self, topic_id: str, concept_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取指定概念

        Args:
            topic_id: 主题ID
            concept_id: 概念ID

        Returns:
            概念数据，如果不存在返回 None
        """
        topic = self.get_topic(topic_id)
        if topic:
            return topic["concepts"].get(concept_id)
        return None

    def update_status(self, topic_id: str, concept_id: str, status_key: str, value: Any) -> None:
        """
        更新概念状态

        Args:
            topic_id: 主题ID
            concept_id: 概念ID
            status_key: 状态键名
            value: 状态值
        """
        concept = self.get_concept(topic_id, concept_id)
        if concept:
            if 'status' not in concept:
                concept['status'] = {}
            concept['status'][status_key] = value

    def update_mastery(
        self, topic_id: str, concept_id: str, score_percent: float
    ) -> None:
        """
        更新概念掌握程度

        Args:
            topic_id: 主题ID
            concept_id: 概念ID
            score_percent: 得分百分比
        """
        concept = self.get_concept(topic_id, concept_id)
        if concept:
            if 'mastery' not in concept:
                concept['mastery'] = {}
            current_best = concept['mastery'].get(
                'best_score_percent', -1
            )
            if score_percent > current_best:
                concept['mastery']['best_score_percent'] = score_percent

    # 兼容性方法（用于向后兼容）
    def get_default_topic_id(self) -> Optional[str]:
        """
        获取默认主题ID（用于单主题兼容）

        Returns:
            默认主题ID，如果有多个主题则返回第一个
        """
        topics = self.list_topics()
        if not topics:
            return None

        # 优先返回 "default" 主题
        if "default" in topics:
            return "default"

        # 否则返回第一个主题
        return topics[0]

    def get_all_concepts_flat(self) -> Dict[str, Any]:
        """
        获取所有概念的扁平化视图（用于向后兼容）

        Returns:
            扁平化的概念字典
        """
        flat_concepts = {}
        for topic_id, topic_data in self.data["topics"].items():
            flat_concepts.update(topic_data["concepts"])
        return flat_concepts

    def get_topic_by_concept(self, concept_id: str) -> Optional[str]:
        """根据概念ID查找所属主题"""
        for topic_id, topic_data in self.data["topics"].items():
            if concept_id in topic_data.get("concepts", {}):
                return topic_id
        return None

    # 知识图谱关系管理方法
    
    def add_relationship(self, from_concept: str, to_concept: str, relationship_type: str, topic_id: str = None) -> None:
        """
        添加概念间关系
        
        Args:
            from_concept: 源概念ID
            to_concept: 目标概念ID  
            relationship_type: 关系类型 (prerequisite, dependency, related, enables)
            topic_id: 主题ID，如果为None则自动查找
        """
        if topic_id is None:
            topic_id = self.get_topic_by_concept(from_concept)
            if topic_id is None:
                raise ValueError(f"找不到概念 '{from_concept}' 所属的主题")
        
        from_concept_data = self.get_concept(topic_id, from_concept)
        if from_concept_data is None:
            raise ValueError(f"概念 '{from_concept}' 不存在")
            
        # 确保关系字段存在
        if "relationships" not in from_concept_data:
            from_concept_data["relationships"] = {
                "prerequisites": [], "dependencies": [], "related": [], "enables": []
            }
        
        # 添加关系
        if relationship_type in from_concept_data["relationships"]:
            if to_concept not in from_concept_data["relationships"][relationship_type]:
                from_concept_data["relationships"][relationship_type].append(to_concept)
        else:
            raise ValueError(f"不支持的关系类型: {relationship_type}")
    
    def remove_relationship(self, from_concept: str, to_concept: str, relationship_type: str, topic_id: str = None) -> None:
        """移除概念间关系"""
        if topic_id is None:
            topic_id = self.get_topic_by_concept(from_concept)
            if topic_id is None:
                raise ValueError(f"找不到概念 '{from_concept}' 所属的主题")
        
        from_concept_data = self.get_concept(topic_id, from_concept)
        if from_concept_data is None:
            raise ValueError(f"概念 '{from_concept}' 不存在")
            
        if "relationships" in from_concept_data and relationship_type in from_concept_data["relationships"]:
            if to_concept in from_concept_data["relationships"][relationship_type]:
                from_concept_data["relationships"][relationship_type].remove(to_concept)
    
    def get_concept_relationships(self, concept_id: str, topic_id: str = None) -> Dict[str, List[str]]:
        """获取概念的所有关系"""
        if topic_id is None:
            topic_id = self.get_topic_by_concept(concept_id)
            if topic_id is None:
                raise ValueError(f"找不到概念 '{concept_id}' 所属的主题")
        
        concept_data = self.get_concept(topic_id, concept_id)
        if concept_data is None:
            raise ValueError(f"概念 '{concept_id}' 不存在")
            
        return concept_data.get("relationships", {
            "prerequisites": [], "dependencies": [], "related": [], "enables": []
        })

    def remove_relationship(self, from_concept: str, to_concept: str, relationship_type: str, topic_id: str = None) -> None:
        """移除概念间关系"""
        if topic_id is None:
            topic_id = self.get_topic_by_concept(from_concept)
            if topic_id is None:
                raise ValueError(f"找不到概念 '{from_concept}' 所属的主题")
        
        from_concept_data = self.get_concept(topic_id, from_concept)
        if from_concept_data is None:
            raise ValueError(f"概念 '{from_concept}' 不存在")
            
        relationships = from_concept_data.get("relationships", {})
        if relationship_type in relationships and to_concept in relationships[relationship_type]:
            relationships[relationship_type].remove(to_concept)
    
    def get_graph_data(self, topic_id: str) -> Dict[str, Any]:
        """获取指定主题的图谱数据"""
        topic = self.get_topic(topic_id)
        if not topic:
            raise ValueError(f"主题 '{topic_id}' 不存在")
        
        nodes = []
        edges = []
        
        # 构建节点数据
        for concept_id, concept_data in topic.get("concepts", {}).items():
            node = {
                "id": concept_id,
                "name": concept_data.get("name", concept_id),
                "difficulty": concept_data.get("graph_metadata", {}).get("difficulty", 1),
                "importance": concept_data.get("graph_metadata", {}).get("importance", 1),
                "tags": concept_data.get("graph_metadata", {}).get("tags", [])
            }
            nodes.append(node)
            
            # 构建边数据
            relationships = concept_data.get("relationships", {})
            for rel_type, targets in relationships.items():
                for target in targets:
                    edge = {
                        "from": concept_id,
                        "to": target,
                        "type": rel_type,
                        "style": self._get_edge_style(rel_type)
                    }
                    edges.append(edge)
        
        return {
            "nodes": nodes,
            "edges": edges
        }
    
    def _get_edge_style(self, relationship_type: str) -> Dict[str, str]:
        """根据关系类型获取边的样式"""
        styles = {
            "prerequisites": {"color": "#FF6B6B", "style": "solid", "arrow": "to"},
            "dependencies": {"color": "#4ECDC4", "style": "dashed", "arrow": "to"},
            "related": {"color": "#45B7D1", "style": "dotted", "arrow": "none"},
            "enables": {"color": "#96CEB4", "style": "solid", "arrow": "to"}
        }
        return styles.get(relationship_type, {"color": "#999", "style": "solid", "arrow": "none"})


def slugify(text: str) -> str:
    """
    将文本转换为适合作为文件名或ID的格式

    Args:
        text: 要转换的文本

    Returns:
        转换后的ID格式字符串
    """
    if not text:
        return ""

    # 移除或替换特殊字符
    text = re.sub(r'[^\w\s-]', '', text.strip())
    # 将空格替换为连字符
    text = re.sub(r'[-\s]+', '-', text)
    return text.lower()
