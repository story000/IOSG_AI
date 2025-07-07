#!/usr/bin/env python3
"""
提取项目融资类文章
只关注项目融资分类，其他暂不处理
"""

import json
import re
from datetime import datetime
import requests
import time

class AIVerifier:
    def __init__(self):
        # 这里可以配置不同的AI API
        self.api_providers = {
            'openai': {
                'url': 'https://api.openai.com/v1/chat/completions',
                'headers': {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer YOUR_OPENAI_API_KEY'
                }
            },
            'anthropic': {
                'url': 'https://api.anthropic.com/v1/messages',
                'headers': {
                    'Content-Type': 'application/json',
                    'x-api-key': 'YOUR_ANTHROPIC_API_KEY'
                }
            }
        }
        
        # 验证提示词
        self.verification_prompt = """
请分析以下新闻内容，判断是否为真实的加密货币/区块链项目融资新闻。

评判标准：
1. 是否明确提到具体的加密货币/区块链/Web3项目名称
2. 是否明确提到获得投资/融资的金额
3. 是否提到具体的投资机构或投资者
4. 内容是否为真实的项目融资，而非：
   - 基金募资
   - 交易所业务
   - 个人投资
   - 并购收购
   - 其他非项目融资

请回答：
- 结论：是/否
- 置信度：0-100%
- 项目名称：[如果是，提取项目名]
- 融资金额：[如果有，提取金额]
- 投资方：[如果有，提取主要投资方]
- 理由：[简要说明判断理由]

新闻内容：
{content}
"""
    
    def verify_with_ai(self, article, provider='local'):
        """使用AI验证文章是否为真实项目融资"""
        if provider == 'local':
            return self.local_verification(article)
        else:
            return self.api_verification(article, provider)
    
    def local_verification(self, article):
        """本地规则验证（不调用外部AI API）"""
        title = article.get('title', '')
        content = article.get('content_text', '')
        combined = f"{title} {content}"
        
        # 初始化结果
        result = {
            'is_real_funding': False,
            'confidence': 0,
            'project_name': '',
            'funding_amount': '',
            'investors': '',
            'reason': '',
            'verification_method': 'local_rules'
        }
        
        # 排除规则（这些不是项目融资）
        exclude_keywords = [
            '基金', '资管', '交易所', '平台', '钱包', '银行', '金融机构',
            '上市公司', '传统企业', '政府', '监管', '合规', '牌照',
            '并购', '收购', '重组', 'IPO', '上市', '股票', '股份'
        ]
        
        # 检查排除关键词
        exclude_score = 0
        for keyword in exclude_keywords:
            if keyword in combined:
                exclude_score += 1
        
        if exclude_score >= 3:
            result['reason'] = f'包含{exclude_score}个排除关键词，可能不是项目融资'
            result['confidence'] = max(0, 20 - exclude_score * 5)
            return result
        
        # 项目类型关键词
        project_keywords = [
            'DeFi', 'NFT', 'GameFi', 'Web3', '区块链', '加密', 'crypto',
            '协议', 'protocol', '平台', 'platform', '项目', 'project',
            '应用', 'dApp', '智能合约', 'smart contract', '去中心化',
            'decentralized', '代币', 'token', '公链', 'blockchain'
        ]
        
        # 融资确认关键词
        funding_confirm_keywords = [
            '完成', '获得', '宣布', '筹集', '融资', 'raised', 'funding',
            '投资', 'investment', '轮', 'round', 'Series'
        ]
        
        # 金额模式
        amount_patterns = [
            r'\d+万美元', r'\d+千万美元', r'\d+亿美元',
            r'\$\d+[KMB]', r'\$\d+\s*(million|billion)',
            r'\d+\.?\d*\s*(万|千万|亿).*?(美元|美金|USD)'
        ]
        
        # 计算各项得分
        project_score = sum(1 for k in project_keywords if k.lower() in combined.lower())
        funding_score = sum(1 for k in funding_confirm_keywords if k.lower() in combined.lower())
        
        # 检查金额
        amount_found = False
        funding_amount = ''
        for pattern in amount_patterns:
            matches = re.findall(pattern, combined, re.IGNORECASE)
            if matches:
                amount_found = True
                funding_amount = matches[0] if isinstance(matches[0], str) else str(matches[0])
                break
        
        # 提取可能的项目名称（简单规则）
        project_name = ''
        # 查找标题中的英文大写词组或中文项目名
        title_words = re.findall(r'[A-Z][a-zA-Z]+|[\u4e00-\u9fff]+(?:协议|平台|项目|网络)', title)
        if title_words:
            project_name = title_words[0]
        
        # 提取投资方（简单规则）
        investors = ''
        investor_patterns = [
            r'([\u4e00-\u9fff]+资本)', r'([\u4e00-\u9fff]+基金)', 
            r'([A-Z][a-zA-Z\s]+Capital)', r'([A-Z][a-zA-Z\s]+Ventures)'
        ]
        for pattern in investor_patterns:
            matches = re.findall(pattern, combined)
            if matches:
                investors = ', '.join(matches[:3])  # 最多显示3个
                break
        
        # 综合评分
        total_score = project_score + funding_score * 2 + (3 if amount_found else 0)
        confidence = min(100, total_score * 8)  # 最高100%
        
        is_real = total_score >= 4 and amount_found and funding_score >= 1
        
        result.update({
            'is_real_funding': is_real,
            'confidence': confidence,
            'project_name': project_name,
            'funding_amount': funding_amount,
            'investors': investors,
            'reason': f'项目词{project_score}个，融资词{funding_score}个，{"有" if amount_found else "无"}金额'
        })
        
        return result
    
    def api_verification(self, article, provider):
        """调用外部AI API验证（可选）"""
        # 这里可以实现调用OpenAI、Claude等API的逻辑
        # 由于需要API密钥，这里只提供框架
        
        return {
            'is_real_funding': True,
            'confidence': 85,
            'project_name': 'Unknown',
            'funding_amount': 'Unknown',
            'investors': 'Unknown',
            'reason': 'API verification not implemented',
            'verification_method': f'{provider}_api'
        }

class FundingArticleExtractor:
    def __init__(self):
        # 项目融资相关的关键词和模式
        self.funding_keywords = [
            "A轮", "B轮", "C轮", "种子轮", "天使轮", "pre-seed", "seed",
            "Series A", "Series B", "Series C", "领投", "跟投", "估值", "风投", "VC",
            "融得", "筹集", "筹到", "募资", "募得", "轮融资", "投资方",
            "投资机构", "战略投资", "pre-A", "A+轮", "B+轮", "oversubscribed",
            "funding", "investment", "investor", "venture", "capital", "round"
        ]
        
        # 精确的融资模式（避免误匹配）
        self.funding_patterns = [
            r"完成.*?融资",
            r"获得.*?融资", 
            r"宣布.*?融资",
            r"融资.*?万美元",
            r"融资.*?千万美元", 
            r"融资.*?亿美元",
            r"获投.*?万美元",
            r"获投.*?千万美元",
            r"获投.*?亿美元",
            r"筹集.*?万美元",
            r"筹集.*?千万美元",
            r"筹集.*?亿美元",
            r"raised.*?\$.*?million",
            r"raised.*?\$.*?billion",
            r"funding.*?\$.*?million",
            r"funding.*?\$.*?billion",
            r"投资.*?万美元",
            r"投资.*?千万美元",
            r"投资.*?亿美元",
            r"完成.*?万美元.*?融资",
            r"完成.*?千万美元.*?融资",
            r"完成.*?亿美元.*?融资"
        ]
    
    def preprocess_text(self, text):
        """预处理文本"""
        if not text:
            return ""
        # 保留中文、英文、数字和基本标点
        text = re.sub(r'[^\u4e00-\u9fff\w\s\.\,\!\?\-\+\%\$]', ' ', text)
        return text.lower()
    
    def calculate_funding_score(self, text):
        """计算融资相关得分"""
        text = self.preprocess_text(text)
        score = 0
        matched_items = []
        
        # 计算关键词匹配分数
        for keyword in self.funding_keywords:
            keyword_lower = keyword.lower()
            # 计算关键词出现次数
            count = len(re.findall(r'\b' + re.escape(keyword_lower) + r'\b', text))
            if count == 0:
                # 对于中文关键词，使用简单的包含匹配
                count = text.count(keyword_lower)
            if count > 0:
                score += count
                matched_items.append(f"关键词:{keyword}({count}次)")
        
        # 计算模式匹配分数（权重更高）
        for pattern in self.funding_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                pattern_score = len(matches) * 3  # 模式匹配给予3倍权重
                score += pattern_score
                matched_items.append(f"模式:{pattern}({len(matches)}次)")
        
        return score, matched_items
    
    def is_funding_article(self, article, min_score=2):
        """判断是否为融资文章"""
        # 合并标题和内容文本
        title = article.get('title', '')
        content = article.get('content_text', '')
        combined_text = f"{title} {content}"
        
        score, matched_items = self.calculate_funding_score(combined_text)
        
        return score >= min_score, score, matched_items
    
    def extract_funding_articles(self, articles, use_ai_verification=True):
        """提取所有融资文章"""
        funding_articles = []
        ai_verifier = AIVerifier() if use_ai_verification else None
        
        print(f"开始筛选融资文章，共 {len(articles)} 篇文章...")
        if use_ai_verification:
            print("🤖 已启用AI验证模块")
        
        for i, article in enumerate(articles, 1):
            if i % 100 == 0:
                print(f"已处理 {i}/{len(articles)} 篇文章")
            
            is_funding, score, matched_items = self.is_funding_article(article)
            
            if is_funding:
                # 添加融资分析信息
                article_with_funding = article.copy()
                article_with_funding.update({
                    'funding_score': score,
                    'funding_matches': matched_items,
                    'is_funding_article': True
                })
                
                # AI验证
                if use_ai_verification:
                    ai_result = ai_verifier.verify_with_ai(article)
                    article_with_funding.update({
                        'ai_verification': ai_result,
                        'ai_is_real_funding': ai_result['is_real_funding'],
                        'ai_confidence': ai_result['confidence'],
                        'ai_project_name': ai_result['project_name'],
                        'ai_funding_amount': ai_result['funding_amount'],
                        'ai_investors': ai_result['investors']
                    })
                    
                    # 只保留AI确认的真实融资文章
                    if ai_result['is_real_funding'] and ai_result['confidence'] >= 60:
                        funding_articles.append(article_with_funding)
                    elif i <= 10:  # 前10篇显示详情用于调试
                        print(f"  ❌ AI拒绝: {article['title'][:50]}... (置信度:{ai_result['confidence']}%)")
                else:
                    funding_articles.append(article_with_funding)
        
        return funding_articles

def main():
    # 读取JSON文件
    input_file = "crypto_feeds_unread_20250706_165100.json"
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ 文件 {input_file} 不存在")
        return
    except json.JSONDecodeError:
        print(f"❌ 文件 {input_file} 格式错误")
        return
    
    articles = data.get('articles', [])
    metadata = data.get('metadata', {})
    
    print(f"=== 项目融资文章提取器 ===")
    print(f"输入文件: {input_file}")
    print(f"文章总数: {len(articles)}")
    print(f"来源统计: {metadata.get('feeds_stats', {})}")
    
    # 创建提取器并筛选融资文章
    extractor = FundingArticleExtractor()
    
    # 询问是否使用AI验证
    use_ai = input("\n是否启用AI验证模块？(y/n，默认y): ").strip().lower()
    use_ai_verification = use_ai != 'n'
    
    funding_articles = extractor.extract_funding_articles(articles, use_ai_verification)
    
    print(f"\n=== 筛选结果 ===")
    print(f"📊 找到融资文章: {len(funding_articles)} 篇")
    print(f"📊 占总数比例: {len(funding_articles)/len(articles)*100:.1f}%")
    
    if not funding_articles:
        print("❌ 未找到符合条件的融资文章")
        return
    
    # 按得分排序
    funding_articles.sort(key=lambda x: x['funding_score'], reverse=True)
    
    # 显示得分最高的前10篇
    print(f"\n=== 融资文章预览（按得分排序，前10篇） ===")
    for i, article in enumerate(funding_articles[:10], 1):
        title = article['title']
        source = article['source_feed']
        score = article['funding_score']
        matches = article['funding_matches']
        
        print(f"\n{i:2d}. 【{source}】{title}")
        print(f"    关键词得分: {score}")
        print(f"    匹配内容: {', '.join(matches[:2])}{'...' if len(matches) > 2 else ''}")
        
        # 显示AI验证结果
        if 'ai_verification' in article:
            ai_info = article['ai_verification']
            print(f"    🤖 AI验证: {'✅通过' if ai_info['is_real_funding'] else '❌拒绝'} (置信度:{ai_info['confidence']}%)")
            if ai_info['project_name']:
                print(f"    📋 项目名称: {ai_info['project_name']}")
            if ai_info['funding_amount']:
                print(f"    💰 融资金额: {ai_info['funding_amount']}")
            if ai_info['investors']:
                print(f"    🏢 投资方: {ai_info['investors']}")
            print(f"    💭 AI分析: {ai_info['reason']}")
        
        print(f"    🔗 链接: {article['url']}")
    
    # 按来源统计
    source_stats = {}
    for article in funding_articles:
        source = article['source_feed']
        source_stats[source] = source_stats.get(source, 0) + 1
    
    print(f"\n=== 各来源融资文章统计 ===")
    for source, count in sorted(source_stats.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(funding_articles)) * 100
        print(f"📰 {source}: {count} 篇 ({percentage:.1f}%)")
    
    # 保存融资文章
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"funding_articles_{timestamp}.json"
    
    output_data = {
        'metadata': {
            **metadata,
            'extraction_date': datetime.now().isoformat(),
            'total_articles': len(articles),
            'funding_articles_count': len(funding_articles),
            'funding_percentage': len(funding_articles)/len(articles)*100,
            'source_stats': source_stats,
            'extraction_criteria': {
                'min_score': 2,
                'keywords_count': len(extractor.funding_keywords),
                'patterns_count': len(extractor.funding_patterns)
            }
        },
        'funding_articles': funding_articles
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 融资文章已保存到: {output_file}")
    
    # 生成简化的融资报告
    report_file = f"funding_report_{timestamp}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=== 项目融资文章报告 ===\n\n")
        f.write(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"文章总数: {len(articles)}\n")
        f.write(f"融资文章: {len(funding_articles)} 篇 ({len(funding_articles)/len(articles)*100:.1f}%)\n\n")
        
        f.write("各来源统计:\n")
        for source, count in sorted(source_stats.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(funding_articles)) * 100
            f.write(f"  {source}: {count} 篇 ({percentage:.1f}%)\n")
        
        f.write(f"\n热门融资文章（前20篇）:\n")
        for i, article in enumerate(funding_articles[:20], 1):
            f.write(f"  {i:2d}. [{article['source_feed']}] {article['title']} (得分:{article['funding_score']})\n")
            if 'ai_verification' in article:
                ai_info = article['ai_verification']
                f.write(f"      AI验证: {'通过' if ai_info['is_real_funding'] else '拒绝'} ({ai_info['confidence']}%)\n")
                if ai_info['project_name']:
                    f.write(f"      项目: {ai_info['project_name']}\n")
                if ai_info['funding_amount']:
                    f.write(f"      金额: {ai_info['funding_amount']}\n")
            f.write(f"      链接: {article['url']}\n")
    
    print(f"📄 融资报告已保存到: {report_file}")
    print(f"\n🎯 提取完成！找到 {len(funding_articles)} 篇融资相关文章")

if __name__ == "__main__":
    main()