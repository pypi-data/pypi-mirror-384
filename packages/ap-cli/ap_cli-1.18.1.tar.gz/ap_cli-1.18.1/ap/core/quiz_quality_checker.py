"""
测验质量检查模块

该模块用于验证AI生成的测验题目质量，确保：
1. 正确答案在各个位置的分布符合均匀随机分布
2. 正确答案为选项2的概率不超过随机分布预期值
3. 提供答案位置随机化功能
"""

import logging
import random
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# 配置日志
logger = logging.getLogger(__name__)


class QuizQualityChecker:
    """测验质量检查器"""

    def __init__(self, tolerance: float = 0.1, quality_threshold: float = 80.0):
        """
        初始化质量检查器
        
        Args:
            tolerance: 允许的偏差范围 (默认0.1)
            quality_threshold: 质量分数阈值 (默认80.0)
        """
        self.expected_probability = 0.25  # 4选1的期望概率
        self.tolerance = tolerance
        self.quality_threshold = quality_threshold
        
        logger.info(f"初始化质量检查器: tolerance={tolerance}, threshold={quality_threshold}")

    def check_and_improve_quiz(self, quiz_data: List[Dict], max_attempts: int = 3) -> Tuple[List[Dict], Dict]:
        """
        检查并改进测验质量的主要方法
        
        Args:
            quiz_data: 测验数据
            max_attempts: 最大尝试次数
            
        Returns:
            Tuple[改进后的测验数据, 详细报告]
        """
        try:
            logger.info(f"开始质量检查，题目数量: {len(quiz_data)}")
            
            # 初始分析
            initial_analysis = self.analyze_answer_distribution(quiz_data)
            if "error" in initial_analysis:
                logger.error(f"初始分析失败: {initial_analysis['error']}")
                return quiz_data, initial_analysis
            
            initial_score = initial_analysis.get("quality_score", 0)
            logger.info(f"初始质量分数: {initial_score}")
            
            # 如果质量已经足够好，直接返回
            if initial_score >= self.quality_threshold:
                logger.info("质量已达标，无需改进")
                return quiz_data, {
                    "status": "success",
                    "improved": False,
                    "initial_analysis": initial_analysis,
                    "final_analysis": initial_analysis,
                    "attempts": 0
                }
            
            # 尝试改进
            current_quiz = quiz_data
            best_quiz = quiz_data
            best_score = initial_score
            
            for attempt in range(max_attempts):
                logger.info(f"尝试改进 {attempt + 1}/{max_attempts}")
                
                # 随机化答案位置
                shuffled_quiz, shuffle_stats = self.shuffle_quiz_answers(current_quiz)
                
                # 分析改进后的质量
                new_analysis = self.analyze_answer_distribution(shuffled_quiz)
                if "error" in new_analysis:
                    logger.warning(f"第{attempt + 1}次改进分析失败: {new_analysis['error']}")
                    continue
                
                new_score = new_analysis.get("quality_score", 0)
                logger.info(f"第{attempt + 1}次改进后分数: {new_score}")
                
                # 保存最佳结果
                if new_score > best_score:
                    best_quiz = shuffled_quiz
                    best_score = new_score
                    logger.info(f"找到更好的结果，分数: {new_score}")
                
                # 如果达到阈值，停止尝试
                if new_score >= self.quality_threshold:
                    logger.info(f"质量达标，停止改进")
                    break
                
                current_quiz = shuffled_quiz
            
            final_analysis = self.analyze_answer_distribution(best_quiz)
            
            return best_quiz, {
                "status": "success",
                "improved": best_score > initial_score,
                "initial_analysis": initial_analysis,
                "final_analysis": final_analysis,
                "attempts": max_attempts,
                "improvement": best_score - initial_score
            }
            
        except Exception as e:
            logger.error(f"质量检查过程中发生错误: {str(e)}", exc_info=True)
            return quiz_data, {
                "status": "error",
                "error": str(e),
                "improved": False
            }

    def analyze_answer_distribution(self, quiz_data: List[Dict]) -> Dict:
        """
        分析测验题目中正确答案的位置分布

        Args:
            quiz_data: 测验题目数据列表

        Returns:
            分析结果字典
        """
        if not quiz_data:
            return {"error": "测验数据为空"}

        answer_positions = []
        invalid_questions = []

        for i, question in enumerate(quiz_data):
            if not all(key in question for key in ['question', 'options', 'answer']):
                invalid_questions.append(f"题目{i+1}: 缺少必要字段")
                continue

            correct_answer = question['answer']
            options = question['options']

            # 处理不同的选项格式
            if isinstance(options, dict):
                # 选项是字典格式 {"A": "选项内容", "B": "选项内容", ...}
                if correct_answer in options:
                    # 将字母转换为位置 (A=1, B=2, C=3, D=4)
                    position = ord(correct_answer.upper()) - ord('A') + 1
                    if 1 <= position <= 4:
                        answer_positions.append(position)
                    else:
                        invalid_questions.append(f"题目{i+1}: 答案位置超出范围 ({correct_answer})")
                else:
                    invalid_questions.append(f"题目{i+1}: 正确答案不在选项中 ({correct_answer})")
            elif isinstance(options, list):
                # 选项是列表格式 ["选项1", "选项2", "选项3", "选项4"]
                try:
                    position = options.index(correct_answer) + 1  # 1-based index
                    answer_positions.append(position)
                except ValueError:
                    invalid_questions.append(f"题目{i+1}: 正确答案不在选项中")
            else:
                invalid_questions.append(f"题目{i+1}: 选项格式不支持")

        if not answer_positions:
            return {
                "error": "未找到有效的题目数据",
                "invalid_questions": invalid_questions
            }

        # 统计各位置的分布
        position_counts = Counter(answer_positions)
        total_questions = len(answer_positions)

        # 计算各位置的概率
        position_probabilities = {
            pos: count / total_questions
            for pos, count in position_counts.items()
        }

        # 检查是否符合均匀分布
        uniform_check = self._check_uniform_distribution(
            position_probabilities, total_questions)

        # 特别检查选项2的概率
        option2_probability = position_probabilities.get(2, 0)
        option2_check = option2_probability <= (
            self.expected_probability + self.tolerance)

        return {
            "total_questions": total_questions,
            "valid_questions": len(answer_positions),
            "invalid_questions": invalid_questions,
            "position_counts": dict(position_counts),
            "position_probabilities": position_probabilities,
            "uniform_distribution_check": uniform_check,
            "option2_probability": option2_probability,
            "option2_check_passed": option2_check,
            "quality_score": self._calculate_quality_score(position_probabilities),
            "recommendations": self._generate_recommendations(position_probabilities)
        }

    def _check_uniform_distribution(self, probabilities: Dict[int, float], total_questions: int) -> Dict:
        """检查是否符合均匀分布"""
        # 计算卡方检验统计量
        expected_count = total_questions / 4
        chi_square = 0

        for position in range(1, 5):
            observed_count = probabilities.get(position, 0) * total_questions
            chi_square += (observed_count -
                           expected_count) ** 2 / expected_count

        # 简化的判断：如果所有位置的概率都在期望值±容差范围内，认为符合均匀分布
        is_uniform = all(
            abs(probabilities.get(pos, 0) -
                self.expected_probability) <= self.tolerance
            for pos in range(1, 5)
        )

        return {
            "is_uniform": is_uniform,
            "chi_square": chi_square,
            "deviations": {
                pos: abs(probabilities.get(pos, 0) - self.expected_probability)
                for pos in range(1, 5)
            }
        }

    def _calculate_quality_score(self, probabilities: Dict[int, float]) -> float:
        """计算质量分数 (0-100)"""
        # 计算与理想均匀分布的偏差
        total_deviation = sum(
            abs(probabilities.get(pos, 0) - self.expected_probability)
            for pos in range(1, 5)
        )

        # 转换为质量分数 (偏差越小，分数越高)
        max_possible_deviation = 4 * self.expected_probability  # 最大可能偏差
        quality_score = max(
            0, 100 * (1 - total_deviation / max_possible_deviation))

        return round(quality_score, 2)

    def _generate_recommendations(self, probabilities: Dict[int, float]) -> List[str]:
        """生成改进建议"""
        recommendations = []

        # 检查各位置的偏差
        for position in range(1, 5):
            prob = probabilities.get(position, 0)
            deviation = abs(prob - self.expected_probability)

            if deviation > self.tolerance:
                if prob > self.expected_probability:
                    recommendations.append(
                        f"位置{position}的正确答案过多 ({prob:.2%})，建议减少")
                else:
                    recommendations.append(
                        f"位置{position}的正确答案过少 ({prob:.2%})，建议增加")

        # 特别检查选项2
        option2_prob = probabilities.get(2, 0)
        if option2_prob > self.expected_probability + self.tolerance:
            recommendations.append(f"选项2作为正确答案的频率过高 ({option2_prob:.2%})，建议调整")

        if not recommendations:
            recommendations.append("答案分布良好，符合随机分布要求")

        return recommendations

    def shuffle_quiz_answers(self, quiz_data: List[Dict]) -> Tuple[List[Dict], Dict]:
        """
        随机化测验题目的正确答案位置，使用更智能的分布策略

        Args:
            quiz_data: 原始测验题目数据

        Returns:
            Tuple[随机化后的测验数据, 统计信息]
        """
        if not quiz_data:
            return quiz_data, {"error": "测验数据为空"}

        shuffled_quiz = []
        position_changes = []
        target_positions = []
        
        # 计算目标分布：尽量均匀分配到4个位置
        total_questions = len(quiz_data)
        questions_per_position = total_questions // 4
        remaining_questions = total_questions % 4
        
        # 生成目标位置列表
        for position in range(1, 5):
            count = questions_per_position + (1 if position <= remaining_questions else 0)
            target_positions.extend([position] * count)
        
        # 随机打乱目标位置
        random.shuffle(target_positions)

        for i, question in enumerate(quiz_data):
            if not all(key in question for key in ['question', 'options', 'answer']):
                shuffled_quiz.append(question)
                continue

            # 复制题目数据
            new_question = question.copy()
            options = question['options']
            correct_answer = question['answer']

            # 处理不同的选项格式
            if isinstance(options, dict):
                # 字典格式 {"A": "选项内容", "B": "选项内容", ...}
                if correct_answer not in options:
                    shuffled_quiz.append(question)
                    continue
                
                current_position = ord(correct_answer.upper()) - ord('A') + 1
                target_position = target_positions[i] if i < len(target_positions) else random.randint(1, 4)
                
                if current_position != target_position:
                    # 创建新的选项字典
                    option_keys = list(options.keys())
                    option_values = list(options.values())
                    
                    # 找到当前正确答案的值
                    correct_value = options[correct_answer]
                    
                    # 将正确答案移动到目标位置
                    target_key = chr(ord('A') + target_position - 1)
                    
                    # 交换选项内容
                    if target_key in options:
                        # 交换两个选项的内容
                        current_key = correct_answer
                        current_value = options[current_key]
                        target_value = options[target_key]
                        
                        new_options = options.copy()
                        new_options[current_key] = target_value
                        new_options[target_key] = current_value
                        
                        new_question['options'] = new_options
                        new_question['answer'] = target_key
                        
                        position_changes.append({
                            'question_index': i + 1,
                            'old_position': current_position,
                            'new_position': target_position,
                            'old_answer': current_key,
                            'new_answer': target_key
                        })
                
            elif isinstance(options, list):
                # 列表格式 ["选项1", "选项2", "选项3", "选项4"]
                try:
                    current_position = options.index(correct_answer) + 1
                    target_position = target_positions[i] if i < len(target_positions) else random.randint(1, 4)
                    
                    if current_position != target_position:
                        new_options = options.copy()
                        current_index = current_position - 1
                        target_index = target_position - 1
                        
                        # 交换选项位置
                        new_options[current_index], new_options[target_index] = \
                            new_options[target_index], new_options[current_index]
                        
                        new_question['options'] = new_options
                        # 答案内容不变，但位置改变了
                        
                        position_changes.append({
                            'question_index': i + 1,
                            'old_position': current_position,
                            'new_position': target_position
                        })
                        
                except ValueError:
                    # 如果找不到正确答案，保持原样
                    pass

            shuffled_quiz.append(new_question)

        # 统计信息
        stats = {
            'total_questions': len(quiz_data),
            'shuffled_questions': len(position_changes),
            'shuffle_rate': len(position_changes) / len(quiz_data) if quiz_data else 0,
            'position_changes': position_changes,
            'target_distribution': {
                i: target_positions.count(i) for i in range(1, 5)
            }
        }

        return shuffled_quiz, stats

    def generate_quality_report(self, analysis_result: Dict, concept: str) -> str:
        """生成质量检查报告"""
        report_lines = [
            f"测验质量检查报告 - {concept}",
            "=" * 50,
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"📊 基本统计:",
            f"  总题目数: {analysis_result.get('total_questions', 0)}",
            f"  质量分数: {analysis_result.get('quality_score', 0)}/100",
            "",
            f"📍 答案位置分布:",
        ]

        position_counts = analysis_result.get('position_counts', {})
        position_probs = analysis_result.get('position_probabilities', {})

        for position in range(1, 5):
            count = position_counts.get(position, 0)
            prob = position_probs.get(position, 0)
            expected = self.expected_probability
            status = "✅" if abs(prob - expected) <= self.tolerance else "❌"

            report_lines.append(
                f"  位置{position}: {count}题 ({prob:.1%}) {status}")

        report_lines.extend([
            "",
            f"🎯 均匀分布检查:",
            f"  符合均匀分布: {'✅ 是' if analysis_result.get('uniform_distribution_check', {}).get('is_uniform', False) else '❌ 否'}",
            "",
            f"🔍 选项2特别检查:",
            f"  选项2概率: {analysis_result.get('option2_probability', 0):.1%}",
            f"  检查通过: {'✅ 是' if analysis_result.get('option2_check_passed', False) else '❌ 否'}",
            "",
            f"💡 改进建议:",
        ])

        recommendations = analysis_result.get('recommendations', [])
        for rec in recommendations:
            report_lines.append(f"  • {rec}")

        return "\n".join(report_lines)

    def save_quality_report(self, report: str, concept_slug: str, topic_slug: str, workspace_dir: Path):
        """保存质量检查报告"""
        reports_dir = workspace_dir / topic_slug / "quality_reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = reports_dir / f"{concept_slug}_quality_{timestamp}.txt"

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        return report_file
