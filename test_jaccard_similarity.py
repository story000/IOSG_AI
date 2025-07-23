#!/usr/bin/env python3
"""
测试 Jaccard 相似度计算效果
"""

import jieba
import re
import difflib

def clean_title_for_comparison(title):
    """清理标题用于相似度比较"""
    title = re.sub(r'\s+', ' ', title).strip()
    title = re.sub(r'^\d+\.\s*', '', title)
    title = re.sub(r'.*?消息[，,]\s*', '', title)
    title = re.sub(r'.*?报道[，,]\s*', '', title)
    title = re.sub(r'深潮\s*TechFlow\s*[消息报道]*[，,]\s*', '', title)
    title = re.sub(r'PANews\s*\d+月\d+日消息[，,]\s*', '', title)
    title = re.sub(r'Wu\s*Blockchain\s*[消息报道]*[，,]\s*', '', title)
    return title.lower()

def jaccard_similarity(title1, title2):
    """使用 Jaccard 相似度计算"""
    clean_title1 = clean_title_for_comparison(title1)
    clean_title2 = clean_title_for_comparison(title2)
    
    # 使用jieba进行中文分词
    words1 = set(jieba.cut(clean_title1))
    words2 = set(jieba.cut(clean_title2))
    
    # 过滤掉长度小于2的词和常见停用词
    stop_words = {'的', '了', '在', '是', '与', '和', '或', '及', '等', '将', '已', '为', '从', '于', '对', 'by', 'of', 'the', 'a', 'an', 'and', 'or'}
    words1 = {word for word in words1 if len(word) >= 2 and word not in stop_words}
    words2 = {word for word in words2 if len(word) >= 2 and word not in stop_words}
    
    # 计算 Jaccard 相似度
    if not words1 and not words2:
        return 1.0
    if not words1 or not words2:
        return 0.0
        
    intersection = words1 & words2
    union = words1 | words2
    
    jaccard_sim = len(intersection) / len(union)
    
    # 如果有关键金额数字匹配，提高相似度
    amount_pattern = r'(\d+(?:\.\d+)?)\s*(?:万|千万|亿|million|billion)'
    amounts1 = set(re.findall(amount_pattern, clean_title1))
    amounts2 = set(re.findall(amount_pattern, clean_title2))
    
    if amounts1 & amounts2:
        jaccard_sim = min(1.0, jaccard_sim + 0.2)
    
    print(f"  分词结果1: {words1}")
    print(f"  分词结果2: {words2}")
    print(f"  交集: {intersection}")
    print(f"  并集: {union}")
    if amounts1 & amounts2:
        print(f"  匹配金额: {amounts1 & amounts2}")
    
    return jaccard_sim

def char_similarity(title1, title2):
    """字符序列相似度（原方法）"""
    clean_title1 = clean_title_for_comparison(title1)
    clean_title2 = clean_title_for_comparison(title2)
    return difflib.SequenceMatcher(None, clean_title1, clean_title2).ratio()

def test_similarity_methods():
    """测试不同相似度方法"""
    
    # 测试用例
    test_cases = [
        # 完全相同
        ("币安将支持Shentu（CTK）网络升级及硬分叉", "币安将支持Shentu（CTK）网络升级及硬分叉"),
        
        # 高度相似（不同表述）
        ("Bittensor生态公司xTAO将在加拿大上市，从DCG等机构筹集2280万美元", 
         "Bittensor生态公司xTAO将在加拿大上市，获DCG等2280万美元投资"),
        
        # 词序不同
        ("AI代理平台Questflow完成650万美元种子轮融资，CyberFund领投", 
         "链上AI智能体编排层完成650万美元种子轮融资，CyberFund领投"),
        
        # 中英文混合
        ("去中心化消息协议 XMTP 完成 2000 万美元 B 轮融资，a16z 等领投", 
         "去中心化消息传递协议XMTP完成2000万美元B轮融资，a16z crypto等领投"),
        
        # 相同公司不同事件
        ("币安将支持Kadena（KDA）网络升级及硬分叉", 
         "币安理财、一键买币、闪兑、杠杆上线Chainbase（C）"),
        
        # 完全不同
        ("以太坊推出The Torch NFT纪念其成立十周年", 
         "Web3梦幻足球游戏Football.Fun完成200万美元融资")
    ]
    
    print("=== Jaccard 相似度 vs 字符相似度测试 ===\n")
    
    for i, (title1, title2) in enumerate(test_cases, 1):
        print(f"测试用例 {i}:")
        print(f"标题1: {title1}")
        print(f"标题2: {title2}")
        
        # Jaccard 相似度
        jaccard_sim = jaccard_similarity(title1, title2)
        
        # 字符相似度
        char_sim = char_similarity(title1, title2)
        
        print(f"  Jaccard 相似度: {jaccard_sim:.3f}")
        print(f"  字符相似度: {char_sim:.3f}")
        
        # 判断结果（阈值70%）
        jaccard_match = jaccard_sim >= 0.7
        char_match = char_sim >= 0.7
        
        print(f"  Jaccard 判断: {'✅ 重复' if jaccard_match else '❌ 不重复'}")
        print(f"  字符判断: {'✅ 重复' if char_match else '❌ 不重复'}")
        print("-" * 80)

if __name__ == "__main__":
    test_similarity_methods()