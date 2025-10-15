import os
import sys
from openai import OpenAI
from dotenv import load_dotenv


def get_deepseek_client():
    """获取DeepSeek API客户端"""
    # 加载 .env 文件
    load_dotenv()

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("错误：未找到DEEPSEEK_API_KEY环境变量")
        print("请在.env文件中设置您的DeepSeek API密钥")
        sys.exit(1)

    return OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )


def call_deepseek_api(
    messages,
    model="deepseek-chat",
    temperature=0.7,
    max_tokens=2000,
    system_message=None
):
    """
    统一的DeepSeek API调用接口

    Args:
        messages: 消息列表或单个用户消息字符串
        model: 使用的模型，默认为deepseek-chat
        temperature: 温度参数，控制随机性
        max_tokens: 最大token数量
        system_message: 系统消息（可选）

    Returns:
        API响应的内容字符串
    """
    client = get_deepseek_client()

    # 处理消息格式
    if isinstance(messages, str):
        # 如果是字符串，转换为消息格式
        formatted_messages = []
        if system_message:
            formatted_messages.append(
                {"role": "system", "content": system_message}
            )
        formatted_messages.append(
            {"role": "user", "content": messages}
        )
    elif isinstance(messages, list):
        # 如果已经是列表格式，直接使用
        formatted_messages = messages
        if (system_message and
                not any(msg.get("role") == "system"
                        for msg in formatted_messages)):
            # 如果没有系统消息且提供了system_message，添加到开头
            formatted_messages.insert(
                0, {"role": "system", "content": system_message}
            )
    else:
        raise ValueError("messages必须是字符串或消息列表")

    try:
        response = client.chat.completions.create(
            model=model,
            messages=formatted_messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"DeepSeek API调用失败: {e}")
        raise


def call_deepseek_with_retry(
    messages,
    model="deepseek-chat",
    max_retries=3,
    base_temperature=0.3,
    max_tokens=2000,
    system_message=None,
    retry_callback=None
):
    """
    带重试机制的DeepSeek API调用

    Args:
        messages: 消息列表或单个用户消息字符串
        model: 使用的模型
        max_retries: 最大重试次数
        base_temperature: 基础温度，每次重试会递增
        max_tokens: 最大token数量
        system_message: 系统消息（可选）
        retry_callback: 重试时的回调函数，接收(attempt, max_retries)参数

    Returns:
        API响应的内容字符串
    """
    last_exception = None

    for attempt in range(max_retries):
        try:
            if retry_callback:
                retry_callback(attempt + 1, max_retries)

            # 每次重试增加温度以增加随机性
            temperature = base_temperature + (attempt * 0.1)

            return call_deepseek_api(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                system_message=system_message
            )

        except Exception as e:
            last_exception = e
            if attempt == max_retries - 1:
                # 最后一次重试失败，抛出异常
                break
            # 继续重试
            continue

    # 所有重试都失败了
    print(f"DeepSeek API调用失败，已重试{max_retries}次")
    raise last_exception
