# Crypto News Analysis Web Interface

这是一个基于Flask的Web界面，用于运行加密货币新闻分析系统。通过直观的网页界面，您可以轻松执行新闻获取、分类和AI过滤的完整流程。

## 功能特性

### 🔄 三步式工作流程
1. **获取特定Feeds** - 从指定的加密货币新闻源获取最新文章
2. **文章智能分类** - 使用AI算法将文章分类到不同类别
3. **AI过滤与结构化生成** - 使用OpenAI API进行智能过滤并生成最终报告

### 🎯 核心功能
- **实时日志显示** - 查看每个步骤的详细执行日志
- **进度跟踪** - 实时显示任务执行进度
- **Markdown渲染** - 自动渲染最终输出的markdown报告
- **响应式设计** - 支持桌面和移动设备

### 📊 支持的新闻分类
- 项目融资
- 基金融资  
- 基础设施/项目主网上线
- DeFi/RWA
- NFT/GameFi/Metaverse
- 交易所/钱包
- Portfolio项目 (IOSG投资组合)

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 启动Web应用
```bash
python run_web.py
```

### 3. 访问Web界面
打开浏览器访问: http://localhost:5000

### 4. 执行分析流程
1. 点击 **"开始获取"** 按钮获取最新的加密货币新闻
2. 点击 **"开始分类"** 按钮对文章进行智能分类
3. 输入您的OpenAI API密钥，点击 **"开始AI过滤"** 生成最终报告

## 系统要求

- Python 3.7+
- OpenAI API密钥 (用于AI过滤步骤)
- 网络连接 (用于获取新闻和调用API)

## 使用说明

### 步骤1: 获取特定Feeds
- 自动从以下新闻源获取文章:
  - PANews
  - TechFlow 
  - Wu Blockchain
  - Cointelegraph中文
- 实时显示获取进度和日志

### 步骤2: 文章分类
- 使用关键词匹配和模式识别对文章分类
- 自动检测IOSG投资组合项目
- 显示分类统计和示例文章

### 步骤3: AI过滤与结构化生成
- 需要输入有效的OpenAI API密钥
- 使用GPT-3.5-turbo进行智能过滤
- 生成结构化的markdown格式报告
- 自动在页面底部渲染最终输出

## 文件结构

```
/
├── app.py                 # Flask主应用
├── run_web.py            # 启动脚本
├── templates/
│   └── index.html        # Web界面模板
├── requirements.txt      # Python依赖
├── README_WEB.md        # 本文档
└── [原有Python脚本]      # 核心功能模块
```

## 技术栈

- **后端**: Flask + Flask-SocketIO
- **前端**: Bootstrap 5 + Socket.IO + Marked.js
- **实时通信**: WebSocket
- **Markdown渲染**: Marked.js + Highlight.js

## 注意事项

1. **API密钥安全**: OpenAI API密钥仅在当前会话中使用，不会被保存
2. **文件访问**: 确保Python脚本有权限读写当前目录的JSON文件
3. **网络连接**: 需要稳定的网络连接以获取新闻和调用API
4. **浏览器兼容性**: 建议使用现代浏览器 (Chrome, Firefox, Safari, Edge)

## 故障排除

### 常见问题

**Q: Web界面无法启动**
A: 检查是否已安装所有依赖: `pip install -r requirements.txt`

**Q: 获取新闻失败**
A: 确保网络连接正常，并检查Inoreader认证状态

**Q: AI过滤失败**
A: 确认OpenAI API密钥有效且有足够余额

**Q: 页面显示空白**
A: 检查浏览器控制台错误，确保JavaScript正常加载

### 查看详细日志
Web界面会实时显示每个步骤的详细执行日志，包括错误信息。如果遇到问题，请查看相应步骤的日志输出。

## 支持

如有问题或建议，请查看日志输出或联系开发团队。