import yaml
import json
from datetime import datetime
from ap.core.concept_map import ConceptMap, slugify
from ap.core.settings import WORKSPACE_DIR


def quiz(
    concept: str,
    verbose: bool = False,
    auto_mode: bool = False
):
    """
    开始交互式测验

    Args:
        concept: 要进行测验的概念名称
        verbose: bool = False, 是否显示详细输出
        auto_mode: bool = False, 是否自动模式（跳过交互）
    """
    if verbose:
        print(f"[QUIZ] 开始交互式测验: {concept}")
    
    try:
        # 创建概念地图实例
        concept_map = ConceptMap()
        
        # 解析概念名称，提取主题和概念部分（与 explain 和 generate_quiz 保持一致）
        if '/' in concept:
            topic_slug, concept_part = concept.split('/', 1)
            concept_slug = slugify(concept_part)
        else:
            concept_slug = slugify(concept)
            # 如果没有提供主题，则需要查找
            topic_slug = concept_map.get_topic_by_concept(concept_slug)
            if not topic_slug:
                print(f"错误：找不到概念 '{concept}' 所属的主题。")
                raise

        # 构造输入文件路径 - 按主题组织
        quiz_file = WORKSPACE_DIR / topic_slug / \
            "quizzes" / f"{concept_slug}.yml"

        # 检查文件是否存在
        if not quiz_file.exists():
            print(f"错误: 未找到 '{concept}' 的测验文件。")
            print(f"请先运行 'ap g \"{concept}\"'。")
            raise FileNotFoundError(f"测验文件不存在: {quiz_file}")

        # 读取并解析 YAML 文件
        try:
            with open(quiz_file, 'r', encoding='utf-8') as f:
                questions = yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"错误: YAML 文件格式不正确: {str(e)}")
            raise
        except Exception as e:
            print(f"错误: 无法读取测验文件: {str(e)}")
            raise

        # 验证文件格式
        if not isinstance(questions, list) or not questions:
            print("错误: 测验文件格式不正确，应包含问题列表。")
            raise ValueError("无效的测验文件格式")

        # 验证每个问题的格式
        for i, q in enumerate(questions):
            if not isinstance(q, dict) or not all(
                key in q for key in ['question', 'options', 'answer']
            ):
                print(f"错误: 第 {i+1} 题格式不正确，缺少必要的键。")
                raise ValueError(f"第 {i+1} 题格式无效")
            
            # 支持字典格式的选项（A、B、C、D作为键）
            if isinstance(q['options'], dict):
                expected_keys = {'A', 'B', 'C', 'D'}
                if set(q['options'].keys()) != expected_keys:
                    print(f"错误: 第 {i+1} 题选项应包含A、B、C、D四个键。")
                    raise ValueError(f"第 {i+1} 题选项无效")
            # 支持列表格式的选项
            elif isinstance(q['options'], list):
                if len(q['options']) != 4:
                    print(f"错误: 第 {i+1} 题应包含4个选项。")
                    raise ValueError(f"第 {i+1} 题选项无效")
            else:
                print(f"错误: 第 {i+1} 题选项格式不正确。")
                raise ValueError(f"第 {i+1} 题选项无效")

        print(f"开始 '{concept}' 的测验！共 {len(questions)} 题")
        print("=" * 50)

        # 记录测验结果
        results = []
        correct_count = 0

        # 遍历问题进行测验
        for i, question in enumerate(questions, 1):
            print(f"\n问题 {i}/{len(questions)}: {question['question']}")

            # --- 统一显示选项为 A, B, C, D ---
            options_map = {}
            options_list = []  # 用于后续答案判断
            if isinstance(question['options'], dict):
                # 如果是字典，直接使用
                options_map = question['options']
                options_list = list(options_map.values())
            else:
                # 如果是列表，转换为字典
                keys = ['A', 'B', 'C', 'D']
                options_map = {
                    keys[i]: opt for i, opt in enumerate(question['options'])
                }
                options_list = question['options']

            for key, value in options_map.items():
                print(f"  {key}. {value}")
            # --- 结束选项显示修改 ---

            # --- 修改用户输入逻辑 ---
            while True:
                user_input = input("\n请选择答案 (A-D): ").upper()
                if not user_input:
                    print("\n测验已取消")
                    return

                if user_input in options_map:
                    break
                else:
                    print("请输入 A, B, C, 或 D")
            # --- 结束用户输入修改 ---

            # 判断答案
            user_answer = options_map[user_input]
            correct_answer_key_or_value = question['answer']

            # --- 查找正确答案的键和文本 ---
            correct_answer_key = None
            correct_answer_text = None

            if correct_answer_key_or_value in options_map:
                # Case 1: 答案是 'A', 'B', 'C', 'D' 等键
                correct_answer_key = correct_answer_key_or_value
                correct_answer_text = options_map[correct_answer_key]
            else:
                # Case 2: 答案是选项的文本内容
                correct_answer_text = correct_answer_key_or_value
                for key, value in options_map.items():
                    if value == correct_answer_text:
                        correct_answer_key = key
                        break

            # 判断用户答案是否正确 (通过比较键)
            is_correct = (user_input == correct_answer_key)

            if is_correct:
                print("✅ 正确！")
                correct_count += 1
            else:
                if correct_answer_key:
                    print(
                        f"❌ 错误，正确答案是："
                        f"{correct_answer_key} ({correct_answer_text})"
                    )
                else:
                    # 如果因数据错误找不到键，则只显示文本
                    print(f"❌ 错误，正确答案是：{correct_answer_text}")

            # 记录结果
            results.append({
                "question": question['question'],
                "options": options_list,
                "user_answer": user_answer,
                "correct_answer": correct_answer_text,
                "is_correct": is_correct
            })

        # 计算并显示最终结果
        total_questions = len(questions)
        accuracy = (correct_count / total_questions) * 100

        print("\n" + "=" * 50)
        print(
            f"测验完成！你答对了 {correct_count}/{total_questions} 题，"
            f"正确率 {accuracy:.1f}%"
        )

        # 保存结果到 JSON 文件 - 按主题组织
        results_dir = WORKSPACE_DIR / topic_slug / "results"
        results_dir.mkdir(parents=True, exist_ok=True)

        # 生成时间戳
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        result_file = results_dir / f"{concept_slug}_{timestamp}.json"

        # 创建结果对象
        quiz_result = {
            "concept": concept,
            "concept_slug": concept_slug,
            "topic": topic_slug,
            "quiz_time": datetime.now().isoformat(),
            "total_questions": total_questions,
            "correct_count": correct_count,
            "accuracy": accuracy,
            "questions": results
        }

        # 保存到文件
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(quiz_result, f, ensure_ascii=False, indent=2)

        print(f"测验结果已保存到: {result_file}")

        # 使用多主题ConceptMap
        concept_map = ConceptMap()

        # 处理概念名称：如果包含主题前缀，只使用概念部分作为概念ID
        if '/' in concept:
            topic_part, concept_part = concept.split('/', 1)
            topic_slug = slugify(topic_part)
            concept_id = slugify(concept_part)
        else:
            concept_id = slugify(concept)
            # 如果没有提供主题，则需要查找
            topic = concept_map.get_topic_by_concept(concept_id)
            topic_slug = slugify(topic) if topic else None

        # 确保主题存在
        if topic_slug and not concept_map.topic_exists(topic_slug):
            # 从概念名称中提取主题名称
            if '/' in concept:
                topic_name = concept.split('/', 1)[0]
            else:
                topic_name = topic_slug
            concept_map.add_topic(topic_slug, topic_name)

        # 确保概念存在于主题中
        if topic_slug:
            existing_concept = concept_map.get_concept(topic_slug, concept_id)
            if not existing_concept:
                concept_map.add_concept(topic_slug, concept_id, {
                    "name": concept_part if '/' in concept else concept,
                    "children": [],
                    "status": {},
                    "mastery": {}
                })

            # 更新测验状态
            concept_map.update_status(topic_slug, concept_id, "quiz_taken", True)
            concept_map.update_status(
                topic_slug, concept_id, "last_quiz_time",
                datetime.now().isoformat()
            )

            # 更新掌握程度
            concept_map.update_mastery(topic_slug, concept_id, accuracy)

            # 保存概念地图
            concept_map.save()

            print(f"学习进度已更新：{concept} - 掌握程度 {accuracy:.1f}%")
        else:
            print(f"警告：无法确定概念 '{concept}' 所属的主题，"
                  f"跳过进度更新。")

    except Exception as e:
        print(f"测验过程中发生错误: {str(e)}")
        raise