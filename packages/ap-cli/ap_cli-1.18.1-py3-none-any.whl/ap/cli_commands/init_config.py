import sys
from pathlib import Path
import typer
import getpass


def init_config():
    """
    初始化配置：交互式设置 DEEPSEEK_API_KEY
    
    询问用户输入 API 密钥，并将其保存到 .env 文件中
    """
    print("🔧 AP CLI 配置初始化")
    print("=" * 40)
    
    # 获取项目根目录的 .env 文件路径
    project_root = Path(__file__).parent.parent.parent
    env_file = project_root / ".env"
    
    # 检查是否已存在 .env 文件
    if env_file.exists():
        print(f"📁 发现现有配置文件: {env_file}")
        
        # 读取现有配置
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "DEEPSEEK_API_KEY=" in content:
            overwrite = typer.confirm("⚠️  已存在 DEEPSEEK_API_KEY 配置，是否要覆盖？")
            if not overwrite:
                print("❌ 配置初始化已取消")
                return
    
    # 交互式输入 API 密钥
    print("\n🔑 请输入您的 DeepSeek API 密钥:")
    print("💡 提示: 您可以在 https://platform.deepseek.com/api_keys 获取 API 密钥")
    print("🔒 输入的密钥将被隐藏以保护安全")
    
    while True:
        try:
            # 使用 getpass 进行安全的密码输入
            api_key = getpass.getpass("DEEPSEEK_API_KEY: ")
            
            if not api_key:
                print("❌ API 密钥不能为空，请重新输入")
                continue
            
            # 简单验证 API 密钥格式
            if not api_key.startswith("sk-"):
                print("⚠️  警告: API 密钥通常以 'sk-' 开头，请确认输入正确")
                confirm = typer.confirm("是否继续使用此密钥？")
                if not confirm:
                    continue
            
            break
            
        except KeyboardInterrupt:
            print("\n❌ 配置初始化已取消")
            return
        except Exception as e:
            print(f"❌ 输入错误: {e}")
            continue
    
    # 保存到 .env 文件
    try:
        # 如果文件存在，读取现有内容并更新
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 查找并替换现有的 DEEPSEEK_API_KEY 行
            updated = False
            for i, line in enumerate(lines):
                if line.strip().startswith("DEEPSEEK_API_KEY="):
                    lines[i] = f"DEEPSEEK_API_KEY={api_key}\n"
                    updated = True
                    break
            
            # 如果没找到现有配置，添加新行
            if not updated:
                lines.append(f"DEEPSEEK_API_KEY={api_key}\n")
            
            # 写回文件
            with open(env_file, 'w', encoding='utf-8') as f:
                f.writelines(lines)
        else:
            # 创建新的 .env 文件
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(f"DEEPSEEK_API_KEY={api_key}\n")
        
        print(f"\n✅ API 密钥已成功保存到 {env_file}")
        print("🎉 配置初始化完成！现在您可以使用 AP CLI 的所有功能了")
        
        # 提示用户可以开始使用
        print("\n🚀 快速开始:")
        print("   ap e \"概念名称\"     # 生成概念解释")
        print("   ap g \"概念名称\"     # 生成测验题目") 
        print("   ap s \"概念名称\"     # 完整学习流程")
        
    except Exception as e:
        print(f"❌ 保存配置时发生错误: {e}")
        print("请检查文件权限或手动创建 .env 文件")
        return