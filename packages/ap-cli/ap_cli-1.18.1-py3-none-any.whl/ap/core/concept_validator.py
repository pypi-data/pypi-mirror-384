"""概念质量检查器

用于检测和改进概念地图中的概念质量，确保概念的原子性和合理性。
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    issues: List[str]
    suggestions: List[str]


class ConceptValidator:
    """概念质量检查器"""
    
    # 复合概念的连接词模式
    COMPOUND_PATTERNS = [
        r'(.+)[与和及](.+)',  # 匹配"与"、"和"、"及"
        r'(.+)和(.+)',
        r'(.+)与(.+)',
        r'(.+)及(.+)',
        r'(.+)以及(.+)',
        r'(.+)、(.+)',  # 匹配顿号分隔
    ]
    
    # 过于宽泛的概念关键词
    BROAD_KEYWORDS = [
        '基础', '入门', '概述', '介绍', '总览', '综合',
        '全面', '完整', '整体', '系统', '通用', '常用',
        '基本', '核心', '重要', '主要', '关键'
    ]
    
    # 理想的概念长度范围
    IDEAL_LENGTH_RANGE = (2, 8)
    
    def validate_concept(self, concept_name: str) -> ValidationResult:
        """验证单个概念的质量
        
        Args:
            concept_name: 概念名称
            
        Returns:
            ValidationResult: 验证结果
        """
        issues = []
        suggestions = []
        
        # 检查复合概念
        compound_result = self._check_compound_concept(concept_name)
        if compound_result:
            issues.append(f"检测到复合概念：{concept_name}")
            suggestions.extend(compound_result)
        
        # 检查概念长度
        length_issue = self._check_concept_length(concept_name)
        if length_issue:
            issues.append(length_issue)
        
        # 检查是否过于宽泛
        broad_issue = self._check_broad_concept(concept_name)
        if broad_issue:
            issues.append(broad_issue)
            suggestions.append(f"建议将'{concept_name}'具体化为更细粒度的概念")
        
        # 检查概念格式
        format_issue = self._check_concept_format(concept_name)
        if format_issue:
            issues.append(format_issue)
        
        is_valid = len(issues) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            suggestions=suggestions
        )
    
    def validate_concept_list(self, concepts: List[str]) -> Dict[str, ValidationResult]:
        """批量验证概念列表
        
        Args:
            concepts: 概念名称列表
            
        Returns:
            Dict[str, ValidationResult]: 每个概念的验证结果
        """
        results = {}
        for concept in concepts:
            results[concept] = self.validate_concept(concept)
        return results
    
    def get_quality_score(self, concepts: List[str]) -> float:
        """计算概念列表的整体质量分数
        
        Args:
            concepts: 概念名称列表
            
        Returns:
            float: 质量分数 (0-1)
        """
        if not concepts:
            return 0.0
        
        results = self.validate_concept_list(concepts)
        valid_count = sum(1 for result in results.values() if result.is_valid)
        
        return valid_count / len(concepts)
    
    def suggest_improvements(self, concepts: List[str]) -> List[Dict]:
        """为概念列表提供改进建议
        
        Args:
            concepts: 概念名称列表
            
        Returns:
            List[Dict]: 改进建议列表
        """
        improvements = []
        results = self.validate_concept_list(concepts)
        
        for concept, result in results.items():
            if not result.is_valid:
                improvements.append({
                    'concept': concept,
                    'issues': result.issues,
                    'suggestions': result.suggestions
                })
        
        return improvements
    
    def _check_compound_concept(self, concept_name: str) -> Optional[List[str]]:
        """检查是否为复合概念
        
        Args:
            concept_name: 概念名称
            
        Returns:
            Optional[List[str]]: 如果是复合概念，返回分解建议
        """
        for pattern in self.COMPOUND_PATTERNS:
            match = re.search(pattern, concept_name)
            if match:
                parts = [part.strip() for part in match.groups() if part.strip()]
                if len(parts) >= 2:
                    return [f"建议拆分为：{' + '.join(parts)}"]
        return None
    
    def _check_concept_length(self, concept_name: str) -> Optional[str]:
        """检查概念名称长度
        
        Args:
            concept_name: 概念名称
            
        Returns:
            Optional[str]: 如果长度不合适，返回问题描述
        """
        length = len(concept_name)
        min_len, max_len = self.IDEAL_LENGTH_RANGE
        
        if length < min_len:
            return f"概念名称过短（{length}字），建议更具体化"
        elif length > max_len:
            return f"概念名称过长（{length}字），建议简化"
        
        return None
    
    def _check_broad_concept(self, concept_name: str) -> Optional[str]:
        """检查是否为过于宽泛的概念
        
        Args:
            concept_name: 概念名称
            
        Returns:
            Optional[str]: 如果过于宽泛，返回问题描述
        """
        for keyword in self.BROAD_KEYWORDS:
            if keyword in concept_name:
                return f"概念过于宽泛，包含关键词：{keyword}"
        
        return None
    
    def _check_concept_format(self, concept_name: str) -> Optional[str]:
        """检查概念格式
        
        Args:
            concept_name: 概念名称
            
        Returns:
            Optional[str]: 如果格式不当，返回问题描述
        """
        # 检查是否包含不当字符
        if re.search(r'[？！。，；：""''（）【】]', concept_name):
            return "概念名称不应包含标点符号"
        
        # 检查是否为动词短语
        verb_patterns = [
            r'如何.+', r'怎样.+', r'学习.+', r'掌握.+', r'理解.+', r'使用.+'
        ]
        for pattern in verb_patterns:
            if re.match(pattern, concept_name):
                return "概念名称应为名词短语，不应为动词短语"
        
        return None


def validate_concept_map_quality(concept_map_data: Dict) -> Dict:
    """验证整个概念地图的质量
    
    Args:
        concept_map_data: 概念地图数据
        
    Returns:
        Dict: 质量报告
    """
    validator = ConceptValidator()
    
    # 收集所有概念
    all_concepts = []
    if 'main_concept' in concept_map_data:
        all_concepts.append(concept_map_data['main_concept'])
    
    if 'children' in concept_map_data:
        all_concepts.extend(concept_map_data['children'])
    
    # 验证概念质量
    validation_results = validator.validate_concept_list(all_concepts)
    quality_score = validator.get_quality_score(all_concepts)
    improvements = validator.suggest_improvements(all_concepts)
    
    return {
        'quality_score': quality_score,
        'total_concepts': len(all_concepts),
        'valid_concepts': sum(1 for r in validation_results.values() if r.is_valid),
        'invalid_concepts': sum(1 for r in validation_results.values() if not r.is_valid),
        'validation_results': validation_results,
        'improvements': improvements
    }