"""Main routes for the web interface"""

from flask import Blueprint, render_template, request, jsonify, current_app
import threading
from datetime import datetime

from ...utils.config import get_crypto_config
from ...services.storage_service import JSONStorageService
from ...services.ai_service import create_ai_service
from ...services.email_service import EmailService
from ...core.processor import NewsProcessor
from ...utils.logger import LogCapture, get_logger

main_bp = Blueprint('main', __name__)
logger = get_logger(__name__)

# Global state for backward compatibility with original app
process_status = {
    'fetch': {'running': False, 'progress': 0, 'logs': []},
    'classify': {'running': False, 'progress': 0, 'logs': []},
    'ai_filter': {'running': False, 'progress': 0, 'logs': []}
}

auto_report_status = {
    'running': False,
    'fetch': {'running': False, 'completed': False, 'failed': False},
    'classify': {'running': False, 'completed': False, 'failed': False},
    'ai_filter': {'running': False, 'completed': False, 'failed': False},
    'email': {'running': False, 'completed': False, 'failed': False},
}


@main_bp.route('/')
def index():
    """Main page"""
    try:
        crypto_config = get_crypto_config()
        categories = crypto_config.get_category_list(exclude=['portfolios', '其他'])
        return render_template('index.html', categories=categories)
    except Exception as e:
        current_app.logger.error(f"Error loading index page: {e}")
        return render_template('index.html', categories=[])


@main_bp.route('/auto')
def auto_report():
    """Auto report page"""
    return render_template('auto_report.html')


@main_bp.route('/labelhub')
def labelhub():
    """Label Hub page for manual article labeling"""
    return render_template('labelhub.html')


@main_bp.route('/evaluation')
def evaluation():
    """System evaluation page"""
    return render_template('evaluation.html')


@main_bp.route('/preview_email')
def preview_email():
    """Preview email HTML effect"""
    try:
        from ...services.storage_service import JSONStorageService
        from ...services.email_service import EmailService
        
        # Get storage service
        storage = JSONStorageService()
        
        # Get latest formatted report
        content = storage.get_latest_formatted_report()
        if not content:
            return "暂无报告文件可供预览", 404
        
        # Create a dummy email service for HTML generation
        email_service = EmailService(current_app.mail)
        
        # Convert markdown content to HTML
        html_content = email_service._convert_markdown_to_html(content)
        return html_content
        
    except Exception as e:
        current_app.logger.error(f"Preview email error: {e}")
        return f"预览失败: {str(e)}", 500


# Legacy routes for backward compatibility
@main_bp.route('/get_latest_output')
def get_latest_output_legacy():
    """Legacy route - redirects to /api/get_latest_output"""
    from .api import get_latest_output
    return get_latest_output()


@main_bp.route('/auto_generate_report', methods=['POST'])
def auto_generate_report_legacy():
    """Legacy route - redirects to /api/auto_generate_report"""
    from .api import auto_generate_report
    return auto_generate_report()


@main_bp.route('/auto_report_status')
def auto_report_status_route():
    """Legacy route - redirects to /api/auto_report_status"""
    from .api import get_auto_report_status
    return get_auto_report_status()


@main_bp.route('/test_email', methods=['POST'])
def test_email_legacy():
    """Legacy route - redirects to /api/test_email"""
    from .api import test_email
    return test_email()


