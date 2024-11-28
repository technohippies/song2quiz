# Song2Quiz2

[English](README.md) | [简体中文](README.zh-CN.md)

一个先进的歌词分析和测验生成系统，利用AI提供对歌词的深度语义理解。

## 功能特点

- **歌词分析**
  - 语义单元分析，深入理解歌词含义
  - 词汇分析，包含上下文感知解释
  - 内容警告系统，识别敏感内容
  - 集成Genius注释功能

- **测验生成**
  - 填空练习
  - 多选翻译题
  - 词序排列练习

## 文档

完整文档请访问我们的 [Mintlify 文档](./docs/)。

## 系统要求

- Python 3.12+
- 依赖包见 `requirements.txt`
- 需要以下API密钥：
  - Genius API
  - OpenRouter API
  - LRCLib API
  - Langfuse（用于监控）
  - Prefect Cloud（可选，用于云端执行）

## 快速开始

1. 克隆仓库：
```bash
git clone https://github.com/technohippies/song2quiz.git
cd song2quiz
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 设置环境变量（复制 .env.example 到 .env 并填写你的密钥）：
```bash
cp .env.example .env
# 在.env中编辑以下API密钥：
# - GENIUS_API_KEY
# - OPENROUTER_API_KEY
# - LRCLIB_API_KEY
# - LANGFUSE_PUBLIC_KEY
# - LANGFUSE_SECRET_KEY
# - LANGFUSE_HOST
```

4. 配置 Prefect（云端执行可选）：
```bash
# 仅本地执行：
prefect server start

# Prefect Cloud：
prefect cloud login
```

5. 运行分析流程：
```bash
# 本地执行
python -m src.scripts.run_pipeline

# 云端执行
prefect deploy -n song2quiz
prefect worker start -p song2quiz-pool
```

## 项目结构

```
song2quiz2/
├── src/               # 源代码
│   ├── flows/         # Prefect 工作流
│   ├── services/      # 外部API集成
│   ├── tasks/         # 独立任务定义
│   └── utils/         # 实用工具函数
├── tests/             # 测试套件
├── docs/              # 文档
└── data/              # 数据存储
```

## 开发

### 测试

运行测试套件：
```bash
pytest
```

### 贡献代码

1. Fork 本仓库
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

本项目采用 GNU Affero General Public License v3.0 许可证 - 详见 LICENSE 文件。
