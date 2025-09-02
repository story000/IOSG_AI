"""Core business processor that orchestrates the entire pipeline"""

import time
from typing import List, Dict, Any, Callable, Optional
from datetime import datetime

from ..models.article import Article, ArticleStatus
from ..models.report import Report, ReportSection
from ..services.storage_service import StorageService
from ..services.ai_service import AIService
from ..services.email_service import EmailService
from ..services.report_generator import ReportGenerator
from ..services.deduplication_service import DeduplicationService
from ..utils.config import get_settings, get_crypto_config
from ..utils.logger import get_logger

logger = get_logger(__name__)


class NewsProcessor:
    """Main news processing pipeline orchestrator"""
    
    def __init__(self, 
                 storage_service: StorageService,
                 ai_service: AIService,
                 email_service: Optional[EmailService] = None):
        self.storage = storage_service
        self.ai_service = ai_service
        self.email_service = email_service
        self.settings = get_settings()
        self.crypto_config = get_crypto_config()
        
        # Processing state
        self.current_articles: List[Article] = []
        self.processing_stats = {}
        
    def run_full_pipeline(self, 
                         recipient_email: str = None,
                         progress_callback: Callable = None,
                         log_callback: Callable = None) -> Report:
        """Run the complete news processing pipeline"""
        
        logger.info("Starting full news processing pipeline")
        start_time = time.time()
        
        try:
            # Step 1: Fetch articles
            if progress_callback:
                progress_callback(0, "Fetching articles...")
            if log_callback:
                log_callback("开始获取新闻文章...")
                
            articles = self._fetch_articles()
            logger.info(f"Fetched {len(articles)} articles")
            
            if progress_callback:
                progress_callback(20, f"Fetched {len(articles)} articles")
                
            # Step 2: Classify articles
            if progress_callback:
                progress_callback(25, "Classifying articles...")
            if log_callback:
                log_callback("开始文章分类...")
                
            classified_articles = self._classify_articles(articles)
            logger.info(f"Classified {len(classified_articles)} articles")
            
            if progress_callback:
                progress_callback(50, "Classification completed")
                
            # Step 3: AI filtering and deduplication
            if progress_callback:
                progress_callback(55, "AI filtering...")
            if log_callback:
                log_callback("开始AI智能筛选...")
                
            filtered_articles = self._filter_and_deduplicate(classified_articles)
            logger.info(f"Filtered to {len(filtered_articles)} articles")
            
            if progress_callback:
                progress_callback(80, "AI filtering completed")
                
            # Step 4: Generate report
            if progress_callback:
                progress_callback(85, "Generating report...")
            if log_callback:
                log_callback("生成结构化报告...")
                
            report = self._generate_report(filtered_articles)
            
            # Step 5: Send email if requested
            if recipient_email and self.email_service:
                if progress_callback:
                    progress_callback(90, "Sending email...")
                if log_callback:
                    log_callback("发送邮件报告...")
                    
                success = self.email_service.send_report(report, recipient_email)
                if success:
                    logger.info(f"Report sent successfully to {recipient_email}")
                else:
                    logger.error(f"Failed to send report to {recipient_email}")
            
            # Update processing stats
            processing_time = time.time() - start_time
            self.processing_stats = {
                'processing_time_seconds': processing_time,
                'total_articles_processed': len(articles),
                'total_articles_classified': len(classified_articles),
                'total_articles_filtered': len(filtered_articles),
                'completion_time': datetime.now().isoformat()
            }
            
            report.processing_stats = self.processing_stats
            
            if progress_callback:
                progress_callback(100, "Pipeline completed")
            if log_callback:
                log_callback(f"流程完成！处理了{len(filtered_articles)}篇文章")
                
            logger.info(f"Pipeline completed in {processing_time:.2f} seconds")
            return report
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            if log_callback:
                log_callback(f"处理失败: {str(e)}")
            raise
    
    def _fetch_articles(self) -> List[Article]:
        """Fetch articles from storage or RSS feeds"""
        from ..services.inoreader_service import InoreaderService
        
        # Use InoreaderService to fetch latest data
        inoreader = InoreaderService()
        feeds_data = inoreader.fetch_feeds()
        
        articles = []
        for article_data in feeds_data.get('articles', []):
            try:
                article = Article.from_dict(article_data)
                article.status = ArticleStatus.RAW
                articles.append(article)
            except Exception as e:
                logger.warning(f"Failed to load article: {e}")
                continue
        
        self.current_articles = articles
        return articles
    
    def _classify_articles(self, articles: List[Article]) -> List[Article]:
        """Classify articles into categories"""
        from ..services.classification_service import ClassificationService
        
        # Use ClassificationService for proper classification
        classifier = ClassificationService()
        
        # Convert articles to dicts for classifier
        articles_data = [a.to_dict() for a in articles]
        
        # Apply filtering and classification
        filtered_articles = classifier.filter_by_keywords(articles_data)
        classified_articles_data, stats = classifier.classify_articles(filtered_articles)
        
        # Convert back to Article objects with classification
        classified_articles = []
        for article_data in classified_articles_data:
            try:
                article = Article.from_dict(article_data)
                article.classification = article_data.get('classification', '其他')
                article.status = ArticleStatus.CLASSIFIED
                classified_articles.append(article)
            except Exception as e:
                logger.warning(f"Failed to process classified article: {e}")
                continue
        
        logger.info(f"Classification stats: {stats}")
        return classified_articles
    
    def _classify_single_article(self, article: Article, 
                                categories: Dict[str, Any],
                                portfolio_projects: List[str]) -> Optional[str]:
        """Classify a single article"""
        text = f"{article.title} {article.content_text}".lower()
        
        # Check for portfolio projects first
        if article.is_portfolio_related(portfolio_projects):
            return "Portfolio"
        
        # Check other categories
        best_category = None
        best_score = 0
        
        for category_name, category_config in categories.items():
            if category_name in ['portfolios', '其他']:
                continue
                
            keywords = category_config.get('keywords', [])
            score = sum(1 for keyword in keywords if keyword.lower() in text)
            
            if score > best_score:
                best_score = score
                best_category = category_name
        
        return best_category if best_score > 0 else None
    
    def _filter_and_deduplicate(self, articles: List[Article]) -> List[Article]:
        """Apply AI filtering and deduplication using original ai_filter.py logic"""
        if not articles:
            return []
        
        # Import original AI filter
        import sys
        sys.path.insert(0, '/Users/liusiyuan/Desktop/AIVC/IOSG/src/services')
        from ai_filter_original import AIFundingFilter
        
        try:
            # Create original filter instance
            api_key = self.ai_service.api_key if hasattr(self.ai_service, 'api_key') else None
            provider = getattr(self.ai_service, 'provider', 'openai')
            
            if not api_key:
                logger.warning("No API key available for AI filtering, skipping AI filter")
                return self._simple_deduplication(articles)
                
            filter_instance = AIFundingFilter(api_key, provider)
            
            # Group articles by category
            categorized = {}
            for article in articles:
                category = article.classification or "其他"
                if category not in categorized:
                    categorized[category] = []
                categorized[category].append(article.to_dict())
            
            # Map categories to old format expected by ai_filter
            category_mapping = {
                "项目融资": "project",
                "基金融资": "fund", 
                "公链/L2/主网": "blockchain",
                "中间件/工具协议": "middleware",
                "DeFi": "defi",
                "RWA": "rwa",
                "稳定币": "stablecoin",
                "应用协议": "application",
                "GameFi": "gamefi",
                "交易所/钱包": "exchange_wallet",
                "AI + Crypto": "ai_crypto",
                "DePIN": "depin",
                "portfolios": "portfolio"
            }
            
            # Process each category using original logic
            filtered_results = {}
            batch_size = 20
            max_articles = None
            
            for category_name, category_articles in categorized.items():
                if category_articles:
                    article_type = category_mapping.get(category_name, category_name)
                    logger.info(f'Filtering {len(category_articles)} articles in {category_name}...')
                    
                    # Portfolio articles don't need AI filtering
                    if category_name == "portfolios":
                        deduplicated, dedup_stat = filter_instance.deduplicate_articles_by_title(category_articles, "Portfolio")
                        filtered_results[article_type] = deduplicated
                    else:
                        # Use original batch_filter method
                        ai_filtered = filter_instance.batch_filter_no_prompt(category_articles, batch_size, max_articles, article_type)
                        
                        # Apply title deduplication
                        if ai_filtered:
                            deduplicated, dedup_stat = filter_instance.deduplicate_articles_by_title(ai_filtered, category_name)
                            filtered_results[article_type] = deduplicated
                        else:
                            filtered_results[article_type] = []
                else:
                    article_type = category_mapping.get(category_name, category_name)
                    filtered_results[article_type] = []
            
            # Apply cross-category deduplication using original logic
            logger.info('Applying cross-category deduplication...')
            filtered_results, cross_dedup_stats = filter_instance.cross_category_deduplication(filtered_results)
            
            # Convert back to Article objects
            final_articles = []
            for category_key, article_dicts in filtered_results.items():
                for article_dict in article_dicts:
                    # Find the original Article object
                    for article in articles:
                        if article.title == article_dict.get('title'):
                            article.ai_filtered = True
                            article.status = ArticleStatus.AI_FILTERED
                            final_articles.append(article)
                            break
            
            logger.info(f"AI filtering completed: {len(final_articles)} articles remaining")
            return final_articles
            
        except Exception as e:
            logger.error(f"AI filtering failed: {e}, falling back to simple deduplication")
            return self._simple_deduplication(articles)
    
    def _simple_deduplication(self, articles: List[Article]) -> List[Article]:
        """Simple title-based deduplication"""
        seen_titles = set()
        deduplicated = []
        
        for article in articles:
            title_key = article.title.lower().strip()
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                deduplicated.append(article)
        
        logger.info(f"Deduplication: {len(deduplicated)}/{len(articles)} articles kept")
        return deduplicated
    
    def _generate_report(self, articles: List[Article]) -> Report:
        """Generate final report"""
        
        # Group articles by category for report generation
        categorized = {}
        for article in articles:
            category = article.classification or "其他"
            if category not in categorized:
                categorized[category] = []
            # Convert to dict format for ReportGenerator
            article_dict = article.to_dict()
            article_dict['content_text'] = article.content_text  # Ensure content_text is included
            categorized[category].append(article_dict)
        
        # Use ReportGenerator to create the formatted report
        report_generator = ReportGenerator(ai_service=self.ai_service)
        report_content = report_generator.generate_report(categorized)
        
        # Save the formatted report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        suffix = "_ai_deduplicated" if self.ai_service else "_deduplicated"
        report_file = f'formatted_report_{timestamp}{suffix}.txt'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"Report saved to: {report_file}")
        
        # Create Report object for compatibility
        report = Report(
            title="IOSG 加密货币新闻分析报告",
            generated_at=datetime.now(),
            total_articles=len(articles)
        )
        
        # Add formatted content to report
        report.formatted_content = report_content
        report.file_path = report_file
        
        # Group articles by category for report sections (for email compatibility)
        categorized_articles = {}
        for article in articles:
            category = article.classification or "其他"
            if category not in categorized_articles:
                categorized_articles[category] = []
            categorized_articles[category].append(article)
        
        # Create report sections for compatibility
        for category, category_articles in categorized_articles.items():
            if category_articles:
                section = ReportSection(
                    title=self._get_category_display_name(category),
                    category=category,
                    articles=category_articles
                )
                report.add_section(section)
        
        # Save report metadata
        self.storage.save_report(report)
        
        return report
    
    def _get_category_display_name(self, category: str) -> str:
        """Get display name for category"""
        display_names = {
            "项目融资": "🚀 项目融资",
            "基金融资": "💰 基金融资", 
            "公链/L2/主网": "⛓️ 公链/L2/主网",
            "中间件/工具协议": "🛠️ 中间件/工具协议",
            "DeFi": "🏦 DeFi",
            "GameFi": "🎮 GameFi",
            "应用协议": "📱 应用协议",
            "RWA": "🏢 RWA",
            "稳定币": "💵 稳定币",
            "交易所/钱包": "💱 交易所/钱包", 
            "AI + Crypto": "🤖 AI + Crypto",
            "DePIN": "📡 DePIN",
            "Portfolio": "⭐ IOSG Portfolio"
        }
        
        return display_names.get(category, f"📄 {category}")
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get current processing statistics"""
        return self.processing_stats.copy()
    
    def get_current_articles_count(self) -> int:
        """Get count of currently loaded articles"""
        return len(self.current_articles)