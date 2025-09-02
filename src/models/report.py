"""Report data model"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum

from .article import Article


class ReportFormat(Enum):
    """Report output format"""
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"


@dataclass
class ReportSection:
    """Report section containing articles by category"""
    
    title: str
    category: str
    articles: List[Article] = field(default_factory=list)
    summary: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_article(self, article: Article):
        """Add article to section"""
        self.articles.append(article)
    
    def get_article_count(self) -> int:
        """Get number of articles in section"""
        return len(self.articles)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'title': self.title,
            'category': self.category,
            'articles': [article.to_dict() for article in self.articles],
            'summary': self.summary,
            'metadata': self.metadata
        }


@dataclass
class Report:
    """Main report containing all sections and metadata"""
    
    title: str
    generated_at: datetime = field(default_factory=datetime.now)
    sections: List[ReportSection] = field(default_factory=list)
    format: ReportFormat = ReportFormat.MARKDOWN
    
    # Statistics
    total_articles: int = 0
    total_sources: int = 0
    processing_stats: Dict[str, Any] = field(default_factory=dict)
    
    # Email settings
    recipient_email: str = ""
    email_sent: bool = False
    email_sent_at: Optional[datetime] = None
    
    def add_section(self, section: ReportSection):
        """Add section to report"""
        self.sections.append(section)
        self._update_stats()
    
    def get_section_by_category(self, category: str) -> Optional[ReportSection]:
        """Get section by category name"""
        for section in self.sections:
            if section.category == category:
                return section
        return None
    
    def _update_stats(self):
        """Update report statistics"""
        self.total_articles = sum(len(section.articles) for section in self.sections)
        
        all_sources = set()
        for section in self.sections:
            for article in section.articles:
                all_sources.add(article.source_feed)
        self.total_sources = len(all_sources)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary"""
        result = {
            'title': self.title,
            'generated_at': self.generated_at.isoformat(),
            'sections': [section.to_dict() for section in self.sections],
            'format': self.format.value,
            'total_articles': self.total_articles,
            'total_sources': self.total_sources,
            'processing_stats': self.processing_stats,
            'recipient_email': self.recipient_email,
            'email_sent': self.email_sent
        }
        
        if self.email_sent_at:
            result['email_sent_at'] = self.email_sent_at.isoformat()
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Report':
        """Create Report from dictionary"""
        # Handle datetime fields
        generated_at = data.get('generated_at')
        if isinstance(generated_at, str):
            generated_at = datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
        
        email_sent_at = data.get('email_sent_at')
        if isinstance(email_sent_at, str):
            email_sent_at = datetime.fromisoformat(email_sent_at.replace('Z', '+00:00'))
        
        # Create sections
        sections = []
        for section_data in data.get('sections', []):
            articles = [Article.from_dict(art_data) for art_data in section_data.get('articles', [])]
            section = ReportSection(
                title=section_data.get('title', ''),
                category=section_data.get('category', ''),
                articles=articles,
                summary=section_data.get('summary', ''),
                metadata=section_data.get('metadata', {})
            )
            sections.append(section)
        
        return cls(
            title=data.get('title', ''),
            generated_at=generated_at or datetime.now(),
            sections=sections,
            format=ReportFormat(data.get('format', ReportFormat.MARKDOWN.value)),
            total_articles=data.get('total_articles', 0),
            total_sources=data.get('total_sources', 0),
            processing_stats=data.get('processing_stats', {}),
            recipient_email=data.get('recipient_email', ''),
            email_sent=data.get('email_sent', False),
            email_sent_at=email_sent_at
        )