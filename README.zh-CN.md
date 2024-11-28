# Song2Quiz

[English](README.md) | [简体中文](README.zh-CN.md)

一个先进的歌词分析和测验生成系统，利用AI提供对歌词的深度语义理解。

## 文档

完整文档请访问我们的 [Mintlify 文档](https://song2quiz.mintlify.app)。

## 快速开始

1. 克隆仓库：
```bash
git clone https://github.com/technohippies/song2quiz.git
cd song2quiz
```

2. 安装依赖：
```bash
uv pip install -r requirements.txt
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

## 许可证

本项目采用 GNU Affero General Public License v3.0 许可证 - 详见 LICENSE 文件。
