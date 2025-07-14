# AI API配置指南

本系统支持两种AI API提供商：DeepSeek和OpenAI。

## 方式1: 配置DeepSeek API (推荐)

### 选项A: 直接在代码中配置
编辑 `ai_filter.py` 文件的第21行，将您的DeepSeek API密钥直接写入：

```python
# 方式1: 直接在代码中配置
self.deepseek_key = "sk-your-actual-deepseek-key-here"  # 取消注释并输入真实密钥
```

### 选项B: 使用环境变量
1. 复制 `.env.example` 为 `.env`：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，设置您的DeepSeek API密钥：
```
DEEPSEEK_API_KEY=sk-your-actual-deepseek-key-here
```

## 方式2: 使用OpenAI API

用户在Web界面中选择"OpenAI API (用户输入)"，然后输入OpenAI API密钥。

## 使用说明

1. **默认使用DeepSeek**: 系统默认使用DeepSeek API，用户无需在Web界面输入任何密钥
2. **切换到OpenAI**: 用户可以在Web界面的下拉菜单中选择OpenAI，然后输入API密钥
3. **成本优势**: DeepSeek API通常比OpenAI API更便宜

## API端点信息

- **DeepSeek API**: `https://api.deepseek.com`
- **OpenAI API**: `https://api.openai.com` (默认)

## 模型配置

- **DeepSeek**: `deepseek-chat`
- **OpenAI**: `gpt-3.5-turbo`