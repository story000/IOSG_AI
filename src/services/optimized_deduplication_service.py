"""Optimized article deduplication service with performance enhancements"""

import hashlib
import difflib
import time
import sqlite3
import threading
from typing import List, Dict, Tuple, Set, Optional, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from functools import lru_cache
import numpy as np
import os

# Try to import scikit-learn components, use fallback if not available
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    print("⚠️ scikit-learn not available, using fallback algorithms")
    SKLEARN_AVAILABLE = False


@dataclass
class DeduplicationStats:
    """Statistics for deduplication operations"""
    total_articles: int = 0
    exact_removed: int = 0
    similarity_removed: int = 0
    processing_time: float = 0.0
    method_used: str = ""
    duplicate_groups: List = None
    
    def __post_init__(self):
        if self.duplicate_groups is None:
            self.duplicate_groups = []
    
    @property
    def total_removed(self) -> int:
        return self.exact_removed + self.similarity_removed
    
    @property
    def removal_rate(self) -> float:
        if self.total_articles == 0:
            return 0.0
        return (self.total_removed / self.total_articles) * 100
    
    @property
    def final_count(self) -> int:
        return self.total_articles - self.total_removed


class DeduplicationCache:
    """SQLite-based caching system for similarity calculations"""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self.db_path = os.path.join(cache_dir, "dedup_cache.db")
        self._lock = threading.Lock()
        self._init_cache_db()
    
    def _init_cache_db(self):
        """Initialize cache database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS similarity_cache (
                    title1_hash TEXT,
                    title2_hash TEXT,
                    similarity REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (title1_hash, title2_hash)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_title_hashes 
                ON similarity_cache(title1_hash, title2_hash)
            """)
    
    def get_similarity(self, title1: str, title2: str) -> Optional[float]:
        """Get cached similarity score"""
        hash1 = self._hash_title(title1)
        hash2 = self._hash_title(title2)
        
        # Ensure consistent ordering
        if hash1 > hash2:
            hash1, hash2 = hash2, hash1
        
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT similarity FROM similarity_cache WHERE title1_hash=? AND title2_hash=?",
                    (hash1, hash2)
                )
                result = cursor.fetchone()
                return result[0] if result else None
    
    def cache_similarity(self, title1: str, title2: str, similarity: float):
        """Cache similarity score"""
        hash1 = self._hash_title(title1)
        hash2 = self._hash_title(title2)
        
        # Ensure consistent ordering
        if hash1 > hash2:
            hash1, hash2 = hash2, hash1
        
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO similarity_cache (title1_hash, title2_hash, similarity) VALUES (?, ?, ?)",
                    (hash1, hash2, similarity)
                )
    
    def _hash_title(self, title: str) -> str:
        """Generate hash for title"""
        return hashlib.md5(title.encode('utf-8')).hexdigest()
    
    def clear_cache(self):
        """Clear all cached data"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM similarity_cache")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM similarity_cache")
            count = cursor.fetchone()[0]
            
            cursor = conn.execute("""
                SELECT AVG(similarity), MIN(similarity), MAX(similarity) 
                FROM similarity_cache
            """)
            stats = cursor.fetchone()
            
            return {
                'total_entries': count,
                'avg_similarity': stats[0] if stats[0] else 0,
                'min_similarity': stats[1] if stats[1] else 0,
                'max_similarity': stats[2] if stats[2] else 0
            }


class OptimizedDeduplicationService:
    """Optimized deduplication service with multiple performance enhancements"""
    
    def __init__(self, 
                 similarity_threshold: float = 0.7,
                 use_vectorization: bool = True,
                 enable_cache: bool = True,
                 max_workers: int = 4,
                 vectorization_min_articles: int = 50):
        
        self.similarity_threshold = similarity_threshold
        self.use_vectorization = use_vectorization and SKLEARN_AVAILABLE
        self.enable_cache = enable_cache
        self.max_workers = max_workers
        self.vectorization_min_articles = vectorization_min_articles
        
        # Initialize cache
        self.cache = DeduplicationCache() if enable_cache else None
        
        # Initialize TF-IDF vectorizer
        if self.use_vectorization:
            self.tfidf_vectorizer = TfidfVectorizer(
                ngram_range=(1, 2),
                max_features=10000,
                stop_words=None,  # Custom stop words can be added
                lowercase=True,
                token_pattern=r'\b\w+\b'
            )
        
        print(f"✅ Initialized OptimizedDeduplicationService")
        print(f"   - Similarity threshold: {similarity_threshold}")
        print(f"   - Vectorization: {self.use_vectorization}")
        print(f"   - Caching: {enable_cache}")
        print(f"   - Max workers: {max_workers}")
    
    def deduplicate_by_title(self, articles: List[Dict], category_name: str = "") -> Tuple[List[Dict], Dict]:
        """
        Enhanced deduplication with multiple optimization strategies
        """
        start_time = time.time()
        
        if not articles:
            return articles, self._create_empty_stats()
        
        print(f"  🚀 Starting optimized deduplication for {len(articles)} articles...")
        
        # Phase 1: Exact duplicate removal using hashes
        print(f"  📋 Phase 1: Hash-based exact duplicate removal...")
        unique_articles, hash_stats = self._remove_exact_duplicates(articles)
        
        if len(unique_articles) <= 1:
            processing_time = time.time() - start_time
            return unique_articles, {
                'total_articles': len(articles),
                'exact_removed': hash_stats['exact_removed'],
                'similarity_removed': 0,
                'processing_time': processing_time,
                'method_used': 'hash_only',
                'duplicate_groups': [],
                'removal_rate': hash_stats['exact_removed'] / len(articles) * 100 if articles else 0
            }
        
        # Phase 2: Choose similarity algorithm based on data size and settings
        print(f"  🔍 Phase 2: Similarity-based deduplication...")
        
        if self.use_vectorization and len(unique_articles) >= self.vectorization_min_articles:
            remaining_articles, similarity_stats = self._vectorized_deduplication(unique_articles)
            method_used = "vectorized"
        else:
            remaining_articles, similarity_stats = self._optimized_sequential_deduplication(unique_articles)
            method_used = "optimized_sequential"
        
        processing_time = time.time() - start_time
        
        # Combine statistics
        final_stats = {
            'total_articles': len(articles),
            'exact_removed': hash_stats['exact_removed'],
            'similarity_removed': similarity_stats['similarity_removed'],
            'processing_time': processing_time,
            'method_used': method_used,
            'duplicate_groups': similarity_stats.get('duplicate_groups', []),
            'removal_rate': (hash_stats['exact_removed'] + similarity_stats['similarity_removed']) / len(articles) * 100 if articles else 0
        }
        
        total_removed = final_stats['exact_removed'] + final_stats['similarity_removed']
        print(f"  ✅ Deduplication complete: {len(articles)} → {len(remaining_articles)} articles")
        print(f"     Exact duplicates removed: {final_stats['exact_removed']}")
        print(f"     Similar articles removed: {final_stats['similarity_removed']}")
        print(f"     Processing time: {processing_time:.2f}s")
        print(f"     Method used: {method_used}")
        
        return remaining_articles, final_stats
    
    def _remove_exact_duplicates(self, articles: List[Dict]) -> Tuple[List[Dict], Dict]:
        """Phase 1: Remove exact duplicates using hash comparison"""
        seen_hashes: Set[str] = set()
        unique_articles = []
        removed_exact = 0
        
        for article in articles:
            title = article.get('title', '')
            clean_title = self._clean_title_for_comparison(title)
            title_hash = hashlib.md5(clean_title.encode('utf-8')).hexdigest()
            
            if title_hash not in seen_hashes:
                seen_hashes.add(title_hash)
                unique_articles.append(article)
            else:
                removed_exact += 1
        
        if removed_exact > 0:
            print(f"    ✅ Removed {removed_exact} exact duplicates")
        
        return unique_articles, {'exact_removed': removed_exact}
    
    def _vectorized_deduplication(self, articles: List[Dict]) -> Tuple[List[Dict], Dict]:
        """Phase 2a: Vectorized deduplication using TF-IDF and cosine similarity"""
        try:
            print(f"    🔬 Using vectorized approach for {len(articles)} articles...")
            
            # Extract and clean titles
            titles = [self._clean_title_for_comparison(a.get('title', '')) for a in articles]
            
            # Create TF-IDF matrix
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(titles)
            
            # Calculate cosine similarity matrix (only upper triangle to save memory)
            print(f"    📊 Computing similarity matrix...")
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            # Find duplicate groups
            duplicate_indices = set()
            duplicate_groups = []
            
            n = len(articles)
            for i in range(n):
                if i in duplicate_indices:
                    continue
                
                current_group = [i]
                for j in range(i + 1, n):
                    if j not in duplicate_indices and similarity_matrix[i, j] >= self.similarity_threshold:
                        current_group.append(j)
                        duplicate_indices.add(j)
                
                if len(current_group) > 1:
                    duplicate_groups.append(current_group)
                    print(f"    📝 Found duplicate group: {len(current_group)} articles (similarity: {max(similarity_matrix[i, current_group[1:]]*100):.1f}%)")
            
            # Build result keeping first article from each group
            keep_indices = set(range(n)) - duplicate_indices
            for group in duplicate_groups:
                keep_indices.add(group[0])  # Keep first article from each group
            
            unique_articles = [articles[i] for i in sorted(keep_indices)]
            similarity_removed = len(articles) - len(unique_articles)
            
            return unique_articles, {
                'similarity_removed': similarity_removed,
                'duplicate_groups': duplicate_groups,
                'method': 'vectorized'
            }
            
        except Exception as e:
            print(f"    ⚠️ Vectorized deduplication failed: {e}, falling back to sequential method")
            return self._optimized_sequential_deduplication(articles)
    
    def _optimized_sequential_deduplication(self, articles: List[Dict]) -> Tuple[List[Dict], Dict]:
        """Phase 2b: Optimized sequential deduplication with caching and parallel processing"""
        print(f"    🔄 Using optimized sequential approach for {len(articles)} articles...")
        
        n = len(articles)
        if n <= 1:
            return articles, {'similarity_removed': 0, 'duplicate_groups': [], 'method': 'sequential'}
        
        # Pre-process titles for comparison
        clean_titles = [self._clean_title_for_comparison(a.get('title', '')) for a in articles]
        
        # Find duplicate pairs using parallel processing
        duplicate_pairs = []
        
        # Process in batches to balance memory and performance
        batch_size = min(100, n)
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            
            # Submit batch jobs
            for i in range(0, n, batch_size):
                batch_end = min(i + batch_size, n)
                future = executor.submit(
                    self._find_duplicates_in_batch,
                    clean_titles, articles, i, batch_end, n
                )
                futures.append(future)
            
            # Collect results
            for future in as_completed(futures):
                try:
                    batch_pairs = future.result()
                    duplicate_pairs.extend(batch_pairs)
                except Exception as e:
                    print(f"    ⚠️ Batch processing error: {e}")
        
        # Build final result using Union-Find algorithm
        return self._build_dedup_result(articles, duplicate_pairs)
    
    def _find_duplicates_in_batch(self, clean_titles: List[str], articles: List[Dict],
                                  start_idx: int, end_idx: int, total_len: int) -> List[Tuple[int, int, float]]:
        """Find duplicate pairs in a batch with optimizations"""
        pairs = []
        
        for i in range(start_idx, end_idx):
            title_i = clean_titles[i]
            
            for j in range(i + 1, total_len):
                title_j = clean_titles[j]
                
                # Quick pre-screening: skip if length difference is too large
                if abs(len(title_i) - len(title_j)) > max(len(title_i), len(title_j)) * 0.4:
                    continue
                
                # Check cache first
                similarity = None
                if self.cache:
                    similarity = self.cache.get_similarity(title_i, title_j)
                
                # Calculate similarity if not cached
                if similarity is None:
                    similarity = difflib.SequenceMatcher(None, title_i, title_j).ratio()
                    
                    # Cache the result
                    if self.cache:
                        self.cache.cache_similarity(title_i, title_j, similarity)
                
                if similarity >= self.similarity_threshold:
                    pairs.append((i, j, similarity))
                    print(f"    📝 Found duplicate pair: {similarity*100:.1f}% similarity")
        
        return pairs
    
    def _build_dedup_result(self, articles: List[Dict], 
                           duplicate_pairs: List[Tuple[int, int, float]]) -> Tuple[List[Dict], Dict]:
        """Build final deduplication result using Union-Find algorithm"""
        
        if not duplicate_pairs:
            return articles, {
                'similarity_removed': 0,
                'duplicate_groups': [],
                'method': 'optimized_sequential'
            }
        
        # Union-Find data structure for grouping duplicates
        parent = list(range(len(articles)))
        
        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])  # Path compression
            return parent[x]
        
        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[py] = px
        
        # Group duplicates
        for i, j, sim in duplicate_pairs:
            union(i, j)
        
        # Collect groups
        groups = {}
        for i in range(len(articles)):
            root = find(i)
            if root not in groups:
                groups[root] = []
            groups[root].append(i)
        
        # Filter duplicate groups and build result
        duplicate_groups = []
        duplicate_indices = set()
        
        for group in groups.values():
            if len(group) > 1:
                duplicate_groups.append(group)
                duplicate_indices.update(group[1:])  # Keep first, mark others as duplicates
        
        # Build final article list
        unique_articles = [articles[i] for i in range(len(articles)) if i not in duplicate_indices]
        
        return unique_articles, {
            'similarity_removed': len(duplicate_indices),
            'duplicate_groups': duplicate_groups,
            'method': 'optimized_sequential'
        }
    
    def cross_category_deduplication(self, filtered_results: Dict[str, List[Dict]]) -> Tuple[Dict, Dict]:
        """
        Enhanced cross-category deduplication with optimizations
        """
        start_time = time.time()
        
        # Define priority order
        priority_order = [
            "portfolios",
            "项目融资", 
            "基金融资",
            "公链/L2/主网",
            "中间件/工具协议",
            "DeFi",
            "RWA",
            "稳定币",
            "应用协议",
            "GameFi",
            "交易所/钱包",
            "AI + Crypto",
            "DePIN"
        ]
        
        # Use hash set for O(1) lookups instead of similarity calculations where possible
        seen_hashes: Set[str] = set()
        seen_titles: Set[str] = set()
        cross_dedup_stats = {}
        
        print("\n🔄 Starting optimized cross-category deduplication...")
        
        # Process categories by priority
        for category in priority_order:
            if category not in filtered_results:
                continue
                
            articles = filtered_results[category]
            if not articles:
                cross_dedup_stats[category] = {'removed_count': 0}
                continue
            
            remaining_articles = []
            removed_count = 0
            
            for article in articles:
                title = article.get('title', '')
                clean_title = self._clean_title_for_comparison(title)
                title_hash = hashlib.md5(clean_title.encode('utf-8')).hexdigest()
                
                # First check exact hash match (fastest)
                if title_hash in seen_hashes:
                    removed_count += 1
                    print(f"  ❌ Exact duplicate in {category}: {title[:50]}...")
                    continue
                
                # Then check similarity against all seen titles
                is_duplicate = False
                for seen_title in seen_titles:
                    similarity = difflib.SequenceMatcher(None, clean_title, seen_title).ratio()
                    if similarity >= self.similarity_threshold:
                        is_duplicate = True
                        removed_count += 1
                        print(f"  ❌ Similar duplicate in {category} (similarity: {similarity:.2f}): {title[:50]}...")
                        break
                
                if not is_duplicate:
                    remaining_articles.append(article)
                    seen_hashes.add(title_hash)
                    seen_titles.add(clean_title)
            
            # Update results
            filtered_results[category] = remaining_articles
            cross_dedup_stats[category] = {'removed_count': removed_count}
            
            if removed_count > 0:
                print(f"  📊 {category}: {len(articles)} → {len(remaining_articles)} articles (removed {removed_count})")
        
        processing_time = time.time() - start_time
        
        # Report results
        total_removed = sum(stats['removed_count'] for stats in cross_dedup_stats.values())
        if total_removed > 0:
            print(f"\n📊 Cross-category deduplication complete: removed {total_removed} duplicates in {processing_time:.2f}s")
        else:
            print(f"\n📊 Cross-category deduplication complete: no duplicates found in {processing_time:.2f}s")
        
        return filtered_results, cross_dedup_stats
    
    def _clean_title_for_comparison(self, title: str) -> str:
        """Enhanced title cleaning for better comparison accuracy"""
        import re
        
        # Convert to lowercase
        title = title.lower()
        
        # Remove common prefixes/suffixes
        title = re.sub(r'^\d+\.\s*', '', title)  # Remove numbering
        title = re.sub(r'\s*\[.*?\]$', '', title)  # Remove trailing brackets
        title = re.sub(r'\s*\(.*?\)$', '', title)  # Remove trailing parentheses
        
        # Normalize whitespace and punctuation
        title = re.sub(r'[^\w\s]', ' ', title)  # Replace punctuation with spaces
        title = re.sub(r'\s+', ' ', title)  # Normalize whitespace
        title = title.strip()
        
        # Remove very common words that don't add meaning
        common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = title.split()
        words = [w for w in words if w not in common_words and len(w) > 1]
        
        return ' '.join(words)
    
    def _create_empty_stats(self) -> Dict:
        """Create empty statistics dictionary"""
        return {
            'total_articles': 0,
            'exact_removed': 0,
            'similarity_removed': 0,
            'processing_time': 0.0,
            'method_used': 'none',
            'duplicate_groups': [],
            'removal_rate': 0.0
        }
    
    def get_performance_stats(self) -> Dict:
        """Get performance and cache statistics"""
        stats = {
            'service_settings': {
                'similarity_threshold': self.similarity_threshold,
                'use_vectorization': self.use_vectorization,
                'enable_cache': self.enable_cache,
                'max_workers': self.max_workers,
                'vectorization_min_articles': self.vectorization_min_articles
            },
            'sklearn_available': SKLEARN_AVAILABLE
        }
        
        if self.cache:
            stats['cache_stats'] = self.cache.get_cache_stats()
        
        return stats
    
    def clear_cache(self):
        """Clear similarity cache"""
        if self.cache:
            self.cache.clear_cache()
            print("✅ Cache cleared successfully")
        else:
            print("ℹ️ No cache to clear")