#!/usr/bin/env python3
"""
Crypto News Analysis Web Application
Web interface for cryptocurrency news fetching, classification, and AI filtering
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_socketio import SocketIO, emit
from flask_mail import Mail, Message
import json
import os
import glob
import subprocess
import threading
import time
from datetime import datetime
import sys
import io
import contextlib
import markdown
import yaml

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional

app = Flask(__name__)
app.config['SECRET_KEY'] = 'crypto-news-analyzer-secret-key'

# 邮件配置 - 使用环境变量或默认配置
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'your-email@gmail.com')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'your-app-password')
app.config['MAIL_DEFAULT_SENDER'] = app.config['MAIL_USERNAME']

socketio = SocketIO(app, cors_allowed_origins="*")
mail = Mail(app)

# Global variables to store process status
process_status = {
    'fetch': {'running': False, 'progress': 0, 'logs': []},
    'classify': {'running': False, 'progress': 0, 'logs': []},
    'ai_filter': {'running': False, 'progress': 0, 'logs': []}
}

# 自动报告状态
auto_report_status = {
    'running': False,
    'fetch': {'running': False, 'completed': False, 'failed': False},
    'classify': {'running': False, 'completed': False, 'failed': False},
    'ai_filter': {'running': False, 'completed': False, 'failed': False},
    'email': {'running': False, 'completed': False, 'failed': False},
    'completed': False,
    'failed': False,
    'error': None,
    'user_email': None
}

class LogCapture:
    """Capture print statements and send to web interface"""
    def __init__(self, process_name):
        self.process_name = process_name
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
    def __enter__(self):
        sys.stdout = self
        sys.stderr = self
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        
    def write(self, text):
        if text.strip():
            log_entry = {
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'message': text.strip()
            }
            process_status[self.process_name]['logs'].append(log_entry)
            socketio.emit('log_update', {
                'process': self.process_name,
                'log': log_entry
            })
        self.original_stdout.write(text)
        
    def flush(self):
        self.original_stdout.flush()

def load_crypto_config():
    """Load crypto configuration from YAML file"""
    try:
        with open('crypto_config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"Error loading crypto config: {e}")
        return {}

@app.route('/')
def index():
    """Main page"""
    # Load crypto configuration
    crypto_config = load_crypto_config()
    categories = list(crypto_config.get('classification', {}).get('categories', {}).keys())
    
    # Filter out 'portfolios' and '其他' for display
    display_categories = [cat for cat in categories if cat not in ['portfolios', '其他']]
    
    return render_template('index.html', categories=display_categories)

@app.route('/auto')
def auto_report():
    """Auto report page"""
    return render_template('auto_report.html')

@app.route('/labelhub')
def labelhub():
    """Label Hub page for manual article labeling"""
    return render_template('labelhub.html')

@app.route('/status')
def status():
    """Get current process status"""
    return jsonify(process_status)

@app.route('/fetch', methods=['POST'])
def fetch_feeds():
    """Fetch specific feeds"""
    if process_status['fetch']['running']:
        return jsonify({'error': 'Fetch process already running'}), 400
    
    def run_fetch():
        process_status['fetch']['running'] = True
        process_status['fetch']['progress'] = 0
        process_status['fetch']['logs'] = []
        
        try:
            with LogCapture('fetch'):
                # Import and run the fetch functionality with automation
                import fetch_specific_feeds
                # Mock user input for automated execution
                import builtins
                original_input = builtins.input
                
                def mock_input(prompt):
                    if "是否将这" in prompt and "篇文章标记为已读" in prompt:
                        print("自动选择: 跳过标记已读 (Web界面模式)")
                        return "n"  # Don't mark as read in web mode
                    else:
                        return "n"  # Default to no for any input
                
                builtins.input = mock_input
                
                try:
                    fetch_specific_feeds.main()
                finally:
                    builtins.input = original_input
                
            process_status['fetch']['progress'] = 100
            socketio.emit('process_complete', {'process': 'fetch'})
            
        except Exception as e:
            error_log = {
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'message': f'Error: {str(e)}'
            }
            process_status['fetch']['logs'].append(error_log)
            socketio.emit('log_update', {
                'process': 'fetch',
                'log': error_log
            })
        finally:
            process_status['fetch']['running'] = False
    
    thread = threading.Thread(target=run_fetch)
    thread.start()
    
    return jsonify({'status': 'started'})

@app.route('/classify', methods=['POST'])
def classify_articles():
    """Classify articles"""
    if process_status['classify']['running']:
        return jsonify({'error': 'Classification process already running'}), 400
    
    def run_classify():
        process_status['classify']['running'] = True
        process_status['classify']['progress'] = 0
        process_status['classify']['logs'] = []
        
        try:
            with LogCapture('classify'):
                # Import and run the classification functionality
                import classify_articles
                # Mock user input for automated execution
                import builtins
                original_input = builtins.input
                
                def mock_input(prompt):
                    # Auto-confirm any inputs in classification
                    return "y"
                
                builtins.input = mock_input
                
                try:
                    classify_articles.main()
                finally:
                    builtins.input = original_input
                
            process_status['classify']['progress'] = 100
            socketio.emit('process_complete', {'process': 'classify'})
            
        except Exception as e:
            error_log = {
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'message': f'Error: {str(e)}'
            }
            process_status['classify']['logs'].append(error_log)
            socketio.emit('log_update', {
                'process': 'classify',
                'log': error_log
            })
        finally:
            process_status['classify']['running'] = False
    
    thread = threading.Thread(target=run_classify)
    thread.start()
    
    return jsonify({'status': 'started'})

@app.route('/ai_filter', methods=['POST'])
def ai_filter():
    """AI filter and generate structured output"""
    if process_status['ai_filter']['running']:
        return jsonify({'error': 'AI filter process already running'}), 400
    
    # 获取API提供商和密钥
    provider = request.json.get('provider', 'deepseek')
    api_key = request.json.get('api_key', '')
    
    # 如果选择OpenAI但没有提供密钥，返回错误
    if provider == 'openai' and not api_key:
        return jsonify({'error': 'OpenAI API key is required when using OpenAI provider'}), 400
    
    def run_ai_filter():
        process_status['ai_filter']['running'] = True
        process_status['ai_filter']['progress'] = 0
        process_status['ai_filter']['logs'] = []
        
        try:
            # 设置环境变量
            if provider == 'openai':
                os.environ['OPENAI_API_KEY'] = api_key
            
            with LogCapture('ai_filter'):
                # Import and run the AI filter functionality
                from ai_filter import main as ai_filter_main
                
                # Mock user input for automated execution
                import builtins
                original_input = builtins.input
                
                def mock_input(prompt):
                    if "选择AI API提供商" in prompt:
                        return "1" if provider == "deepseek" else "2"
                    elif "请输入OpenAI API密钥" in prompt:
                        return api_key if provider == "openai" else ""
                    elif "要处理多少篇文章" in prompt:
                        return ""  # Use default (all articles)
                    elif "批处理大小" in prompt:
                        return "20"  # Use batch size 20
                    elif "确认处理" in prompt and "篇" in prompt and "文章" in prompt:
                        return "y"  # Confirm processing
                    else:
                        return "y"  # Default confirm
                
                builtins.input = mock_input
                
                try:
                    ai_filter_main()
                finally:
                    builtins.input = original_input
                
            process_status['ai_filter']['progress'] = 100
            socketio.emit('process_complete', {'process': 'ai_filter'})
            
        except Exception as e:
            error_log = {
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'message': f'Error: {str(e)}'
            }
            process_status['ai_filter']['logs'].append(error_log)
            socketio.emit('log_update', {
                'process': 'ai_filter',
                'log': error_log
            })
        finally:
            process_status['ai_filter']['running'] = False
    
    thread = threading.Thread(target=run_ai_filter)
    thread.start()
    
    return jsonify({'status': 'started'})

@app.route('/get_latest_output')
def get_latest_output():
    """Get the latest formatted output file"""
    try:
        # Find the latest formatted_report file
        report_files = glob.glob("formatted_report_*.txt")
        if not report_files:
            return jsonify({'error': 'No formatted report found'}), 404
        
        latest_file = max(report_files, key=os.path.getctime)
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            'filename': latest_file,
            'content': content,
            'created_at': datetime.fromtimestamp(os.path.getctime(latest_file)).isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/clear_logs/<process_name>')
def clear_logs(process_name):
    """Clear logs for a specific process"""
    if process_name in process_status:
        process_status[process_name]['logs'] = []
        return jsonify({'status': 'cleared'})
    return jsonify({'error': 'Invalid process name'}), 400

def convert_markdown_to_html(markdown_content):
    """将Markdown内容转换为HTML"""
    # 配置markdown扩展，添加sane_lists确保有序列表正确渲染
    md = markdown.Markdown(extensions=['tables', 'fenced_code', 'codehilite', 'sane_lists'])
    html_content = md.convert(markdown_content)
    
    # 添加CSS样式
    styled_html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f8f9fa;
            }}
            .container {{
                background-color: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            h1, h2, h3, h4, h5, h6 {{
                color: #2c3e50;
                margin-top: 2em;
                margin-bottom: 1em;
                font-weight: 600;
            }}
            h1 {{
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
                color: #3498db;
            }}
            h2 {{
                border-bottom: 2px solid #e74c3c;
                padding-bottom: 8px;
                color: #e74c3c;
            }}
            h3 {{
                color: #f39c12;
            }}
            a {{
                color: #3498db;
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
            p {{
                margin-bottom: 1em;
                text-align: justify;
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 8px;
            }}
            .footer {{
                margin-top: 40px;
                padding: 20px;
                background-color: #f8f9fa;
                border-radius: 8px;
                text-align: center;
                color: #6c757d;
                font-size: 14px;
            }}
            .section {{
                margin: 20px 0;
                padding: 15px;
                border-left: 4px solid #3498db;
                background-color: #f8f9fa;
            }}
            ul, ol {{
                padding-left: 20px;
                margin: 1em 0;
            }}
            ol {{
                list-style-type: decimal;
                counter-reset: item;
            }}
            ol > li {{
                display: block;
                margin-bottom: 8px;
            }}
            ol > li:before {{
                content: counter(item) ". ";
                counter-increment: item;
                font-weight: bold;
                color: #3498db;
            }}
            li {{
                margin-bottom: 8px;
            }}
            code {{
                background-color: #f1f1f1;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin: 0; border: none; color: white;">📊 IOSG 加密货币新闻分析报告</h1>
                <p style="margin: 10px 0 0 0; font-size: 16px;">
                    {datetime.now().strftime("%Y年%m月%d日")} | 专业版
                </p>
            </div>
            
            <div class="content">
                {html_content}
            </div>
            
            <div class="footer">
                <p><strong>本报告由 IOSG Crypto News Analysis System 自动生成</strong></p>
                <p>生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                <p>
                    <a href="https://iosg.vc" style="color: #3498db;">IOSG Ventures</a> | 
                    专业的加密投资机构
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    return styled_html

def send_report_email(email, report_content):
    """发送报告邮件"""
    try:
        with app.app_context():
            # 转换markdown为HTML
            html_content = convert_markdown_to_html(report_content)
            
            # 创建纯文本版本（备用）
            plain_text = f"""
IOSG 加密货币新闻分析报告 - {datetime.now().strftime("%Y-%m-%d")}

{report_content}

---
本报告由 IOSG Crypto News Analysis System 自动生成
生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

IOSG Team
            """.strip()
            
            msg = Message(
                subject=f'📊 IOSG 加密货币新闻分析报告 - {datetime.now().strftime("%Y-%m-%d")}',
                recipients=[email],
                body=plain_text,  # 纯文本版本
                html=html_content  # HTML版本
            )
            mail.send(msg)
        return True
    except Exception as e:
        print(f"邮件发送失败: {e}")
        return False

def reset_auto_report_status():
    """重置自动报告状态"""
    global auto_report_status
    auto_report_status.update({
        'running': False,
        'fetch': {'running': False, 'completed': False, 'failed': False},
        'classify': {'running': False, 'completed': False, 'failed': False},
        'ai_filter': {'running': False, 'completed': False, 'failed': False},
        'email': {'running': False, 'completed': False, 'failed': False},
        'completed': False,
        'failed': False,
        'error': None,
        'user_email': None
    })

def run_auto_step(step_name, step_function):
    """运行自动化步骤"""
    global auto_report_status
    
    auto_report_status[step_name]['running'] = True
    
    try:
        result = step_function()
        if result:
            auto_report_status[step_name]['completed'] = True
        else:
            auto_report_status[step_name]['failed'] = True
            auto_report_status['failed'] = True
            auto_report_status['error'] = f'{step_name} 步骤执行失败'
    except Exception as e:
        auto_report_status[step_name]['failed'] = True
        auto_report_status['failed'] = True
        auto_report_status['error'] = f'{step_name} 步骤出错: {str(e)}'
    finally:
        auto_report_status[step_name]['running'] = False

def auto_fetch():
    """自动执行获取步骤"""
    try:
        import fetch_specific_feeds
        import builtins
        original_input = builtins.input
        
        def mock_input(prompt):
            return "n"  # 跳过标记已读
        
        builtins.input = mock_input
        try:
            fetch_specific_feeds.main()
            return True
        finally:
            builtins.input = original_input
    except Exception as e:
        print(f"获取步骤失败: {e}")
        return False

def auto_classify():
    """自动执行分类步骤"""
    try:
        import classify_articles
        import builtins
        original_input = builtins.input
        
        def mock_input(prompt):
            return "y"
        
        builtins.input = mock_input
        try:
            classify_articles.main()
            return True
        finally:
            builtins.input = original_input
    except Exception as e:
        print(f"分类步骤失败: {e}")
        return False

def auto_ai_filter():
    """自动执行AI过滤步骤"""
    try:
        from ai_filter import main as ai_filter_main
        import builtins
        original_input = builtins.input
        
        def mock_input(prompt):
            if "选择AI API提供商" in prompt:
                return "1"  # DeepSeek
            elif "要处理多少篇文章" in prompt:
                return ""  # 默认全部
            elif "批处理大小" in prompt:
                return "20"  # 使用20的批处理大小
            elif "确认处理" in prompt:
                return "y"
            else:
                return "y"
        
        builtins.input = mock_input
        try:
            ai_filter_main()
            return True
        finally:
            builtins.input = original_input
    except Exception as e:
        print(f"AI过滤步骤失败: {e}")
        return False

def auto_send_email():
    """自动发送邮件"""
    try:
        # 获取最新的报告文件
        report_files = glob.glob("formatted_report_*.txt")
        if not report_files:
            return False
        
        latest_file = max(report_files, key=os.path.getctime)
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 发送邮件
        return send_report_email(auto_report_status['user_email'], content)
    except Exception as e:
        print(f"邮件发送步骤失败: {e}")
        return False

@app.route('/auto_generate_report', methods=['POST'])
def auto_generate_report():
    """启动自动生成报告"""
    global auto_report_status
    
    if auto_report_status['running']:
        return jsonify({'error': '自动报告生成正在进行中'}), 400
    
    email = request.json.get('email', '')
    if not email:
        return jsonify({'error': '邮箱地址是必需的'}), 400
    
    # 重置状态
    reset_auto_report_status()
    auto_report_status['running'] = True
    auto_report_status['user_email'] = email
    
    def run_auto_process():
        with app.app_context():
            try:
                # 步骤1: 获取文章
                run_auto_step('fetch', auto_fetch)
                if auto_report_status['failed']:
                    return
                
                time.sleep(2)  # 短暂等待
                
                # 步骤2: 分类文章
                run_auto_step('classify', auto_classify)
                if auto_report_status['failed']:
                    return
                
                time.sleep(2)  # 短暂等待
                
                # 步骤3: AI过滤
                run_auto_step('ai_filter', auto_ai_filter)
                if auto_report_status['failed']:
                    return
                
                time.sleep(2)  # 短暂等待
                
                # 步骤4: 发送邮件
                run_auto_step('email', auto_send_email)
                if auto_report_status['failed']:
                    return
                
                # 全部完成
                auto_report_status['completed'] = True
                
            except Exception as e:
                auto_report_status['failed'] = True
                auto_report_status['error'] = f'自动化流程出错: {str(e)}'
            finally:
                auto_report_status['running'] = False
    
    # 在新线程中运行
    thread = threading.Thread(target=run_auto_process)
    thread.start()
    
    return jsonify({'status': 'started'})

@app.route('/auto_report_status')
def get_auto_report_status():
    """获取自动报告状态"""
    return jsonify(auto_report_status)

@app.route('/preview_email')
def preview_email():
    """预览邮件HTML效果"""
    try:
        # 获取最新的报告文件
        report_files = glob.glob("formatted_report_*.txt")
        if not report_files:
            return "暂无报告文件可供预览", 404
        
        latest_file = max(report_files, key=os.path.getctime)
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 转换为HTML并返回
        html_content = convert_markdown_to_html(content)
        return html_content
        
    except Exception as e:
        return f"预览失败: {str(e)}", 500

@app.route('/test_email', methods=['POST'])
def test_email():
    """测试邮件发送功能"""
    try:
        email = request.json.get('email', '')
        if not email:
            return jsonify({'error': '邮箱地址是必需的'}), 400
        
        # 创建测试markdown内容
        test_markdown = f"""
# 📧 IOSG 邮件系统测试

## 测试成功！

恭喜！如果您收到这封邮件，说明：

- ✅ **邮件配置正确**
- ✅ **SMTP连接正常**  
- ✅ **HTML渲染功能正常**

## 有序列表测试

以下是测试有序列表的渲染效果：

1. [第一篇测试文章](https://example.com/article1)

这是第一篇文章的测试内容，用于验证有序列表编号是否正确显示...

2. [第二篇测试文章](https://example.com/article2)

这是第二篇文章的测试内容，应该显示编号2而不是重新从1开始...

3. [第三篇测试文章](https://example.com/article3)

这是第三篇文章的测试内容，应该显示编号3，以此类推...

## 测试信息

- **发送时间**：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **接收邮箱**：{email}
- **邮件格式**：HTML (Markdown渲染)
- **列表编号**：如果上面的编号显示为1、2、3，则渲染正常

## 下一步

如果列表编号显示正确，现在您可以安全地使用自动报告功能了！

---

**IOSG Team**
        """.strip()
        
        # 发送测试邮件
        with app.app_context():
            html_content = convert_markdown_to_html(test_markdown)
            
            msg = Message(
                subject='📧 IOSG 邮件系统测试 - 配置成功',
                recipients=[email],
                body=test_markdown,  # 纯文本版本
                html=html_content    # HTML版本
            )
            mail.send(msg)
        
        return jsonify({'status': 'success', 'message': '测试邮件发送成功'})
    except Exception as e:
        return jsonify({'error': f'邮件发送失败: {str(e)}'}), 500

@app.route('/labelhub/get_articles', methods=['GET'])
def get_labelhub_articles():
    """获取用于标注的文章"""
    try:
        count = int(request.args.get('count', 10))  # 每次获取的文章数量
        skip_labeled = request.args.get('skip_labeled', 'true').lower() == 'true'  # 是否跳过已标注的
        
        # 读取历史分类数据
        try:
            with open('historical_classified.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            return jsonify({'error': '未找到历史分类数据文件'}), 404
        
        articles = data.get('all_articles', [])
        
        # 过滤文章
        available_articles = []
        for article in articles:
            # 如果设置跳过已标注的文章
            if skip_labeled and ('human_label' in article and article['human_label'] is not None):
                continue
            available_articles.append(article)
        
        # 随机选择文章
        import random
        selected_articles = random.sample(available_articles, min(count, len(available_articles)))
        
        # 只返回必要的字段
        result_articles = []
        for article in selected_articles:
            result_articles.append({
                'id': article['id'],
                'title': article['title'],
                'content_text': article['content_text'],
                'source_feed': article['source_feed'],
                'published_formatted': article['published_formatted'],
                'classification': article['classification'],
                'url': article['url'],
                'human_label': article.get('human_label', None),
                'human_importance': article.get('human_importance', None)
            })
        
        return jsonify({
            'articles': result_articles,
            'total_available': len(available_articles),
            'total_articles': len(articles)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/labelhub/save_label', methods=['POST'])
def save_labelhub_label():
    """保存文章标签"""
    try:
        data = request.json
        article_id = data.get('article_id')
        human_label = data.get('human_label')
        human_importance = data.get('human_importance')
        
        if not article_id:
            return jsonify({'error': '文章ID是必需的'}), 400
        
        # 读取历史分类数据
        try:
            with open('historical_classified.json', 'r', encoding='utf-8') as f:
                historical_data = json.load(f)
        except FileNotFoundError:
            return jsonify({'error': '未找到历史分类数据文件'}), 404
        
        # 查找并更新文章（兼容新旧格式）
        articles_list = historical_data.get('all_articles', historical_data.get('articles', []))
        article_found = False
        for article in articles_list:
            if article['id'] == article_id:
                if human_label is not None:
                    article['human_label'] = human_label
                if human_importance is not None:
                    article['human_importance'] = bool(human_importance)  # 确保存储为布尔值
                # 添加标注时间戳
                article['human_labeled_at'] = datetime.now().isoformat()
                article_found = True
                break
        
        if not article_found:
            return jsonify({'error': '未找到指定文章'}), 404
        
        # 保存更新后的数据
        with open('historical_classified.json', 'w', encoding='utf-8') as f:
            json.dump(historical_data, f, ensure_ascii=False, indent=2)
        
        return jsonify({'status': 'success', 'message': '标签保存成功'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/labelhub/stats', methods=['GET'])
def get_labelhub_stats():
    """获取标注统计信息"""
    try:
        # 读取历史分类数据
        try:
            with open('historical_classified.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            return jsonify({'error': '未找到历史分类数据文件'}), 404
        
        # 兼容新旧格式
        articles = data.get('all_articles', data.get('articles', []))
        
        # 统计信息
        total_articles = len(articles)
        labeled_articles = len([a for a in articles if a.get('human_label') is not None])
        unlabeled_articles = total_articles - labeled_articles
        
        # 按分类统计
        label_counts = {}
        for article in articles:
            label = article.get('human_label')
            if label:
                label_counts[label] = label_counts.get(label, 0) + 1
        
        # 重要程度统计
        importance_counts = {
            'important': len([a for a in articles if a.get('human_importance') is True]),
            'not_important': len([a for a in articles if a.get('human_importance') is False])
        }
        
        # AI分类与人工标注准确率对比
        ai_correct = 0
        ai_total = 0
        for article in articles:
            ai_class = article.get('classification')
            human_label = article.get('human_label')
            if ai_class and human_label:
                ai_total += 1
                if ai_class == human_label:
                    ai_correct += 1
        
        ai_accuracy = round((ai_correct / ai_total) * 100, 1) if ai_total > 0 else 0
        
        return jsonify({
            'total_articles': total_articles,
            'labeled_articles': labeled_articles,
            'unlabeled_articles': unlabeled_articles,
            'label_counts': label_counts,
            'importance_counts': importance_counts,
            'ai_accuracy': ai_accuracy,
            'ai_correct': ai_correct,
            'ai_total': ai_total,
            'labeling_progress': round((labeled_articles / total_articles) * 100, 1) if total_articles > 0 else 0
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 全局评估状态
evaluation_status = {
    'running': False,
    'progress': 0,
    'current_step': '',
    'logs': [],
    'completed': False,
    'failed': False,
    'error': None,
    'results': None
}

@app.route('/evaluation')
def evaluation():
    """评估页面"""
    return render_template('evaluation.html')

@app.route('/evaluation/dataset_info')
def get_dataset_info():
    """获取测试数据集信息"""
    try:
        with open('historical_classified.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        articles = data.get('all_articles', data.get('articles', []))
        
        # 筛选有标注的文章
        labeled_articles = [a for a in articles if 
                          a.get('human_label') is not None and 
                          a.get('human_importance') is not None]
        
        # 统计信息
        important_count = len([a for a in labeled_articles if a.get('human_importance') is True])
        not_important_count = len([a for a in labeled_articles if a.get('human_importance') is False])
        
        # 获取所有分类
        categories = list(set(a.get('human_label') for a in labeled_articles if a.get('human_label')))
        
        return jsonify({
            'total_labeled': len(labeled_articles),
            'important_count': important_count,
            'not_important_count': not_important_count,
            'categories': sorted(categories)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/evaluation/start', methods=['POST'])
def start_evaluation():
    """开始评估"""
    global evaluation_status
    
    if evaluation_status['running']:
        return jsonify({'error': '评估正在进行中'}), 400
    
    # 重置状态
    evaluation_status.update({
        'running': True,
        'progress': 0,
        'current_step': '初始化评估...',
        'logs': [],
        'completed': False,
        'failed': False,
        'error': None,
        'results': None
    })
    
    def run_evaluation():
        try:
            # 导入评估模块
            from evaluation_system import SystemEvaluator
            
            evaluator = SystemEvaluator()
            
            # 添加日志函数
            def add_log(message):
                evaluation_status['logs'].append({
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'message': message
                })
            
            # 运行评估
            results = evaluator.run_evaluation(
                progress_callback=lambda p, step: evaluation_status.update({
                    'progress': p, 
                    'current_step': step
                }),
                log_callback=add_log
            )
            
            evaluation_status.update({
                'completed': True,
                'results': results,
                'progress': 100,
                'current_step': '评估完成'
            })
            
        except Exception as e:
            evaluation_status.update({
                'failed': True,
                'error': str(e),
                'current_step': f'评估失败: {str(e)}'
            })
        finally:
            evaluation_status['running'] = False
    
    # 在新线程中运行评估
    thread = threading.Thread(target=run_evaluation)
    thread.start()
    
    return jsonify({'status': 'started'})

@app.route('/evaluation/status')
def get_evaluation_status():
    """获取评估状态"""
    return jsonify(evaluation_status)

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('connected', {'data': 'Connected to server'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')

if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(line_buffering=True)  # 强制行缓冲
    socketio.run(app, debug=False, host='0.0.0.0', port=8080)