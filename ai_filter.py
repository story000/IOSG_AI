#!/usr/bin/env python3
"""
基于OpenAI API的项目融资文章筛选器
从classify_articles.py的结果中进一步筛选真实的项目融资
"""

import json
import openai
import time
from datetime import datetime
import os
import re

class OpenAIFundingFilter:
    def __init__(self, api_key=None):
        # 设置OpenAI API密钥
        if api_key:
            openai.api_key = api_key
        else:
            # 从环境变量获取API密钥
            openai.api_key = os.getenv('OPENAI_API_KEY')
            if not openai.api_key:
                print("❌ 请设置OPENAI_API_KEY环境变量或在代码中提供API密钥")
                return
        
        # IOSG投资组合项目列表
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
        
        # 项目融资筛选提示词
        self.project_funding_prompt = """请分析以下{count}篇加密货币新闻，判断哪些是真实的项目融资新闻。

筛选标准：
✅ 保留：具体的单个加密货币/区块链/Web3项目获得融资
✅ 保留：有明确的项目名称，明确完成了融资
❌ 抛弃：基金募资、交易所融资、传统企业投资、政府资助，计划
❌ 抛弃：上市公司，筹集资金购买加密货币等非初创项目融资行为
❌ 抛弃：并购收购、股票投资、个人投资
❌ 抛弃：爆仓、交易、价格变动等非融资内容

请只返回符合条件的文章ID，格式：[id1, id2, id3]
如果没有符合条件的文章，返回：[]

返回注意：
1. 只返回符合条件的文章ID，不要返回其他内容
2. 返回文章的 ID+数字，错误格式：数组定位、标题、数字
文章列表：
{articles}"""

        # 基金融资筛选提示词
        self.fund_funding_prompt = """请分析以下{count}篇加密货币新闻，判断哪些是真实的基金融资新闻。

筛选标准：
✅ 保留：投资机构/VC设立新的加密货币/区块链投资基金
✅ 保留：基金公司募集专门投资Web3/crypto的新基金
✅ 保留：有明确的基金规模、基金名称、管理机构
❌ 抛弃：单个项目的融资（不是基金设立）
❌ 抛弃：交易所业务、个人投资
❌ 抛弃：并购收购、股票投资
❌ 抛弃：爆仓、交易、价格变动等非融资内容

请只返回符合条件的文章ID，格式：[id1, id2, id3]
如果没有符合条件的文章，返回：[]

返回注意：
1. 只返回符合条件的文章ID，不要返回其他内容
2. 返回文章的 ID+数字，错误格式：数组定位、标题、数字
文章列表：
{articles}"""

        # 基础设施/项目主网上线筛选提示词
        self.infrastructure_prompt = """请分析以下{count}篇加密货币新闻，判断哪些是真实的基础设施/项目主网上线新闻。

筛选标准：
✅ 保留：区块链主网正式上线、测试网上线
✅ 保留：Layer 1/Layer 2网络升级、硬分叉
✅ 保留：重要协议更新、网络扩容方案
✅ 保留：跨链桥、互操作性解决方案上线
❌ 抛弃：价格变动、交易相关内容
❌ 抛弃：融资、投资相关内容
❌ 抛弃：简单的功能更新、小版本升级
❌ 抛弃：个人观点、市场分析

请只返回符合条件的文章ID，格式：[id1, id2, id3]
如果没有符合条件的文章，返回：[]

返回注意：
1. 只返回符合条件的文章ID，不要返回其他内容
2. 返回文章的 ID+数字，错误格式：数组定位、标题、数字
文章列表：
{articles}"""

        # DeFi/RWA筛选提示词
        self.defi_rwa_prompt = """请分析以下{count}篇加密货币新闻，判断哪些是真实的DeFi/RWA新闻。

筛选标准：
✅ 保留：去中心化金融协议上线、重大更新
✅ 保留：现实世界资产(RWA)代币化项目
✅ 保留：重要的流动性池、借贷协议变化
✅ 保留：稳定币机制、算法稳定币发展
✅ 保留：收益farming、质押机制创新
❌ 抛弃：纯粹的价格变动、交易量变化
❌ 抛弃：融资相关内容
❌ 抛弃：个人投资建议、市场预测
❌ 抛弃：安全事件、黑客攻击

请只返回符合条件的文章ID，格式：[id1, id2, id3]
如果没有符合条件的文章，返回：[]

返回注意：
1. 只返回符合条件的文章ID，不要返回其他内容
2. 返回文章的 ID+数字，错误格式：数组定位、标题、数字
文章列表：
{articles}"""

        # NFT/GameFi/Metaverse筛选提示词
        self.nft_gamefi_prompt = """请分析以下{count}篇加密货币新闻，判断哪些是真实的NFT/GameFi/Metaverse新闻。

筛选标准：
✅ 保留：重要NFT项目发布、合作伙伴关系
✅ 保留：区块链游戏正式上线、重大更新
✅ 保留：元宇宙平台重要功能发布
✅ 保留：P2E游戏机制创新、游戏代币经济
✅ 保留：知名IP进入NFT/GameFi领域
❌ 抛弃：纯粹的价格变动、交易量变化
❌ 抛弃：融资相关内容
❌ 抛弃：个人收藏、小型NFT项目
❌ 抛弃：市场炒作、价格预测

请只返回符合条件的文章ID，格式：[id1, id2, id3]
如果没有符合条件的文章，返回：[]

返回注意：
1. 只返回符合条件的文章ID，不要返回其他内容
2. 返回文章的 ID+数字，错误格式：数组定位、标题、数字
文章列表：
{articles}"""

        # 交易所/钱包筛选提示词
        self.exchange_wallet_prompt = """请分析以下{count}篇加密货币新闻，判断哪些是真实的交易所/钱包新闻。

筛选标准：
✅ 保留：主要交易所新产品发布、重要合作
✅ 保留：新交易所正式上线、获得牌照
✅ 保留：钱包重要功能更新、安全机制
✅ 保留：监管政策对交易所的重要影响
✅ 保留：交易所与传统金融机构合作
❌ 抛弃：纯粹的上币公告、价格变动
❌ 抛弃：融资相关内容
❌ 抛弃：个人交易策略、技术分析
❌ 抛弃：小型交易所日常运营

请只返回符合条件的文章ID，格式：[id1, id2, id3]
如果没有符合条件的文章，返回：[]

返回注意：
1. 只返回符合条件的文章ID，不要返回其他内容
2. 返回文章的 ID+数字，错误格式：数组定位、标题、数字
文章列表：
{articles}"""


    def filter_batch_articles(self, articles_batch, article_type="project"):
        """批处理筛选文章"""
        # 为每篇文章生成简短ID
        articles_text = ""
        id_mapping = {}
        
        for i, article in enumerate(articles_batch):
            article_id = f"ID{i+1}"
            title = article.get('title', '')
            content = article.get('content_text', '')[:100]
            id_mapping[article_id] = i
            if article_type in ["project", "infrastructure", "defi_rwa", "nft_gamefi", "exchange_wallet"]:
                articles_text += f"\n{article_id}: {title}\n"
            else:  # fund and others
                articles_text += f"\n{article_id}: {title}  - {content} \n"
        
        # 根据文章类型选择不同的prompt
        if article_type == "project":
            prompt = self.project_funding_prompt.format(
                count=len(articles_batch),
                articles=articles_text
            )
        elif article_type == "fund":
            prompt = self.fund_funding_prompt.format(
                count=len(articles_batch),
                articles=articles_text
            )
        elif article_type == "infrastructure":
            prompt = self.infrastructure_prompt.format(
                count=len(articles_batch),
                articles=articles_text
            )
        elif article_type == "defi_rwa":
            prompt = self.defi_rwa_prompt.format(
                count=len(articles_batch),
                articles=articles_text
            )
        elif article_type == "nft_gamefi":
            prompt = self.nft_gamefi_prompt.format(
                count=len(articles_batch),
                articles=articles_text
            )
        elif article_type == "exchange_wallet":
            prompt = self.exchange_wallet_prompt.format(
                count=len(articles_batch),
                articles=articles_text
            )
        else:
            # 默认使用项目融资prompt
            prompt = self.project_funding_prompt.format(
                count=len(articles_batch),
                articles=articles_text
            )
            
        
        try:
            # Using current OpenAI client library
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
            )
            
            result = response.choices[0].message.content.strip()
            print(f"  🤖 AI返回: {result}")
            
            # 解析返回的ID列表
            import re
            # Extract IDs from the AI response
            raw_ids = re.findall(r'\d+', result)
            # Add 'ID' prefix to each number
            id_matches = ['ID' + num for num in raw_ids]
            
            # 转换为文章索引
            selected_indices = []
            for id_str in id_matches:
                if id_str in id_mapping:
                    selected_indices.append(id_mapping[id_str])
            
            return {
                'selected_indices': selected_indices,
                'ai_response': result,
                'success': True
            }
            
        except Exception as e:
            print(f"  ❌ API调用失败: {e}")
            return {
                'selected_indices': [],
                'ai_response': f"API错误: {str(e)}",
                'success': False
            }
    
    def batch_filter(self, articles, batch_size=10, max_articles=None, article_type="project"):
        """批量筛选文章"""
        if max_articles:
            articles = articles[:max_articles]
        
        type_name = "项目融资" if article_type == "project" else "基金融资"
        print(f"开始使用OpenAI API批量筛选 {len(articles)} 篇{type_name}文章...")
        print(f"📦 批处理大小: {batch_size} 篇/次")
        
        # 计算预估成本
        num_batches = (len(articles) + batch_size - 1) // batch_size
        print(f"📊 预计API调用次数: {num_batches} 次")
        print("⚠️ 注意：这将消耗API调用次数")
        
        # 询问确认
        confirm = input(f"确认处理{len(articles)}篇{type_name}文章？(y/n): ").strip().lower()
        if confirm != 'y':
            print("取消处理")
            return []
        
        filtered_articles = []
        
        # 分批处理
        for batch_start in range(0, len(articles), batch_size):
            batch_end = min(batch_start + batch_size, len(articles))
            batch_articles = articles[batch_start:batch_end]
            batch_num = (batch_start // batch_size) + 1
            
            print(f"\n📦 处理{type_name}批次 {batch_num}/{num_batches} ({len(batch_articles)} 篇文章)")
            print(f"   文章 {batch_start+1}-{batch_end}")
            
            # 显示当前批次文章标题
            for i, article in enumerate(batch_articles):
                print(f"   ID{i+1}: {article['title'][:60]}")
            
            # 调用API批量筛选，传入文章类型
            filter_result = self.filter_batch_articles(batch_articles, article_type)
            
            if filter_result['success']:
                selected_indices = filter_result['selected_indices']
                print(f"  ✅ 选中 {len(selected_indices)} 篇: {selected_indices}")
                
                # 添加选中的文章
                for idx in selected_indices:
                    if 0 <= idx < len(batch_articles):
                        article_with_filter = batch_articles[idx].copy()
                        
                        
                        article_with_filter['ai_filter'] = {
                            'keep': True,
                            'reason': filter_result['ai_response'],
                            'batch_processed': True,
                            'batch_id': batch_num,
                            'article_type': article_type
                        }
                        
                        
                        filtered_articles.append(article_with_filter)
            else:
                print(f"  ❌ 批次处理失败")
            
            # 避免API速率限制
            if batch_num < num_batches:
                print(f"  ⏳ 暂停1秒...")
                time.sleep(1)
        
        print(f"\n🎯 {type_name}批量筛选完成！")
        print(f"原始文章: {len(articles)} 篇")
        print(f"筛选后: {len(filtered_articles)} 篇")
        print(f"过滤率: {(1 - len(filtered_articles)/len(articles))*100:.1f}%")
        print(f"API调用次数: {num_batches} 次")
        
        return filtered_articles

def main():
    # 查找最新的分类结果文件
    import glob
    
    classified_files = glob.glob("classified_articles_*.json")
    if not classified_files:
        print("❌ 未找到classified_articles_*.json文件")
        print("请先运行 python classify_articles.py")
        return
    
    # 使用最新的文件
    latest_file = max(classified_files)
    print(f"读取文件: {latest_file}")
    
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return
    
    # 获取各类文章
    articles_by_category = data.get('articles_by_category', {})
    project_funding_articles = articles_by_category.get('项目融资', [])
    fund_funding_articles = articles_by_category.get('基金融资', [])
    infrastructure_articles = articles_by_category.get('基础设施/项目主网上线', [])
    defi_rwa_articles = articles_by_category.get('DeFi/RWA', [])
    nft_gamefi_articles = articles_by_category.get('NFT/GameFi/Metaverse', [])
    exchange_wallet_articles = articles_by_category.get('交易所/钱包', [])
    portfolio_articles = articles_by_category.get('portfolios', [])
    
    # 计算总文章数
    total_articles = (len(project_funding_articles) + len(fund_funding_articles) + 
                     len(infrastructure_articles) + len(defi_rwa_articles) + 
                     len(nft_gamefi_articles) + len(exchange_wallet_articles) + 
                     len(portfolio_articles))
    
    if total_articles == 0:
        print("❌ 未找到可筛选的文章")
        return
    
    print(f"=== OpenAI API 文章筛选器 ===")
    print(f"找到项目融资分类文章: {len(project_funding_articles)} 篇")
    print(f"找到基金融资分类文章: {len(fund_funding_articles)} 篇")
    print(f"找到基础设施/项目主网上线文章: {len(infrastructure_articles)} 篇")
    print(f"找到DeFi/RWA文章: {len(defi_rwa_articles)} 篇")
    print(f"找到NFT/GameFi/Metaverse文章: {len(nft_gamefi_articles)} 篇")
    print(f"找到交易所/钱包文章: {len(exchange_wallet_articles)} 篇")
    print(f"找到Portfolio文章: {len(portfolio_articles)} 篇")
    
    # 设置API密钥
    api_key = input("请输入OpenAI API密钥 (或按回车使用环境变量OPENAI_API_KEY): ").strip()
    if not api_key:
        api_key = None
    
    # 创建筛选器
    filter = OpenAIFundingFilter(api_key)
    if not openai.api_key:
        return
    
    # 询问处理数量和批大小
    max_articles = input(f"要处理多少篇文章？(默认全部{total_articles}篇，输入数字限制数量): ").strip()
    if max_articles.isdigit():
        max_articles = int(max_articles)
    else:
        max_articles = None
    
    batch_size = input("批处理大小？(默认10篇/次，输入数字修改): ").strip()
    if batch_size.isdigit():
        batch_size = int(batch_size)
    else:
        batch_size = 10
    
    # 分别筛选各类文章
    real_project_funding = []
    real_fund_funding = []
    real_infrastructure = []
    real_defi_rwa = []
    real_nft_gamefi = []
    real_exchange_wallet = []
    real_portfolio = []
    
    if project_funding_articles:
        print(f"\n🎯 开始筛选项目融资文章...")
        real_project_funding = filter.batch_filter(project_funding_articles, batch_size, max_articles, "project")
    
    if fund_funding_articles:
        print(f"\n🎯 开始筛选基金融资文章...")
        real_fund_funding = filter.batch_filter(fund_funding_articles, batch_size, max_articles, "fund")
    
    if infrastructure_articles:
        print(f"\n🎯 开始筛选基础设施/项目主网上线文章...")
        real_infrastructure = filter.batch_filter(infrastructure_articles, batch_size, max_articles, "infrastructure")
    
    if defi_rwa_articles:
        print(f"\n🎯 开始筛选DeFi/RWA文章...")
        real_defi_rwa = filter.batch_filter(defi_rwa_articles, batch_size, max_articles, "defi_rwa")
    
    if nft_gamefi_articles:
        print(f"\n🎯 开始筛选NFT/GameFi/Metaverse文章...")
        real_nft_gamefi = filter.batch_filter(nft_gamefi_articles, batch_size, max_articles, "nft_gamefi")
    
    if exchange_wallet_articles:
        print(f"\n🎯 开始筛选交易所/钱包文章...")
        real_exchange_wallet = filter.batch_filter(exchange_wallet_articles, batch_size, max_articles, "exchange_wallet")
    
    # Portfolio文章不需要AI筛选，直接使用
    if portfolio_articles:
        print(f"\n⭐ Portfolio文章无需AI筛选，直接使用...")
        real_portfolio = portfolio_articles
    

    
    # 保存结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
 
    # 生成格式化输出
    formatted_output_file = f"formatted_report_{timestamp}.txt"
    with open(formatted_output_file, 'w', encoding='utf-8') as f:
        def clean_content(content):
            import re
            # 删除各种新闻来源前缀，包括带空格的模式
            content = re.sub(r'.*?消息[，,]\s*', '', content)
            content = re.sub(r'.*?报道[，,]\s*', '', content)
            content = re.sub(r'深潮\s*TechFlow\s*[消息报道]*[，,]\s*', '', content)
            content = re.sub(r'TechFlow\s*深潮\s*[消息报道]*[，,]\s*', '', content)
            content = re.sub(r'PANews\s*\d+月\d+日消息[，,]\s*', '', content)
            content = re.sub(r'Wu\s*Blockchain\s*[消息报道]*[，,]\s*', '', content)
            content = re.sub(r'Cointelegraph\s*中文\s*[消息报道]*[，,]\s*', '', content)
            # 删除多余的空白
            content = re.sub(r'\s+', ' ', content).strip()
            return content
        
        def delete_reports(articles):
            new_articles = []
            for article in articles:
                if not re.search(r"周报|日报|月报", article['title']) or len(article.get('content_text', '')) > 200:
                    new_articles.append(article)
            return new_articles

        # 项目融资板块
        if real_project_funding:
            f.write("# 2. 项目融资介绍 (后续需加上项目类别并删除前缀，不要写据XX报道）\n")
            for i, article in enumerate(delete_reports(real_project_funding), 1):
                title = article['title']
                url = article['url']
                content = clean_content(article.get('content_text', ''))
                
                f.write(f"{i}. [{title}]({url})\n\n{content}\n\n")
        
        # 基金融资板块
        if real_fund_funding:
            f.write("# 3. 基金融资介绍\n")
            for i, article in enumerate(delete_reports(real_fund_funding), 1):
                title = article['title']
                url = article['url']
                content = clean_content(article.get('content_text', ''))
                
                f.write(f"{i}. [{title}]({url})\n\n{content}\n\n")
        
        # 基础设施/项目主网上线板块
        if real_infrastructure:
            f.write("# 4. 基础设施/项目主网上线\n")
            for i, article in enumerate(delete_reports(real_infrastructure), 1):
                title = article['title']
                url = article['url']
                content = clean_content(article.get('content_text', ''))
                
                f.write(f"{i}. [{title}]({url})\n\n{content}\n\n")
        
        # DeFi/RWA板块
        if real_defi_rwa:
            f.write("# 5. DeFi/RWA\n")
            for i, article in enumerate(delete_reports(real_defi_rwa), 1):
                title = article['title']
                url = article['url']
                content = clean_content(article.get('content_text', ''))
                
                f.write(f"{i}. [{title}]({url})\n\n{content}\n\n")
        
        # NFT/GameFi/Metaverse板块
        if real_nft_gamefi:
            f.write("# 6. NFT/GameFi/Metaverse\n")
            for i, article in enumerate(delete_reports(real_nft_gamefi), 1):
                title = article['title']
                url = article['url']
                content = clean_content(article.get('content_text', ''))
                
                f.write(f"{i}. [{title}]({url})\n\n{content}\n\n")
        
        # 交易所/钱包板块
        if real_exchange_wallet:
            f.write("# 7. 交易所/钱包\n")
            for i, article in enumerate(delete_reports(real_exchange_wallet), 1):
                title = article['title']
                url = article['url']
                content = clean_content(article.get('content_text', ''))
                
                f.write(f"{i}. [{title}]({url})\n\n{content}\n\n")
        
        # Portfolio板块
        if real_portfolio:
            f.write("# 8. Our portfolio (这里标红的在公众号编辑时对应标红即可)\n")
            for i, article in enumerate(delete_reports(real_portfolio), 1):
                title = article['title']
                url = article['url']
                content = clean_content(article.get('content_text', ''))
                
                f.write(f"{i}. [{title}]({url})\n\n{content}\n\n")
    
    print(f"📋 格式化输出已保存到: {formatted_output_file}")
    print(f"\n🎯 AI筛选完成！")
    print(f"   项目融资: {len(project_funding_articles)} → {len(real_project_funding)} 篇")
    print(f"   基金融资: {len(fund_funding_articles)} → {len(real_fund_funding)} 篇")
    print(f"   基础设施/项目主网上线: {len(infrastructure_articles)} → {len(real_infrastructure)} 篇")
    print(f"   DeFi/RWA: {len(defi_rwa_articles)} → {len(real_defi_rwa)} 篇")
    print(f"   NFT/GameFi/Metaverse: {len(nft_gamefi_articles)} → {len(real_nft_gamefi)} 篇")
    print(f"   交易所/钱包: {len(exchange_wallet_articles)} → {len(real_exchange_wallet)} 篇")
    print(f"   Portfolio: {len(portfolio_articles)} → {len(real_portfolio)} 篇")
    
    # 计算总计
    total_original = (len(project_funding_articles) + len(fund_funding_articles) + 
                     len(infrastructure_articles) + len(defi_rwa_articles) + 
                     len(nft_gamefi_articles) + len(exchange_wallet_articles) + 
                     len(portfolio_articles))
    total_filtered = (len(real_project_funding) + len(real_fund_funding) + 
                     len(real_infrastructure) + len(real_defi_rwa) + 
                     len(real_nft_gamefi) + len(real_exchange_wallet) + 
                     len(real_portfolio))
    print(f"   总计: {total_original} → {total_filtered} 篇")
    
    
    # 在控制台显示格式化输出预览
    print(f"\n=== 格式化输出预览 ===")
    
    def clean_content_preview(content):
        import re
        content = re.sub(r'.*?消息[，,]\s*', '', content)
        content = re.sub(r'.*?报道[，,]\s*', '', content)
        content = re.sub(r'深潮\s*TechFlow\s*[消息报道]*[，,]\s*', '', content)
        content = re.sub(r'TechFlow\s*深潮\s*[消息报道]*[，,]\s*', '', content)
        content = re.sub(r'PANews\s*\d+月\d+日消息[，,]\s*', '', content)
        content = re.sub(r'Wu\s*Blockchain\s*[消息报道]*[，,]\s*', '', content)
        content = re.sub(r'Cointelegraph\s*中文\s*[消息报道]*[，,]\s*', '', content)
        content = re.sub(r'\s+', ' ', content).strip()
        return content
    
    if real_project_funding:
        print("\n# 2. 项目融资介绍 (后续需加上项目类别并删除前缀，不要写据XX报道）")
        for i, article in enumerate(real_project_funding[:2], 1):
            title = article['title']
            url = article['url']
            content = clean_content_preview(article.get('content_text', ''))
            preview_content = content[:150] + "..." if len(content) > 150 else content
            print(f"\n{i}.[{title}]({url})")
            print(f"{preview_content}")
    
    if real_fund_funding:
        print("\n# 3. 基金融资介绍")
        for i, article in enumerate(real_fund_funding[:2], 1):
            title = article['title']
            url = article['url']
            content = clean_content_preview(article.get('content_text', ''))
            preview_content = content[:150] + "..." if len(content) > 150 else content
            print(f"\n{i}.[{title}]({url})")
            print(f"{preview_content}")
    
    # Portfolio板块
    if portfolio_articles: 
        print("\n# 4. Our portfolio (这里标红的在公众号编辑时对应标红即可)")
        for i, article in enumerate(portfolio_articles[:2], 1):
            title = article['title']
            url = article['url']
            content = clean_content_preview(article.get('content_text', ''))
            mentioned = article.get('mentioned_projects', [])
            mentioned_str = f" [{', '.join(mentioned)}]" if mentioned else ""
            preview_content = content[:150] + "..." if len(content) > 150 else content
            print(f"\n{i}.[{title}]({url}){mentioned_str}")
            print(f"{preview_content}")

if __name__ == "__main__":
    main()