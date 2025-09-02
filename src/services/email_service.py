"""Email service for sending reports"""

import os
import yaml
import re
import markdown
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from typing import Optional
from flask_mail import Mail, Message
from pathlib import Path

from ..models.report import Report


class EmailService:
    """Service for sending email reports"""
    
    def __init__(self, mail: Mail = None, smtp_config: dict = None):
        self.mail = mail
        self.smtp_config = smtp_config or {}
    
    def send_report(self, report: Report, recipient_email: str, 
                   subject: str = None) -> bool:
        """Send report via email using direct SMTP"""
        try:
            if subject is None:
                subject = f'📊 IOSG 加密货币新闻分析报告 - {datetime.now().strftime("%Y-%m-%d")}'
            
            # Use formatted content if available, otherwise convert report to markdown
            if hasattr(report, 'formatted_content') and report.formatted_content:
                report_content = report.formatted_content
            else:
                report_content = self._report_to_markdown(report)
            
            # Convert markdown to HTML using old version logic
            html_content = self._convert_markdown_to_html_old_style(report_content)
            
            # Create plain text version following old version format
            plain_text = f"""
IOSG 加密货币新闻分析报告 - {datetime.now().strftime("%Y-%m-%d")}

{report_content}

---
本报告由 IOSG Crypto News Analysis System 自动生成
生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

IOSG Team
            """.strip()
            
            # Send using direct SMTP
            return self._send_email_direct_smtp(
                recipient_email, subject, plain_text, html_content
            )
            
        except Exception as e:
            print(f"邮件发送失败: {e}")
            return False
    
    def send_test_email(self, recipient_email: str) -> bool:
        """Send test email"""
        try:
            test_content = self._generate_test_content(recipient_email)
            html_content = self._convert_markdown_to_html_old_style(test_content)
            
            # Send using direct SMTP
            return self._send_email_direct_smtp(
                recipient_email,
                "📧 IOSG 邮件系统测试 - 配置成功", 
                test_content,
                html_content
            )
            
        except Exception as e:
            print(f"Failed to send test email: {e}")
            return False
    
    def _generate_html_content(self, report: Report) -> str:
        """Generate HTML email content from report"""
        # Convert report sections to markdown
        markdown_content = self._report_to_markdown(report)
        
        # Convert to HTML with styling
        return self._convert_markdown_to_html_old_style(markdown_content)
    
    def _generate_plain_content(self, report: Report) -> str:
        """Generate plain text email content"""
        content = f"""
IOSG 加密货币新闻分析报告 - {datetime.now().strftime("%Y-%m-%d")}

{self._report_to_markdown(report)}

---
本报告由 IOSG Crypto News Analysis System 自动生成
生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

IOSG Team
        """.strip()
        
        return content
    
    def _report_to_markdown(self, report: Report) -> str:
        """Convert report to markdown format"""
        # If report has formatted content from ReportGenerator, use it
        if hasattr(report, 'formatted_content') and report.formatted_content:
            return report.formatted_content
        
        # Otherwise generate standard format
        lines = [f"# {report.title}", ""]
        
        # Add statistics
        lines.extend([
            "## 📊 本期统计",
            "",
            f"- **总文章数**: {report.total_articles}篇",
            f"- **新闻源数**: {report.total_sources}个", 
            f"- **生成时间**: {report.generated_at.strftime('%Y-%m-%d %H:%M')}",
            ""
        ])
        
        # Add sections
        for section in report.sections:
            if section.articles:
                lines.extend([
                    f"## {section.title}",
                    ""
                ])
                
                if section.summary:
                    lines.extend([section.summary, ""])
                
                # Add articles as numbered list
                for i, article in enumerate(section.articles, 1):
                    lines.append(f"{i}. [{article.title}]({article.url})")
                    lines.append(f"   *来源: {article.source_feed}*")
                    lines.append("")
        
        return "\n".join(lines)
    
    def _convert_markdown_to_html(self, markdown_content: str) -> str:
        """Convert markdown to styled HTML"""
        # Convert markdown to HTML
        md = markdown.Markdown(extensions=['tables', 'fenced_code', 'codehilite', 'sane_lists'])
        html_content = md.convert(markdown_content)
        
        # Add CSS styling
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
                    border-bottom: 3px solid #ff604a;
                    padding-bottom: 10px;
                    color: #ff604a;
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
                    background: linear-gradient(135deg, #ff604a 0%, #ff8a7a 100%);
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
                ol, ul {{
                    padding-left: 20px;
                    margin: 1em 0;
                }}
                ol {{
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
                    color: #ff604a;
                }}
                li {{
                    margin-bottom: 8px;
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
                        <a href="https://iosg.vc" style="color: #ff604a;">IOSG Ventures</a> | 
                        专业的加密投资机构
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return styled_html
    
    def _send_email_direct_smtp(self, recipient_email: str, subject: str, 
                              plain_text: str, html_content: str) -> bool:
        """Send email using direct SMTP connection"""
        try:
            # Get SMTP configuration
            smtp_server = self.smtp_config.get('server', 'smtp.gmail.com')
            smtp_port = self.smtp_config.get('port', 587)
            username = self.smtp_config.get('username', os.getenv('MAIL_USERNAME'))
            password = self.smtp_config.get('password', os.getenv('MAIL_PASSWORD'))
            
            if not username or not password:
                print("❌ SMTP credentials not configured")
                return False
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = username
            msg['To'] = recipient_email
            
            # Create the plain-text and HTML version of your message
            part1 = MIMEText(plain_text, 'plain', 'utf-8')
            part2 = MIMEText(html_content, 'html', 'utf-8')
            
            # Add HTML/plain-text parts to MIMEMultipart message
            msg.attach(part1)
            msg.attach(part2)
            
            # Send the message via SMTP server
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()  # Enable encryption
                server.login(username, password)
                server.send_message(msg)
            
            print(f"✅ Email sent successfully to {recipient_email}")
            return True
            
        except Exception as e:
            print(f"❌ Direct SMTP failed: {e}")
            return False
    
    def _convert_markdown_to_html_old_style(self, markdown_content: str) -> str:
        """Convert markdown to HTML using old version logic"""
        # Convert markdown to HTML with same extensions as old version
        md = markdown.Markdown(extensions=['tables', 'fenced_code', 'codehilite', 'sane_lists'])
        html_content = md.convert(markdown_content)
        
        # Add CSS styling exactly like old version
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
        
        # Apply portfolio keyword highlighting in HTML
        styled_html = self._highlight_portfolio_in_html(styled_html)
        
        return styled_html
    
    def _highlight_portfolio_in_html(self, html_content: str) -> str:
        """Highlight portfolio keywords in HTML content"""
        try:
            # Load portfolio projects from config
            config_file = Path("crypto_config.yaml")
            if not config_file.exists():
                return html_content
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            portfolio_projects = config.get('portfolio_projects', [])
            if not portfolio_projects:
                return html_content
            
            # Only highlight keywords in Our portfolio section
            portfolio_section_pattern = r'(<h2[^>]*>Our portfolio</h2>.*?)(?=<h[12][^>]*>|$)'
            
            def highlight_portfolio_section(match):
                section_content = match.group(1)
                
                # Highlight each portfolio project name
                for project in portfolio_projects:
                    # Use word boundary to avoid partial matches
                    pattern = r'\b' + re.escape(project) + r'\b'
                    replacement = f'<span style="color: #e74c3c; font-weight: bold;">{project}</span>'
                    section_content = re.sub(pattern, replacement, section_content, flags=re.IGNORECASE)
                
                return section_content
            
            # Apply highlighting only to Our portfolio section
            highlighted_html = re.sub(
                portfolio_section_pattern,
                highlight_portfolio_section,
                html_content,
                flags=re.DOTALL | re.IGNORECASE
            )
            
            return highlighted_html
            
        except Exception as e:
            print(f"Portfolio highlighting failed: {e}")
            return html_content
    
    def _generate_test_content(self, recipient_email: str) -> str:
        """Generate test email content"""
        return f"""
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
- **接收邮箱**：{recipient_email}
- **邮件格式**：HTML (Markdown渲染)
- **列表编号**：如果上面的编号显示为1、2、3，则渲染正常

## 下一步

如果列表编号显示正确，现在您可以安全地使用自动报告功能了！

---

**IOSG Team**
        """.strip()