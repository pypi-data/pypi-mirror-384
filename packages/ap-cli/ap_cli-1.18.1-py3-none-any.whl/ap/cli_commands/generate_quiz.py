import yaml
import typer
import asyncio
import os
import re
import time
import random
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from ap.core.concept_map import ConceptMap, slugify
from ap.core.utils import call_deepseek_with_retry
from ap.core.settings import WORKSPACE_DIR
from ap.cli_commands.explain import analyze_document_structure


@dataclass
class ContentChunk:
    """内容块"""
    title: str
    content: str
    target_questions: int
    chunk_id: int


@dataclass
class GenerationResult:
    """生成结果"""
    chunk_id: int
    questions: List[Dict[str, Any]]
    generation_time: float
    error: str = None


class ParallelQuizGenerator:
    """并行测试题生成器"""
    
    def __init__(self, max_concurrent: int = 6):
        """
        初始化生成器
        
        Args:
            max_concurrent: 最大并发数，默认为6
        """
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)

    def extract_keywords(self, text: str) -> set:
        """
        从题目文本中提取关键词
        
        Args:
            text: 题目文本
            
        Returns:
            关键词集合
        """
        # 移除标点符号，转换为小写
        cleaned_text = re.sub(r'[^\w\s]', '', text.lower())
        # 分词并过滤短词
        words = [word for word in cleaned_text.split() if len(word) > 1]
        return set(words)

    def calculate_similarity(self, question1: Dict[str, Any], question2: Dict[str, Any]) -> float:
        """
        计算两个题目的相似度（使用Jaccard相似度）
        
        Args:
            question1: 第一个题目
            question2: 第二个题目
            
        Returns:
            相似度分数 (0-1)
        """
        text1 = question1.get('question', '')
        text2 = question2.get('question', '')
        
        keywords1 = self.extract_keywords(text1)
        keywords2 = self.extract_keywords(text2)
        
        if not keywords1 and not keywords2:
            return 0.0
        
        intersection = keywords1.intersection(keywords2)
        union = keywords1.union(keywords2)
        
        return len(intersection) / len(union) if union else 0.0

    def remove_duplicate_questions(self, questions: List[Dict[str, Any]], 
                                 similarity_threshold: float = 0.6) -> List[Dict[str, Any]]:
        """
        移除重复的题目
        
        Args:
            questions: 题目列表
            similarity_threshold: 相似度阈值，超过此值认为是重复题目
            
        Returns:
            去重后的题目列表
        """
        if not questions:
            return []
        
        unique_questions = []
        
        for current_question in questions:
            is_duplicate = False
            
            for existing_question in unique_questions:
                similarity = self.calculate_similarity(current_question, existing_question)
                if similarity > similarity_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_questions.append(current_question)
        
        return unique_questions

    def create_chunk_prompt(self, chunk: ContentChunk, concept_name: str) -> str:
        """为内容块创建生成提示"""
        return f"""基于以下内容，为概念 "{concept_name}" 的 "{chunk.title}" 部分生成 {chunk.target_questions} 道高质量的选择题。

内容：
{chunk.content}

要求：
1. 题目应覆盖这部分内容的关键知识点
2. 每道题有4个选项（A、B、C、D）
3. 只有一个正确答案
4. 选项分布要相对均匀
5. 题目难度适中，适合初学者
6. 使用中文

请严格按照以下YAML格式输出，不要包含任何代码块标记：

- question: "题目内容"
  options:
    A: "选项A内容"
    B: "选项B内容"
    C: "选项C内容"
    D: "选项D内容"
  answer: "A"
  explanation: "答案解释内容"

生成 {chunk.target_questions} 道题目："""

    async def generate_chunk_questions(self, chunk: ContentChunk, concept_name: str) -> GenerationResult:
        """为单个内容块生成题目"""
        async with self.semaphore:  # 控制并发数
            start_time = time.time()
            
            try:
                prompt = self.create_chunk_prompt(chunk, concept_name)
                
                # 使用项目统一的API调用函数
                def retry_callback(attempt, max_retries):
                    print(f"   块 {chunk.chunk_id}: 第 {attempt}/{max_retries} 次尝试...")
                
                # 将同步调用包装在异步执行中
                content = await asyncio.to_thread(
                    call_deepseek_with_retry,
                    messages=prompt,
                    model="deepseek-chat",
                    max_retries=3,
                    base_temperature=0.3,
                    max_tokens=4096,
                    retry_callback=retry_callback
                )
                
                # 解析YAML
                questions = yaml.safe_load(content)
                
                # 验证格式
                if not isinstance(questions, list):
                    raise ValueError(f"块 {chunk.chunk_id} 生成的内容不是列表格式")
                
                # 验证每个题目
                for i, q in enumerate(questions):
                    if not all(key in q for key in ['question', 'options', 'answer', 'explanation']):
                        raise ValueError(f"块 {chunk.chunk_id} 第 {i+1} 题格式不完整")
                
                generation_time = time.time() - start_time
                
                return GenerationResult(
                    chunk_id=chunk.chunk_id,
                    questions=questions,
                    generation_time=generation_time
                )
                
            except Exception as e:
                generation_time = time.time() - start_time
                return GenerationResult(
                    chunk_id=chunk.chunk_id,
                    questions=[],
                    generation_time=generation_time,
                    error=str(e)
                )

    def merge_and_optimize_results(self, results: List[GenerationResult]) -> List[Dict[str, Any]]:
        """合并结果并优化答案分布"""
        all_questions = []
        
        # 合并所有成功生成的题目
        for result in results:
            if result.error is None:
                all_questions.extend(result.questions)
        
        if not all_questions:
            raise ValueError("没有成功生成任何题目")
        
        # 去重处理
        all_questions = self.remove_duplicate_questions(all_questions)
        
        # 分析答案分布
        answer_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
        for q in all_questions:
            answer = q.get('answer', '')
            if answer in answer_counts:
                answer_counts[answer] += 1
        
        # 如果分布不均匀，进行调整
        total_questions = len(all_questions)
        target_per_option = total_questions / 4
        
        # 找出需要调整的题目
        adjustments_needed = {}
        for option, count in answer_counts.items():
            diff = count - target_per_option
            if abs(diff) > 1:  # 允许1题的误差
                adjustments_needed[option] = diff
        
        # 简单的答案重新分配（保持题目内容不变，只调整答案）
        if adjustments_needed:
            self._rebalance_answers(all_questions, adjustments_needed)
        
        return all_questions

    def _rebalance_answers(self, questions: List[Dict[str, Any]], adjustments: Dict[str, float]):
        """重新平衡答案分布"""
        # 找出过多和过少的选项
        excess_options = [opt for opt, diff in adjustments.items() if diff > 1]
        deficit_options = [opt for opt, diff in adjustments.items() if diff < -1]
        
        if not excess_options or not deficit_options:
            return
        
        # 简单策略：随机重新分配一些题目的答案
        for i, question in enumerate(questions):
            current_answer = question.get('answer', '')
            
            # 如果当前答案是过多的选项，考虑改为不足的选项
            if current_answer in excess_options and deficit_options:
                if random.random() < 0.3:  # 30%的概率进行调整
                    new_answer = random.choice(deficit_options)
                    
                    # 交换选项内容
                    options = question['options']
                    if current_answer in options and new_answer in options:
                        # 交换选项内容，使新答案成为正确答案
                        options[current_answer], options[new_answer] = options[new_answer], options[current_answer]
                        question['answer'] = new_answer

    async def generate_parallel_quiz(self, concept_name: str, content: str, 
                                   target_questions: int = 10) -> Dict[str, Any]:
        """
        并行生成测试题
        
        Args:
            concept_name: 概念名称
            content: 内容文本
            target_questions: 目标题目数量
            
        Returns:
            包含题目和统计信息的字典
        """
        print(f"🚀 开始并行生成 '{concept_name}' 的 {target_questions} 道测试题")
        
        start_time = time.time()
        
        # 根据题目数量决定分块策略
        if target_questions <= 5:
            # 少量题目，单块处理
            chunks = [ContentChunk(
                title="完整内容",
                content=content,
                target_questions=target_questions,
                chunk_id=0
            )]
        elif target_questions <= 12:
            # 中等数量，分为两块
            chunk_size = target_questions // 2
            remaining = target_questions % 2
            
            # 简单按内容长度分割
            words = content.split()
            mid_point = len(words) // 2
            
            chunks = [
                ContentChunk(
                    title="前半部分",
                    content=" ".join(words[:mid_point]),
                    target_questions=chunk_size + remaining,
                    chunk_id=0
                ),
                ContentChunk(
                    title="后半部分", 
                    content=" ".join(words[mid_point:]),
                    target_questions=chunk_size,
                    chunk_id=1
                )
            ]
        else:
            # 大量题目，多块处理（每块最多5题）
            max_questions_per_chunk = 5
            num_chunks = (target_questions + max_questions_per_chunk - 1) // max_questions_per_chunk
            
            words = content.split()
            chunk_size = len(words) // num_chunks
            
            chunks = []
            for i in range(num_chunks):
                start_idx = i * chunk_size
                end_idx = start_idx + chunk_size if i < num_chunks - 1 else len(words)
                
                questions_for_chunk = min(max_questions_per_chunk, 
                                        target_questions - len(chunks) * max_questions_per_chunk)
                if i == num_chunks - 1:  # 最后一块包含剩余题目
                    questions_for_chunk = target_questions - sum(c.target_questions for c in chunks)
                
                chunks.append(ContentChunk(
                    title=f"第 {i+1} 部分",
                    content=" ".join(words[start_idx:end_idx]),
                    target_questions=questions_for_chunk,
                    chunk_id=i
                ))
        
        print(f"✂️  内容已切分为 {len(chunks)} 个块")
        for chunk in chunks:
            print(f"   块 {chunk.chunk_id + 1}: {chunk.title} ({chunk.target_questions} 题)")
        
        # 并行生成
        print(f"⚡ 开始并行生成 (最大并发: {self.max_concurrent})...")
        
        tasks = [
            self.generate_chunk_questions(chunk, concept_name) 
            for chunk in chunks
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"❌ 块 {i} 生成失败: {result}")
            else:
                valid_results.append(result)
                if result.error:
                    print(f"❌ 块 {result.chunk_id} 生成失败: {result.error}")
                else:
                    print(f"✅ 块 {result.chunk_id} 生成成功: {len(result.questions)} 题 ({result.generation_time:.1f}s)")
        
        # 合并和优化
        print("🔄 合并结果并优化答案分布...")
        final_questions = self.merge_and_optimize_results(valid_results)
        
        total_time = time.time() - start_time
        
        # 生成报告
        successful_chunks = len([r for r in valid_results if r.error is None])
        avg_chunk_time = sum(r.generation_time for r in valid_results if r.error is None) / max(1, successful_chunks)
        
        return {
            "questions": final_questions,
            "generation_stats": {
                "total_time": total_time,
                "target_questions": target_questions,
                "actual_questions": len(final_questions),
                "chunks_processed": len(chunks),
                "successful_chunks": successful_chunks,
                "average_chunk_time": avg_chunk_time,
                "parallel_efficiency": avg_chunk_time / total_time if total_time > 0 else 0
            }
        }


def create_quiz_prompt(concept: str, explanation_content: str,
                       num_questions: int) -> str:
    """构建生成测验的 Prompt"""
    return f"""基于以下解释文档，为概念 "{concept}" 生成 {num_questions} 道高质量的选择题。

解释文档内容：
{explanation_content}

要求：
1. 题目应覆盖文档中的关键知识点
2. 每道题有4个选项（A、B、C、D）
3. 只有一个正确答案
4. 选项分布要均匀（避免所有答案都是A或B）
5. 题目难度适中，适合初学者
6. 使用中文

**YAML格式要求（严格遵守）：**
- 使用2个空格缩进，不要使用Tab
- 所有文本内容必须用双引号包围
- 如果文本包含双引号，请使用单引号包围整个文本
- 每个题目之间用空行分隔
- 选项必须严格按照A、B、C、D顺序
- answer字段只能是"A"、"B"、"C"或"D"

请严格按照以下YAML格式输出，不要包含任何代码块标记：

- question: "题目内容"
  options:
    A: "选项A内容"
    B: "选项B内容"
    C: "选项C内容"
    D: "选项D内容"
  answer: "A"
  explanation: "答案解释内容"

- question: "第二道题目内容"
  options:
    A: "选项A内容"
    B: "选项B内容"
    C: "选项C内容"
    D: "选项D内容"
  answer: "B"
  explanation: "答案解释内容"

**重要提醒：**
1. 直接输出YAML内容，不要使用```yaml```代码块包装
2. 确保每个字段都有值，不要留空
3. 所有冒号后面必须有一个空格
4. 检查缩进是否一致（使用2个空格）
5. 确保没有多余的空格或特殊字符

生成 {num_questions} 道题目："""


def generate_quiz_internal(
    concept: str,
    **kwargs
):
    """
    基于解释文档生成测验题目（内部函数）

    Args:
        concept: 要生成测验的概念名称
        **kwargs: 配置参数
            - num_questions: int = None, 指定题目数量（默认为智能分析）
            - mode: str = "auto", 生成模式：auto（智能分析）或 fixed（固定模式）
            - max_tokens: int = 8192, 最大输出长度
            - use_parallel: bool = True, 是否使用并行生成
            - verbose: bool = False, 是否显示详细输出
    """
    # 提取参数，设置默认值
    num_questions = kwargs.get('num_questions', None)
    mode = kwargs.get('mode', "auto")
    max_tokens = kwargs.get('max_tokens', 8192)
    use_parallel = kwargs.get('use_parallel', True)
    verbose = kwargs.get('verbose', False)
    
    if verbose:
        print(f"[GENERATE_QUIZ] 开始生成测验题目: {concept}")
        print(f"[GENERATE_QUIZ] 参数: num_questions={num_questions}, mode={mode}, use_parallel={use_parallel}")
    try:
        if verbose:
            print(f"[GENERATE_QUIZ] 创建概念地图实例")
        # 创建概念地图实例
        concept_map = ConceptMap()

        # 处理概念名称
        if '/' in concept:
            topic_slug, concept_part = concept.split('/', 1)
            concept_slug = slugify(concept_part)
        else:
            concept_slug = slugify(concept)
            # 如果没有提供主题，则需要查找
            topic_slug = concept_map.get_topic_by_concept(concept_slug)
            if not topic_slug:
                print(f"错误：找不到概念 '{concept}' 所属的主题。")
                return

        # 构造解释文档路径
        explanation_dir = WORKSPACE_DIR / topic_slug / "explanation"
        explanation_file = explanation_dir / f"{concept_slug}.md"

        if not explanation_file.exists():
            print(f"错误：找不到解释文档 {explanation_file}")
            print("请先运行 'ap e' 命令生成解释文档")
            return

        # 读取解释文档内容
        with open(explanation_file, 'r', encoding='utf-8') as f:
            explanation_content = f.read()

        # 智能分析题目数量
        if num_questions is None and mode == "auto":
            analysis = analyze_document_structure(explanation_content)
            num_questions = analysis['recommended_questions']
            print(
                f"📊 智能分析: 发现 {analysis['section_count']} 个主要知识点，"
                f"建议生成 {num_questions} 道题目"
            )

        # 如果仍然没有指定数量，使用默认值
        if num_questions is None:
            num_questions = 25

        # 确保按主题组织的 quizzes 目录存在
        quizzes_dir = WORKSPACE_DIR / topic_slug / "quizzes"
        quizzes_dir.mkdir(parents=True, exist_ok=True)

        # 构造输出文件路径
        quiz_file = quizzes_dir / f"{concept_slug}.yml"

        # 选择生成策略
        if use_parallel and num_questions >= 5:
            print(f"🚀 使用并行生成策略")
            
            # 使用并行生成器
            async def run_parallel_generation():
                generator = ParallelQuizGenerator(max_concurrent=6)
                
                result = await generator.generate_parallel_quiz(
                    concept_name=concept,
                    content=explanation_content,
                    target_questions=num_questions
                )
                return result
            
            # 运行异步生成
            result = asyncio.run(run_parallel_generation())
            quiz_data = result["questions"]
            
            # 显示性能统计
            stats = result["generation_stats"]
            print(f"⚡ 并行生成完成:")
            print(f"   总耗时: {stats['total_time']:.1f}秒")
            print(f"   生成题目: {stats['actual_questions']}/{stats['target_questions']}")
            print(f"   并行效率: {stats['parallel_efficiency']:.1%}")
            print(f"   成功块数: {stats['successful_chunks']}/{stats['chunks_processed']}")
            
        else:
            print(f"🐌 使用传统单线程生成 (题目数较少或禁用并行)")
            
            # 使用原有的单线程生成逻辑
            quiz_content = call_deepseek_with_retry(
                messages=create_quiz_prompt(
                    concept, explanation_content, num_questions
                ),
                model="deepseek-chat",
                max_tokens=max_tokens,
                max_retries=3,
                base_temperature=0.5
            )

            # 尝试解析YAML
            quiz_data = yaml.safe_load(quiz_content)

        # 验证数据结构
        if not isinstance(quiz_data, list):
            error_type = type(quiz_data).__name__
            raise ValueError(f"生成的内容不是列表格式，而是 {error_type}")

        if len(quiz_data) == 0:
            raise ValueError("生成的题目列表为空")

        # 验证每个题目的结构
        for i, question in enumerate(quiz_data):
            if not isinstance(question, dict):
                raise ValueError(f"第 {i+1} 题不是字典格式")

            required_fields = ['question', 'options', 'answer', 'explanation']
            for field in required_fields:
                if field not in question:
                    raise ValueError(f"第 {i+1} 题缺少必需字段: {field}")

            # 验证选项格式
            options = question.get('options', {})
            if not isinstance(options, dict):
                raise ValueError(f"第 {i+1} 题的选项不是字典格式")

            expected_options = ['A', 'B', 'C', 'D']
            missing_options = [opt for opt in expected_options
                               if opt not in options]
            if missing_options:
                options_str = ', '.join(missing_options)
                raise ValueError(f"第 {i+1} 题缺少选项: {options_str}")

            # 验证答案格式
            answer = question.get('answer', '')
            if answer not in expected_options:
                raise ValueError(
                    f"第 {i+1} 题的答案 '{answer}' 不在有效选项中"
                )

        print(f"✅ YAML格式正确，成功生成 {len(quiz_data)} 道题目")

        # 解析生成的YAML内容进行质量检查
        try:
            # 导入质量检查器
            from ap.core.quiz_quality_checker import QuizQualityChecker
            quality_checker = QuizQualityChecker()

            # 分析答案分布
            analysis_result = quality_checker.analyze_answer_distribution(
                quiz_data
            )

            if "error" not in analysis_result:
                quality_score = analysis_result.get('quality_score', 0)
                
                print(f"🎯 答案分布质量检查:")
                distribution = analysis_result.get('distribution', {})
                for option, count in distribution.items():
                    percentage = (count / len(quiz_data)) * 100
                    print(f"   选项 {option}: {count} 题 ({percentage:.1f}%)")
                print(f"   质量分数: {quality_score:.1f}/100")

                # 如果质量分数低于80，进行静默答案随机化
                if quality_score < 80:
                    print(f"🔄 质量分数偏低，正在优化答案分布...")
                    shuffled_quiz, shuffle_info = quality_checker.shuffle_quiz_answers(
                        quiz_data
                    )

                    # 重新分析随机化后的分布
                    new_analysis = quality_checker.analyze_answer_distribution(
                        shuffled_quiz
                    )

                    # 使用随机化后的数据
                    quiz_data = shuffled_quiz
                    analysis_result = new_analysis
                    
                    new_quality_score = new_analysis.get('quality_score', 0)
                    print(f"✅ 答案分布优化完成，新质量分数: {new_quality_score:.1f}/100")

            # 将处理后的数据转换回YAML格式
            quiz_content = yaml.dump(
                quiz_data, default_flow_style=False,
                allow_unicode=True, sort_keys=False
            )

        except Exception as e:
            print(f"⚠️  质量检查过程中出现问题: {e}")
            # 静默处理质量检查错误，使用原始数据
            quiz_content = yaml.dump(
                quiz_data, default_flow_style=False,
                allow_unicode=True, sort_keys=False
            )

        # 保存到文件
        with open(quiz_file, 'w', encoding='utf-8') as f:
            f.write(quiz_content)

        print(f"✅ 成功: '{concept}' 的 {len(quiz_data)} 道测验题已生成在 {quiz_file}")

    except Exception as e:
        print(f"❌ 生成测验时发生严重错误: {str(e)}")
        raise


def generate_quiz(
    concept: str,
    num_questions: int = typer.Option(
        None,
        "--num-questions",
        "-n",
        help="指定题目数量（默认为智能分析）",
        min=3,
        max=50
    ),
    mode: str = typer.Option(
        "auto",
        "--mode",
        help="生成模式：auto（智能分析）或 fixed（固定模式）"
    ),
    max_tokens: int = typer.Option(
        8192,  # chat模型默认4K，最大8K
        "--max-tokens",
        help="最大输出长度（默认8K，chat模型最大8K）",
        min=1000,
        max=8192
    )
):
    """
    基于解释文档生成测验题目

    Args:
        concept: 要生成测验的概念名称
        num_questions: 题目数量（可选，默认智能分析）
        mode: 生成模式 (auto/fixed，默认auto)
        max_tokens: 最大输出长度（默认8K，chat模型最大8K）
    """
    # 调用内部版本，避免typer.Option序列化问题
    return generate_quiz_internal(
        concept=concept,
        num_questions=num_questions,
        mode=mode,
        max_tokens=max_tokens
    )
