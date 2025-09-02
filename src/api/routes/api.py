"""API endpoints for core functionality"""

import threading
import time
import os
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app

from ...services.storage_service import JSONStorageService
from ...services.ai_service import create_ai_service
from ...services.email_service import EmailService
from ...core.processor import NewsProcessor
from ...utils.logger import LogCapture, get_logger

api_bp = Blueprint('api', __name__, url_prefix='/api')
logger = get_logger(__name__)

# Global state for processing status
process_status = {
    'fetch': {'running': False, 'progress': 0, 'logs': []},
    'classify': {'running': False, 'progress': 0, 'logs': []},
    'ai_filter': {'running': False, 'progress': 0, 'logs': []}
}

# Auto report status
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


@api_bp.route('/status')
def status():
    """Get current process status"""
    return jsonify(process_status)


@api_bp.route('/auto_report_status')
def get_auto_report_status():
    """Get auto report status"""
    return jsonify(auto_report_status)


@api_bp.route('/auto_generate_report', methods=['POST'])
def auto_generate_report():
    """Start automated report generation using same API endpoints as manual mode"""
    global auto_report_status
    
    if auto_report_status['running']:
        return jsonify({'error': '自动报告生成正在进行中'}), 400
    
    data = request.json or {}
    email = data.get('email', '')
    provider = data.get('provider', 'openai')
    api_key = data.get('api_key', '')
    
    if not email:
        return jsonify({'error': '邮箱地址是必需的'}), 400
    
    # Reset status
    reset_auto_report_status()
    auto_report_status['running'] = True
    auto_report_status['user_email'] = email
    
    # Capture current app and settings for background thread
    app = current_app._get_current_object()
    settings = current_app.settings
    
    def run_auto_process():
        """Run automated processing by calling same API endpoints as manual mode"""
        with app.app_context():
            try:
                # Step 1: Fetch
                auto_report_status['fetch']['running'] = True
                logger.info("Auto Step 1: Starting fetch...")
                
                from .process import fetch
                with app.test_request_context('/api/fetch', method='POST'):
                    fetch_result = fetch()
                    # fetch() returns a Response object, check if it's successful
                    if hasattr(fetch_result, 'status_code') and fetch_result.status_code != 200:
                        raise Exception("Fetch step failed")
                    elif isinstance(fetch_result, tuple) and len(fetch_result) > 1 and fetch_result[1] != 200:
                        raise Exception("Fetch step failed")
                
                # Wait for fetch to complete by polling process_status
                while True:
                    from .process import process_status
                    if not process_status['fetch']['running'] and process_status['fetch']['progress'] == 100:
                        auto_report_status['fetch']['completed'] = True
                        auto_report_status['fetch']['running'] = False
                        break
                    elif process_status['fetch'].get('error'):
                        raise Exception("Fetch failed")
                    time.sleep(1)
                
                time.sleep(2)  # Brief pause between steps
                
                # Step 2: Classify  
                auto_report_status['classify']['running'] = True
                logger.info("Auto Step 2: Starting classification...")
                
                from .process import classify
                with app.test_request_context('/api/classify', method='POST'):
                    classify_result = classify()
                    # classify() returns a Response object, check if it's successful
                    if hasattr(classify_result, 'status_code') and classify_result.status_code != 200:
                        raise Exception("Classify step failed")
                    elif isinstance(classify_result, tuple) and len(classify_result) > 1 and classify_result[1] != 200:
                        raise Exception("Classify step failed")
                
                # Wait for classify to complete
                while True:
                    from .process import process_status
                    if not process_status['classify']['running'] and process_status['classify']['progress'] == 100:
                        auto_report_status['classify']['completed'] = True
                        auto_report_status['classify']['running'] = False
                        break
                    elif process_status['classify'].get('error'):
                        raise Exception("Classify failed")
                    time.sleep(1)
                
                time.sleep(2)  # Brief pause between steps
                
                # Step 3: AI Filter
                auto_report_status['ai_filter']['running'] = True
                logger.info("Auto Step 3: Starting AI filter...")
                
                from .process import ai_filter
                with app.test_request_context('/api/ai_filter', method='POST', 
                                           json={'provider': provider, 'api_key': api_key}):
                    ai_filter_result = ai_filter()
                    # ai_filter() returns a Response object, check if it's successful
                    if hasattr(ai_filter_result, 'status_code') and ai_filter_result.status_code != 200:
                        raise Exception("AI filter step failed")
                    elif isinstance(ai_filter_result, tuple) and len(ai_filter_result) > 1 and ai_filter_result[1] != 200:
                        raise Exception("AI filter step failed")
                
                # Wait for AI filter to complete
                while True:
                    from .process import process_status
                    if not process_status['ai_filter']['running'] and process_status['ai_filter']['progress'] == 100:
                        auto_report_status['ai_filter']['completed'] = True
                        auto_report_status['ai_filter']['running'] = False
                        break
                    elif process_status['ai_filter'].get('error'):
                        raise Exception("AI filter failed")
                    time.sleep(1)
                
                time.sleep(2)  # Brief pause before email
                
                # Step 4: Send Email
                auto_report_status['email']['running'] = True
                logger.info("Auto Step 4: Sending email...")
                
                # Get latest report and send email
                storage = JSONStorageService()
                report_content = storage.get_latest_formatted_report()
                
                if not report_content:
                    raise Exception("No report content found after AI filtering")
                
                # Create email service with SMTP config
                smtp_config = {
                    'server': settings.mail_server,
                    'port': settings.mail_port,
                    'username': settings.mail_username,
                    'password': settings.mail_password
                }
                email_service = EmailService(smtp_config=smtp_config)
                
                # Send report email
                success = email_service._send_email_direct_smtp(
                    email,
                    f'📊 IOSG 加密货币新闻分析报告 - {datetime.now().strftime("%Y-%m-%d")}',
                    report_content,
                    email_service._convert_markdown_to_html_old_style(report_content)
                )
                
                if success:
                    auto_report_status['email']['completed'] = True
                    auto_report_status['email']['running'] = False
                    auto_report_status['completed'] = True
                    logger.info(f"Auto report completed successfully for {email}")
                else:
                    raise Exception("Email sending failed")
                
            except Exception as e:
                auto_report_status['failed'] = True
                auto_report_status['error'] = str(e)
                logger.error(f"Auto report failed: {e}")
            finally:
                auto_report_status['running'] = False
    
    # Start processing in background thread
    thread = threading.Thread(target=run_auto_process)
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'started'})


@api_bp.route('/test_email', methods=['POST'])
def test_email():
    """Test email sending functionality"""
    try:
        data = request.json or {}
        email = data.get('email', '')
        
        if not email:
            return jsonify({'error': '邮箱地址是必需的'}), 400
        
        # Create email service and send test email
        email_service = EmailService(current_app.mail)
        success = email_service.send_test_email(email)
        
        if success:
            return jsonify({'status': 'success', 'message': '测试邮件发送成功'})
        else:
            return jsonify({'error': '邮件发送失败'}), 500
            
    except Exception as e:
        logger.error(f"Test email error: {e}")
        return jsonify({'error': f'邮件发送失败: {str(e)}'}), 500


@api_bp.route('/get_latest_output')
def get_latest_output():
    """Get the latest formatted output file"""
    try:
        storage = JSONStorageService()
        content = storage.get_latest_formatted_report()
        
        if not content:
            return jsonify({'error': 'No formatted report found'}), 404
        
        return jsonify({
            'content': content,
            'created_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Get latest output error: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/clear_logs/<process_name>')
def clear_logs(process_name):
    """Clear logs for a specific process"""
    if process_name in process_status:
        process_status[process_name]['logs'] = []
        return jsonify({'status': 'cleared'})
    return jsonify({'error': 'Invalid process name'}), 400


def reset_auto_report_status():
    """Reset auto report status"""
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