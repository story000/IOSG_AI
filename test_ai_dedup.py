#!/usr/bin/env python3
"""
测试AI语义去重功能
"""

import os
from ai_filter import AIFundingFilter

def test_ai_semantic_deduplication():
    """测试AI语义去重"""
    
    # 创建测试数据
    test_articles = [
        {
            'title': 'AI 去中心化数据层项目 Poseidon 完成 1500 万美元种子轮融资，a16z 领投',
            'url': 'https://example1.com',
            'content_text': 'AI去中心化数据层项目Poseidon完成1500万美元种子轮融资...'
        },
        {
            'title': 'a16z领投Poseidon 1500万美元种子轮，推动AI去中心化数据层发展',
            'url': 'https://example2.com', 
            'content_text': 'a16z领投Poseidon完成1500万美元种子轮融资...'
        },
        {
            'title': 'AI代理平台Questflow完成650万美元种子轮融资，CyberFund领投',
            'url': 'https://example3.com',
            'content_text': 'AI代理平台Questflow宣布完成650万美元种子轮融资...'
        },
        {
            'title': 'AI驱动的治理协议Quack AI完成360万美元融资，Animoca Brands等参投',
            'url': 'https://example4.com',
            'content_text': 'AI驱动的治理协议Quack AI宣布完成360万美元融资...'
        }
    ]
    
    print("=== AI语义去重测试 ===")
    print(f"测试文章数量: {len(test_articles)}")
    
    # 创建筛选器（使用DeepSeek）
    filter = AIFundingFilter(provider="deepseek")
    
    if not filter.api_key:
        print("❌ API密钥未配置，无法进行测试")
        return
    
    print("\n测试文章:")
    for i, article in enumerate(test_articles, 1):
        print(f"{i}. {article['title']}")
    
    print("\n=== 使用AI语义去重 ===")
    # 测试AI语义去重
    ai_deduplicated, ai_stats = filter.deduplicate_articles_by_title(
        test_articles, "测试类别", use_ai=True
    )
    
    print(f"\nAI语义去重结果:")
    print(f"原始: {len(test_articles)} 篇")
    print(f"去重后: {len(ai_deduplicated)} 篇")
    print(f"删除: {ai_stats['removed_count']} 篇")
    print(f"AI比较次数: {ai_stats['ai_comparisons']} 次")
    
    print("\n保留的文章:")
    for i, article in enumerate(ai_deduplicated, 1):
        print(f"{i}. {article['title']}")
    
    print("\n=== 使用字符相似度去重 ===")
    # 测试字符相似度去重（对比）
    char_deduplicated, char_stats = filter.deduplicate_articles_by_title(
        test_articles, "测试类别", use_ai=False
    )
    
    print(f"\n字符相似度去重结果:")
    print(f"原始: {len(test_articles)} 篇")
    print(f"去重后: {len(char_deduplicated)} 篇")
    print(f"删除: {char_stats['removed_count']} 篇")
    
    print("\n保留的文章:")
    for i, article in enumerate(char_deduplicated, 1):
        print(f"{i}. {article['title']}")
    
    print("\n=== 对比结果 ===")
    print(f"AI语义去重删除了 {ai_stats['removed_count']} 篇文章")
    print(f"字符相似度去重删除了 {char_stats['removed_count']} 篇文章")
    
    if ai_stats['removed_count'] != char_stats['removed_count']:
        print("✨ AI语义去重与字符相似度去重结果不同，展现了AI的优势")
    else:
        print("📊 两种方法结果相同")

if __name__ == "__main__":
    test_ai_semantic_deduplication()