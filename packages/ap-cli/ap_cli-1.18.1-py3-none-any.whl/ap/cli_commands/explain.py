from ap.core.concept_map import ConceptMap, slugify
from ap.core.utils import call_deepseek_api
from ap.core.settings import WORKSPACE_DIR


def create_explanation_prompt(concept: str) -> str:
    """构建生成解释的 Prompt"""
    return f"""请为以下概念生成一份详细的、适合初学者的中文解释文档：

概念：{concept}

文档应包含：
1.  **核心定义**：用简洁的语言解释这个概念是什么。
2.  **关键特征**：列出并解释该概念的主要特点或属性。
3.  **简单类比**：使用一个或多个生活中的例子或类比来帮助理解。
4.  **代码示例**（如果适用）：如果概念与编程相关，提供一个清晰、简洁、可运行的代码示例，并附上详细的注释。
5.  **常见问题**：提出2-3个关于该概念的常见问题，并给出解答。

请使用 Markdown 格式，确保结构清晰、排版整洁。"""


def analyze_document_structure(content: str) -> dict:
    """分析文档结构，返回建议的题目数量"""
    lines = content.split('\n')
    section_count = 0
    subsection_count = 0
    code_blocks = 0
    examples = 0
    in_code_block = False

    for line in lines:
        line = line.strip()
        # 统计主要章节（# 和 ##）
        if line.startswith('##'):
            subsection_count += 1
        elif line.startswith('#'):
            section_count += 1
        # 改进代码块检测：跟踪代码块状态
        elif line.startswith('```'):
            if not in_code_block:
                code_blocks += 1
                in_code_block = True
            else:
                in_code_block = False
        # 改进示例识别：更精确的关键词匹配
        elif not in_code_block and any(
                keyword in line.lower() 
                for keyword in ['例如：', '示例：', 'example:', '举例：', '比如：', 
                                '例子：', '实例：', '案例：', '演示：']
        ):
            examples += 1

    # 计算总知识点数量
    total_knowledge_points = (section_count + subsection_count + 
                              code_blocks + examples)

    # 题目数量推荐算法：与知识点数量保持一致
    if total_knowledge_points <= 3:
        recommended = 3  # 最少3道题
    else:
        # 题目数量应该与知识点数量匹配，确保充分覆盖
        recommended = total_knowledge_points

    return {
        'section_count': total_knowledge_points,  # 返回总知识点数量
        'recommended_questions': recommended,
        'details': {
            'main_sections': section_count,
            'subsections': subsection_count,
            'code_blocks': code_blocks,
            'examples': examples
        }
    }


def explain(
    concept: str,
    verbose: bool = False,
    force_regenerate: bool = False
):
    """
    生成概念的详细解释文档

    Args:
        concept: 要解释的概念名称
        verbose: bool = False, 是否显示详细输出
        force_regenerate: bool = False, 是否强制重新生成
    """
    if verbose:
        print(f"[EXPLAIN] 开始生成概念解释: {concept}")
    
    try:
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

        # 构造输出文件路径 - 按主题组织
        explanation_dir = WORKSPACE_DIR / topic_slug / "explanation"
        explanation_dir.mkdir(parents=True, exist_ok=True)

        explanation_file = explanation_dir / f"{concept_slug}.md"

        # 使用抽象的DeepSeek调用函数（推理模式）
        explanation_content = call_deepseek_api(
            messages=create_explanation_prompt(concept),
            model="deepseek-reasoner",
            temperature=0.7,
            max_tokens=32768  # 32K 默认长度
        )

        # 保存到文件
        with open(explanation_file, 'w', encoding='utf-8') as f:
            f.write(explanation_content)

        print(f"成功为 \"{concept}\" 生成解释文档，已保存至 {explanation_file}")

    except Exception as e:
        print(f"生成解释文档时发生错误: {str(e)}")
        raise
