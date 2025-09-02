#!/usr/bin/env python3
"""
Test script for deduplication optimization
Tests performance comparison between original and optimized services
"""

import sys
import os
import time
import random
from typing import List, Dict
import json

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from services.deduplication_service import DeduplicationService
from services.optimized_deduplication_service import OptimizedDeduplicationService


class DeduplicationTester:
    """Test suite for deduplication services"""
    
    def __init__(self):
        self.original_service = DeduplicationService()
        self.optimized_service = OptimizedDeduplicationService()
    
    def generate_test_articles(self, count: int) -> List[Dict]:
        """Generate test articles with varying degrees of similarity"""
        
        # Base titles for creating variations
        base_titles = [
            "以太坊 Layer 2 项目融资",
            "DeFi 协议获得投资",  
            "NFT 市场平台融资",
            "区块链基础设施项目",
            "Web3 社交应用融资",
            "加密货币交易所投资",
            "去中心化存储项目",
            "跨链桥接协议融资",
            "GameFi 项目获得资金",
            "隐私保护技术融资"
        ]
        
        articles = []
        
        # Generate exact duplicates (10%)
        exact_duplicate_count = count // 10
        for i in range(exact_duplicate_count):
            base_title = random.choice(base_titles)
            article = {
                'title': base_title,
                'content': f'Content for article {i}',
                'url': f'https://example.com/{i}',
                'published_at': f'2024-01-{i%30+1:02d}'
            }
            articles.append(article)
            # Add exact duplicate
            articles.append(article.copy())
        
        # Generate similar articles (20%) 
        similar_count = count // 5
        for i in range(similar_count):
            base_title = random.choice(base_titles)
            variations = [
                f"{base_title}完成新一轮融资",
                f"{base_title}获得战略投资",
                f"{base_title}宣布融资消息",
                f"最新消息：{base_title}"
            ]
            
            original = {
                'title': base_title,
                'content': f'Content for original {i}',
                'url': f'https://example.com/orig_{i}',
                'published_at': f'2024-02-{i%28+1:02d}'
            }
            
            similar = {
                'title': random.choice(variations),
                'content': f'Content for similar {i}',
                'url': f'https://example.com/sim_{i}',
                'published_at': f'2024-02-{i%28+1:02d}'
            }
            
            articles.extend([original, similar])
        
        # Generate unique articles for the rest
        remaining = count - len(articles)
        for i in range(remaining):
            article = {
                'title': f"{random.choice(base_titles)} {random.randint(1000, 9999)}",
                'content': f'Unique content for article {i}',
                'url': f'https://example.com/unique_{i}',
                'published_at': f'2024-03-{i%31+1:02d}'
            }
            articles.append(article)
        
        # Shuffle to mix different types
        random.shuffle(articles)
        return articles[:count]
    
    def run_performance_test(self, article_counts: List[int]):
        """Run performance comparison tests"""
        
        print("🧪 Starting deduplication performance tests...\n")
        
        results = {}
        
        for count in article_counts:
            print(f"📊 Testing with {count} articles...")
            
            # Generate test data
            test_articles = self.generate_test_articles(count)
            
            # Test original service
            print(f"  🔄 Testing original service...")
            start_time = time.time()
            original_result, original_stats = self.original_service.deduplicate_by_title(
                test_articles.copy(), f"test_{count}"
            )
            original_time = time.time() - start_time
            
            # Test optimized service  
            print(f"  🚀 Testing optimized service...")
            start_time = time.time()
            optimized_result, optimized_stats = self.optimized_service.deduplicate_by_title(
                test_articles.copy(), f"test_{count}"
            )
            optimized_time = time.time() - start_time
            
            # Calculate improvement
            speedup = original_time / optimized_time if optimized_time > 0 else float('inf')
            memory_improvement = 1.0  # Placeholder, would need memory profiling
            
            results[count] = {
                'original': {
                    'time': original_time,
                    'removed_count': original_stats.get('removed_count', 0),
                    'final_count': len(original_result),
                    'removal_rate': original_stats.get('removal_rate', 0)
                },
                'optimized': {
                    'time': optimized_time, 
                    'removed_count': optimized_stats.get('total_removed', optimized_stats.get('exact_removed', 0) + optimized_stats.get('similarity_removed', 0)),
                    'final_count': len(optimized_result),
                    'removal_rate': optimized_stats.get('removal_rate', 0),
                    'method_used': optimized_stats.get('method_used', 'unknown'),
                    'exact_removed': optimized_stats.get('exact_removed', 0),
                    'similarity_removed': optimized_stats.get('similarity_removed', 0)
                },
                'improvement': {
                    'speedup': speedup,
                    'time_saved': original_time - optimized_time,
                    'time_saved_percent': ((original_time - optimized_time) / original_time * 100) if original_time > 0 else 0
                }
            }
            
            print(f"  📈 Results for {count} articles:")
            print(f"     Original: {original_time:.2f}s, removed {original_stats.get('removed_count', 0)} articles")
            print(f"     Optimized: {optimized_time:.2f}s, removed {results[count]['optimized']['removed_count']} articles")
            print(f"     Speedup: {speedup:.1f}x, Time saved: {results[count]['improvement']['time_saved_percent']:.1f}%")
            print(f"     Method: {optimized_stats.get('method_used', 'unknown')}")
            print()
        
        return results
    
    def test_accuracy(self, test_count: int = 100):
        """Test accuracy comparison between services"""
        
        print(f"🎯 Testing deduplication accuracy with {test_count} articles...\n")
        
        test_articles = self.generate_test_articles(test_count)
        
        # Run both services
        original_result, original_stats = self.original_service.deduplicate_by_title(
            test_articles.copy(), "accuracy_test"
        )
        
        optimized_result, optimized_stats = self.optimized_service.deduplicate_by_title(
            test_articles.copy(), "accuracy_test"
        )
        
        # Compare results
        original_titles = set(a['title'] for a in original_result)
        optimized_titles = set(a['title'] for a in optimized_result)
        
        # Calculate accuracy metrics
        common_titles = original_titles.intersection(optimized_titles)
        original_only = original_titles - optimized_titles
        optimized_only = optimized_titles - original_titles
        
        accuracy_score = len(common_titles) / max(len(original_titles), len(optimized_titles)) * 100
        
        print(f"📊 Accuracy Test Results:")
        print(f"   Original service: {len(original_result)} articles")
        print(f"   Optimized service: {len(optimized_result)} articles")
        print(f"   Common articles: {len(common_titles)}")
        print(f"   Original only: {len(original_only)}")
        print(f"   Optimized only: {len(optimized_only)}")
        print(f"   Accuracy score: {accuracy_score:.1f}%")
        
        if original_only:
            print(f"\n   Articles only in original (first 3):")
            for title in list(original_only)[:3]:
                print(f"     - {title}")
        
        if optimized_only:
            print(f"\n   Articles only in optimized (first 3):")
            for title in list(optimized_only)[:3]:
                print(f"     - {title}")
        
        return {
            'accuracy_score': accuracy_score,
            'original_count': len(original_result),
            'optimized_count': len(optimized_result),
            'common_count': len(common_titles),
            'original_only': len(original_only),
            'optimized_only': len(optimized_only)
        }
    
    def test_cache_effectiveness(self):
        """Test cache system effectiveness"""
        
        print("🗄️ Testing cache effectiveness...\n")
        
        # Generate test articles  
        test_articles = self.generate_test_articles(200)
        
        # First run (cold cache)
        print("   First run (cold cache):")
        start_time = time.time()
        result1, stats1 = self.optimized_service.deduplicate_by_title(test_articles.copy(), "cache_test_1")
        first_run_time = time.time() - start_time
        
        # Second run (warm cache)
        print("   Second run (warm cache):")
        start_time = time.time()
        result2, stats2 = self.optimized_service.deduplicate_by_title(test_articles.copy(), "cache_test_2")
        second_run_time = time.time() - start_time
        
        # Calculate cache effectiveness
        cache_speedup = first_run_time / second_run_time if second_run_time > 0 else float('inf')
        time_saved = first_run_time - second_run_time
        
        # Get cache stats
        perf_stats = self.optimized_service.get_performance_stats()
        cache_stats = perf_stats.get('cache_stats', {})
        
        print(f"📈 Cache Test Results:")
        print(f"   First run: {first_run_time:.2f}s")
        print(f"   Second run: {second_run_time:.2f}s")
        print(f"   Cache speedup: {cache_speedup:.1f}x")
        print(f"   Time saved: {time_saved:.2f}s ({time_saved/first_run_time*100:.1f}%)")
        print(f"   Cache entries: {cache_stats.get('total_entries', 'N/A')}")
        print(f"   Avg similarity: {cache_stats.get('avg_similarity', 0):.3f}")
        
        return {
            'first_run_time': first_run_time,
            'second_run_time': second_run_time,
            'cache_speedup': cache_speedup,
            'time_saved': time_saved,
            'cache_stats': cache_stats
        }
    
    def generate_report(self, results: Dict):
        """Generate detailed test report"""
        
        report = {
            'test_summary': {
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'test_counts': list(results['performance'].keys()) if 'performance' in results else [],
                'total_tests': len(results)
            },
            'performance_results': results.get('performance', {}),
            'accuracy_results': results.get('accuracy', {}),
            'cache_results': results.get('cache', {}),
            'service_info': {
                'original_settings': {
                    'similarity_threshold': self.original_service.similarity_threshold
                },
                'optimized_settings': self.optimized_service.get_performance_stats()
            }
        }
        
        return report


def main():
    """Run comprehensive deduplication tests"""
    
    print("🚀 IOSG去重算法优化测试\n")
    print("=" * 50)
    
    tester = DeduplicationTester()
    results = {}
    
    try:
        # Performance tests with different data sizes
        test_counts = [50, 100, 200, 500]
        print(f"Testing with article counts: {test_counts}")
        
        performance_results = tester.run_performance_test(test_counts)
        results['performance'] = performance_results
        
        # Accuracy test
        accuracy_results = tester.test_accuracy(200)
        results['accuracy'] = accuracy_results
        
        # Cache effectiveness test
        cache_results = tester.test_cache_effectiveness()
        results['cache'] = cache_results
        
        # Generate comprehensive report
        report = tester.generate_report(results)
        
        # Save results to file
        os.makedirs('test_results', exist_ok=True)
        with open('test_results/deduplication_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print("=" * 50)
        print("🎉 All tests completed successfully!")
        print("📊 Results saved to: test_results/deduplication_test_results.json")
        
        # Print summary
        print("\n📈 PERFORMANCE SUMMARY:")
        if performance_results:
            best_speedup = max(result['improvement']['speedup'] for result in performance_results.values())
            avg_speedup = sum(result['improvement']['speedup'] for result in performance_results.values()) / len(performance_results)
            print(f"   Best speedup: {best_speedup:.1f}x")
            print(f"   Average speedup: {avg_speedup:.1f}x")
            print(f"   Accuracy: {accuracy_results.get('accuracy_score', 0):.1f}%")
            print(f"   Cache effectiveness: {cache_results.get('cache_speedup', 1):.1f}x")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())