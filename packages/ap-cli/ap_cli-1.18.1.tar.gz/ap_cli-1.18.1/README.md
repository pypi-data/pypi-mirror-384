# AP CLI - 智能学习助手

一个基于AI的命令行学习工具，帮助用户通过"地图-解释-测验-追踪"的完整学习循环来掌握新概念。支持多主题管理和智能质量控制。

## ✨ 核心功能

### 🗺️ 多主题学习系统
- **📋 学习地图生成 (`ap m`)**: 为指定主题生成结构化的概念学习地图
- **🌳 进度可视化 (`ap t`)**: 显示全局或特定主题的学习进度树状图
- **🔄 多主题管理**: 支持同时管理多个学习主题，数据隔离存储

### 🎓 智能学习循环
- **🤔 智能解释 (`ap e`)**: 使用DeepSeek AI生成概念的详细Markdown解释文档
- **📝 自动出题 (`ap g`)**: 基于解释文档智能生成高质量选择题测验
- **🎯 交互测验 (`ap q`)**: 命令行交互式测验，实时反馈和结果统计
- **🚀 一键学习 (`ap s`)**: 完整学习流程自动化，从解释到测验一步到位

### 🔧 质量保证与自动化
- **⚡ 智能质量检查**: 自动检测测验题目质量，确保答案分布均匀
- **🔄 答案随机化**: 智能重排选项顺序，避免答案位置偏向
- **🤖 Pre-commit Hook**: AI驱动的版本管理，自动分析代码变更并更新版本号
- **⚙️ 配置管理 (`ap i`)**: 一键初始化和配置API密钥

## 🛠️ 技术栈

- **Python 3.8+** - 核心开发语言
- **Typer** - 现代化CLI框架，支持类型提示
- **OpenAI SDK** - DeepSeek API集成
- **python-dotenv** - 环境变量安全管理
- **PyYAML** - YAML格式数据处理

## 🚀 快速开始

### 自动化安装（推荐）

**Windows 用户：**
```bash
# 双击运行或在命令行执行
init.bat
```

**Linux/Mac 用户：**
```bash
# 给脚本执行权限并运行
chmod +x init.sh
./init.sh
```

### 手动安装

1. **克隆项目并进入目录**
   ```bash
   git clone <repository-url>
   cd ap
   ```

2. **创建虚拟环境**
   ```bash
   python -m venv .venv
   ```

3. **激活虚拟环境**
   ```bash
   # Windows
   .venv\Scripts\activate
   
   # Linux/Mac
   source .venv/bin/activate
   ```

4. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

5. **安装CLI工具**
   ```bash
   pip install -e .
   ```

6. **配置API密钥**
   ```bash
   # 复制环境变量示例文件
   cp .env.example .env
   
   # 编辑.env文件，填入您的DeepSeek API密钥
   # DEEPSEEK_API_KEY=your_actual_api_key_here
   ```

## 📖 使用指南

### 基础命令

```bash
# 查看帮助
ap --help

# 初始化配置（首次使用）
ap i

# 为主题生成学习地图
ap m "机器学习"

# 查看学习进度
ap t                    # 显示所有主题概览
ap t "机器学习"          # 显示特定主题详情

# 生成概念解释（支持多主题格式）
ap e "机器学习/监督学习"

# 基于解释生成测验题目
ap g "机器学习/监督学习"

# 开始交互式测验
ap q "机器学习/监督学习"

# 一键完成完整学习流程
ap s "机器学习/监督学习"
```

### 多主题学习工作流

#### 1. 创建学习地图 (`ap m`)

```bash
ap m "深度学习"
```

这将：
- 调用DeepSeek AI生成该主题的结构化学习路径
- 创建概念层级关系和依赖图谱
- 自动创建主题相关的目录结构
- 保存学习地图到 `workspace/concept_map.json`

#### 2. 查看学习进度 (`ap t`)

```bash
# 查看所有主题概览
ap t

# 查看特定主题详情
ap t "深度学习"
```

这将：
- 显示所有主题的学习统计和进度
- 树状结构展示概念层级关系
- 使用状态图标标识学习状态
- 提供学习建议和瓶颈分析

#### 3. 学习特定概念

```bash
# 使用多主题路径格式
ap e "深度学习/卷积神经网络"
ap g "深度学习/卷积神经网络"  
ap q "深度学习/卷积神经网络"

# 或使用一键学习流程
ap s "深度学习/卷积神经网络"
```

### 替代使用方式

如果遇到Typer相关问题，可以使用简化版本：

```bash
# 使用简化版本生成解释
python main_simple.py e "概念名称"

# 使用完整版本（推荐）
python main.py e "概念名称"
```

## 📁 项目结构

```
ap/
├── .env                    # API密钥配置（需手动创建）
├── .env.example           # 环境变量示例
├── .gitignore             # Git忽略文件
├── README.md              # 项目说明文档
├── requirements.txt       # Python依赖包
├── setup.py              # 项目安装配置
├── init.sh               # Linux/Mac自动化安装脚本
├── install-hook.py       # Pre-commit Hook安装脚本
├── pre-commit-hook.py    # AI驱动的版本管理Hook
├── PRE_COMMIT_HOOK_README.md  # Hook使用说明
├── ap/                   # 核心包目录
│   ├── __init__.py
│   ├── __main__.py       # 程序入口点
│   ├── cli.py           # CLI命令注册
│   ├── cli_commands/    # 命令实现模块
│   │   ├── init_config.py    # 配置初始化
│   │   ├── generate_map.py   # 学习地图生成
│   │   ├── display_tree.py   # 进度树显示
│   │   ├── explain.py        # 概念解释
│   │   ├── generate_quiz.py  # 测验生成
│   │   ├── quiz.py          # 交互测验
│   │   └── study.py         # 完整学习流程
│   ├── core/            # 核心功能模块
│   │   ├── concept_map.py    # 多主题概念地图管理
│   │   ├── quiz_quality_checker.py  # 测验质量检查
│   │   ├── settings.py       # 配置管理
│   │   └── utils.py         # 工具函数
│   ├── docs/            # 文档目录
│   └── tests/           # 测试目录
├── dev/                 # 开发文档和规范
│   ├── 00-specs/        # 模板和规范
│   ├── 01-epics/        # Epic级别需求
│   └── README.md        # 开发指南
└── workspace/           # 生成内容存储目录
    ├── concept_map.json     # 多主题概念地图数据
    ├── explanation/         # 概念解释文档
    │   └── <topic>/        # 按主题分类
    ├── quizzes/            # 测验题目文件
    │   └── <topic>/        # 按主题分类
    └── results/            # 测验结果记录
        └── <topic>/        # 按主题分类
```

## 🔧 环境验证

运行环境检查脚本确保配置正确：

```bash
python setup_env.py
```

该脚本将检查：
- Python版本兼容性
- 虚拟环境状态
- 依赖包安装情况
- API密钥配置
- CLI命令可用性

## 📊 功能状态

### ✅ 已完成功能
- **多主题学习系统** - 完全实现
  - 学习地图生成 (`ap m`)
  - 进度可视化 (`ap t`) 
  - 多主题数据管理和迁移
- **智能学习循环** - 完全实现
  - 概念解释生成 (`ap e`)
  - 测验题目生成 (`ap g`)
  - 交互式测验 (`ap q`)
  - 完整学习流程 (`ap s`)
- **质量保证系统** - 完全实现
  - 智能质量检查器
  - 答案分布均匀性验证
  - 自动答案随机化
- **开发工具** - 完全实现
  - AI驱动的Pre-commit Hook
  - 自动版本管理
  - 配置管理 (`ap i`)

### 🚧 开发中功能
- **云端同步** - 规划中
  - Cloudflare D1数据库集成
  - 多设备数据同步
  - 教师管理界面

## 🔧 高级功能

### 🤖 AI驱动的版本管理

项目集成了智能的Pre-commit Hook，能够：
- 自动分析Git提交内容
- 使用DeepSeek AI判断变更类型
- 智能更新版本号（MAJOR/MINOR/PATCH）
- 详细说明请参考 [PRE_COMMIT_HOOK_README.md](PRE_COMMIT_HOOK_README.md)

### ⚡ 智能质量控制

测验生成包含质量检查机制：
- **答案分布检查**: 确保正确答案在各选项位置均匀分布
- **质量评分**: 基于统计学原理计算质量分数
- **自动优化**: 智能重排选项顺序，消除位置偏向
- **详细报告**: 生成质量分析报告和改进建议

### 🗺️ 多主题架构

支持复杂的学习场景：
- **主题隔离**: 不同主题的数据完全隔离存储
- **路径格式**: 使用 `主题/概念` 格式组织内容
- **数据迁移**: 自动从旧格式迁移到多主题格式
- **向后兼容**: 保持对旧命令格式的支持

## 🔍 故障排除

### 常见问题

1. **环境变量未找到**
   ```bash
   # 确保.env文件存在且包含正确的API密钥
   cp .env.example .env
   # 编辑.env文件填入真实的API密钥
   ```

2. **Typer相关错误**
   ```bash
   # 使用简化版本
   python main_simple.py e "概念名称"
   ```

3. **依赖安装失败**
   ```bash
   # 升级pip并重新安装
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **CLI命令不可用**
   ```bash
   # 重新安装包
   pip install -e .
   ```

### 获取帮助

- 查看命令帮助：`ap --help`
- 查看特定命令帮助：`ap e --help`
- 运行环境检查：`python setup_env.py`

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 👥 作者

- **AP CLI Team** - *初始开发* - yangjh@xbmu.edu.cn

---

**享受智能化的学习体验！** 🎓✨

## 🔗 相关文档

- [Pre-commit Hook使用指南](PRE_COMMIT_HOOK_README.md) - AI驱动的版本管理详细说明
- [开发文档](dev/README.md) - 项目开发规范和Epic管理
- [概念图使用说明](ap/docs/concept_map_usage.md) - 多主题概念地图详细用法
# Test
