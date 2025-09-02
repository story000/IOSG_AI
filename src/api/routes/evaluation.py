"""Evaluation routes for system performance testing"""

import threading
import random
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import json

from ...services.storage_service import JSONStorageService
from ...utils.logger import get_logger

evaluation_bp = Blueprint('evaluation', __name__, url_prefix='/evaluation')
logger = get_logger(__name__)

# Global evaluation status
evaluation_status = {
    'running': False,
    'completed': False,
    'progress': 0,
    'current_phase': '',
    'results': None,
    'error': None
}


@evaluation_bp.route('/dataset_info')
def dataset_info():
    """Get information about the evaluation dataset"""
    try:
        storage = JSONStorageService()
        
        # Load historical classified data
        historical_data = storage.load_classified_articles('historical_classified.json')
        
        if not historical_data:
            return jsonify({
                'total_articles': 0,
                'labeled_articles': 0,
                'categories': {}
            })
        
        # Get articles
        articles = historical_data.get('all_articles', historical_data.get('articles', []))
        
        # Count labeled articles
        labeled_count = len([a for a in articles if a.get('human_label') is not None])
        
        # Count by category
        category_counts = {}
        for article in articles:
            label = article.get('human_label')
            if label:
                category_counts[label] = category_counts.get(label, 0) + 1
        
        return jsonify({
            'total_articles': len(articles),
            'labeled_articles': labeled_count,
            'categories': category_counts,
            'ready_for_evaluation': labeled_count >= 100
        })
        
    except Exception as e:
        logger.error(f"Dataset info error: {e}")
        return jsonify({'error': str(e)}), 500


@evaluation_bp.route('/start', methods=['POST'])
def start_evaluation():
    """Start the evaluation process"""
    global evaluation_status
    
    if evaluation_status['running']:
        return jsonify({'error': 'Evaluation already running'}), 400
    
    data = request.json or {}
    test_size = data.get('test_size', 0.2)
    
    # Reset status
    evaluation_status = {
        'running': True,
        'completed': False,
        'progress': 0,
        'current_phase': 'Initializing...',
        'results': None,
        'error': None
    }
    
    # Capture current app for background thread
    app = current_app._get_current_object()
    
    def run_evaluation():
        with app.app_context():
            try:
                storage = JSONStorageService()
                
                # Phase 1: Load data
                evaluation_status['current_phase'] = 'Loading dataset...'
                evaluation_status['progress'] = 10
                
                historical_data = storage.load_classified_articles('historical_classified.json')
                if not historical_data:
                    raise ValueError("No historical data found")
                
                articles = historical_data.get('all_articles', historical_data.get('articles', []))
                labeled_articles = [a for a in articles if a.get('human_label') is not None]
                
                if len(labeled_articles) < 10:
                    raise ValueError(f"Not enough labeled data: {len(labeled_articles)} articles")
                
                # Phase 2: Split dataset
                evaluation_status['current_phase'] = 'Splitting dataset...'
                evaluation_status['progress'] = 20
                
                random.shuffle(labeled_articles)
                split_point = int(len(labeled_articles) * (1 - test_size))
                test_set = labeled_articles[split_point:]
                
                # Phase 3: Evaluate AI classification
                evaluation_status['current_phase'] = 'Evaluating AI classifications...'
                evaluation_status['progress'] = 40
                
                correct = 0
                total = len(test_set)
                confusion_matrix = {}
                
                for i, article in enumerate(test_set):
                    ai_label = article.get('classification')
                    human_label = article.get('human_label')
                    
                    if ai_label and human_label:
                        if ai_label == human_label:
                            correct += 1
                        
                        # Build confusion matrix
                        if ai_label not in confusion_matrix:
                            confusion_matrix[ai_label] = {}
                        if human_label not in confusion_matrix[ai_label]:
                            confusion_matrix[ai_label][human_label] = 0
                        confusion_matrix[ai_label][human_label] += 1
                    
                    # Update progress
                    evaluation_status['progress'] = 40 + int((i + 1) / total * 40)
                
                # Phase 4: Calculate metrics
                evaluation_status['current_phase'] = 'Calculating metrics...'
                evaluation_status['progress'] = 85
                
                accuracy = (correct / total * 100) if total > 0 else 0
                
                # Calculate per-category metrics
                category_metrics = {}
                for category in confusion_matrix:
                    tp = confusion_matrix[category].get(category, 0)
                    fp = sum(confusion_matrix[category].values()) - tp
                    fn = sum(confusion_matrix.get(c, {}).get(category, 0) 
                            for c in confusion_matrix if c != category)
                    
                    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
                    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
                    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
                    
                    category_metrics[category] = {
                        'precision': round(precision * 100, 1),
                        'recall': round(recall * 100, 1),
                        'f1_score': round(f1 * 100, 1),
                        'support': tp + fn
                    }
                
                # Phase 5: Complete
                evaluation_status['current_phase'] = 'Evaluation completed!'
                evaluation_status['progress'] = 100
                evaluation_status['completed'] = True
                evaluation_status['results'] = {
                    'accuracy': round(accuracy, 1),
                    'total_evaluated': total,
                    'correct_predictions': correct,
                    'category_metrics': category_metrics,
                    'confusion_matrix': confusion_matrix,
                    'timestamp': datetime.now().isoformat()
                }
                
                logger.info(f"Evaluation completed: {accuracy:.1f}% accuracy")
                
            except Exception as e:
                logger.error(f"Evaluation error: {e}")
                evaluation_status['error'] = str(e)
                evaluation_status['current_phase'] = f'Error: {str(e)}'
            finally:
                evaluation_status['running'] = False
    
    # Start in background thread
    thread = threading.Thread(target=run_evaluation)
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'started'})


@evaluation_bp.route('/status')
def get_evaluation_status():
    """Get current evaluation status"""
    return jsonify(evaluation_status)