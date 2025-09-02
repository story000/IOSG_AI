#!/usr/bin/env python3
"""
Basic test for deduplication optimization - standalone version
"""

import time
import difflib
import hashlib
from typing import List, Dict, Set
import random


class BasicDeduplicationService:
    """Original basic deduplication approach"""
    
    def __init__(self, similarity_threshold: float = 0.7):
        self.similarity_threshold = similarity_threshold
    
    def deduplicate_by_title(self, articles: List[Dict]) -> List[Dict]:
        """Original O(n²) deduplication algorithm"""
        if not articles:
            return articles
        
        # Track which articles to keep
        keep_indices = []
        seen_titles = []  # Using list - O(n) lookup
        
        for i, article in enumerate(articles):
            title = article.get('title', '')
            clean_current = self._clean_title(title)
            
            # Check against all previously seen titles - O(n) operation
            is_duplicate = False
            for seen_title in seen_titles:
                similarity = difflib.SequenceMatcher(None, clean_current, seen_title).ratio()
                if similarity >= self.similarity_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                keep_indices.append(i)
                seen_titles.append(clean_current)  # Append to list
        
        return [articles[i] for i in keep_indices]
    
    def _clean_title(self, title: str) -> str:
        """Basic title cleaning"""
        import re
        title = re.sub(r'[^\w\s]', '', title.lower())
        title = re.sub(r'\s+', ' ', title).strip()
        return title


class OptimizedBasicDeduplicationService:
    """Optimized version with hash pre-filtering and set-based lookups"""
    
    def __init__(self, similarity_threshold: float = 0.7):
        self.similarity_threshold = similarity_threshold
    
    def deduplicate_by_title(self, articles: List[Dict]) -> List[Dict]:
        """Optimized deduplication with hash pre-filtering"""
        if not articles:
            return articles
        
        # Phase 1: Remove exact duplicates using hash - O(n)
        exact_unique, hash_stats = self._remove_exact_duplicates(articles)
        
        if len(exact_unique) <= 1:
            return exact_unique
        
        # Phase 2: Similarity-based deduplication with optimizations
        return self._similarity_deduplication(exact_unique)
    
    def _remove_exact_duplicates(self, articles: List[Dict]) -> tuple:
        """Remove exact duplicates using hash comparison"""
        seen_hashes: Set[str] = set()  # Using set - O(1) lookup
        unique_articles = []
        removed_count = 0
        
        for article in articles:
            title = article.get('title', '')
            clean_title = self._clean_title(title)
            title_hash = hashlib.md5(clean_title.encode('utf-8')).hexdigest()
            
            if title_hash not in seen_hashes:  # O(1) lookup
                seen_hashes.add(title_hash)
                unique_articles.append(article)
            else:
                removed_count += 1
        
        return unique_articles, {'removed': removed_count}
    
    def _similarity_deduplication(self, articles: List[Dict]) -> List[Dict]:
        """Optimized similarity-based deduplication"""
        n = len(articles)
        if n <= 1:
            return articles
        
        # Pre-process titles
        clean_titles = [self._clean_title(a.get('title', '')) for a in articles]
        
        # Track which articles to keep
        keep_indices = set(range(n))
        
        for i in range(n):
            if i not in keep_indices:
                continue
                
            title_i = clean_titles[i]
            
            for j in range(i + 1, n):
                if j not in keep_indices:
                    continue
                
                title_j = clean_titles[j]
                
                # Quick pre-screening: skip if length difference is too large
                if abs(len(title_i) - len(title_j)) > max(len(title_i), len(title_j)) * 0.3:
                    continue
                
                similarity = difflib.SequenceMatcher(None, title_i, title_j).ratio()
                if similarity >= self.similarity_threshold:
                    keep_indices.remove(j)  # Remove duplicate
        
        return [articles[i] for i in sorted(keep_indices)]
    
    def _clean_title(self, title: str) -> str:
        """Enhanced title cleaning"""
        import re
        title = title.lower()
        title = re.sub(r'^\d+\.\s*', '', title)  # Remove numbering
        title = re.sub(r'[^\w\s]', ' ', title)   # Replace punctuation with spaces
        title = re.sub(r'\s+', ' ', title).strip()  # Normalize whitespace
        return title


def generate_test_articles(count: int) -> List[Dict]:
    """Generate test articles with known duplicates"""
    
    base_titles = [
        "以太坊Layer 2项目融资1000万美元",
        "DeFi协议获得风险投资",  
        "NFT市场平台完成A轮融资",
        "区块链基础设施项目融资",
        "Web3社交应用获得投资",
        "加密货币交易所融资",
        "去中心化存储项目",
        "跨链桥接协议融资",
        "GameFi项目获得资金",
        "隐私保护技术融资"
    ]
    
    articles = []
    
    # Generate exact duplicates (10% of total)
    exact_count = count // 10
    for i in range(exact_count):
        title = random.choice(base_titles)
        article = {'title': title, 'content': f'Content {i}'}
        articles.extend([article, article.copy()])  # Add duplicate
    
    # Generate similar articles (20% of total)
    similar_count = count // 5
    for i in range(similar_count):
        base = random.choice(base_titles)
        variations = [
            base,
            f"{base}完成新一轮融资",
            f"{base}获得战略投资", 
            f"最新：{base}"
        ]
        for variation in variations[:2]:  # Add 2 similar articles
            articles.append({'title': variation, 'content': f'Content {len(articles)}'})
    
    # Fill remaining with unique articles
    while len(articles) < count:
        title = f"{random.choice(base_titles)} {random.randint(1000, 9999)}"
        articles.append({'title': title, 'content': f'Unique content {len(articles)}'})
    
    return articles[:count]


def run_performance_test():
    """Run performance comparison test"""
    
    print("🚀 去重算法性能测试")
    print("=" * 50)
    
    basic_service = BasicDeduplicationService()
    optimized_service = OptimizedBasicDeduplicationService()
    
    test_sizes = [100, 200, 500, 1000]
    results = []
    
    for size in test_sizes:
        print(f"\n📊 测试 {size} 篇文章...")
        
        # Generate test data
        test_articles = generate_test_articles(size)
        print(f"   生成测试数据: {len(test_articles)} 篇文章")
        
        # Test basic service
        print("   🔄 测试基础算法...")
        start_time = time.time()
        basic_result = basic_service.deduplicate_by_title(test_articles.copy())
        basic_time = time.time() - start_time
        
        # Test optimized service
        print("   🚀 测试优化算法...")
        start_time = time.time()
        optimized_result = optimized_service.deduplicate_by_title(test_articles.copy())
        optimized_time = time.time() - start_time
        
        # Calculate metrics
        speedup = basic_time / optimized_time if optimized_time > 0 else float('inf')
        basic_removed = len(test_articles) - len(basic_result)
        optimized_removed = len(test_articles) - len(optimized_result)
        
        result = {
            'size': size,
            'basic_time': basic_time,
            'optimized_time': optimized_time,
            'speedup': speedup,
            'basic_removed': basic_removed,
            'optimized_removed': optimized_removed,
            'basic_final': len(basic_result),
            'optimized_final': len(optimized_result)
        }
        results.append(result)
        
        print(f"   📈 结果:")
        print(f"      基础算法: {basic_time:.3f}s, 删除 {basic_removed} 篇")
        print(f"      优化算法: {optimized_time:.3f}s, 删除 {optimized_removed} 篇") 
        print(f"      性能提升: {speedup:.1f}x")
        print(f"      时间节省: {((basic_time - optimized_time) / basic_time * 100):.1f}%")
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 测试总结:")
    
    avg_speedup = sum(r['speedup'] for r in results) / len(results)
    max_speedup = max(r['speedup'] for r in results)
    
    print(f"   平均性能提升: {avg_speedup:.1f}x")
    print(f"   最高性能提升: {max_speedup:.1f}x")
    
    print(f"\n   详细结果:")
    print(f"   {'文章数':<8} {'基础(s)':<10} {'优化(s)':<10} {'提升':<8} {'准确性':<8}")
    print(f"   {'-'*8} {'-'*10} {'-'*10} {'-'*8} {'-'*8}")
    
    for r in results:
        accuracy = "✅" if abs(r['basic_removed'] - r['optimized_removed']) <= 2 else "⚠️"
        print(f"   {r['size']:<8} {r['basic_time']:<10.3f} {r['optimized_time']:<10.3f} {r['speedup']:<8.1f}x {accuracy:<8}")
    
    return results


if __name__ == "__main__":
    try:
        results = run_performance_test()
        print(f"\n🎉 测试完成!")
        
        # Save basic results
        import json
        with open('basic_test_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        print(f"📄 结果已保存到: basic_test_results.json")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()