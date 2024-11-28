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
  - Langfuse（可选，用于监控）

## 快速开始

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/song2quiz2.git
cd song2quiz2
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 设置环境变量：
```bash
export GENIUS_API_KEY="your_key_here"
export OPENROUTER_API_KEY="your_key_here"
export LRCLIB_API_KEY="your_key_here"
```

4. 运行分析流程：
```bash
python -m src.scripts.run_pipeline
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
