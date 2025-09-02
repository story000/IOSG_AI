"""Process routes for fetch, classify, and AI filter functionality"""

import threading
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import json
import subprocess
import os

from ...services.storage_service import JSONStorageService
from ...services.ai_service import create_ai_service
from ...services.inoreader_service import InoreaderService
from ...services.classification_service import ClassificationService
from ...services.report_generator import ReportGenerator
from ...services.adaptive_deduplication_service import AdaptiveDeduplicationService
from ...utils.logger import get_logger
from ...utils.config import get_settings, get_crypto_config

process_bp = Blueprint('process', __name__)
logger = get_logger(__name__)

# Global process status
process_status = {
    'fetch': {'running': False, 'progress': 0, 'logs': []},
    'classify': {'running': False, 'progress': 0, 'logs': []},
    'ai_filter': {'running': False, 'progress': 0, 'logs': []}
}

# Maximum log entries
MAX_LOG_ENTRIES = 1000


@process_bp.route('/fetch', methods=['POST'])
def fetch():
    """Start fetching news from Inoreader"""
    global process_status
    
    if process_status['fetch']['running']:
        return jsonify({'error': 'Fetch process already running'}), 400
    
    process_status['fetch']['running'] = True
    process_status['fetch']['progress'] = 0
    process_status['fetch']['logs'] = []
    
    # Capture current app for background thread
    app = current_app._get_current_object()
    
    def run_fetch():
        with app.app_context():
            try:
                # Initialize Inoreader service
                inoreader_service = InoreaderService()
                
                # Progress callback
                def progress_callback(progress, status):
                    process_status['fetch']['progress'] = progress
                
                # Log callback
                def log_callback(message):
                    log_entry = {
                        'timestamp': datetime.now().strftime('%H:%M:%S'),
                        'message': message
                    }
                    process_status['fetch']['logs'].append(log_entry)
                    # Keep only last 1000 logs
                    if len(process_status['fetch']['logs']) > MAX_LOG_ENTRIES:
                        process_status['fetch']['logs'] = process_status['fetch']['logs'][-MAX_LOG_ENTRIES:]
                
                # Start fetching
                log_callback('Starting news fetch from Inoreader...')
                process_status['fetch']['progress'] = 10
                
                # Run fetch process
                feeds_data = inoreader_service.fetch_feeds(
                    progress_callback=progress_callback,
                    log_callback=log_callback
                )
                
                # Log summary
                if feeds_data:
                    total = feeds_data['metadata']['total_articles']
                    log_callback(f'Fetch completed! Total articles: {total}')
                
                process_status['fetch']['progress'] = 100
                
            except Exception as e:
                logger.error(f"Fetch error: {e}")
                log_entry = {
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'message': f'Error: {str(e)}'
                }
                process_status['fetch']['logs'].append(log_entry)
            finally:
                process_status['fetch']['running'] = False
    
    # Start in background thread
    thread = threading.Thread(target=run_fetch)
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'started'})


@process_bp.route('/classify', methods=['POST'])
def classify():
    """Start classification process"""
    global process_status
    
    if process_status['classify']['running']:
        return jsonify({'error': 'Classification already running'}), 400
    
    process_status['classify']['running'] = True
    process_status['classify']['progress'] = 0
    process_status['classify']['logs'] = []
    
    # Capture current app for background thread
    app = current_app._get_current_object()
    settings = current_app.settings
    
    def run_classify():
        with app.app_context():
            try:
                log_entry = {
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'message': 'Starting article classification...'
                }
                process_status['classify']['logs'].append(log_entry)
                
                # Initialize Classification service
                classification_service = ClassificationService()
                
                # Progress callback
                def progress_callback(progress, status):
                    process_status['classify']['progress'] = progress
                
                # Log callback
                def log_callback(message):
                    log_entry = {
                        'timestamp': datetime.now().strftime('%H:%M:%S'),
                        'message': message
                    }
                    process_status['classify']['logs'].append(log_entry)
                    # Keep only last 1000 logs
                    if len(process_status['classify']['logs']) > MAX_LOG_ENTRIES:
                        process_status['classify']['logs'] = process_status['classify']['logs'][-MAX_LOG_ENTRIES:]
                
                # Start classification
                log_callback('Starting article classification...')
                process_status['classify']['progress'] = 10
                
                # Run classification process
                classified_data = classification_service.run_classification(
                    progress_callback=progress_callback,
                    log_callback=log_callback
                )
                
                # Log summary
                if classified_data:
                    total = classified_data['metadata']['total_articles']
                    log_callback(f'Classification completed! Processed {total} articles')
                    for category, count in classified_data['metadata']['category_stats'].items():
                        log_callback(f'  {category}: {count} articles')
                
                process_status['classify']['progress'] = 100
                
            except Exception as e:
                logger.error(f"Classification error: {e}")
                log_entry = {
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'message': f'Error: {str(e)}'
                }
                process_status['classify']['logs'].append(log_entry)
            finally:
                process_status['classify']['running'] = False
    
    # Start in background thread
    thread = threading.Thread(target=run_classify)
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'started'})


@process_bp.route('/ai_filter', methods=['POST'])
def ai_filter():
    """Start AI filtering process using original ai_filter.py logic"""
    global process_status
    
    if process_status['ai_filter']['running']:
        return jsonify({'error': 'AI filter already running'}), 400
    
    data = request.json or {}
    provider = data.get('provider', 'openai')
    
    process_status['ai_filter']['running'] = True
    process_status['ai_filter']['progress'] = 0
    process_status['ai_filter']['logs'] = []
    
    # Capture current app and settings for background thread
    app = current_app._get_current_object()
    settings = current_app.settings
    
    def run_ai_filter():
        with app.app_context():
            try:
                # Import the original ai_filter module
                import sys
                sys.path.insert(0, '/Users/liusiyuan/Desktop/AIVC/IOSG/src/services')
                from ai_filter_original import AIFundingFilter
                
                log_entry = {
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'message': f'Starting AI filter with {provider}...'
                }
                process_status['ai_filter']['logs'].append(log_entry)
                
                # Log callback
                def log_callback(message):
                    log_entry = {
                        'timestamp': datetime.now().strftime('%H:%M:%S'),
                        'message': message
                    }
                    process_status['ai_filter']['logs'].append(log_entry)
                    # Keep only last 1000 logs
                    if len(process_status['ai_filter']['logs']) > MAX_LOG_ENTRIES:
                        process_status['ai_filter']['logs'] = process_status['ai_filter']['logs'][-MAX_LOG_ENTRIES:]
                
                # Progress callback  
                def progress_callback(progress, status):
                    process_status['ai_filter']['progress'] = progress
                
                log_callback('Using original ai_filter.py logic...')
                
                # Get API key
                if provider == 'openai':
                    api_key = data.get('api_key') or settings.openai_api_key
                    if not api_key:
                        raise ValueError("OpenAI API key not configured")
                else:
                    api_key = settings.deepseek_api_key
                    if not api_key:
                        raise ValueError("DeepSeek API key not configured")
                
                # Create original filter
                filter_instance = AIFundingFilter(api_key, provider)
                
                # Load classified articles
                storage = JSONStorageService()
                classified_data = storage.load_classified_articles('latest_classified.json')
                
                if not classified_data:
                    raise ValueError("No classified data found")
                
                log_callback(f"Loaded {classified_data.get('metadata', {}).get('total_articles', 0)} classified articles")
                
                # Get articles by category from classified data
                articles_by_category = classified_data.get('categories', {})
                
                # Map to old format expected by ai_filter
                project_funding_articles = articles_by_category.get('项目融资', [])
                fund_funding_articles = articles_by_category.get('基金融资', [])
                blockchain_articles = articles_by_category.get('公链/L2/主网', [])
                middleware_articles = articles_by_category.get('中间件/工具协议', [])
                defi_articles = articles_by_category.get('DeFi', [])
                rwa_articles = articles_by_category.get('RWA', [])
                stablecoin_articles = articles_by_category.get('稳定币', [])
                application_articles = articles_by_category.get('应用协议', [])
                gamefi_articles = articles_by_category.get('GameFi', [])
                exchange_wallet_articles = articles_by_category.get('交易所/钱包', [])
                ai_crypto_articles = articles_by_category.get('AI + Crypto', [])
                depin_articles = articles_by_category.get('DePIN', [])
                portfolio_articles = articles_by_category.get('portfolios', [])
                
                # Define all categories config
                categories_config = [
                    ("项目融资", project_funding_articles, "project"),
                    ("基金融资", fund_funding_articles, "fund"),
                    ("公链/L2/主网", blockchain_articles, "blockchain"),
                    ("中间件/工具协议", middleware_articles, "middleware"),
                    ("DeFi", defi_articles, "defi"),
                    ("RWA", rwa_articles, "rwa"),
                    ("稳定币", stablecoin_articles, "stablecoin"),
                    ("应用协议", application_articles, "application"),
                    ("GameFi", gamefi_articles, "gamefi"),
                    ("交易所/钱包", exchange_wallet_articles, "exchange_wallet"),
                    ("AI + Crypto", ai_crypto_articles, "ai_crypto"),
                    ("DePIN", depin_articles, "depin")
                ]
                
                # Process each category using original logic
                filtered_results = {}
                dedup_stats = {}
                batch_size = 20
                max_articles = None  # Process all
                
                for category_name, articles, article_type in categories_config:
                    if articles:
                        log_callback(f'Filtering {len(articles)} articles in {category_name}...')
                        
                        # Use original batch_filter method
                        ai_filtered = filter_instance.batch_filter_no_prompt(articles, batch_size, max_articles, article_type)
                        
                        # Apply adaptive deduplication
                        if ai_filtered:
                            log_callback(f'Deduplicating {category_name}...')
                            # Use new adaptive deduplication service
                            adaptive_dedup_service = AdaptiveDeduplicationService(
                                similarity_threshold=0.4,
                                performance_mode='aggressive'
                            )
                            deduplicated, dedup_stats_obj = adaptive_dedup_service.adaptive_deduplicate(ai_filtered, category_name)
                            filtered_results[article_type] = deduplicated
                            dedup_stats[category_name] = {
                                'removed_count': dedup_stats_obj.total_removed,
                                'removal_rate': (dedup_stats_obj.total_removed / dedup_stats_obj.total_articles * 100) if dedup_stats_obj.total_articles > 0 else 0
                            }
                            log_callback(f'  {category_name}: {dedup_stats_obj.total_articles} → {len(deduplicated)} (removed: {dedup_stats_obj.total_removed})')
                        else:
                            filtered_results[article_type] = []
                            dedup_stats[category_name] = {'removed_count': 0, 'removal_rate': 0}
                    else:
                        filtered_results[article_type] = []
                        dedup_stats[category_name] = {'removed_count': 0, 'duplicate_groups': [], 'removal_rate': 0}
                    
                    # Update progress
                    progress_callback(50, f'Processed {category_name}')
                
                # Portfolio articles - no AI filtering needed, only internal deduplication
                if portfolio_articles:
                    log_callback('Processing Portfolio articles (internal deduplication only)...')
                    # Use new adaptive deduplication service for portfolios
                    adaptive_dedup_service = AdaptiveDeduplicationService(
                        similarity_threshold=0.4,
                        performance_mode='aggressive'
                    )
                    deduplicated_portfolio, portfolio_dedup_stats = adaptive_dedup_service.adaptive_deduplicate(portfolio_articles, "portfolios")
                    filtered_results["portfolio"] = deduplicated_portfolio
                    dedup_stats["Portfolio"] = {
                        'removed_count': portfolio_dedup_stats.total_removed,
                        'removal_rate': (portfolio_dedup_stats.total_removed / portfolio_dedup_stats.total_articles * 100) if portfolio_dedup_stats.total_articles > 0 else 0
                    }
                    log_callback(f'  Portfolios: {portfolio_dedup_stats.total_articles} → {len(deduplicated_portfolio)} (removed: {portfolio_dedup_stats.total_removed})')
                else:
                    filtered_results["portfolio"] = []
                    dedup_stats["Portfolio"] = {'removed_count': 0, 'removal_rate': 0}
                
                # Apply cross-category deduplication (excluding portfolios)
                log_callback('Applying cross-category deduplication (portfolios excluded)...')
                # Separate portfolios from other categories
                portfolios_data = filtered_results.pop('portfolio', [])
                
                # Apply cross-category deduplication only to non-portfolio categories
                if len(filtered_results) > 0:
                    filtered_results, cross_dedup_stats = filter_instance.cross_category_deduplication(filtered_results)
                
                # Add portfolios back without cross-category deduplication
                if portfolios_data:
                    filtered_results['portfolio'] = portfolios_data
                    log_callback(f'Portfolios preserved from cross-category deduplication: {len(portfolios_data)} articles')
                
                progress_callback(80, 'Cross-category deduplication completed')
                
                # Map results back to Chinese category names for ReportGenerator
                mapped_results = {}
                category_mapping = {
                    "project": "项目融资",
                    "fund": "基金融资",
                    "blockchain": "公链/L2/主网",
                    "middleware": "中间件/工具协议",
                    "defi": "DeFi",
                    "rwa": "RWA",
                    "stablecoin": "稳定币",
                    "application": "应用协议",
                    "gamefi": "GameFi",
                    "exchange_wallet": "交易所/钱包",
                    "ai_crypto": "AI + Crypto",
                    "depin": "DePIN",
                    "portfolio": "portfolios"
                }
                
                for key, articles in filtered_results.items():
                    chinese_key = category_mapping.get(key, key)
                    mapped_results[chinese_key] = articles
                    log_callback(f'{chinese_key}: {len(articles)} articles after filtering')
                
                # Generate final report using ReportGenerator
                log_callback('Generating structured report...')
                # Create a simple AI service for report generation
                ai_service = create_ai_service('openai', api_key) if api_key else None
                report_generator = ReportGenerator(ai_service=ai_service)
                report_content = report_generator.generate_report(mapped_results)
                
                # Save report
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                suffix = "_ai_deduplicated"
                report_file = f'formatted_report_{timestamp}{suffix}.txt'
                with open(report_file, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                
                log_callback(f'Report saved to: {report_file}')
                process_status['ai_filter']['progress'] = 100
                log_callback('AI filtering completed successfully!')
                
            except Exception as e:
                logger.error(f"AI filter error: {e}")
                import traceback
                traceback.print_exc()
                log_entry = {
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'message': f'Error: {str(e)}'
                }
                process_status['ai_filter']['logs'].append(log_entry)
            finally:
                process_status['ai_filter']['running'] = False
    
    # Start in background thread
    thread = threading.Thread(target=run_ai_filter)
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'started'})


@process_bp.route('/status')
def status():
    """Get process status"""
    return jsonify(process_status)


@process_bp.route('/clear_logs/<process_name>')
def clear_logs(process_name):
    """Clear logs for a specific process"""
    global process_status
    if process_name in process_status:
        process_status[process_name]['logs'] = []
        return jsonify({'status': 'success'})
    return jsonify({'error': 'Invalid process name'}), 400