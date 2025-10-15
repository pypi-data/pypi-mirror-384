"""
ap t
"""
import typer
from rich.console import Console
from rich.tree import Tree

from ap.core.concept_map import ConceptMap

console = Console()


def display_tree(topic_name: str = typer.Argument(None, help="要显示的主题名称")):
    """
    以树状结构显示学习进度
    """
    concept_map = ConceptMap()
    if topic_name:
        if not concept_map.topic_exists(topic_name):
            typer.echo(f"主题 '{topic_name}' 不存在。")
            suggest_available_topics(concept_map)
            raise typer.Exit(1)
        display_topic_details(concept_map, topic_name)
    else:
        display_global_overview(concept_map)


def display_global_overview(concept_map: ConceptMap):
    """显示所有主题的全局概览"""
    if not concept_map.data["topics"]:
        typer.echo("还没有任何学习主题。")
        return

    tree = Tree("📚 [bold cyan]学习主题总览[/bold cyan]")

    for topic_id, topic_data in concept_map.data["topics"].items():
        topic_name = topic_data.get("name", topic_id)
        
        # 计算主题的统计信息
        concepts = topic_data.get("concepts", {})
        total_concepts = len(concepts)
        completed_concepts = sum(1 for c in concepts.values() if c.get("status", {}).get("completed"))
        
        completion_rate = (completed_concepts / total_concepts * 100) if total_concepts > 0 else 0
        
        topic_branch = tree.add(f"🌳 [bold]{topic_name}[/bold] (完成度: {completion_rate:.1f}%)")

        modules = topic_data.get("modules", {})
        if modules:
            for module_id, module_data in modules.items():
                module_name = module_data.get("name", module_id)
                module_branch = topic_branch.add(f"📦 {module_name}")
                
                module_concepts = module_data.get("concepts", {})
                for concept_id, concept_data in module_concepts.items():
                    icon = get_status_icon_from_concept(concept_data)
                    concept_name = concept_data.get("name", concept_id)
                    mastery_score = concept_data.get("mastery", {}).get("best_score_percent", 0)
                    if mastery_score == -1:
                        module_branch.add(f"{icon} {concept_name}")
                    else:
                        module_branch.add(f"{icon} {concept_name} (掌握度: {mastery_score:.1f}%)")
        
        # 处理没有模块的孤立概念
        topic_concepts = {k: v for k, v in concepts.items() if not v.get("module_id")}
        if topic_concepts:
            isolated_branch = topic_branch.add("📚 [bold]独立概念[/bold]")
            for concept_id, concept_data in topic_concepts.items():
                icon = get_status_icon_from_concept(concept_data)
                concept_name = concept_data.get("name", concept_id)
                mastery_score = concept_data.get("mastery", {}).get("best_score_percent", 0)
                if mastery_score == -1:
                    isolated_branch.add(f"{icon} {concept_name}")
                else:
                    isolated_branch.add(f"{icon} {concept_name} (掌握度: {mastery_score:.1f}%)")

    console.print(tree)


def display_topic_details(concept_map: ConceptMap, topic_id: str):
    """显示单个主题的详细信息"""
    topic_data = concept_map.get_topic(topic_id)
    if not topic_data:
        typer.echo(f"主题 '{topic_id}' 不存在。")
        return

    topic_name = topic_data.get("name", topic_id)
    
    # 计算统计信息
    concepts = topic_data.get("concepts", {})
    total_concepts = len(concepts)
    completed_concepts = sum(1 for c in concepts.values() if c.get("status", {}).get("completed"))
    
    completion_rate = (completed_concepts / total_concepts * 100) if total_concepts > 0 else 0
    
    avg_mastery = (
        sum(c.get("mastery", {}).get("best_score_percent", 0) for c in concepts.values()) / total_concepts
        if total_concepts > 0
        else 0
    )

    tree = Tree(f"🗺️ [bold cyan]主题: {topic_name}[/bold cyan]")
    topic_branch = tree

    # 统计信息后移到末端以提升可读性（稍后添加）

    modules = topic_data.get("modules", {})
    all_concepts_flat = topic_data.get("concepts", {})
    concepts_in_modules = set()

    if modules:
        for module_id, module_data in modules.items():
            module_name = module_data.get("name", module_id)
            module_branch = topic_branch.add(f"📦 [bold]{module_name}[/bold]")
            
            module_concepts = module_data.get("concepts", {})
            
            if not module_concepts:
                module_branch.add("[italic]该模块下暂无概念[/italic]")
            else:
                for concept_id, concept_data in module_concepts.items():
                    icon = get_status_icon_from_concept(concept_data)
                    concept_name = concept_data.get("name", concept_id)
                    mastery_score = concept_data.get("mastery", {}).get("best_score_percent", 0)
                    if mastery_score == -1:
                        module_branch.add(f"{icon} {concept_name}")
                    else:
                        module_branch.add(f"{icon} {concept_name} (掌握度: {mastery_score:.1f}%)")
                    concepts_in_modules.add(concept_id)

    # 处理没有模块的孤立概念
    isolated_concepts = {cid: cdata for cid, cdata in all_concepts_flat.items() if cid not in concepts_in_modules}
    if isolated_concepts:
        isolated_branch = topic_branch.add("📚 [bold]独立概念[/bold]")
        for concept_id, concept_data in isolated_concepts.items():
            icon = get_status_icon_from_concept(concept_data)
            concept_name = concept_data.get("name", concept_id)
            mastery_score = concept_data.get("mastery", {}).get("best_score_percent", 0)
            if mastery_score == -1:
                isolated_branch.add(f"{icon} {concept_name}")
            else:
                isolated_branch.add(f"{icon} {concept_name} (掌握度: {mastery_score:.1f}%)")

    if not modules and not isolated_concepts:
        topic_branch.add("[italic]该主题下没有任何模块或概念。[/italic]")
    
    console.print(tree)

    # 以分行方式显示详细统计（取消树形结构）
    mastery_values = [
        c.get("mastery", {}).get("best_score_percent", -1)
        for c in concepts.values()
        if c.get("mastery", {}).get("best_score_percent", -1) != -1
    ]
    learned_count = len(mastery_values)
    progress_percent = ((learned_count / total_concepts) * 100) if total_concepts > 0 else 0.0
    typer.echo("\n详细统计：")
    typer.echo(f"概念总数: {total_concepts}")
    typer.echo(f"已学习数量: {learned_count}")
    typer.echo(f"学习进度: {progress_percent:.1f}%")


def get_status_icon_from_concept(concept: dict) -> str:
    """根据概念的状态返回一个图标"""
    status = concept.get("status", {})
    if status.get("completed"):
        return "✅"
    if status.get("learned"):
        return "📖"
    if status.get("reviewed"):
        return "👀"
    return "📝"


def suggest_available_topics(concept_map: ConceptMap):
    """当用户输入的主题不存在时，给出可用主题的建议"""
    available_topics = concept_map.list_topics()
    if available_topics:
        typer.echo("可用的主题有:")
        for topic in available_topics:
            typer.echo(f"- {topic}")
    else:
        typer.echo("当前没有可用的主题。")