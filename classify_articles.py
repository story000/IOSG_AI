#!/usr/bin/env python3
"""
加密货币文章分类器
根据关键词对文章进行分类
"""

import json
import re
from datetime import datetime
from collections import defaultdict

class CryptoArticleClassifier:
    def __init__(self):
        # 定义分类和对应的关键词和模式
        self.portfolios = [
            "Autonomys", "Avalanche", "Celestia", "Conflux", "Cosmos", "Dfinity", "IoTex", 
            "Marlin", "Mina", "Near", "Oasis Labs", "Phala", "Polkadot", "Monad", "0x", 
            "Morpho", "Brink", "Centrifuge", "ChainSafe", "DeBank", "dHEDGE", "DODO", 
            "Bluefin", "Impossible Finance", "Kyber", "MakerDAO", "Mangata", "MCDEX", 
            "Metapool", "Orderly Network", "prePO", "Solv", "SynFutures", "Synthetix", 
            "Transak", "UMA", "Volmex Finance", "Wootrade", "Arbitrum", "Aurora", "Aztec", 
            "BOB", "Celer", "Connext", "Debridge", "Fhenix", "Moonbeam", "NIL", "Scroll", 
            "Starkware", "Taiko", "zkSync", "Optimism", "Polygon", "Atherscope", "AltLayer", 
            "Arweave", "Automata", "Babylon", "Blocknative", "CARV", "ConsenSys", "Covalent", 
            "Dappback", "EigenLayer", "Filecoin", "Flashbots", "Gelato", "Infura", "Ingonyama", 
            "Kiln", "Kyve", "Liquifi", "Lisk", "Lurk Labs", "Plasm", "Astar Network", 
            "Primev", "Renzo", "Redstone", "REDPILL", "Space and Time", "zCloak network", 
            "Swell", "3rm", "WeaveDB", "Ancient8", "Artifact", "Mixmob", "Big Time", 
            "Blade DAO", "NOR", "Gomble Games", "Illuvium", "Playmint", "Polemos", 
            "Shrapnel", "The Beacon", "Kettle", "Alethea AI", "CyberConnect", "ETHSign", 
            "GALXE", "Mintbase", "Mintgate", "PIANITY", "RMRK", "Roll", "Ardrive", "Coin98", 
            "Kravata", "Push", "Safe", "Mask Network", "MetaMask", "Onekey", "DAOhaus", 
            "DAOSquare", "DeFi Alliance", "Gitcoin", "LearnWeb3", "MetaCartel", 
            "Permanent Ventures", "Seed Club", "Arkhivist", "Audit Wizard", "Hats", 
            "Runtime Verification"
        ]

        self.categories = {
            "项目融资": {
                "keywords": [
                    "A轮", "B轮", "C轮", "种子轮", "天使轮", "pre-seed", "seed",
                    "Series A", "Series B", "Series C", "领投", "跟投", "估值", "风投", "VC",
                    "融得", "筹集", "筹到", "募资", "募得", "轮融资", "投资方",
                    "投资机构", "战略投资", "pre-A", "A+轮", "B+轮", "oversubscribed",
                    "funding", "investment", "investor", "venture", "capital", "round"
                ],
                "patterns": [
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
                    r"投资.*?亿美元"
                ],
                "weight": 1.0
            },
            "基金融资": {
                "keywords": [
                    "基金", "fund", "资管", "LP", "管理规模", "AUM", "募集基金", "基金管理",
                    "投资基金", "crypto fund", "区块链基金", "数字资产基金", "风险投资基金",
                    "hedge fund", "对冲基金", "私募基金", "公募基金", "基金规模", "基金成立",
                    "基金启动", "基金募资", "资产管理", "investment fund", "venture fund",
                    "新基金", "基金公司", "资管公司", "基金合伙人", "GP", "有限合伙人"
                ],
                "patterns": [
                    r"设立.*?基金",
                    r"成立.*?基金",
                    r"推出.*?基金",
                    r"启动.*?基金",
                    r"基金.*?万美元",
                    r"基金.*?千万美元",
                    r"基金.*?亿美元",
                    r"fund.*?\$.*?million",
                    r"fund.*?\$.*?billion"
                ],
                "weight": 1.0
            },
            "基础设施/项目主网上线": {
                "keywords": [
                    "主网", "mainnet", "测试网", "testnet", "网络升级", "硬分叉", "软分叉", 
                    "fork", "upgrade", "protocol", "协议", "区块链网络", "公链", "侧链", 
                    "Layer 1", "Layer 2", "L1", "L2", "zkEVM", "Rollup", "bridging", 
                    "跨链", "互操作", "interoperability", "节点", "node", "验证者", "validator", 
                    "共识", "consensus", "PoS", "PoW", "DPoS", "分片", "sharding", "扩容", 
                    "scaling", "TPS", "吞吐量", "网络性能"
                ],
                "patterns": [
                    r"主网.*?上线",
                    r"主网.*?启动", 
                    r"mainnet.*?launch",
                    r"测试网.*?上线",
                    r"testnet.*?launch",
                    r"正式.*?上线",
                    r"宣布.*?上线",
                    r"成功.*?上线"
                ],
                "weight": 1.0
            },
            "DeFi/RWA": {
                "keywords": [
                    "DeFi", "去中心化金融", "decentralized finance", "流动性", "liquidity",
                    "AMM", "自动做市商", "yield farming", "流动性挖矿", "质押", "staking",
                    "借贷", "lending", "borrowing", "抵押", "collateral", "TVL", "锁仓量",
                    "DEX", "去中心化交易所", "swap", "兑换", "收益率", "APY", "APR",
                    "RWA", "现实世界资产", "real world assets", "代币化", "tokenization",
                    "资产代币化", "债券代币化", "房地产代币化", "商品代币化", "稳定币",
                    "stablecoin", "USDT", "USDC", "DAI", "algorithmic stablecoin"
                ],
                "patterns": [],
                "weight": 1.0
            },
            "NFT/GameFi/Metaverse": {
                "keywords": [
                    "NFT", "non-fungible token", "数字藏品", "数字收藏品", "艺术品", "头像",
                    "PFP", "profile picture", "OpenSea", "marketplace", "铸造", "mint",
                    "GameFi", "区块链游戏", "P2E", "play to earn", "边玩边赚", "游戏代币",
                    "游戏NFT", "游戏道具", "虚拟土地", "land", "sandbox", "decentraland",
                    "Metaverse", "元宇宙", "虚拟世界", "virtual world", "VR", "AR",
                    "虚拟现实", "增强现实", "数字身份", "avatar", "虚拟人", "数字人",
                    "社交代币", "social token", "创作者经济", "creator economy"
                ],
                "patterns": [],
                "weight": 1.0
            },
            "交易所/钱包": {
                "keywords": [
                    "交易所", "exchange", "CEX", "中心化交易所", "币安", "Binance", "OKX",
                    "Coinbase", "Kraken", "Bybit", "Gate", "Huobi", "FTX", "KuCoin",
                    "上币", "listing", "下架", "delisting", "充值", "提现", "deposit", "withdraw",
                    "钱包", "wallet", "metamask", "trust wallet", "冷钱包", "热钱包",
                    "硬件钱包", "software wallet", "私钥", "private key", "助记词", "seed phrase",
                    "多签", "multisig", "custody", "托管", "KYC", "实名认证", "监管合规",
                    "牌照", "license", "合规", "compliance", "反洗钱", "AML",
                    "爆仓", "liquidation", "合约", "futures", "期货", "杠杆", "leverage",
                    "多单", "空单", "long", "short", "保证金", "margin", "强平", "强制平仓"
                ],
                "patterns": [],
                "weight": 1.0
            },
            "portfolios": {
                "keywords": [],  # 由portfolio检测逻辑单独处理
                "patterns": [],
                "weight": 0.0
            },
            "其他": {
                "keywords": [],  # 兜底分类，无特定关键词
                "patterns": [],
                "weight": 0.0
            }
        }
    
    def preprocess_text(self, text):
        """预处理文本：转换为小写，移除特殊字符"""
        if not text:
            return ""
        # 保留中文、英文、数字和基本标点
        text = re.sub(r'[^\u4e00-\u9fff\w\s\.\,\!\?\-\+\%\$]', ' ', text)
        return text.lower()
    
    def calculate_score(self, text, keywords, patterns):
        """计算文本与关键词和模式的匹配分数"""
        text = self.preprocess_text(text)
        score = 0
        
        # 计算关键词匹配分数
        for keyword in keywords:
            keyword_lower = keyword.lower()
            # 计算关键词出现次数
            count = len(re.findall(r'\b' + re.escape(keyword_lower) + r'\b', text))
            if count == 0:
                # 对于中文关键词，使用简单的包含匹配
                count = text.count(keyword_lower)
            score += count
        
        # 计算模式匹配分数（权重更高）
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            score += len(matches) * 2  # 模式匹配给予2倍权重
        
        return score

    def check_portfolio_mention(self, article):
        """检查文章是否提到了IOSG投资组合项目"""
        title = article.get('title', '')
        
        text = self.preprocess_text(title.lower())
        mentioned_projects = []
        for project in self.portfolios:
            pattern = r'\b' + re.escape(project.lower()) + r'\b'
            if re.search(pattern, text):
                mentioned_projects.append(project)
        
        portfolio = len(mentioned_projects) > 0
        
        return {
            'portfolio': portfolio,
            'mentioned_projects': mentioned_projects,
            'mention_count': len(mentioned_projects)
        }

    def classify_article(self, article):
        """对单篇文章进行分类"""
        # 合并标题和内容文本
        title = article.get('title', '')
        content = article.get('content_text', '')
        combined_text = f"{title} {content}"
        
        scores = {}
        
        # 检查portfolio关键词
        portfolio_info = self.check_portfolio_mention(article)
        
        # 如果文章提到了portfolio项目，直接分类为portfolios
        if portfolio_info['portfolio']:
            return {
                'category': 'portfolios',
                'confidence': portfolio_info['mention_count'],
                'scores': {'portfolios': portfolio_info['mention_count']},
                'portfolio': portfolio_info['portfolio'],
                'mentioned_projects': portfolio_info['mentioned_projects'],
                'mention_count': portfolio_info['mention_count']
            }
        
        # 计算每个分类的得分（排除portfolios和其他）
        for category, config in self.categories.items():
            if category in ["其他", "portfolios"]:
                continue  # 跳过兜底分类和portfolios分类
            
            keywords = config['keywords']
            patterns = config.get('patterns', [])
            weight = config['weight']
            score = self.calculate_score(combined_text, keywords, patterns) * weight
            scores[category] = score
        
        # 找到最高分的分类
        if scores and max(scores.values()) > 0:
            best_category = max(scores, key=scores.get)
            confidence = scores[best_category]
        else:
            best_category = "其他"
            confidence = 0
        
        return {
            'category': best_category,
            'confidence': confidence,
            'scores': scores,
            'portfolio': portfolio_info['portfolio'],
            'mentioned_projects': portfolio_info['mentioned_projects'],
            'mention_count': portfolio_info['mention_count']
        }
    
    def classify_articles(self, articles):
        """对所有文章进行分类"""
        classified_articles = []
        category_stats = defaultdict(int)
        
        print(f"开始分类 {len(articles)} 篇文章...")
        
        for i, article in enumerate(articles, 1):
            if i % 100 == 0:
                print(f"已处理 {i}/{len(articles)} 篇文章")
            
            classification = self.classify_article(article)
            
            # 添加分类信息到文章
            article_with_class = article.copy()
            article_with_class.update({
                'classification': classification['category'],
                'classification_confidence': classification['confidence'],
                'classification_scores': classification['scores'],
                'portfolio': classification['portfolio'],
                'mentioned_projects': classification['mentioned_projects'],
                'mention_count': classification['mention_count']
            })
            
            classified_articles.append(article_with_class)
            category_stats[classification['category']] += 1
        
        return classified_articles, dict(category_stats)

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
    
    print(f"=== 加密货币文章智能分类器 ===")
    print(f"输入文件: {input_file}")
    print(f"文章总数: {len(articles)}")
    print(f"来源统计: {metadata.get('feeds_stats', {})}")
    
    # 标题关键词筛选
    title_keywords = ['上线','转移','活动','下架','24小时','24 小时','爆仓','涨幅','跌幅','奖励']
    # 标题关键词筛选 - 只保留标题不包含任何关键词的文章
    articles = [
        article for article in articles 
        if not any(keyword.lower() in article.get('title', '').lower() for keyword in title_keywords)
    ]
    
    # 文章长度筛选
    articles = [
        article for article in articles 
        if len(article.get('content_text', '')) < 300 
    ]
    
    # 创建分类器并进行分类
    classifier = CryptoArticleClassifier()
    classified_articles, category_stats = classifier.classify_articles(articles)
    
    
    
    
    # 显示分类统计
    print(f"\n=== 分类结果统计 ===")
    total_classified = len(classified_articles)
    
    for category, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_classified) * 100
        print(f"📊 {category}: {count} 篇 ({percentage:.1f}%)")
    
    # Portfolio统计
    portfolio_articles = [a for a in classified_articles if a.get('portfolio', False)]
    print(f"\n⭐ Portfolio项目相关文章: {len(portfolio_articles)} 篇 ({len(portfolio_articles)/total_classified*100:.1f}%)")
    
    # 按分类统计portfolio文章
    portfolio_by_category = defaultdict(int)
    for article in portfolio_articles:
        portfolio_by_category[article['classification']] += 1
    
    if portfolio_by_category:
        print("   按分类分布:")
        for category, count in sorted(portfolio_by_category.items(), key=lambda x: x[1], reverse=True):
            print(f"   - {category}: {count} 篇")
    
    # 按分类组织文章
    articles_by_category = defaultdict(list)
    for article in classified_articles:
        category = article['classification']
        articles_by_category[category].append(article)
    
    # 显示每个分类的示例文章
    print(f"\n=== 分类示例（每类显示前3篇） ===")
    for category, articles_list in articles_by_category.items():
        print(f"\n🏷️ {category} ({len(articles_list)} 篇):")
        
        # 按置信度排序，显示前3篇
        sorted_articles = sorted(articles_list, 
                                key=lambda x: x['classification_confidence'], 
                                reverse=True)
        
        for i, article in enumerate(sorted_articles[:3], 1):
            title = article['title']
            source = article['source_feed']
            confidence = article['classification_confidence']
            portfolio_mark = "⭐" if article.get('portfolio', False) else ""
            mentioned = article.get('mentioned_projects', [])
            mentioned_str = f" [{', '.join(mentioned[:2])}{'...' if len(mentioned) > 2 else ''}]" if mentioned else ""
            print(f"  {i}. {portfolio_mark}[{source}] {title} (得分: {confidence}){mentioned_str}")
    
    # 保存分类结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"classified_articles_{timestamp}.json"
    
    output_data = {
        'metadata': {
            **metadata,
            'classification_date': datetime.now().isoformat(),
            'total_articles': len(classified_articles),
            'category_stats': category_stats,
            'categories_defined': list(classifier.categories.keys())
        },
        'articles': classified_articles,
        'articles_by_category': dict(articles_by_category)
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 分类结果已保存到: {output_file}")
    
    # 保存简化的分类报告
    report_file = f"classification_report_{timestamp}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=== 加密货币文章分类报告 ===\n\n")
        f.write(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"文章总数: {len(classified_articles)}\n\n")
        
        f.write("分类统计:\n")
        for category, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_classified) * 100
            f.write(f"  {category}: {count} 篇 ({percentage:.1f}%)\n")
        
        f.write("\n各分类热门文章:\n")
        for category, articles_list in articles_by_category.items():
            f.write(f"\n{category}:\n")
            sorted_articles = sorted(articles_list, 
                                    key=lambda x: x['classification_confidence'], 
                                    reverse=True)
            for i, article in enumerate(sorted_articles[:5], 1):
                f.write(f"  {i}. [{article['source_feed']}] {article['title']}\n")
    
    print(f"📄 分类报告已保存到: {report_file}")
    print(f"\n🎯 分类完成！共处理 {len(classified_articles)} 篇文章")

if __name__ == "__main__":
    main()