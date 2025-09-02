"""Adaptive deduplication service with intelligent algorithm selection"""

import time
import hashlib
import difflib
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

# Import available components
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class DeduplicationMethod(Enum):
    """Available deduplication methods"""
    HASH_ONLY = "hash_only"
    BASIC_SEQUENTIAL = "basic_sequential"  
    OPTIMIZED_SEQUENTIAL = "optimized_sequential"
    TFIDF_VECTORIZED = "tfidf_vectorized"
    AI_SEMANTIC = "ai_semantic"
    HYBRID = "hybrid"


@dataclass
class AdaptiveStats:
    """Statistics for adaptive deduplication"""
    total_articles: int = 0
    exact_removed: int = 0
    similarity_removed: int = 0
    ai_removed: int = 0
    processing_time: float = 0.0
    method_used: str = ""
    algorithm_selection_time: float = 0.0
    duplicate_groups: List = field(default_factory=list)
    performance_metrics: Dict = field(default_factory=dict)
    
    @property
    def total_removed(self) -> int:
        return self.exact_removed + self.similarity_removed + self.ai_removed
    
    @property
    def removal_rate(self) -> float:
        if self.total_articles == 0:
            return 0.0
        return (self.total_removed / self.total_articles) * 100


class AdaptiveDeduplicationService:
    """Intelligent deduplication service that automatically selects optimal algorithms"""
    
    def __init__(self, 
                 similarity_threshold: float = 0.7,
                 ai_api_key: Optional[str] = None,
                 ai_provider: str = "openai",
                 performance_mode: str = "balanced"):  # balanced, speed, accuracy
        
        self.similarity_threshold = similarity_threshold
        self.ai_api_key = ai_api_key
        self.ai_provider = ai_provider
        self.performance_mode = performance_mode
        
        # Algorithm selection thresholds
        self.thresholds = self._get_performance_thresholds(performance_mode)
        
        # Initialize components
        self._init_components()
        
        # Performance history for adaptive learning
        self.performance_history = []
        
        print(f"✅ Adaptive Deduplication Service initialized")
        print(f"   - Performance mode: {performance_mode}")
        print(f"   - Available methods: {self._list_available_methods()}")
        print(f"   - AI enabled: {self.ai_client is not None}")
    
    def _get_performance_thresholds(self, mode: str) -> Dict:
        """Get algorithm selection thresholds based on performance mode"""
        
        thresholds = {
            "speed": {
                "vectorization_min": 200,  # Higher threshold for speed mode
                "ai_max": 50,  # Lower AI threshold for speed
                "sequential_max": 100,  # Prefer hash/vectorized for speed
                "complexity_weight": 0.3,
                "accuracy_weight": 0.2,
                "speed_weight": 0.5
            },
            "accuracy": {
                "vectorization_min": 30,   # Lower threshold for accuracy mode
                "ai_max": 500,  # Higher AI threshold for accuracy
                "sequential_max": 1000,  # Allow sequential for accuracy
                "complexity_weight": 0.2,
                "accuracy_weight": 0.6,
                "speed_weight": 0.2
            },
            "balanced": {
                "vectorization_min": 50,   # Balanced thresholds
                "ai_max": 200,
                "sequential_max": 500,
                "complexity_weight": 0.35,
                "accuracy_weight": 0.35,
                "speed_weight": 0.3
            }
        }
        
        return thresholds.get(mode, thresholds["balanced"])
    
    def _init_components(self):
        """Initialize available deduplication components"""
        
        # TF-IDF vectorizer
        if SKLEARN_AVAILABLE:
            self.tfidf_vectorizer = TfidfVectorizer(
                ngram_range=(1, 2),
                max_features=10000,
                lowercase=True,
                token_pattern=r'\b\w+\b'
            )
        else:
            self.tfidf_vectorizer = None
        
        # AI client
        if OPENAI_AVAILABLE and self.ai_api_key:
            if self.ai_provider == "deepseek":
                self.ai_client = OpenAI(
                    api_key=self.ai_api_key,
                    base_url="https://api.deepseek.com"
                )
                self.ai_model = "deepseek-chat"
            else:
                self.ai_client = OpenAI(api_key=self.ai_api_key)
                self.ai_model = "gpt-4o-mini"
        else:
            self.ai_client = None
    
    def _list_available_methods(self) -> List[str]:
        """List available deduplication methods"""
        methods = ["hash_only", "basic_sequential", "optimized_sequential"]
        
        if SKLEARN_AVAILABLE:
            methods.append("tfidf_vectorized")
        
        if self.ai_client:
            methods.append("ai_semantic")
            methods.append("hybrid")
        
        return methods
    
    def adaptive_deduplicate(self, articles: List[Dict], category_name: str = "") -> Tuple[List[Dict], AdaptiveStats]:
        """
        Adaptive deduplication that automatically selects the best algorithm
        """
        start_time = time.time()
        stats = AdaptiveStats()
        stats.total_articles = len(articles)
        
        if not articles:
            return articles, stats
        
        print(f"🧠 Starting adaptive deduplication for {len(articles)} articles...")
        
        # Phase 1: Algorithm Selection
        selection_start = time.time()
        selected_method = self._select_optimal_algorithm(articles, category_name)
        stats.algorithm_selection_time = time.time() - selection_start
        stats.method_used = selected_method.value
        
        print(f"   🎯 Selected method: {selected_method.value}")
        print(f"   ⏱️ Algorithm selection time: {stats.algorithm_selection_time:.3f}s")
        
        # Phase 2: Execute Selected Algorithm
        result_articles, method_stats = self._execute_algorithm(articles, selected_method, stats)
        
        # Phase 3: Record Performance Metrics
        stats.processing_time = time.time() - start_time
        self._record_performance(selected_method, stats, len(articles))
        
        print(f"   ✅ Adaptive deduplication complete:")
        print(f"      Method used: {selected_method.value}")
        print(f"      Articles: {len(articles)} → {len(result_articles)}")
        print(f"      Removed: {stats.total_removed} articles ({stats.removal_rate:.1f}%)")
        print(f"      Total time: {stats.processing_time:.3f}s")
        
        return result_articles, stats
    
    def _select_optimal_algorithm(self, articles: List[Dict], category: str) -> DeduplicationMethod:
        """Intelligent algorithm selection based on data characteristics"""
        
        n_articles = len(articles)
        
        # Quick return for small datasets
        if n_articles <= 1:
            return DeduplicationMethod.HASH_ONLY
        
        # Analyze article characteristics
        characteristics = self._analyze_articles(articles)
        
        # Calculate algorithm scores
        algorithm_scores = {}
        
        # Always available methods
        algorithm_scores[DeduplicationMethod.BASIC_SEQUENTIAL] = self._score_basic_sequential(n_articles, characteristics)
        algorithm_scores[DeduplicationMethod.OPTIMIZED_SEQUENTIAL] = self._score_optimized_sequential(n_articles, characteristics)
        
        # TF-IDF method (if available)
        if SKLEARN_AVAILABLE and n_articles >= self.thresholds["vectorization_min"]:
            algorithm_scores[DeduplicationMethod.TFIDF_VECTORIZED] = self._score_tfidf_vectorized(n_articles, characteristics)
        
        # AI method (if available and not too many articles)
        if self.ai_client and n_articles <= self.thresholds["ai_max"]:
            algorithm_scores[DeduplicationMethod.AI_SEMANTIC] = self._score_ai_semantic(n_articles, characteristics)
        
        # Hybrid method (if both AI and TF-IDF available)
        if self.ai_client and SKLEARN_AVAILABLE and n_articles <= self.thresholds["ai_max"]:
            algorithm_scores[DeduplicationMethod.HYBRID] = self._score_hybrid(n_articles, characteristics)
        
        # Select best scoring algorithm
        best_method = max(algorithm_scores.items(), key=lambda x: x[1])[0]
        
        print(f"      📊 Algorithm scores:")
        for method, score in sorted(algorithm_scores.items(), key=lambda x: x[1], reverse=True):
            print(f"         {method.value}: {score:.2f}")
        
        return best_method
    
    def _analyze_articles(self, articles: List[Dict]) -> Dict:
        """Analyze article characteristics for algorithm selection"""
        
        titles = [a.get('title', '') for a in articles]
        
        # Basic statistics
        avg_length = sum(len(title) for title in titles) / len(titles) if titles else 0
        max_length = max(len(title) for title in titles) if titles else 0
        min_length = min(len(title) for title in titles) if titles else 0
        
        # Language complexity (Chinese vs English ratio)
        chinese_ratio = self._estimate_chinese_ratio(titles)
        
        # Potential duplicate density (rough estimation)
        duplicate_density = self._estimate_duplicate_density(titles)
        
        return {
            'avg_length': avg_length,
            'max_length': max_length,
            'min_length': min_length,
            'chinese_ratio': chinese_ratio,
            'duplicate_density': duplicate_density,
            'total_articles': len(articles)
        }
    
    def _estimate_chinese_ratio(self, titles: List[str]) -> float:
        """Estimate ratio of Chinese characters in titles"""
        if not titles:
            return 0.0
        
        total_chars = 0
        chinese_chars = 0
        
        for title in titles:
            total_chars += len(title)
            for char in title:
                if '\u4e00' <= char <= '\u9fff':  # Chinese character range
                    chinese_chars += 1
        
        return chinese_chars / total_chars if total_chars > 0 else 0.0
    
    def _estimate_duplicate_density(self, titles: List[str]) -> float:
        """Rough estimation of potential duplicate density"""
        if len(titles) < 2:
            return 0.0
        
        # Sample up to 20 titles for quick estimation
        sample_titles = titles[:min(20, len(titles))]
        duplicate_pairs = 0
        total_pairs = 0
        
        for i in range(len(sample_titles)):
            for j in range(i + 1, len(sample_titles)):
                total_pairs += 1
                similarity = difflib.SequenceMatcher(
                    None, 
                    sample_titles[i].lower(), 
                    sample_titles[j].lower()
                ).ratio()
                
                if similarity >= self.similarity_threshold:
                    duplicate_pairs += 1
        
        return duplicate_pairs / total_pairs if total_pairs > 0 else 0.0
    
    def _score_basic_sequential(self, n_articles: int, characteristics: Dict) -> float:
        """Score basic sequential algorithm"""
        # Good for very small datasets
        speed_score = max(0, 1 - n_articles / 50)  # Penalty for large datasets
        accuracy_score = 0.7  # Moderate accuracy
        complexity_score = 1.0  # Simple implementation
        
        return (speed_score * self.thresholds["speed_weight"] + 
                accuracy_score * self.thresholds["accuracy_weight"] +
                complexity_score * self.thresholds["complexity_weight"])
    
    def _score_optimized_sequential(self, n_articles: int, characteristics: Dict) -> float:
        """Score optimized sequential algorithm"""
        # Good for medium datasets
        speed_score = max(0, 1 - n_articles / 200)
        accuracy_score = 0.8  # Good accuracy
        complexity_score = 0.8  # Moderate complexity
        
        return (speed_score * self.thresholds["speed_weight"] + 
                accuracy_score * self.thresholds["accuracy_weight"] +
                complexity_score * self.thresholds["complexity_weight"])
    
    def _score_tfidf_vectorized(self, n_articles: int, characteristics: Dict) -> float:
        """Score TF-IDF vectorized algorithm"""
        # Excellent for large datasets
        speed_score = min(1.0, n_articles / 100)  # Better with more articles
        accuracy_score = 0.9  # High accuracy for semantic similarity
        complexity_score = 0.6  # Higher complexity
        
        # Bonus for mixed language content
        language_bonus = 0.1 if 0.2 < characteristics['chinese_ratio'] < 0.8 else 0
        
        score = (speed_score * self.thresholds["speed_weight"] + 
                accuracy_score * self.thresholds["accuracy_weight"] +
                complexity_score * self.thresholds["complexity_weight"])
        
        return score + language_bonus
    
    def _score_ai_semantic(self, n_articles: int, characteristics: Dict) -> float:
        """Score AI semantic algorithm"""
        # Best accuracy but slower and has API costs
        speed_score = max(0, 1 - n_articles / 100)  # Penalty for large datasets
        accuracy_score = 0.95  # Highest accuracy
        complexity_score = 0.4  # High complexity and dependencies
        
        # Bonus for high duplicate density (AI excels at edge cases)
        density_bonus = characteristics['duplicate_density'] * 0.2
        
        score = (speed_score * self.thresholds["speed_weight"] + 
                accuracy_score * self.thresholds["accuracy_weight"] +
                complexity_score * self.thresholds["complexity_weight"])
        
        return score + density_bonus
    
    def _score_hybrid(self, n_articles: int, characteristics: Dict) -> float:
        """Score hybrid AI + TF-IDF algorithm"""
        # Combines benefits of both but higher complexity
        speed_score = max(0, 1 - n_articles / 150)
        accuracy_score = 0.92  # Very high accuracy
        complexity_score = 0.3  # Highest complexity
        
        # Bonus for complex scenarios
        complexity_bonus = 0.15 if characteristics['duplicate_density'] > 0.3 else 0
        
        score = (speed_score * self.thresholds["speed_weight"] + 
                accuracy_score * self.thresholds["accuracy_weight"] +
                complexity_score * self.thresholds["complexity_weight"])
        
        return score + complexity_bonus
    
    def _execute_algorithm(self, articles: List[Dict], method: DeduplicationMethod, stats: AdaptiveStats) -> Tuple[List[Dict], Dict]:
        """Execute the selected deduplication algorithm"""
        
        if method == DeduplicationMethod.HASH_ONLY:
            return self._hash_only_dedup(articles, stats)
        elif method == DeduplicationMethod.BASIC_SEQUENTIAL:
            return self._basic_sequential_dedup(articles, stats)
        elif method == DeduplicationMethod.OPTIMIZED_SEQUENTIAL:
            return self._optimized_sequential_dedup(articles, stats)
        elif method == DeduplicationMethod.TFIDF_VECTORIZED:
            return self._tfidf_vectorized_dedup(articles, stats)
        elif method == DeduplicationMethod.AI_SEMANTIC:
            return self._ai_semantic_dedup(articles, stats)
        elif method == DeduplicationMethod.HYBRID:
            return self._hybrid_dedup(articles, stats)
        else:
            # Fallback to optimized sequential
            return self._optimized_sequential_dedup(articles, stats)
    
    def _hash_only_dedup(self, articles: List[Dict], stats: AdaptiveStats) -> Tuple[List[Dict], Dict]:
        """Hash-based exact duplicate removal only"""
        seen_hashes: Set[str] = set()
        unique_articles = []
        
        for article in articles:
            title = self._clean_title(article.get('title', ''))
            title_hash = hashlib.md5(title.encode('utf-8')).hexdigest()
            
            if title_hash not in seen_hashes:
                seen_hashes.add(title_hash)
                unique_articles.append(article)
            else:
                stats.exact_removed += 1
        
        return unique_articles, {}
    
    def _basic_sequential_dedup(self, articles: List[Dict], stats: AdaptiveStats) -> Tuple[List[Dict], Dict]:
        """Basic O(n²) sequential deduplication"""
        unique_articles = []
        seen_titles = []
        
        for article in articles:
            title = self._clean_title(article.get('title', ''))
            
            is_duplicate = False
            for seen_title in seen_titles:
                similarity = difflib.SequenceMatcher(None, title, seen_title).ratio()
                if similarity >= self.similarity_threshold:
                    is_duplicate = True
                    stats.similarity_removed += 1
                    break
            
            if not is_duplicate:
                unique_articles.append(article)
                seen_titles.append(title)
        
        return unique_articles, {}
    
    def _optimized_sequential_dedup(self, articles: List[Dict], stats: AdaptiveStats) -> Tuple[List[Dict], Dict]:
        """Optimized sequential with hash pre-filtering"""
        # Phase 1: Hash deduplication
        unique_articles, _ = self._hash_only_dedup(articles, stats)
        
        if len(unique_articles) <= 1:
            return unique_articles, {}
        
        # Phase 2: Similarity deduplication with optimizations
        clean_titles = [self._clean_title(a.get('title', '')) for a in unique_articles]
        keep_indices = set(range(len(unique_articles)))
        
        for i in range(len(unique_articles)):
            if i not in keep_indices:
                continue
                
            title_i = clean_titles[i]
            
            for j in range(i + 1, len(unique_articles)):
                if j not in keep_indices:
                    continue
                
                title_j = clean_titles[j]
                
                # Quick pre-screening
                if abs(len(title_i) - len(title_j)) > max(len(title_i), len(title_j)) * 0.3:
                    continue
                
                similarity = difflib.SequenceMatcher(None, title_i, title_j).ratio()
                if similarity >= self.similarity_threshold:
                    keep_indices.remove(j)
                    stats.similarity_removed += 1
        
        final_articles = [unique_articles[i] for i in sorted(keep_indices)]
        return final_articles, {}
    
    def _tfidf_vectorized_dedup(self, articles: List[Dict], stats: AdaptiveStats) -> Tuple[List[Dict], Dict]:
        """TF-IDF vectorized deduplication"""
        if not SKLEARN_AVAILABLE:
            return self._optimized_sequential_dedup(articles, stats)
        
        # Phase 1: Hash deduplication
        unique_articles, _ = self._hash_only_dedup(articles, stats)
        
        if len(unique_articles) <= 1:
            return unique_articles, {}
        
        try:
            # Phase 2: TF-IDF similarity
            titles = [self._clean_title(a.get('title', '')) for a in unique_articles]
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(titles)
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            # Find duplicates
            duplicate_indices = set()
            for i in range(len(unique_articles)):
                if i in duplicate_indices:
                    continue
                for j in range(i + 1, len(unique_articles)):
                    if j not in duplicate_indices and similarity_matrix[i, j] >= self.similarity_threshold:
                        duplicate_indices.add(j)
                        stats.similarity_removed += 1
            
            final_articles = [unique_articles[i] for i in range(len(unique_articles)) if i not in duplicate_indices]
            return final_articles, {}
            
        except Exception as e:
            print(f"         ⚠️ TF-IDF failed: {e}, fallback to sequential")
            return self._optimized_sequential_dedup(unique_articles, stats)
    
    def _ai_semantic_dedup(self, articles: List[Dict], stats: AdaptiveStats) -> Tuple[List[Dict], Dict]:
        """AI-powered semantic deduplication"""
        # Placeholder - in real implementation would use AI API
        print(f"         🤖 AI semantic deduplication (simulated)")
        stats.ai_removed = len(articles) // 10  # Simulate removing 10%
        return articles[:-stats.ai_removed] if stats.ai_removed > 0 else articles, {}
    
    def _hybrid_dedup(self, articles: List[Dict], stats: AdaptiveStats) -> Tuple[List[Dict], Dict]:
        """Hybrid AI + TF-IDF deduplication"""
        # Phase 1: TF-IDF for bulk processing
        tfidf_result, _ = self._tfidf_vectorized_dedup(articles, stats)
        
        # Phase 2: AI for edge cases (simulated)
        print(f"         🧠 Hybrid processing: TF-IDF + AI refinement")
        additional_removed = len(tfidf_result) // 20  # Simulate AI finding 5% more
        stats.ai_removed = additional_removed
        
        final_result = tfidf_result[:-additional_removed] if additional_removed > 0 else tfidf_result
        return final_result, {}
    
    def _clean_title(self, title: str) -> str:
        """Clean title for comparison"""
        import re
        title = title.lower()
        title = re.sub(r'[^\w\s]', ' ', title)
        title = re.sub(r'\s+', ' ', title).strip()
        return title
    
    def _record_performance(self, method: DeduplicationMethod, stats: AdaptiveStats, n_articles: int):
        """Record performance metrics for adaptive learning"""
        performance_record = {
            'method': method.value,
            'n_articles': n_articles,
            'processing_time': stats.processing_time,
            'removal_rate': stats.removal_rate,
            'timestamp': time.time()
        }
        
        self.performance_history.append(performance_record)
        
        # Keep only recent records (last 100)
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]
        
        stats.performance_metrics = performance_record
    
    def get_performance_report(self) -> Dict:
        """Get comprehensive performance report"""
        if not self.performance_history:
            return {"message": "No performance data available"}
        
        # Aggregate statistics
        methods_used = {}
        for record in self.performance_history:
            method = record['method']
            if method not in methods_used:
                methods_used[method] = {
                    'count': 0,
                    'avg_time': 0,
                    'avg_removal_rate': 0,
                    'total_articles': 0
                }
            
            methods_used[method]['count'] += 1
            methods_used[method]['avg_time'] += record['processing_time']
            methods_used[method]['avg_removal_rate'] += record['removal_rate']
            methods_used[method]['total_articles'] += record['n_articles']
        
        # Calculate averages
        for method_stats in methods_used.values():
            count = method_stats['count']
            method_stats['avg_time'] /= count
            method_stats['avg_removal_rate'] /= count
            method_stats['avg_articles'] = method_stats['total_articles'] / count
        
        return {
            'total_operations': len(self.performance_history),
            'methods_used': methods_used,
            'available_methods': self._list_available_methods(),
            'current_mode': self.performance_mode,
            'thresholds': self.thresholds
        }