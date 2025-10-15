import json
import os
import time
from datetime import datetime
from ap.cli_commands.explain import explain
from ap.cli_commands.generate_quiz import generate_quiz_internal
from ap.cli_commands.quiz import quiz
from ap.core.concept_map import ConceptMap, slugify
from ap.core.settings import WORKSPACE_DIR


def show_progress_bar(current: int, total: int, step_name: str = "", width: int = 30):
    """显示进度条"""
    if total == 0:
        return
    
    progress = current / total
    filled = int(width * progress)
    bar = '█' * filled + '░' * (width - filled)
    percentage = int(progress * 100)
    
    print(f"\r进度: [{bar}] {percentage}% - {step_name}", end='', flush=True)
    if current == total:
        print()  # 完成时换行


def show_step_status(step_num: int, total_steps: int, step_name: str, status: str):
    """显示步骤状态"""
    status_icons = {
        'running': '🔄',
        'completed': '✅',
        'skipped': '⏭️',
        'failed': '❌'
    }
    
    icon = status_icons.get(status, '❓')
    print(f"{icon} 步骤 {step_num}/{total_steps}: {step_name} - {status}")


class StudyState:
    """学习状态管理类"""
    
    def __init__(self, concept: str):
        self.concept = concept
        self.state_file = os.path.join(WORKSPACE_DIR, f".study_state_{slugify(concept)}.json")
        self.state = self._load_state()
    
    def _load_state(self):
        """加载学习状态"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {
            'concept': self.concept,
            'steps': {
                'explain': {'completed': False, 'timestamp': None},
                'generate_quiz': {'completed': False, 'timestamp': None},
                'quiz': {'completed': False, 'timestamp': None}
            },
            'created_at': datetime.now().isoformat()
        }
    
    def save_state(self):
        """保存学习状态"""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"警告：无法保存学习状态: {e}")
    
    def mark_step_completed(self, step: str):
        """标记步骤完成"""
        if step in self.state['steps']:
            self.state['steps'][step]['completed'] = True
            self.state['steps'][step]['timestamp'] = datetime.now().isoformat()
            self.save_state()
    
    def is_step_completed(self, step: str) -> bool:
        """检查步骤是否已完成"""
        return self.state['steps'].get(step, {}).get('completed', False)
    
    def get_progress_summary(self) -> dict:
        """获取进度摘要"""
        completed_steps = sum(1 for step in self.state['steps'].values() if step['completed'])
        total_steps = len(self.state['steps'])
        return {
            'completed': completed_steps,
            'total': total_steps,
            'percentage': int((completed_steps / total_steps) * 100) if total_steps > 0 else 0
        }
    
    def cleanup(self):
        """清理状态文件"""
        if os.path.exists(self.state_file):
            try:
                os.remove(self.state_file)
            except:
                pass


def study(
    concept: str,
    num_questions: int = None,
    mode: str = "auto",
    skip_steps: str = None,
    verbose: bool = False,
    resume: bool = True,
    **kwargs
):
    """
    一键完成学习流程：生成解释文档 -> 创建测验题目 -> 运行交互式测验

    Args:
        concept: 要学习的概念名称
        num_questions: 指定题目数量（默认为智能分析）
        mode: 生成模式：auto（智能分析）或 fixed（固定模式）
        skip_steps: 跳过的步骤，用逗号分隔（如："explain,quiz"）
        verbose: 是否显示详细输出
        resume: 是否支持断点续传
        **kwargs: 其他参数透传给子命令
    """
    # 解析跳过的步骤
    skip_list = []
    if skip_steps:
        skip_list = [step.strip() for step in skip_steps.split(',')]
    
    # 初始化状态管理
    state_manager = StudyState(concept) if resume else None
    
    if verbose:
        print(f"[STUDY] 开始学习流程: {concept}")
        print(f"[STUDY] 参数: num_questions={num_questions}, mode={mode}, skip_steps={skip_steps}")
    
    print(f"开始学习 '{concept}' 的完整流程...")
    
    # 显示当前进度（如果有状态管理）
    if state_manager:
        progress = state_manager.get_progress_summary()
        if progress['completed'] > 0:
            print(f"检测到之前的进度: {progress['completed']}/{progress['total']} 步骤已完成 ({progress['percentage']}%)")
    
    print("=" * 50)

    try:
        # 预检查：验证概念是否存在于概念地图中
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
                print(f"请先使用 'ap m <主题名称>' 命令生成学习地图，然后再进行学习。")
                print("例如：ap m 机器学习")
                return

        # 准备参数
        common_kwargs = {
            'verbose': verbose,
            **kwargs
        }
        
        quiz_kwargs = {
            **common_kwargs
        }
        
        generate_kwargs = {
            'num_questions': num_questions,
            'mode': mode,
            **common_kwargs
        }

        total_steps = 3
        current_step = 0

        # 步骤1: 生成解释文档
        if 'explain' not in skip_list:
            current_step += 1
            if not (state_manager and state_manager.is_step_completed('explain')):
                show_step_status(current_step, total_steps, "生成概念解释文档", "running")
                try:
                    explain(concept, **common_kwargs)
                    if state_manager:
                        state_manager.mark_step_completed('explain')
                    show_step_status(current_step, total_steps, "生成概念解释文档", "completed")
                except Exception as e:
                    show_step_status(current_step, total_steps, "生成概念解释文档", "failed")
                    print(f"错误详情: {str(e)}")
                    print("建议：检查网络连接和 API 配置，然后使用 --resume 参数重新运行")
                    raise
            else:
                show_step_status(current_step, total_steps, "生成概念解释文档", "skipped")
        else:
            current_step += 1
            show_step_status(current_step, total_steps, "生成概念解释文档", "skipped")
        print()

        # 步骤2: 生成测验题目
        if 'generate_quiz' not in skip_list:
            current_step += 1
            if not (state_manager and state_manager.is_step_completed('generate_quiz')):
                show_step_status(current_step, total_steps, "生成测验题目", "running")
                try:
                    generate_quiz_internal(concept, **generate_kwargs)
                    if state_manager:
                        state_manager.mark_step_completed('generate_quiz')
                    show_step_status(current_step, total_steps, "生成测验题目", "completed")
                except Exception as e:
                    show_step_status(current_step, total_steps, "生成测验题目", "failed")
                    print(f"错误详情: {str(e)}")
                    print("建议：确保解释文档已生成，检查 API 配置，然后使用 --resume 参数重新运行")
                    raise
            else:
                show_step_status(current_step, total_steps, "生成测验题目", "skipped")
        else:
            current_step += 1
            show_step_status(current_step, total_steps, "生成测验题目", "skipped")
        print()

        # 步骤3: 运行交互式测验
        if 'quiz' not in skip_list:
            current_step += 1
            if not (state_manager and state_manager.is_step_completed('quiz')):
                show_step_status(current_step, total_steps, "开始交互式测验", "running")
                print("=" * 50)
                try:
                    quiz(concept, **quiz_kwargs)
                    if state_manager:
                        state_manager.mark_step_completed('quiz')
                    show_step_status(current_step, total_steps, "交互式测验", "completed")
                except Exception as e:
                    show_step_status(current_step, total_steps, "交互式测验", "failed")
                    print(f"错误详情: {str(e)}")
                    print("建议：确保测验题目已生成，然后使用 --resume 参数重新运行")
                    raise
            else:
                show_step_status(current_step, total_steps, "交互式测验", "skipped")
        else:
            current_step += 1
            show_step_status(current_step, total_steps, "交互式测验", "skipped")

        print()
        print("=" * 50)
        print(f"🎉 学习流程完成！'{concept}' 的完整学习已结束。")
        
        # 显示最终进度
        if verbose and state_manager:
            progress = state_manager.get_progress_summary()
            show_progress_bar(progress['completed'], progress['total'], "总体进度")
        
        # 清理状态文件
        if state_manager:
            state_manager.cleanup()

    except KeyboardInterrupt:
        print()
        print("=" * 50)
        print("学习流程被用户中断。")
        if state_manager and verbose:
            print(f"进度已保存，可使用 'ap s {concept} --resume' 继续执行")
        raise
    except Exception as e:
        print()
        print("=" * 50)
        print(f"学习流程中断：在处理 '{concept}' 时发生错误。")
        print(f"详细信息: {str(e)}")
        if state_manager:
            print(f"进度已保存，可使用 'ap s {concept} --resume' 继续执行")
            if verbose:
                print(f"状态文件位置: {state_manager.state_file}")
        print("或者使用 --skip 参数跳过失败的步骤")
        raise