"""Article data model"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
import hashlib


class ArticleStatus(Enum):
    """Article processing status"""
    RAW = "raw"
    CLASSIFIED = "classified"  
    AI_FILTERED = "ai_filtered"
    PROCESSED = "processed"
    COMPLETED = "completed"


@dataclass
class Article:
    """Article data model with comprehensive metadata"""
    
    id: str
    title: str
    content_text: str
    url: str
    source_feed: str
    published_formatted: str
    created_at: datetime = field(default_factory=datetime.now)
    status: ArticleStatus = ArticleStatus.RAW
    
    # Classification fields
    classification: Optional[str] = None
    classification_score: Optional[float] = None
    
    # AI filtering fields
    ai_filtered: bool = False
    ai_importance_score: Optional[float] = None
    ai_filter_reason: Optional[str] = None
    
    # Human annotation fields
    human_label: Optional[str] = None
    human_importance: Optional[bool] = None
    human_labeled_at: Optional[datetime] = None
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Generate ID if not provided"""
        if not self.id:
            # Generate ID based on URL + title hash
            content = f"{self.url}{self.title}"
            self.id = hashlib.md5(content.encode()).hexdigest()[:12]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Article':
        """Create Article from dictionary (for JSON loading)"""
        # Handle datetime fields
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        elif created_at is None:
            created_at = datetime.now()
            
        human_labeled_at = data.get('human_labeled_at')
        if isinstance(human_labeled_at, str):
            human_labeled_at = datetime.fromisoformat(human_labeled_at.replace('Z', '+00:00'))
        
        # Handle status enum
        status = data.get('status', ArticleStatus.RAW)
        if isinstance(status, str):
            status = ArticleStatus(status)
            
        return cls(
            id=data.get('id', ''),
            title=data.get('title', ''),
            content_text=data.get('content_text', ''),
            url=data.get('url', ''),
            source_feed=data.get('source_feed', ''),
            published_formatted=data.get('published_formatted', ''),
            created_at=created_at,
            status=status,
            classification=data.get('classification'),
            classification_score=data.get('classification_score'),
            ai_filtered=data.get('ai_filtered', False),
            ai_importance_score=data.get('ai_importance_score'),
            ai_filter_reason=data.get('ai_filter_reason'),
            human_label=data.get('human_label'),
            human_importance=data.get('human_importance'),
            human_labeled_at=human_labeled_at,
            metadata=data.get('metadata', {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Article to dictionary (for JSON saving)"""
        result = {
            'id': self.id,
            'title': self.title,
            'content_text': self.content_text,
            'url': self.url,
            'source_feed': self.source_feed,
            'published_formatted': self.published_formatted,
            'created_at': self.created_at.isoformat(),
            'status': self.status.value,
            'classification': self.classification,
            'classification_score': self.classification_score,
            'ai_filtered': self.ai_filtered,
            'ai_importance_score': self.ai_importance_score,
            'ai_filter_reason': self.ai_filter_reason,
            'human_label': self.human_label,
            'human_importance': self.human_importance,
            'metadata': self.metadata
        }
        
        if self.human_labeled_at:
            result['human_labeled_at'] = self.human_labeled_at.isoformat()
            
        return result
    
    def is_portfolio_related(self, portfolio_projects: list) -> bool:
        """Check if article is related to portfolio projects"""
        text = f"{self.title} {self.content_text}".lower()
        return any(project.lower() in text for project in portfolio_projects)
    
    def get_content_preview(self, max_length: int = 200) -> str:
        """Get truncated content preview"""
        if len(self.content_text) <= max_length:
            return self.content_text
        return self.content_text[:max_length] + "..."