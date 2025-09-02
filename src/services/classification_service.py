"""Article classification service"""

import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple
import yaml

class ClassificationService:
    """Service for classifying crypto news articles"""
    
    def __init__(self):
        self.config = self._load_config()
        self.portfolios = self.config.get('portfolio_projects', [])
        self.categories = self.config.get('classification', {}).get('categories', {})
        self.title_exclusion_keywords = self.config.get('content_filters', {}).get('title_exclusion_keywords', [])
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            config_file = Path("crypto_config.yaml")
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                print(f"✅ 已加载配置文件: {config_file}")
                return config
        except Exception as e:
            print(f"❌ 加载配置失败: {e}，使用默认配置")
        
        # Return default config
        return {
            'portfolio_projects': [],
            'classification': {'categories': {}},
            'content_filters': {'title_exclusion_keywords': []}
        }
    
    def preprocess_text(self, text: str) -> str:
        """Preprocess text: convert to lowercase, remove special characters"""
        if not text:
            return ""
        # Keep Chinese, English, numbers and basic punctuation
        text = re.sub(r'[^\u4e00-\u9fff\w\s\.\,\!\?\-\+\%\$]', ' ', text)
        return text.lower()
    
    def calculate_score(self, text: str, keywords: List[str], patterns: List[str]) -> float:
        """Calculate text matching score with keywords and patterns"""
        text = self.preprocess_text(text)
        score = 0
        
        # Calculate keyword matching score
        for keyword in keywords:
            keyword_lower = keyword.lower()
            # Count keyword occurrences
            count = len(re.findall(r'\b' + re.escape(keyword_lower) + r'\b', text))
            if count == 0:
                # For Chinese keywords, use simple contains match
                count = text.count(keyword_lower)
            score += count
        
        # Calculate pattern matching score (higher weight)
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            score += len(matches) * 2  # Pattern matches get 2x weight
        
        return score
    
    def check_portfolio_mention(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Check if article mentions IOSG portfolio projects"""
        title = article.get('title', '')
        text = self.preprocess_text(title.lower())
        mentioned_projects = []
        
        for project in self.portfolios:
            pattern = r'\b' + re.escape(project.lower()) + r'\b'
            if re.search(pattern, text):
                mentioned_projects.append(project)
        
        portfolio = len(mentioned_projects) > 0
        
        return {
            'portfolio': portfolio,
            'mentioned_projects': mentioned_projects,
            'mention_count': len(mentioned_projects)
        }
    
    def classify_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Classify a single article"""
        # Combine title and content text
        title = article.get('title', '')
        content = article.get('content_text', '')
        combined_text = f"{title} {content}"
        
        scores = {}
        
        # Check portfolio keywords
        portfolio_info = self.check_portfolio_mention(article)
        
        # If article mentions portfolio projects, classify as portfolios
        if portfolio_info['portfolio']:
            return {
                'category': 'portfolios',
                'confidence': portfolio_info['mention_count'],
                'scores': {'portfolios': portfolio_info['mention_count']},
                'portfolio': portfolio_info['portfolio'],
                'mentioned_projects': portfolio_info['mentioned_projects'],
                'mention_count': portfolio_info['mention_count']
            }
        
        # Calculate scores for each category (excluding portfolios and 其他)
        for category, config in self.categories.items():
            if category in ["其他", "portfolios"]:
                continue  # Skip fallback category and portfolios
            
            keywords = config['keywords']
            patterns = config.get('patterns', [])
            weight = config['weight']
            score = self.calculate_score(combined_text, keywords, patterns) * weight
            scores[category] = score
        
        # Find the highest scoring category
        if scores and max(scores.values()) > 0:
            best_category = max(scores, key=scores.get)
            confidence = scores[best_category]
        else:
            best_category = "其他"
            confidence = 0
        
        return {
            'category': best_category,
            'confidence': confidence,
            'scores': scores,
            'portfolio': portfolio_info['portfolio'],
            'mentioned_projects': portfolio_info['mentioned_projects'],
            'mention_count': portfolio_info['mention_count']
        }
    
    def classify_articles(self, articles: List[Dict[str, Any]], 
                         progress_callback=None, log_callback=None) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        """Classify all articles"""
        classified_articles = []
        category_stats = defaultdict(int)
        
        if log_callback:
            log_callback(f"开始分类 {len(articles)} 篇文章...")
        
        for i, article in enumerate(articles, 1):
            if i % 100 == 0:
                if log_callback:
                    log_callback(f"已处理 {i}/{len(articles)} 篇文章")
                if progress_callback:
                    progress = int(i / len(articles) * 100)
                    progress_callback(progress, f"Processing {i}/{len(articles)}")
            
            classification = self.classify_article(article)
            
            # Add classification info to article
            article_with_class = article.copy()
            article_with_class.update({
                'classification': classification['category'],
                'classification_confidence': classification['confidence'],
                'classification_scores': classification['scores'],
                'portfolio': classification['portfolio'],
                'mentioned_projects': classification['mentioned_projects'],
                'mention_count': classification['mention_count']
            })
            
            classified_articles.append(article_with_class)
            category_stats[classification['category']] += 1
        
        return classified_articles, dict(category_stats)
    
    def filter_by_keywords(self, articles: List[Dict[str, Any]], 
                          log_callback=None) -> List[Dict[str, Any]]:
        """Filter articles by exclusion keywords"""
        if not self.title_exclusion_keywords:
            return articles
        
        if log_callback:
            log_callback(f"应用标题关键词过滤")
            log_callback(f"排除关键词: {len(self.title_exclusion_keywords)} 个")
        
        original_count = len(articles)
        filtered_articles = []
        
        for article in articles:
            title = article.get('title', '').lower()
            content = article.get('content_text', '').lower()
            combined_text = f"{title} {content}"
            
            # Check if any exclusion keyword is present
            should_exclude = False
            for keyword in self.title_exclusion_keywords:
                if keyword.lower() in combined_text:
                    should_exclude = True
                    break
            
            if not should_exclude:
                filtered_articles.append(article)
        
        if log_callback:
            log_callback(f"原始文章数: {original_count}")
            log_callback(f"过滤后文章数: {len(filtered_articles)}")
            log_callback(f"过滤掉: {original_count - len(filtered_articles)} 篇")
        
        return filtered_articles
    
    def run_classification(self, progress_callback=None, log_callback=None) -> Dict[str, Any]:
        """Run the complete classification process"""
        # Load latest feeds
        input_file = Path("latest_feeds.json")
        
        if not input_file.exists():
            if log_callback:
                log_callback(f"文件 {input_file} 不存在")
            raise FileNotFoundError(f"File {input_file} does not exist")
        
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        articles = data.get('articles', [])
        metadata = data.get('metadata', {})
        
        if log_callback:
            log_callback(f"加密货币文章智能分类器")
            log_callback(f"输入文件: {input_file}")
            log_callback(f"文章总数: {len(articles)}")
            log_callback(f"来源统计: {metadata.get('feeds_stats', {})}")
        
        # Apply keyword filtering
        filtered_articles = self.filter_by_keywords(articles, log_callback)
        
        # Classify articles
        classified_articles, category_stats = self.classify_articles(
            filtered_articles, progress_callback, log_callback
        )
        
        # Organize by category
        articles_by_category = defaultdict(list)
        for article in classified_articles:
            category = article.get('classification', '其他')
            articles_by_category[category].append(article)
        
        # Prepare output data
        output_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_articles': len(classified_articles),
                'original_articles': len(articles),
                'filtered_out': len(articles) - len(filtered_articles),
                'category_stats': category_stats,
                'sources': metadata.get('feeds_stats', {})
            },
            'categories': dict(articles_by_category),
            'all_articles': classified_articles
        }
        
        # Save to file
        output_file = Path("latest_classified.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        if log_callback:
            log_callback(f"分类完成！")
            log_callback(f"结果已保存到: {output_file}")
            for category, count in category_stats.items():
                log_callback(f"  {category}: {count} 篇")
        
        if progress_callback:
            progress_callback(100, "Classification completed")
        
        return output_data