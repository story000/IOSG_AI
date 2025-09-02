"""Report generation service following the original format"""

import re
import json
import glob
import os
from datetime import datetime
from typing import List, Dict, Any, Tuple
from pathlib import Path
import yaml
import openai


class ReportGenerator:
    """Generate formatted report following the original IOSG format"""
    
    def __init__(self, ai_service=None):
        self.ai_service = ai_service
        self.config = self._load_config()
        self.global_counter = 1
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            config_file = Path("crypto_config.yaml")
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
        return {}
    
    def clean_content(self, content: str) -> str:
        """Clean news content by removing source prefixes"""
        if not content:
            return ""
        
        # Remove various news source prefixes
        content = re.sub(r'.*?消息[，,]\s*', '', content)
        content = re.sub(r'.*?报道[，,]\s*', '', content)
        content = re.sub(r'深潮\s*TechFlow\s*[消息报道]*[，,]\s*', '', content)
        content = re.sub(r'TechFlow\s*深潮\s*[消息报道]*[，,]\s*', '', content)
        content = re.sub(r'PANews\s*\d+月\d+日消息[，,]\s*', '', content)
        content = re.sub(r'Wu\s*Blockchain\s*[消息报道]*[，,]\s*', '', content)
        content = re.sub(r'Cointelegraph\s*中文\s*[消息报道]*[，,]\s*', '', content)
        
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content).strip()
        return content
    
    def delete_reports(self, articles: List[Dict]) -> List[Dict]:
        """Filter out daily/weekly/monthly reports"""
        new_articles = []
        for article in articles:
            if not re.search(r"周报|日报|月报", article.get('title', '')) or len(article.get('content_text', '')) > 200:
                new_articles.append(article)
        return new_articles
    
    def categorize_by_length(self, filtered_results: Dict[str, List[Dict]]) -> Tuple[Dict, Dict]:
        """Categorize articles into news and reports based on content length"""
        
        # Define category mappings
        all_sections = [
            ("项目融资", filtered_results.get("项目融资", []), "项目融资介绍"),
            ("基金融资", filtered_results.get("基金融资", []), "基金融资介绍"),
            ("公链/L2/主网", filtered_results.get("公链/L2/主网", []), "公链/L2/主网"),
            ("中间件/工具协议", filtered_results.get("中间件/工具协议", []), "中间件/工具协议"),
            ("DeFi", filtered_results.get("DeFi", []), "DeFi"),
            ("RWA", filtered_results.get("RWA", []), "RWA"),
            ("稳定币", filtered_results.get("稳定币", []), "稳定币"),
            ("应用协议", filtered_results.get("应用协议", []), "应用协议"),
            ("GameFi", filtered_results.get("GameFi", []), "GameFi"),
            ("交易所/钱包", filtered_results.get("交易所/钱包", []), "交易所/钱包"),
            ("AI + Crypto", filtered_results.get("AI + Crypto", []), "AI + Crypto"),
            ("DePIN", filtered_results.get("DePIN", []), "DePIN"),
            ("Portfolio", filtered_results.get("portfolios", []), "Our portfolio")
        ]
        
        news_articles = {}
        report_articles = {}
        
        for category_name, articles_list, section_title in all_sections:
            if articles_list:
                news_articles[category_name] = {'title': section_title, 'articles': []}
                report_articles[category_name] = {'title': section_title, 'articles': []}
                
                for article in self.delete_reports(articles_list):
                    content = self.clean_content(article.get('content_text', ''))
                    
                    # Categorize based on content length
                    article_data = {
                        'title': article.get('title', ''),
                        'url': article.get('url', ''),
                        'content': content
                    }
                    
                    if len(content) > 700:
                        report_articles[category_name]['articles'].append(article_data)
                    else:
                        news_articles[category_name]['articles'].append(article_data)
        
        return news_articles, report_articles
    
    def generate_funding_table(self, funding_articles: List[Dict]) -> str:
        """Generate funding information table using AI"""
        if not funding_articles or not self.ai_service:
            return ""
        
        try:
            # Get funding table extraction config
            funding_config = self.config.get('funding_table_extraction', {})
            prompt_template = funding_config.get('prompt_template', '')
            
            if not prompt_template:
                print("  ⚠️ No funding_table_extraction config found")
                return ""
            
            print(f"  📊 Generating funding table for {len(funding_articles)} articles...")
            
            # Build articles content
            articles_content = ""
            for i, article in enumerate(funding_articles, 1):
                articles_content += f"\n=== 融资新闻 {i} ===\n"
                articles_content += f"标题：{article['title']}\n"
                articles_content += f"内容：{article['content']}\n"
            
            # Format prompt
            prompt = prompt_template.format(
                total_articles=len(funding_articles),
                articles_content=articles_content
            )
            
            # Call AI API
            response = self.ai_service.client.chat.completions.create(
                model=self.ai_service.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4000,
                temperature=0
            )
            
            ai_result = response.choices[0].message.content.strip()
            
            # Parse JSON to markdown table
            return self.parse_json_to_markdown_table(ai_result)
            
        except Exception as e:
            print(f"  ❌ Failed to generate funding table: {e}")
            return ""
    
    def parse_json_to_markdown_table(self, ai_result: str) -> str:
        """Parse AI JSON response to markdown table"""
        try:
            # Extract JSON part
            json_text = ai_result
            if '{' in ai_result:
                start = ai_result.find('{')
                end = ai_result.rfind('}') + 1
                json_text = ai_result[start:end]
            
            # Parse JSON
            data = json.loads(json_text)
            funding_list = data.get('funding_list', [])
            
            if not funding_list:
                return ""
            
            # Generate markdown table
            table_lines = []
            table_lines.append("| 受资方 | 投资方 | 赛道 | 涉及金额 |")
            table_lines.append("|--------|--------|------|----------|")
            
            for item in funding_list:
                company = item.get('company', '未披露')
                investors = item.get('investors', '未披露')
                sector = item.get('sector', '未披露')
                amount = item.get('amount', '未披露')
                
                # Ensure cell content doesn't contain | character
                company = str(company).replace('|', '/')
                investors = str(investors).replace('|', '/')
                sector = str(sector).replace('|', '/')
                amount = str(amount).replace('|', '/')
                
                table_lines.append(f"| {company} | {investors} | {sector} | {amount} |")
            
            return '\n'.join(table_lines) + '\n'
            
        except Exception as e:
            print(f"  ❌ Failed to parse table: {e}")
            return ""
    
    def summarize_report_with_ai(self, article_content: str) -> str:
        """Use AI to summarize report content"""
        if not self.ai_service:
            return article_content
        
        try:
            # Get paragraph_water_info config
            paragraph_config = self.config.get('paragraph_water_info', {})
            prompt_template = paragraph_config.get('prompt_template', '')
            
            if not prompt_template:
                return article_content
            
            # Format prompt
            prompt = prompt_template.format(article_text=article_content)
            
            # Call AI API
            response = self.ai_service.client.chat.completions.create(
                model=self.ai_service.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.3
            )
            
            summarized = response.choices[0].message.content.strip()
            print(f"  ✅ AI summary: {len(article_content)} → {len(summarized)} chars")
            return summarized
            
        except Exception as e:
            print(f"  ❌ AI summary failed: {e}")
            return article_content
    
    def generate_report(self, filtered_results: Dict[str, List[Dict]]) -> str:
        """Generate the complete formatted report"""
        
        # Reset counter
        self.global_counter = 1
        
        # Categorize articles by length
        news_articles, report_articles = self.categorize_by_length(filtered_results)
        
        # Build report content
        report_lines = []
        
        # News section
        report_lines.append("# 📰 新闻\n")
        
        # Generate funding table for project funding
        funding_table = ""
        if "项目融资" in news_articles and news_articles["项目融资"]['articles']:
            funding_articles = news_articles["项目融资"]['articles']
            if self.ai_service:
                funding_table = self.generate_funding_table(funding_articles)
        
        # Write news sections
        for category_name, category_data in news_articles.items():
            if category_data['articles']:
                report_lines.append(f"## {category_data['title']}\n")
                
                # Add funding table for project funding category
                if "项目融资" in category_name and funding_table:
                    report_lines.append("### 📊 投融资清单\n")
                    report_lines.append(funding_table)
                    report_lines.append("\n### 📰 详细新闻\n")
                
                # Add articles
                for article in category_data['articles']:
                    report_lines.append(f"{self.global_counter}. [{article['title']}]({article['url']})\n")
                    report_lines.append(f"{article['content']}\n")
                    self.global_counter += 1
        
        print(f"  📝 Report Generated")
        return '\n'.join(report_lines)
    
    def save_report(self, report_content: str, filename: str = None) -> str:
        """Save report to file"""
        # Clean up old report files before saving new one
        try:
            # Get current working directory for absolute paths
            current_dir = os.getcwd()
            
            # Delete old formatted reports in current directory
            old_reports = glob.glob(os.path.join(current_dir, "formatted_report_*.txt"))
            for old_file in old_reports:
                os.remove(old_file)
                print(f"🗑️ Deleted old report: {os.path.basename(old_file)}")
            
            # Delete old report JSON files in current directory  
            old_jsons = glob.glob(os.path.join(current_dir, "report_*.json"))
            for old_file in old_jsons:
                os.remove(old_file)
                print(f"🗑️ Deleted old JSON: {os.path.basename(old_file)}")
            
            # Delete old test report files
            old_tests = glob.glob(os.path.join(current_dir, "test_report_*.txt"))
            for old_file in old_tests:
                os.remove(old_file)
                print(f"🗑️ Deleted old test report: {os.path.basename(old_file)}")
                
        except Exception as e:
            print(f"⚠️ Failed to clean old files: {e}")
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            suffix = "_ai_deduplicated" if self.ai_service else "_deduplicated"
            filename = f"formatted_report_{timestamp}{suffix}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"📋 Report saved to: {filename}")
        return filename