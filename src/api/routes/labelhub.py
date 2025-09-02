"""Label Hub API routes"""

import json
import random
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app

from ...services.storage_service import JSONStorageService
from ...utils.logger import get_logger

labelhub_bp = Blueprint('labelhub', __name__, url_prefix='/labelhub')
logger = get_logger(__name__)


@labelhub_bp.route('/get_articles', methods=['GET'])
def get_labelhub_articles():
    """Get articles for labeling"""
    try:
        count = int(request.args.get('count', 10))
        skip_labeled = request.args.get('skip_labeled', 'true').lower() == 'true'
        
        storage = JSONStorageService()
        
        # Load historical classified data
        classified_data = storage.load_classified_articles("historical_classified.json")
        articles = classified_data.get('all_articles', [])
        
        if not articles:
            return jsonify({'error': '未找到历史分类数据文件'}), 404
        
        # Filter articles
        available_articles = []
        for article in articles:
            # Skip already labeled articles if requested
            if skip_labeled and ('human_label' in article and article['human_label'] is not None):
                continue
            available_articles.append(article)
        
        # Random selection
        selected_articles = random.sample(
            available_articles, 
            min(count, len(available_articles))
        )
        
        # Return only necessary fields
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
        logger.error(f"Get labelhub articles error: {e}")
        return jsonify({'error': str(e)}), 500


@labelhub_bp.route('/save_label', methods=['POST'])
def save_labelhub_label():
    """Save article label"""
    try:
        data = request.json or {}
        article_id = data.get('article_id')
        human_label = data.get('human_label')
        human_importance = data.get('human_importance')
        
        if not article_id:
            return jsonify({'error': '文章ID是必需的'}), 400
        
        storage = JSONStorageService()
        
        # Load historical data
        historical_data = storage.load_classified_articles("historical_classified.json")
        
        if not historical_data:
            return jsonify({'error': '未找到历史分类数据文件'}), 404
        
        # Find and update article
        articles_list = historical_data.get('all_articles', historical_data.get('articles', []))
        article_found = False
        
        for article in articles_list:
            if article['id'] == article_id:
                if human_label is not None:
                    article['human_label'] = human_label
                if human_importance is not None:
                    article['human_importance'] = bool(human_importance)
                
                # Add timestamp
                article['human_labeled_at'] = datetime.now().isoformat()
                article_found = True
                break
        
        if not article_found:
            return jsonify({'error': '未找到指定文章'}), 404
        
        # Save updated data
        success = storage.save_classified_articles(historical_data, "historical_classified.json")
        
        if success:
            return jsonify({'status': 'success', 'message': '标签保存成功'})
        else:
            return jsonify({'error': '保存失败'}), 500
        
    except Exception as e:
        logger.error(f"Save labelhub label error: {e}")
        return jsonify({'error': str(e)}), 500


@labelhub_bp.route('/stats', methods=['GET'])
def get_labelhub_stats():
    """Get labeling statistics"""
    try:
        storage = JSONStorageService()
        
        # Load historical data
        data = storage.load_classified_articles("historical_classified.json")
        
        if not data:
            return jsonify({'error': '未找到历史分类数据文件'}), 404
        
        # Get articles (handle both new and old formats)
        articles = data.get('all_articles', data.get('articles', []))
        
        # Calculate statistics
        total_articles = len(articles)
        labeled_articles = len([a for a in articles if a.get('human_label') is not None])
        unlabeled_articles = total_articles - labeled_articles
        
        # Count by label
        label_counts = {}
        for article in articles:
            label = article.get('human_label')
            if label:
                label_counts[label] = label_counts.get(label, 0) + 1
        
        # Importance statistics
        importance_counts = {
            'important': len([a for a in articles if a.get('human_importance') is True]),
            'not_important': len([a for a in articles if a.get('human_importance') is False])
        }
        
        # AI vs human accuracy
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
        logger.error(f"Get labelhub stats error: {e}")
        return jsonify({'error': str(e)}), 500