#!/usr/bin/env python3
"""
Advanced deduplication algorithm test with TF-IDF vectorization
"""

import time
import random
import hashlib
import difflib
from typing import List, Dict, Set
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class AdvancedDeduplicationService:
    """Advanced deduplication with TF-IDF vectorization"""
    
    def __init__(self, similarity_threshold: float = 0.7, vectorization_min_articles: int = 50):
        self.similarity_threshold = similarity_threshold
        self.vectorization_min_articles = vectorization_min_articles
        
        self.tfidf_vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=10000,
            lowercase=True,
            token_pattern=r'\b\w+\b'
        )
    
    def deduplicate_by_title(self, articles: List[Dict]) -> tuple:
        """Advanced deduplication with multiple phases"""
        start_time = time.time()
        
        if not articles:
            return articles, {'method': 'empty', 'time': 0, 'removed': 0}
        
        print(f"    🚀 Starting advanced deduplication for {len(articles)} articles...")
        
        # Phase 1: Hash-based exact duplicate removal
        unique_articles, hash_stats = self._remove_exact_duplicates(articles)
        print(f"    📋 Phase 1: Removed {hash_stats['exact_removed']} exact duplicates")
        
        if len(unique_articles) <= 1:
            processing_time = time.time() - start_time
            return unique_articles, {
                'method': 'hash_only',
                'time': processing_time, 
                'exact_removed': hash_stats['exact_removed'],
                'similarity_removed': 0,
                'total_removed': hash_stats['exact_removed']
            }
        
        # Phase 2: Choose algorithm based on size
        if len(unique_articles) >= self.vectorization_min_articles:
            print(f"    🔬 Phase 2: Using TF-IDF vectorization for {len(unique_articles)} articles")
            remaining_articles, similarity_stats = self._vectorized_deduplication(unique_articles)
            method = "tfidf_vectorized"
        else:
            print(f"    🔄 Phase 2: Using optimized sequential for {len(unique_articles)} articles")
            remaining_articles, similarity_stats = self._sequential_deduplication(unique_articles)
            method = "optimized_sequential"
        
        processing_time = time.time() - start_time
        
        total_removed = hash_stats['exact_removed'] + similarity_stats['similarity_removed']
        
        return remaining_articles, {
            'method': method,
            'time': processing_time,
            'exact_removed': hash_stats['exact_removed'],
            'similarity_removed': similarity_stats['similarity_removed'],
            'total_removed': total_removed,
            'duplicate_groups': similarity_stats.get('duplicate_groups', [])
        }
    
    def _remove_exact_duplicates(self, articles: List[Dict]) -> tuple:
        """Phase 1: Hash-based exact duplicate removal"""
        seen_hashes: Set[str] = set()
        unique_articles = []
        removed_count = 0
        
        for article in articles:
            title = article.get('title', '')
            clean_title = self._clean_title(title)
            title_hash = hashlib.md5(clean_title.encode('utf-8')).hexdigest()
            
            if title_hash not in seen_hashes:
                seen_hashes.add(title_hash)
                unique_articles.append(article)
            else:
                removed_count += 1
        
        return unique_articles, {'exact_removed': removed_count}
    
    def _vectorized_deduplication(self, articles: List[Dict]) -> tuple:
        """Phase 2a: TF-IDF vectorized deduplication"""
        try:
            # Extract and clean titles
            titles = [self._clean_title(a.get('title', '')) for a in articles]
            
            # Create TF-IDF matrix
            print(f"        📊 Computing TF-IDF matrix...")
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(titles)
            
            # Calculate cosine similarity matrix
            print(f"        📊 Computing cosine similarity matrix...")
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
                    max_sim = max(similarity_matrix[i, current_group[1:]]) if len(current_group) > 1 else 0
                    print(f"        📝 Found group: {len(current_group)} articles (max similarity: {max_sim:.3f})")
            
            # Build result
            keep_indices = set(range(n)) - duplicate_indices
            for group in duplicate_groups:
                keep_indices.add(group[0])  # Keep first from each group
            
            unique_articles = [articles[i] for i in sorted(keep_indices)]
            similarity_removed = len(articles) - len(unique_articles)
            
            print(f"        ✅ TF-IDF removed {similarity_removed} similar articles")
            
            return unique_articles, {
                'similarity_removed': similarity_removed,
                'duplicate_groups': duplicate_groups
            }
            
        except Exception as e:
            print(f"        ⚠️ TF-IDF failed: {e}, fallback to sequential")
            return self._sequential_deduplication(articles)
    
    def _sequential_deduplication(self, articles: List[Dict]) -> tuple:
        """Phase 2b: Sequential deduplication with optimizations"""
        n = len(articles)
        if n <= 1:
            return articles, {'similarity_removed': 0, 'duplicate_groups': []}
        
        # Pre-process titles
        clean_titles = [self._clean_title(a.get('title', '')) for a in articles]
        
        # Track duplicates
        duplicate_pairs = []
        
        for i in range(n):
            title_i = clean_titles[i]
            
            for j in range(i + 1, n):
                title_j = clean_titles[j]
                
                # Pre-screening
                if abs(len(title_i) - len(title_j)) > max(len(title_i), len(title_j)) * 0.3:
                    continue
                
                similarity = difflib.SequenceMatcher(None, title_i, title_j).ratio()
                if similarity >= self.similarity_threshold:
                    duplicate_pairs.append((i, j, similarity))
        
        # Build result using Union-Find
        return self._build_result_from_pairs(articles, duplicate_pairs)
    
    def _build_result_from_pairs(self, articles: List[Dict], duplicate_pairs: List) -> tuple:
        """Build final result from duplicate pairs"""
        if not duplicate_pairs:
            return articles, {'similarity_removed': 0, 'duplicate_groups': []}
        
        # Union-Find algorithm
        parent = list(range(len(articles)))
        
        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]
        
        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[py] = px
        
        # Group duplicates
        for i, j, _ in duplicate_pairs:
            union(i, j)
        
        # Collect groups
        groups = {}
        for i in range(len(articles)):
            root = find(i)
            if root not in groups:
                groups[root] = []
            groups[root].append(i)
        
        # Filter duplicate groups
        duplicate_groups = [group for group in groups.values() if len(group) > 1]
        duplicate_indices = set()
        for group in duplicate_groups:
            duplicate_indices.update(group[1:])  # Keep first, remove others
        
        unique_articles = [articles[i] for i in range(len(articles)) if i not in duplicate_indices]
        
        return unique_articles, {
            'similarity_removed': len(duplicate_indices),
            'duplicate_groups': duplicate_groups
        }
    
    def _clean_title(self, title: str) -> str:
        """Enhanced title cleaning for better similarity detection"""
        import re
        
        title = title.lower()
        # Remove numbering and common prefixes
        title = re.sub(r'^\d+\.\s*', '', title)
        title = re.sub(r'\s*\[.*?\]$', '', title)
        title = re.sub(r'\s*\(.*?\)$', '', title)
        
        # Normalize punctuation and whitespace
        title = re.sub(r'[^\w\s]', ' ', title)
        title = re.sub(r'\s+', ' ', title).strip()
        
        # Remove very common words
        common_words = {'the', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', '的', '了', '和', '与'}
        words = title.split()
        words = [w for w in words if w not in common_words and len(w) > 1]
        
        return ' '.join(words)


def generate_complex_test_articles(count: int) -> List[Dict]:
    """Generate more complex test data for advanced algorithm testing"""
    
    # More diverse base titles in Chinese and English
    base_titles = [
        "Ethereum Layer 2解决方案获得1000万美元A轮融资",
        "DeFi lending protocol完成2000万美元投资",
        "NFT marketplace项目融资500万美元",
        "区块链基础设施公司获得风险投资",
        "Web3社交媒体平台完成种子轮融资", 
        "加密货币交易所宣布新一轮投资",
        "去中心化存储网络获得战略投资",
        "Cross-chain bridge protocol融资1500万美元",
        "GameFi metaverse项目完成Pre-A轮",
        "Privacy-focused crypto project获得投资",
        "Decentralized identity solution融资",
        "AI + Blockchain startup完成融资",
        "DePIN infrastructure project获投资",
        "Zero-knowledge proof technology融资",
        "Decentralized autonomous organization投资"
    ]
    
    articles = []
    
    # 1. Exact duplicates (5%)
    exact_count = max(1, count // 20)
    for i in range(exact_count):
        title = random.choice(base_titles)
        article = {'title': title, 'content': f'Content {i}', 'id': f'exact_{i}'}
        articles.extend([article, article.copy()])
    
    # 2. High similarity articles (15%)
    high_sim_count = max(1, count // 7)
    for i in range(high_sim_count):
        base = random.choice(base_titles)
        variations = [
            base,
            f"{base}，投资方包括多家知名机构",
            f"最新消息：{base}",
            f"{base}完成新一轮融资",
            f"独家：{base}获得投资",
        ]
        
        # Add 2-3 variations
        selected = random.sample(variations, min(3, len(variations)))
        for j, variation in enumerate(selected):
            articles.append({
                'title': variation, 
                'content': f'High sim content {i}_{j}',
                'id': f'high_sim_{i}_{j}'
            })
    
    # 3. Medium similarity articles (20%)
    med_sim_count = max(1, count // 5)
    for i in range(med_sim_count):
        base = random.choice(base_titles)
        
        # Create medium similarity variations
        if "融资" in base:
            variations = [
                base,
                base.replace("融资", "获得投资"),
                base.replace("融资", "完成融资轮次"),
            ]
        elif "investment" in base.lower():
            variations = [
                base,
                base.replace("investment", "funding round"),
                base.replace("investment", "capital raise"),
            ]
        else:
            variations = [
                base,
                f"{base} raises funds",
                f"{base} completes funding",
            ]
        
        for j, variation in enumerate(variations[:2]):
            articles.append({
                'title': variation,
                'content': f'Med sim content {i}_{j}',
                'id': f'med_sim_{i}_{j}'
            })
    
    # 4. Unique articles for the rest (60%)
    remaining = count - len(articles)
    for i in range(remaining):
        # Create unique variations
        base = random.choice(base_titles)
        unique_title = f"{base} {random.randint(10000, 99999)} {random.choice(['Series A', 'Series B', 'Seed', 'Strategic'])}"
        
        articles.append({
            'title': unique_title,
            'content': f'Unique content {i}',
            'id': f'unique_{i}'
        })
    
    # Shuffle to mix different types
    random.shuffle(articles)
    return articles[:count]


def run_advanced_test():
    """Run comprehensive test of advanced algorithms"""
    
    print("🚀 高级去重算法测试")
    print("=" * 60)
    
    # Initialize services for comparison
    from test_basic_optimization import BasicDeduplicationService, OptimizedBasicDeduplicationService
    
    basic_service = BasicDeduplicationService()
    optimized_basic = OptimizedBasicDeduplicationService()  
    advanced_service = AdvancedDeduplicationService()
    
    test_sizes = [100, 200, 500, 1000, 2000]
    results = {}
    
    for size in test_sizes:
        print(f"\n📊 测试 {size} 篇复杂文章...")
        
        # Generate complex test data
        test_articles = generate_complex_test_articles(size)
        print(f"   生成复杂测试数据: {len(test_articles)} 篇文章")
        
        # Test basic algorithm
        print("   🔄 基础算法测试...")
        start_time = time.time()
        basic_result = basic_service.deduplicate_by_title(test_articles.copy())
        basic_time = time.time() - start_time
        
        # Test optimized basic algorithm  
        print("   ⚡ 优化基础算法测试...")
        start_time = time.time()
        optimized_basic_result = optimized_basic.deduplicate_by_title(test_articles.copy())
        optimized_basic_time = time.time() - start_time
        
        # Test advanced algorithm
        print("   🚀 高级算法测试...")
        start_time = time.time()
        advanced_result, advanced_stats = advanced_service.deduplicate_by_title(test_articles.copy())
        advanced_time = time.time() - start_time
        
        # Calculate metrics
        basic_removed = len(test_articles) - len(basic_result)
        optimized_basic_removed = len(test_articles) - len(optimized_basic_result)
        advanced_removed = advanced_stats['total_removed']
        
        basic_speedup = basic_time / advanced_time if advanced_time > 0 else float('inf')
        optimized_speedup = optimized_basic_time / advanced_time if advanced_time > 0 else float('inf')
        
        result = {
            'size': size,
            'basic_time': basic_time,
            'optimized_basic_time': optimized_basic_time,
            'advanced_time': advanced_time,
            'basic_speedup': basic_speedup,
            'optimized_speedup': optimized_speedup,
            'basic_removed': basic_removed,
            'optimized_basic_removed': optimized_basic_removed,
            'advanced_removed': advanced_removed,
            'advanced_method': advanced_stats['method'],
            'exact_removed': advanced_stats.get('exact_removed', 0),
            'similarity_removed': advanced_stats.get('similarity_removed', 0)
        }
        
        results[size] = result
        
        print(f"   📈 结果对比:")
        print(f"      基础算法:     {basic_time:.3f}s, 删除 {basic_removed} 篇")
        print(f"      优化基础:     {optimized_basic_time:.3f}s, 删除 {optimized_basic_removed} 篇")
        print(f"      高级算法:     {advanced_time:.3f}s, 删除 {advanced_removed} 篇")
        print(f"      vs基础提升:   {basic_speedup:.1f}x")
        print(f"      vs优化提升:   {optimized_speedup:.1f}x") 
        print(f"      使用方法:     {advanced_stats['method']}")
        print(f"      精确去重:     {advanced_stats.get('exact_removed', 0)} 篇")
        print(f"      相似去重:     {advanced_stats.get('similarity_removed', 0)} 篇")
    
    # Print comprehensive summary
    print("\n" + "=" * 60)
    print("📊 高级算法测试总结:")
    
    if results:
        avg_basic_speedup = sum(r['basic_speedup'] for r in results.values()) / len(results)
        avg_optimized_speedup = sum(r['optimized_speedup'] for r in results.values()) / len(results)
        max_basic_speedup = max(r['basic_speedup'] for r in results.values())
        max_optimized_speedup = max(r['optimized_speedup'] for r in results.values())
        
        print(f"   对比基础算法平均提升: {avg_basic_speedup:.1f}x (最高 {max_basic_speedup:.1f}x)")
        print(f"   对比优化基础平均提升: {avg_optimized_speedup:.1f}x (最高 {max_optimized_speedup:.1f}x)")
        
        # Count algorithm usage
        tfidf_count = sum(1 for r in results.values() if 'tfidf' in r['advanced_method'])
        sequential_count = len(results) - tfidf_count
        
        print(f"   TF-IDF向量化使用: {tfidf_count}/{len(results)} 次")
        print(f"   优化序列使用:   {sequential_count}/{len(results)} 次")
        
        print(f"\n   详细性能对比:")
        print(f"   {'文章数':<8} {'基础(s)':<10} {'优化基础(s)':<12} {'高级(s)':<10} {'方法':<18} {'vs基础':<8} {'vs优化':<8}")
        print(f"   {'-'*8} {'-'*10} {'-'*12} {'-'*10} {'-'*18} {'-'*8} {'-'*8}")
        
        for r in results.values():
            method_short = r['advanced_method'].replace('tfidf_vectorized', 'TF-IDF').replace('optimized_sequential', 'Seq-Opt')[:17]
            print(f"   {r['size']:<8} {r['basic_time']:<10.3f} {r['optimized_basic_time']:<12.3f} {r['advanced_time']:<10.3f} {method_short:<18} {r['basic_speedup']:<8.1f}x {r['optimized_speedup']:<8.1f}x")
    
    return results


if __name__ == "__main__":
    try:
        results = run_advanced_test()
        
        # Save results
        import json
        with open('advanced_test_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n🎉 高级算法测试完成!")
        print(f"📄 详细结果已保存到: advanced_test_results.json")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()