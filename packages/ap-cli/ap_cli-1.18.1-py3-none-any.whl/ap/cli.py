import typer

# 从独立的命令模块中导入命令函数
from ap.cli_commands.generate_map import generate_map
from ap.cli_commands.display_tree import display_tree
from ap.cli_commands.explain import explain
from ap.cli_commands.generate_quiz import generate_quiz
from ap.cli_commands.quiz import quiz
from ap.cli_commands.study import study as study_internal
from ap.cli_commands.init_config import init_config

# 初始化 Typer 应用
app = typer.Typer(
    name="ap",
    help="AP (Assisted Learner) - 一个辅助学习命令行工具",
    add_completion=False,
    no_args_is_help=True
)

# Study 命令的 Typer 包装器
def study_command(
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
    skip_steps: str = typer.Option(
        None,
        "--skip",
        help="跳过的步骤，用逗号分隔（如：explain,quiz）"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="显示详细输出"
    ),
    no_resume: bool = typer.Option(
        False,
        "--no-resume",
        help="禁用断点续传功能"
    )
):
    """一键完成学习流程：解释 -> 测验 -> 评估"""
    study_internal(
        concept=concept,
        num_questions=num_questions,
        mode=mode,
        skip_steps=skip_steps,
        verbose=verbose,
        resume=not no_resume
    )

# 将命令注册到 Typer 应用
# 每个命令的实现都委托给对应的模块
app.command("i", help="初始化配置：设置 DEEPSEEK_API_KEY")(init_config)
app.command("m", help="为指定主题生成学习地图")(generate_map)
app.command("t", help="显示全局或特定主题的学习进度树状图")(display_tree)
app.command("e", help="生成概念的详细解释文档")(explain)
app.command("g", help="基于解释文档生成测验题目")(generate_quiz)
app.command("q", help="开始交互式测验")(quiz)
app.command("s", help="一键完成学习流程：解释 -> 测验 -> 评估")(study_command)



def main():
    """主函数"""
    app()


if __name__ == "__main__":
    main()
