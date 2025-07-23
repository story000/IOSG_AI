#!/usr/bin/env python3  
"""
测试AI批量语义去重功能
"""

import os
from ai_filter import AIFundingFilter

def test_ai_batch_semantic_deduplication():
    """测试AI批量语义去重"""
    
    # 创建测试数据，模拟已经过字符去重的文章
    filtered_results = {
        "project": [
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
            }
        ],
        "exchange_wallet": [
            {
                'title': 'FTX寻求延期回应债权人异议，4.7亿美元海外索赔或被冻结',
                'url': 'https://example4.com',
                'content_text': 'FTX申请延期...'
            },
            {
                'title': 'FTX申请延期回应，因债权人反对冻结4.7亿美元海外债权',
                'url': 'https://example5.com',
                'content_text': 'FTX寻求延期...'
            }
        ],
        "fund": [
            {
                'title': '稳定币支付服务平台鲲KUN完成A轮融资，累计融资总金额已超5000万美元',
                'url': 'https://example6.com',
                'content_text': '鲲KUN宣布完成A轮融资...'
            },
            {
                'title': '稳定币支付服务平台鲲 KUN 完成 A 轮融资，BAI Capital 等参投',
                'url': 'https://example7.com',
                'content_text': '鲲KUN完成A轮融资，BAI Capital参投...'
            }
        ]
    }
    
    print("=== AI批量语义去重测试 ===")
    
    # 统计总文章数
    total_articles = sum(len(articles) for articles in filtered_results.values())
    print(f"测试文章总数: {total_articles}")
    
    # 显示测试数据
    print("\n原始测试数据:")
    for category, articles in filtered_results.items():
        print(f"\n{category}:")
        for i, article in enumerate(articles, 1):
            print(f"  {i}. {article['title']}")
    
    # 创建筛选器（使用DeepSeek）
    filter = AIFundingFilter(provider="deepseek")
    
    if not filter.api_key:
        print("❌ API密钥未配置，无法进行测试")
        return
    
    # 验证配置是否正确加载
    semantic_config = filter.config.get('ai_semantic_deduplication', {})
    print(f"配置加载状态: {'✅ 已加载' if semantic_config else '❌ 未找到配置'}")
    if semantic_config:
        settings = semantic_config.get('settings', {})
        print(f"批处理限制: {settings.get('batch_size_limit', 100)} 篇")
        print(f"最大tokens: {settings.get('max_tokens', 1000)}")
        print(f"温度设置: {settings.get('temperature', 0)}")
    
    # 执行AI批量语义去重
    print(f"\n🤖 执行AI批量语义去重...")
    deduplicated_results, stats = filter.ai_batch_semantic_deduplication(filtered_results)
    
    # 显示结果
    print(f"\n=== 去重结果 ===")
    print(f"删除文章数: {stats['removed_count']}")
    print(f"重复组数: {len(stats['duplicate_groups'])}")
    
    # 统计去重后的文章数
    final_total = sum(len(articles) for articles in deduplicated_results.values())
    print(f"最终文章数: {final_total} (原始: {total_articles})")
    
    print("\n去重后结果:")
    for category, articles in deduplicated_results.items():
        if articles:  # 只显示有文章的分类
            print(f"\n{category}:")
            for i, article in enumerate(articles, 1):
                print(f"  {i}. {article['title']}")
    
    # 验证去重效果
    expected_removals = [
        ("Poseidon融资", 2),  # 应该只保留1篇
        ("FTX债权人", 2),     # 应该只保留1篇  
        ("鲲KUN融资", 2)      # 应该只保留1篇
    ]
    
    print(f"\n=== 去重效果验证 ===")
    if stats['removed_count'] >= 3:  # 应该删除至少3篇重复文章
        print("✅ AI批量语义去重成功识别重复文章")
    else:
        print("⚠️ AI可能未完全识别重复文章")
    
    print(f"删除率: {(stats['removed_count'] / total_articles * 100):.1f}%")

if __name__ == "__main__":
    test_ai_batch_semantic_deduplication()