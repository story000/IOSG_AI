# 🚀 快速启动指南

## 1. 配置DeepSeek API密钥

### 方法1: 直接在代码中配置 (推荐)

编辑 `ai_filter.py` 文件第21行：

```python
# 将这行取消注释并填入您的真实密钥
self.deepseek_key = "sk-your-actual-deepseek-key-here"
```

### 方法2: 使用环境变量

```bash
export DEEPSEEK_API_KEY=sk-your-actual-deepseek-key-here
```

## 2. 启动系统

```bash
python run_web.py
```

或者直接：

```bash
python app.py
```

## 3. 访问Web界面

打开浏览器访问：http://localhost:8080

## 4. 使用流程

1. **步骤1**: 点击"开始获取"获取最新新闻
2. **步骤2**: 点击"开始分类"对新闻进行分类  
3. **步骤3**: 选择"DeepSeek API"，点击"开始AI过滤"生成报告

## 🔧 常见问题

### Q: AI过滤启动失败？
A: 检查DeepSeek API密钥是否正确配置

### Q: 如何知道任务完成了？
A: 观察界面上的进度条和日志输出，任务完成后会显示绿色边框

### Q: 想用OpenAI API怎么办？
A: 在步骤3中选择"OpenAI API (用户输入)"，然后输入您的OpenAI密钥

## 💡 提示

- DeepSeek API通常比OpenAI API更便宜
- 可以在日志区域查看详细的处理过程
- 最终报告会在底部的"最终结构化输出"区域显示