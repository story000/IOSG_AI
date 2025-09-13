"""Inoreader service for fetching news articles"""

import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

class InoreaderService:
    """Service for fetching articles from Inoreader feeds"""
    
    # Target feeds configuration
    TARGET_FEEDS = {
        "feed/https://rss.panewslab.com/zh/gtimg/rss": "PANews",
        "feed/https://www.techflowpost.com/rss.aspx": "TechFlow",
        "feed/https://wublockchain123.substack.com/feed": "Wu Blockchain",
        "feed/https://cn.cointelegraph.com/rss": "Cointelegraph中文",
        "feed/https://substack.chainfeeds.xyz/feed": "ChainFeeds",
        "feed/https://api.theblockbeats.news/v1/open-api/home-xml": "The BlockBeats",
        "feed/https://www.odaily.news/v1/openapi/odailyrss": "Odaily",
        "feed/https://www.coindesk.com/arc/outboundfeeds/rss/?outputType=xml": "Coindesk"
    }
    
    def __init__(self, client_id: str = None, client_secret: str = None):
        # 优先使用传入的参数，其次使用环境变量，最后使用默认值
        self.client_id = client_id or os.getenv('INOREADER_CLIENT_ID', '1000001559')
        self.client_secret = client_secret or os.getenv('INOREADER_CLIENT_SECRET', 'lDyl2_XuuueJYcFZOwNipRy79_TibMOH')
        
    def clean_html(self, html_content: str) -> str:
        """Clean HTML tags from content"""
        if not html_content:
            return ""
        # Remove HTML tags
        clean = re.sub(r'<[^>]+>', '', html_content)
        # Decode HTML entities
        import html
        clean = html.unescape(clean)
        # Remove extra whitespace
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean
    
    def format_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Format article information"""
        formatted = {
            'id': article.get('id', ''),
            'title': article.get('title', ''),
            'author': article.get('author', ''),
            'published': article.get('published', 0),
            'published_formatted': '',
            'updated': article.get('updated', 0),
            'url': '',
            'feed_title': '',
            'feed_url': '',
            'content': '',
            'content_text': '',
            'categories': article.get('categories', [])
        }
        
        # Format publish time
        try:
            if formatted['published']:
                dt = datetime.fromtimestamp(formatted['published'])
                formatted['published_formatted'] = dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            pass
        
        # Get article URL
        canonical = article.get('canonical', [])
        if canonical:
            formatted['url'] = canonical[0].get('href', '')
        
        # Get feed info
        origin = article.get('origin', {})
        formatted['feed_title'] = origin.get('title', '')
        formatted['feed_url'] = origin.get('streamId', '')
        
        # Get content
        summary = article.get('summary', {})
        content = summary.get('content', '')
        formatted['content'] = content
        formatted['content_text'] = self.clean_html(content)
        
        return formatted
    
    def fetch_feeds(self, progress_callback=None, log_callback=None) -> Dict[str, Any]:
        """Fetch articles from Inoreader feeds"""
        
        # Check if we have recent data (within 24 hours)
        latest_file = Path("latest_feeds.json")
        if latest_file.exists():
            file_time = datetime.fromtimestamp(latest_file.stat().st_mtime)
            time_diff = datetime.now() - file_time
            
            if log_callback:
                log_callback(f"发现已存在的feeds文件")
                log_callback(f"创建时间: {file_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if time_diff.total_seconds() < 86400:  # 24 hours
                if log_callback:
                    log_callback("文件较新（24小时内），使用现有文件")
                
                with open(latest_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        
        # Import InoreaderClient from project root; fallback to mock on failure
        try:
            from inoreader_client import InoreaderClient
        except Exception:
            return self._create_mock_data(progress_callback, log_callback)
        
        if log_callback:
            log_callback("获取指定Feeds的未读文章")
            log_callback(f"目标feeds: {len(self.TARGET_FEEDS)} 个")
        
        # Create client
        client = InoreaderClient(self.client_id, self.client_secret)
        
        if not client.is_authenticated():
            if log_callback:
                log_callback("需要认证，请运行认证程序")
            raise ValueError("Inoreader authentication required")
        
        all_articles = []
        feed_stats = {}
        
        for feed_id, feed_name in self.TARGET_FEEDS.items():
            if log_callback:
                log_callback(f"正在获取 {feed_name} 的未读文章...")
            
            try:
                # Get unread articles from this feed
                result = client.get_unread_articles(
                    stream_id=feed_id,
                    max_articles=None,
                    include_read=False
                )
                
                articles = result['articles']
                count = len(articles)
                
                if log_callback:
                    log_callback(f"✓ {feed_name}: 找到 {count} 篇未读文章")
                
                # Format articles and add feed identifier
                for article in articles:
                    formatted_article = self.format_article(article)
                    formatted_article['source_feed'] = feed_name
                    formatted_article['source_feed_id'] = feed_id
                    all_articles.append(formatted_article)
                
                feed_stats[feed_name] = count
                
            except Exception as e:
                if log_callback:
                    log_callback(f"✗ {feed_name}: 获取失败 - {e}")
                feed_stats[feed_name] = 0
        
        # Statistics
        total_articles = len(all_articles)
        if log_callback:
            log_callback(f"获取完成: 总计 {total_articles} 篇未读文章")
        
        # Filter articles from last 7 days
        seven_days_ago = datetime.now() - timedelta(days=7)
        seven_days_timestamp = seven_days_ago.timestamp()
        
        original_count = len(all_articles)
        all_articles = [article for article in all_articles 
                       if article.get('published', 0) >= seven_days_timestamp]
        filtered_count = len(all_articles)
        
        if log_callback:
            log_callback(f"应用7天时间过滤: {original_count} -> {filtered_count} 篇")
        
        # Sort by publish time (newest first)
        all_articles.sort(key=lambda x: x.get('published', 0), reverse=True)
        
        # Prepare data to save
        save_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_articles': filtered_count,
                'original_total': original_count,
                'filtered_out': original_count - filtered_count,
                'filter_days': 7,
                'filter_cutoff': seven_days_ago.isoformat(),
                'feeds_stats': feed_stats,
                'target_feeds': list(self.TARGET_FEEDS.values())
            },
            'articles': all_articles
        }
        
        # Save to file
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        
        if log_callback:
            log_callback(f"数据已保存到: {latest_file}")
        
        if progress_callback:
            progress_callback(100, "Fetch completed")
        
        return save_data
    
    def _create_mock_data(self, progress_callback=None, log_callback=None) -> Dict[str, Any]:
        """Create mock data when Inoreader client is not available"""
        if log_callback:
            log_callback("使用模拟数据（Inoreader客户端不可用）")
        
        # Check if we have existing data
        latest_file = Path("latest_feeds.json")
        if latest_file.exists():
            with open(latest_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Create empty structure
        return {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_articles': 0,
                'original_total': 0,
                'filtered_out': 0,
                'filter_days': 7,
                'filter_cutoff': (datetime.now() - timedelta(days=7)).isoformat(),
                'feeds_stats': {feed_name: 0 for feed_name in self.TARGET_FEEDS.values()},
                'target_feeds': list(self.TARGET_FEEDS.values())
            },
            'articles': []
        }
