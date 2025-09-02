"""Storage service abstraction"""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..models.article import Article
from ..models.report import Report


class StorageService(ABC):
    """Abstract storage service interface"""
    
    @abstractmethod
    def save_articles(self, articles: List[Article], filename: str = None) -> bool:
        """Save articles to storage"""
        pass
    
    @abstractmethod
    def load_articles(self, filename: str = None) -> List[Article]:
        """Load articles from storage"""
        pass
    
    @abstractmethod
    def save_report(self, report: Report, filename: str = None) -> bool:
        """Save report to storage"""
        pass
    
    @abstractmethod
    def load_report(self, filename: str) -> Optional[Report]:
        """Load report from storage"""
        pass


class JSONStorageService(StorageService):
    """JSON file-based storage service"""
    
    def __init__(self, data_dir: Path = Path(".")):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
    
    def save_articles(self, articles: List[Article], filename: str = None) -> bool:
        """Save articles to JSON file"""
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"articles_{timestamp}.json"
            
            filepath = self.data_dir / filename
            
            # Prepare data structure
            data = {
                "timestamp": datetime.now().isoformat(),
                "total_articles": len(articles),
                "articles": [article.to_dict() for article in articles]
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error saving articles: {e}")
            return False
    
    def load_articles(self, filename: str = None) -> List[Article]:
        """Load articles from JSON file"""
        try:
            if filename is None:
                # Find the most recent articles file
                article_files = list(self.data_dir.glob("articles_*.json"))
                if not article_files:
                    return []
                filename = max(article_files, key=lambda f: f.stat().st_mtime).name
            
            filepath = self.data_dir / filename
            
            if not filepath.exists():
                return []
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle both new and legacy formats
            articles_data = data.get('articles', data.get('all_articles', []))
            
            return [Article.from_dict(article_data) for article_data in articles_data]
            
        except Exception as e:
            print(f"Error loading articles: {e}")
            return []
    
    def save_report(self, report: Report, filename: str = None) -> bool:
        """Save report to JSON file"""
        try:
            # Clean up old report files before saving new one
            try:
                import glob
                import os
                
                # Delete old report JSON files in data directory
                old_jsons = glob.glob(str(self.data_dir / "report_*.json"))
                for old_file in old_jsons:
                    os.remove(old_file)
                    print(f"🗑️ Deleted old JSON: {os.path.basename(old_file)}")
                    
            except Exception as e:
                print(f"⚠️ Failed to clean old JSON files: {e}")
            
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"report_{timestamp}.json"
            
            filepath = self.data_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error saving report: {e}")
            return False
    
    def load_report(self, filename: str) -> Optional[Report]:
        """Load report from JSON file"""
        try:
            filepath = self.data_dir / filename
            
            if not filepath.exists():
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return Report.from_dict(data)
            
        except Exception as e:
            print(f"Error loading report: {e}")
            return None
    
    def save_classified_articles(self, classified_data: Dict[str, Any], 
                                filename: str = "latest_classified.json") -> bool:
        """Save classified articles (legacy format compatibility)"""
        try:
            filepath = self.data_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(classified_data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error saving classified articles: {e}")
            return False
    
    def load_classified_articles(self, filename: str = "latest_classified.json") -> Dict[str, Any]:
        """Load classified articles (legacy format compatibility)"""
        try:
            filepath = self.data_dir / filename
            
            if not filepath.exists():
                return {}
            
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            print(f"Error loading classified articles: {e}")
            return {}
    
    def save_feeds_data(self, feeds_data: Dict[str, Any], 
                       filename: str = "latest_feeds.json") -> bool:
        """Save feeds data (legacy format compatibility)"""
        try:
            filepath = self.data_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(feeds_data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error saving feeds data: {e}")
            return False
    
    def load_feeds_data(self, filename: str = "latest_feeds.json") -> Dict[str, Any]:
        """Load feeds data (legacy format compatibility)"""
        try:
            filepath = self.data_dir / filename
            
            if not filepath.exists():
                return {}
            
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            print(f"Error loading feeds data: {e}")
            return {}
    
    def get_latest_formatted_report(self) -> Optional[str]:
        """Get the latest formatted report content"""
        try:
            # Find the most recent formatted report file
            report_files = list(self.data_dir.glob("formatted_report_*.txt"))
            if not report_files:
                return None
            
            latest_file = max(report_files, key=lambda f: f.stat().st_mtime)
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                return f.read()
                
        except Exception as e:
            print(f"Error loading formatted report: {e}")
            return None
    
    def load_feeds(self, filename: str = "latest_feeds.json") -> Dict[str, Any]:
        """Alias for load_feeds_data for backward compatibility"""
        return self.load_feeds_data(filename)
    
    def save_feeds(self, feeds_data: Dict[str, Any], filename: str = "latest_feeds.json") -> bool:
        """Alias for save_feeds_data for backward compatibility"""
        return self.save_feeds_data(feeds_data, filename)