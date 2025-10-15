import json
import re

import typer

from ap.core.concept_map import ConceptMap, slugify
from ap.core.utils import call_deepseek_api


def create_concept_map_prompt(topic: str,
                              existing_concepts: list = None) -> str:
    """创建用于生成学习地图的提示词"""
    existing_concepts_text = ""
    if existing_concepts:
        existing_concepts_text = (
            f"\n\n已存在的概念（请避免重复）：\n{', '.join(existing_concepts)}"
        )

    return f"""请为以下主题设计一个符合认知规律的层次化学习结构。

认知规律原则：
1. 🧠 认知负荷理论：将复杂主题分解为若干学习模块，每个模块包含适量核心概念，避免信息过载。
2. 🔗 知识建构理论：概念之间要有清晰的逻辑递进关系，从基础到应用。
3. 📚 布鲁姆分类法：按照记忆→理解→应用→分析的认知层次组织概念。
4. 🎯 同类聚合原则：相关概念归为一组，便于形成知识网络。

层次化结构要求：
- 概念粒度：每个概念学习时间30-60分钟。
- 命名规范：简洁明确，避免复合词汇。
- **核心要求**：请根据主题的复杂度和内在逻辑，自主决定模块和概念的数量，不必拘泥于固定数量。请务必避免生成统一数量的概念，例如所有模块都包含相同数量的概念。

质量标准（通用，避免针对具体主题的特例化）：
- 覆盖性：每个模块需覆盖该类别的典型成员与基础变体，避免明显的基础概念缺失。
- 完整性：避免重复或过于笼统的概念名称，确保模块描述与概念内容一致。
- 差异化：不同模块的概念数可因复杂度与重要性而不同，避免机械统一。
- 一致性：术语与层级结构保持前后一致，便于形成稳固的知识网络。

生成与自检流程（仅用于生成过程，最终只输出JSON）：
1) 先拟定模块与概念清单，遵循以上原则。
2) 对每个模块进行自检：检查是否存在显著遗漏的基础概念或该类别的典型成员；如发现遗漏，请补充至相应模块。
3) 完成自检后，仅输出最终的有效 JSON，不要附加说明文字。

主题: {topic}{existing_concepts_text}

**重要提示**：以下JSON示例仅用于展示期望的格式，其内部的模块和概念数量是虚构的，请勿模仿。请根据实际主题的需要，灵活调整模块和概念的数量。不同模块的概念数量可以不同，请避免所有模块概念数量完全一致。
{{
  "main_concept": "主题名称",
  "learning_modules": [
    {{
      "module_name": "模块1名称",
      "description": "模块简要说明",
      "concepts": [
        "概念示例"
      ]
    }},
    {{
      "module_name": "模块2名称", 
      "description": "模块简要说明",
      "concepts": [
        "概念A",
        "概念B",
        "概念C"
      ]
    }}
  ]
}}
"""


def generate_map(topic: str, model: str = "deepseek-chat"):
    """
    生成学习地图 - 将宏观主题拆解为结构化学习路径

    Args:
        topic: 要学习的主题名称，例如 "Python核心语法"
    """
    if not topic.strip():
        typer.echo("错误：请提供要学习的主题名称", err=True)
        raise typer.Exit(1)

    typer.echo(f"🗺️  正在为主题 '{topic}' 生成学习地图...")

    try:
        # 使用抽象的DeepSeek调用函数
        content = call_deepseek_api(
            messages=create_concept_map_prompt(topic),
            model=model,
            system_message=(
                "你是一名擅长设计层次化学习结构的助手。"
                "请根据主题复杂度为不同模块分配不同数量的概念；"
                "严禁所有模块概念数量完全一致；"
                "概念命名简洁明确，结构清晰；"
                "最终只输出严格有效的 JSON，不要输出任何解释或代码块标记；"
                "JSON 中不允许注释、尾逗号或多余逗号；键与字符串必须使用双引号。"
            ),
            max_tokens=4096,
            temperature=0.7
        )

        # 尝试解析JSON（包含健壮的回退策略）
        def _try_parse_json(text: str):
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                # 简单清理常见尾逗号错误
                cleaned = re.sub(r",\s*}\s*$", "}", text)
                cleaned = re.sub(r",\s*\]", "]", cleaned)
                try:
                    return json.loads(cleaned)
                except json.JSONDecodeError:
                    return None

        map_data = _try_parse_json(content)
        if map_data is None:
            # 尝试提取JSON片段
            json_match = re.search(r"\{[\s\S]*\}", content)
            if json_match:
                map_data = _try_parse_json(json_match.group())

        if map_data is None:
            # 作为最后回退：请求模型将文本转换为严格JSON
            typer.echo("⚠️  首次解析失败，尝试进行格式化回退...")
            reformulated = call_deepseek_api(
                messages=(
                    "请将以下文本内容严格转换为 JSON（仅输出JSON，不要添加任何说明），"
                    "JSON 必须包含键 'main_concept' 和 'learning_modules'，"
                    "其中 'learning_modules' 为数组，数组元素包含 'module_name'、'description' 和 'concepts'（字符串数组）。\n\n"
                    f"原始文本：\n{content}"
                ),
                model=model,
                system_message=(
                    "仅输出严格有效的 JSON；不允许注释、代码块标记或多余文本"
                ),
                max_tokens=4096,
                temperature=0.2
            )

            map_data = _try_parse_json(reformulated)
            if map_data is None:
                json_match = re.search(r"\{[\s\S]*\}", reformulated)
                if json_match:
                    map_data = _try_parse_json(json_match.group())

        if map_data is None:
            typer.echo("错误：AI返回的内容不是有效的JSON格式", err=True)
            typer.echo(f"AI返回内容：{content}", err=True)
            raise typer.Exit(1)

        # 验证数据结构
        if 'main_concept' not in map_data or 'learning_modules' not in map_data:
            typer.echo("错误：AI返回的数据结构不完整", err=True)
            raise typer.Exit(1)

        # 展示层次化结构
        typer.echo("📚 生成的层次化学习结构:")
        typer.echo(f"主题: {map_data['main_concept']}")

        all_concepts = []
        for module in map_data['learning_modules']:
            typer.echo(
                f"  📂 {module['module_name']} ({len(module['concepts'])}个概念)")
            typer.echo(f"     {module['description']}")
            for concept in module['concepts']:
                typer.echo(f"     • {concept}")
                all_concepts.append(concept)
            typer.echo("")

        # 处理主概念
        main_concept_name = map_data['main_concept']
        main_concept_id = slugify(main_concept_name)

        # 创建概念地图管理器
        concept_map = ConceptMap()

        # 添加主题到概念地图
        concept_map.add_topic(main_concept_id, main_concept_name)

        # 添加学习模块和概念（层次化存储）
        for module in map_data['learning_modules']:
            module_id = slugify(module['module_name'])
            module_data = {
                "name": module['module_name'],
                "description": module['description'],
                "concepts": {}
            }

            # 添加模块
            concept_map.add_module(main_concept_id, module_id, module_data)

            # 添加模块内的概念
            for concept_name in module['concepts']:
                concept_id = slugify(concept_name)
                concept_data = {
                    "name": concept_name,
                    "children": [],
                    "status": {
                        "explained": False,
                        "quiz_generated": False
                    },
                    "mastery": {
                        "best_score_percent": -1
                    }
                }
                concept_map.add_concept_to_module(
                    main_concept_id, module_id, concept_id, concept_data)

        # 同时保持扁平化存储（向后兼容）
        for concept_name in all_concepts:
            concept_id = slugify(concept_name)
            concept_data = {
                "name": concept_name,
                "children": [],
                "status": {
                    "explained": False,
                    "quiz_generated": False
                },
                "mastery": {
                    "best_score_percent": -1
                }
            }
            concept_map.add_concept(main_concept_id, concept_id, concept_data)

        # 保存概念地图
        concept_map.save()

        # 显示成功信息
        typer.echo("🗺️  学习地图生成成功！")
        typer.echo("")
        typer.echo(f"主题: {main_concept_name}")
        typer.echo(
            f"└── 包含 {len(map_data['learning_modules'])} 个学习模块，共 {len(all_concepts)} 个概念:")
        typer.echo("")

        # 按模块层次化显示
        for i, module in enumerate(map_data['learning_modules']):
            is_last_module = i == len(map_data['learning_modules']) - 1
            module_prefix = "└──" if is_last_module else "├──"
            typer.echo(
                f"    {module_prefix} 📂 {module['module_name']} ({len(module['concepts'])}个概念)")
            typer.echo(
                f"    {'    ' if is_last_module else '│   '}   {module['description']}")

            # 显示模块内的概念
            for j, concept in enumerate(module['concepts']):
                is_last_concept = j == len(module['concepts']) - 1
                concept_prefix = "└──" if is_last_concept else "├──"
                indent = "        " if is_last_module else "│       "
                typer.echo(f"    {indent}{concept_prefix} {concept}")

            if not is_last_module:
                typer.echo("    │")

        typer.echo("")
        typer.echo(f"💾 概念地图已保存到: {concept_map.file_path}")
        typer.echo("💡 使用 'ap t' 查看完整学习仪表盘")

    except Exception as e:
        typer.echo(f"错误：生成学习地图时发生异常: {e}", err=True)
        raise typer.Exit(1)
