#!/usr/bin/env python3
"""
基于AI API的项目融资文章筛选器 (支持OpenAI和DeepSeek)
从classify_articles.py的结果中进一步筛选真实的项目融资
"""

import json
import openai
import time
from datetime import datetime
import os
import re
import yaml
import difflib

class AIFundingFilter:
    def __init__(self, api_key=None, provider="deepseek"):
        self.provider = provider.lower()
        self.api_key = api_key
        
        # 后台DeepSeek API密钥 (请在这里配置您的DeepSeek API密钥)
        # 方式1: 直接在代码中配置
        # self.deepseek_key = "sk-your-actual-deepseek-key-here"  
        # 方式2: 从环境变量读取
        self.deepseek_key = os.getenv('DEEPSEEK_API_KEY', 'sk-your-deepseek-key-here')
        
        if self.provider == "deepseek":
            # 使用DeepSeek API
            if not self.deepseek_key or self.deepseek_key == 'sk-your-deepseek-key-here':
                print("❌ DeepSeek API密钥未配置")
                print("请在ai_filter.py第21行配置您的DeepSeek API密钥:")
                print('self.deepseek_key = "sk-your-actual-deepseek-key-here"')
                print("或设置环境变量: export DEEPSEEK_API_KEY=sk-your-key")
                self.api_key = None
                return
            self.api_key = self.deepseek_key
            self.base_url = "https://api.deepseek.com"
            self.model = "deepseek-chat"
            print("✅ 使用DeepSeek API")
            print(f"API密钥: {self.api_key[:10]}...")
        else:
            # 使用OpenAI API
            if api_key:
                self.api_key = api_key
            else:
                self.api_key = os.getenv('OPENAI_API_KEY')
            if not self.api_key:
                print("❌ 请提供OpenAI API密钥")
                return
            self.base_url = None  # OpenAI默认
            self.model = "gpt-3.5-turbo"
            print("✅ 使用OpenAI API")
        
        # 设置OpenAI客户端
        if self.provider == "deepseek":
            openai.api_key = self.api_key
            openai.base_url = self.base_url
        else:
            openai.api_key = self.api_key
        
        
        # 从YAML文件加载配置
        self.config = self._load_config()
        self.portfolios = self.config.get('portfolio_projects', [])
        self.prompts_config = self.config.get('ai_filter', {})
        
        # 标题去重相似度阈值
        self.similarity_threshold = 0.7

    def _load_config(self):
        """从YAML文件加载配置"""
        try:
            config_file = "crypto_config.yaml"
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            print(f"✅ 已加载配置文件: {config_file}")
            return config
        except FileNotFoundError:
            print("❌ 未找到crypto_config.yaml配置文件，使用默认配置")
            return {}
        except Exception as e:
            print(f"❌ 加载配置失败: {e}，使用默认配置")
            return {}

    def _format_criteria(self, criteria):
        """格式化筛选标准为可读文本"""
        formatted = ""
        if 'keep' in criteria:
            for item in criteria['keep']:
                formatted += f"✅ 保留：{item}\n"
        if 'discard' in criteria:
            for item in criteria['discard']:
                formatted += f"❌ 抛弃：{item}\n"
        return formatted.strip()

    def _generate_prompt(self, category_name, count, articles_text):
        """根据类别生成prompt"""
        if not self.prompts_config:
            # 使用旧的硬编码方式作为fallback
            return self._get_legacy_prompt(category_name, count, articles_text)
        
        config = self.prompts_config
        
        # 查找对应的类别配置
        category_config = None
        for cat_name, cat_config in config['categories'].items():
            if cat_name == category_name:
                category_config = cat_config
                break
        
        if not category_config:
            print(f"⚠️ 未找到类别 '{category_name}' 的配置，使用项目融资配置")
            category_config = config['categories']['项目融资']
        
        # 格式化筛选标准
        criteria_text = self._format_criteria(category_config['criteria'])
        
        # 生成完整的prompt
        prompt = category_config['prompt_template'].format(
            count=count,
            criteria=criteria_text,
            return_format=config['common']['return_format'],
            empty_return=config['common']['empty_return'],
            instructions=config['common']['instructions'],
            articles=articles_text
        )
        
        return prompt
    
    def _clean_title_for_comparison(self, title):
        """
        清理标题用于相似度比较
        """
        # 移除多余空格和标点
        title = re.sub(r'\s+', ' ', title).strip()
        # 移除常见的新闻前缀
        title = re.sub(r'^\d+\.\s*', '', title)
        return title.lower()
    
    def _calculate_title_similarity(self, title1, title2):
        """
        计算两个标题的相似度
        """
        clean_title1 = self._clean_title_for_comparison(title1)
        clean_title2 = self._clean_title_for_comparison(title2)
        
        similarity = difflib.SequenceMatcher(None, clean_title1, clean_title2).ratio()
        return similarity
    
    def deduplicate_articles_by_title(self, articles, category_name=""):
        """
        根据标题相似度去重文章
        :param articles: 文章列表
        :param category_name: 分类名称（用于日志输出）
        :return: (去重后的文章列表, 重复文章统计)
        """
        if len(articles) <= 1:
            return articles, {'removed_count': 0, 'duplicate_groups': []}
        
        # 用于存储去重后的文章
        unique_articles = []
        # 用于存储重复文章组
        duplicate_groups = []
        # 已处理的文章索引
        processed = set()
        
        print(f"  🔍 开始对{category_name}进行标题去重（阈值: {self.similarity_threshold:.0%}）...")
        
        for i, article1 in enumerate(articles):
            if i in processed:
                continue
                
            # 当前文章组（包含相似的文章）
            current_group = [article1]
            processed.add(i)
            
            # 与后续文章比较
            for j, article2 in enumerate(articles[i+1:], i+1):
                if j in processed:
                    continue
                    
                similarity = self._calculate_title_similarity(
                    article1['title'], article2['title']
                )
                
                if similarity >= self.similarity_threshold:
                    current_group.append(article2)
                    processed.add(j)
                    
            # 如果有重复文章，记录到重复组；否则添加到唯一文章
            if len(current_group) > 1:
                duplicate_groups.append(current_group)
                # 保留第一篇文章（通常是最早发布的）
                unique_articles.append(current_group[0])
                
                # 输出重复信息
                print(f"    📝 发现重复组（{len(current_group)}篇）:")
                for k, article in enumerate(current_group):
                    status = "✅ 保留" if k == 0 else "❌ 删除"
                    title_preview = article['title'][:50] + "..." if len(article['title']) > 50 else article['title']
                    print(f"      {status} {title_preview}")
                    
            else:
                unique_articles.append(current_group[0])
                
        removed_count = len(articles) - len(unique_articles)
        removal_rate = (removed_count / len(articles)) * 100 if len(articles) > 0 else 0
        
        print(f"  📊 {category_name}去重完成: {len(articles)} → {len(unique_articles)} 篇 (删除{removed_count}篇, {removal_rate:.1f}%)")
        
        return unique_articles, {
            'removed_count': removed_count,
            'duplicate_groups': duplicate_groups,
            'removal_rate': removal_rate
        }
    
    def cross_category_deduplication(self, filtered_results):
        """
        跨板块去重：如果文章在高优先级板块出现，则从低优先级板块删除
        优先级：Portfolio > 项目融资 > 基金融资 > 其他板块
        """
        # 定义优先级顺序
        priority_categories = [
            ("portfolio", "Portfolio"),
            ("project", "项目融资"), 
            ("fund", "基金融资"),
            ("blockchain", "公链/L2/主网"),
            ("middleware", "中间件/工具协议"),
            ("defi", "DeFi"),
            ("rwa", "RWA"),
            ("nft", "NFT"),
            ("gamefi", "GameFi"),
            ("metaverse", "Metaverse/Web3社交"),
            ("exchange_wallet", "交易所/钱包"),
            ("ai_crypto", "AI + Crypto"),
            ("depin", "DePIN")
        ]
        
        # 存储已经在高优先级板块出现的文章标题
        seen_titles = set()
        cross_dedup_stats = {}
        
        # 按优先级处理每个板块
        for category_key, category_name in priority_categories:
            articles = filtered_results.get(category_key, [])
            if not articles:
                cross_dedup_stats[category_name] = {'removed_count': 0}
                continue
                
            # 当前板块的文章
            current_titles = set()
            remaining_articles = []
            removed_count = 0
            
            for article in articles:
                article_title_clean = self._clean_title_for_comparison(article['title'])
                
                # 检查是否与已处理的高优先级板块文章重复
                is_duplicate = False
                for seen_title in seen_titles:
                    similarity = difflib.SequenceMatcher(None, article_title_clean, seen_title).ratio()
                    if similarity >= self.similarity_threshold:
                        is_duplicate = True
                        break
                
                if is_duplicate:
                    removed_count += 1
                    print(f"  ❌ 从{category_name}删除重复文章: {article['title'][:50]}...")
                else:
                    remaining_articles.append(article)
                    current_titles.add(article_title_clean)
            
            # 更新结果
            filtered_results[category_key] = remaining_articles
            cross_dedup_stats[category_name] = {'removed_count': removed_count}
            
            # 将当前板块的标题加入已见标题集合
            seen_titles.update(current_titles)
            
            if removed_count > 0:
                original_count = len(articles)
                remaining_count = len(remaining_articles)
                print(f"  📊 {category_name}跨板块去重: {original_count} → {remaining_count} 篇 (删除{removed_count}篇)")
        
        # 统计总的跨板块去重情况
        total_cross_removed = sum(stats['removed_count'] for stats in cross_dedup_stats.values())
        if total_cross_removed > 0:
            print(f"📊 跨板块去重完成，共删除 {total_cross_removed} 篇重复文章")
        else:
            print(f"📊 跨板块去重完成，未发现重复文章")
            
        return filtered_results, cross_dedup_stats

    def _get_legacy_prompt(self, category_name, count, articles_text):
        """旧的硬编码prompt方式（作为fallback）"""
        # 这里可以保留原来的prompt逻辑作为备用
        legacy_prompt = f"""请分析以下{count}篇加密货币新闻，判断哪些是真实的{category_name}新闻。
        
请只返回符合条件的文章ID，格式：[id1, id2, id3]
如果没有符合条件的文章，返回：[]

文章列表：
{articles_text}"""
        return legacy_prompt

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
            if article_type in ["project", "blockchain", "middleware", "defi", "rwa", "nft", "gamefi", "metaverse", "exchange_wallet", "ai_crypto", "depin"]:
                articles_text += f"\n{article_id}: {title}\n"
            else:  # fund and others
                articles_text += f"\n{article_id}: {title}  - {content} \n"
        
        # 映射文章类型到中文类别名称
        type_to_category = {
            "project": "项目融资",
            "fund": "基金融资",
            "blockchain": "公链/L2/主网",
            "middleware": "中间件/工具协议",
            "defi": "DeFi",
            "rwa": "RWA",
            "nft": "NFT",
            "gamefi": "GameFi",
            "metaverse": "Metaverse/Web3社交",
            "exchange_wallet": "交易所/钱包",
            "ai_crypto": "AI + Crypto",
            "depin": "DePIN"
        }
        
        category_name = type_to_category.get(article_type, "项目融资")
        
        # 使用新的prompt生成方法
        prompt = self._generate_prompt(category_name, len(articles_batch), articles_text)
            
        
        try:
            # 根据提供商创建客户端
            if self.provider == "deepseek":
                client = openai.OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
            else:
                client = openai.OpenAI(api_key=self.api_key)
                
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
            )
            
            result = response.choices[0].message.content.strip()
            print(f"  🤖 AI返回: {result}")
            import sys
            sys.stdout.flush()  # 强制刷新输出
            
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
    
    def batch_filter(self, articles, batch_size=20, max_articles=None, article_type="project"):
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
            
            # 计算并显示进度
            progress = int((batch_num / num_batches) * 100)
            print(f"\n📦 处理{type_name}批次 {batch_num}/{num_batches} ({len(batch_articles)} 篇文章) - 进度: {progress}%")
            print(f"   文章 {batch_start+1}-{batch_end}")
            import sys
            sys.stdout.flush()  # 强制刷新进度输出
            
            # 显示当前批次文章标题
            for i, article in enumerate(batch_articles):
                print(f"   ID{i+1}: {article['title'][:60]}")
            sys.stdout.flush()  # 强制刷新文章列表
            
            # 调用API批量筛选，传入文章类型
            filter_result = self.filter_batch_articles(batch_articles, article_type)
            
            if filter_result['success']:
                selected_indices = filter_result['selected_indices']
                print(f"  ✅ 选中 {len(selected_indices)} 篇: {selected_indices}")
                sys.stdout.flush()  # 强制刷新结果输出
                
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
    # 读取最新的分类结果文件
    latest_file = "latest_classified.json"
    
    # 如果最新文件不存在，尝试查找旧格式的文件
    if not os.path.exists(latest_file):
        print("❌ 未找到分类结果文件")
        print("请先运行 python classify_articles.py")
        return
    
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
    blockchain_articles = articles_by_category.get('公链/L2/主网', [])
    middleware_articles = articles_by_category.get('中间件/工具协议', [])
    defi_articles = articles_by_category.get('DeFi', [])
    rwa_articles = articles_by_category.get('RWA', [])
    nft_articles = articles_by_category.get('NFT', [])
    gamefi_articles = articles_by_category.get('GameFi', [])
    metaverse_articles = articles_by_category.get('Metaverse/Web3社交', [])
    exchange_wallet_articles = articles_by_category.get('交易所/钱包', [])
    ai_crypto_articles = articles_by_category.get('AI + Crypto', [])
    depin_articles = articles_by_category.get('DePIN', [])
    portfolio_articles = articles_by_category.get('portfolios', [])
    
    # 计算总文章数
    total_articles = (len(project_funding_articles) + len(fund_funding_articles) + 
                     len(blockchain_articles) + len(middleware_articles) + 
                     len(defi_articles) + len(rwa_articles) + len(nft_articles) +
                     len(gamefi_articles) + len(metaverse_articles) + 
                     len(exchange_wallet_articles) + len(ai_crypto_articles) + 
                     len(depin_articles) + len(portfolio_articles))
    
    if total_articles == 0:
        print("❌ 未找到可筛选的文章")
        return
    
    print(f"=== AI 文章筛选器 ===")
    print(f"找到项目融资分类文章: {len(project_funding_articles)} 篇")
    print(f"找到基金融资分类文章: {len(fund_funding_articles)} 篇")
    print(f"找到公链/L2/主网文章: {len(blockchain_articles)} 篇")
    print(f"找到中间件/工具协议文章: {len(middleware_articles)} 篇")
    print(f"找到DeFi文章: {len(defi_articles)} 篇")
    print(f"找到RWA文章: {len(rwa_articles)} 篇")
    print(f"找到NFT文章: {len(nft_articles)} 篇")
    print(f"找到GameFi文章: {len(gamefi_articles)} 篇")
    print(f"找到Metaverse/Web3社交文章: {len(metaverse_articles)} 篇")
    print(f"找到交易所/钱包文章: {len(exchange_wallet_articles)} 篇")
    print(f"找到AI + Crypto文章: {len(ai_crypto_articles)} 篇")
    print(f"找到DePIN文章: {len(depin_articles)} 篇")
    print(f"找到Portfolio文章: {len(portfolio_articles)} 篇")
    
    # 选择API提供商
    print(f"\n=== 选择AI API提供商 ===")
    print("1. DeepSeek API (后台配置)")
    print("2. OpenAI API (用户输入)")
    
    provider_choice = input("请选择API提供商 (1/2，默认1): ").strip()
    
    api_key = None
    provider = "deepseek"
    
    if provider_choice == "2":
        provider = "openai"
        api_key = input("请输入OpenAI API密钥: ").strip()
        if not api_key:
            print("❌ 未提供OpenAI API密钥")
            return
    else:
        print("✅ 使用后台DeepSeek API")
    
    # 创建筛选器
    filter = AIFundingFilter(api_key, provider)
    if not filter.api_key:
        print("❌ API密钥配置失败，无法继续")
        return
    
    # 询问处理数量和批大小
    max_articles = input(f"要处理多少篇文章？(默认全部{total_articles}篇，输入数字限制数量): ").strip()
    if max_articles.isdigit():
        max_articles = int(max_articles)
    else:
        max_articles = None
    
    batch_size = input("批处理大小？(默认20篇/次，输入数字修改): ").strip()
    if batch_size.isdigit():
        batch_size = int(batch_size)
    else:
        batch_size = 20
    
    # 定义所有类别的配置
    categories_config = [
        ("项目融资", project_funding_articles, "project"),
        ("基金融资", fund_funding_articles, "fund"),
        ("公链/L2/主网", blockchain_articles, "blockchain"),
        ("中间件/工具协议", middleware_articles, "middleware"),
        ("DeFi", defi_articles, "defi"),
        ("RWA", rwa_articles, "rwa"),
        ("NFT", nft_articles, "nft"),
        ("GameFi", gamefi_articles, "gamefi"),
        ("Metaverse/Web3社交", metaverse_articles, "metaverse"),
        ("交易所/钱包", exchange_wallet_articles, "exchange_wallet"),
        ("AI + Crypto", ai_crypto_articles, "ai_crypto"),
        ("DePIN", depin_articles, "depin")
    ]
    
    # 统一筛选各类文章
    filtered_results = {}
    dedup_stats = {}
    
    for category_name, articles, article_type in categories_config:
        if articles:
            print(f"\n🎯 开始筛选{category_name}文章...")
            # 先进行AI筛选
            ai_filtered = filter.batch_filter(articles, batch_size, max_articles, article_type)
            
            # 再进行标题去重
            if ai_filtered:
                print(f"\n🔄 对{category_name}进行标题去重...")
                deduplicated, dedup_stat = filter.deduplicate_articles_by_title(ai_filtered, category_name)
                filtered_results[article_type] = deduplicated
                dedup_stats[category_name] = dedup_stat
            else:
                filtered_results[article_type] = []
                dedup_stats[category_name] = {'removed_count': 0, 'duplicate_groups': [], 'removal_rate': 0}
        else:
            filtered_results[article_type] = []
            dedup_stats[category_name] = {'removed_count': 0, 'duplicate_groups': [], 'removal_rate': 0}
    
    # Portfolio文章不需要AI筛选，但需要去重
    if portfolio_articles:
        print(f"\n⭐ Portfolio文章无需AI筛选，直接进行标题去重...")
        deduplicated_portfolio, portfolio_dedup_stat = filter.deduplicate_articles_by_title(portfolio_articles, "Portfolio")
        filtered_results["portfolio"] = deduplicated_portfolio
        dedup_stats["Portfolio"] = portfolio_dedup_stat
    else:
        filtered_results["portfolio"] = []
        dedup_stats["Portfolio"] = {'removed_count': 0, 'duplicate_groups': [], 'removal_rate': 0}
    
    # 跨板块去重：优先级 Portfolio > 项目融资 > 基金融资 > 其他板块
    print(f"\n🔄 执行跨板块去重...")
    filtered_results, cross_dedup_stats = filter.cross_category_deduplication(filtered_results)
    

    
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

        # 使用全局编号
        global_counter = 1
        
        # 使用循环处理所有分类的输出
        output_sections = [
            ("项目融资", filtered_results.get("project", []), "2. 项目融资介绍"),
            ("基金融资", filtered_results.get("fund", []), "3. 基金融资介绍"),
            ("公链/L2/主网", filtered_results.get("blockchain", []), "4. 公链/L2/主网"),
            ("中间件/工具协议", filtered_results.get("middleware", []), "5. 中间件/工具协议"),
            ("DeFi", filtered_results.get("defi", []), "6. DeFi"),
            ("RWA", filtered_results.get("rwa", []), "7. RWA"),
            ("NFT", filtered_results.get("nft", []), "8. NFT"),
            ("GameFi", filtered_results.get("gamefi", []), "9. GameFi"),
            ("Metaverse/Web3社交", filtered_results.get("metaverse", []), "10. Metaverse/Web3社交"),
            ("交易所/钱包", filtered_results.get("exchange_wallet", []), "11. 交易所/钱包"),
            ("AI + Crypto", filtered_results.get("ai_crypto", []), "12. AI + Crypto"),
            ("DePIN", filtered_results.get("depin", []), "13. DePIN")
        ]
        
        for category_name, articles_list, section_title in output_sections:
            if articles_list:
                f.write(f"# {section_title}\n\n")
                for article in delete_reports(articles_list):
                    title = article['title']
                    url = article['url']
                    content = clean_content(article.get('content_text', ''))
                    
                    f.write(f"{global_counter}. [{title}]({url})\n\n{content}\n\n")
                    global_counter += 1
        
        # Portfolio板块
        if filtered_results["portfolio"]:
            f.write("# 14. Our portfolio (这里标红的在公众号编辑时对应标红即可)\n\n")
            for article in delete_reports(filtered_results["portfolio"]):
                title = article['title']
                url = article['url']
                content = clean_content(article.get('content_text', ''))
                
                f.write(f"{global_counter}. [{title}]({url})\n\n{content}\n\n")
                global_counter += 1
    
    print(f"📋 格式化输出已保存到: {formatted_output_file}")
    print(f"\n🎯 AI筛选 + 标题去重 + 跨板块去重完成！")
    
    # 统计输出，使用循环
    stats_config = [
        ("项目融资", project_funding_articles, "project"),
        ("基金融资", fund_funding_articles, "fund"),
        ("公链/L2/主网", blockchain_articles, "blockchain"),
        ("中间件/工具协议", middleware_articles, "middleware"),
        ("DeFi", defi_articles, "defi"),
        ("RWA", rwa_articles, "rwa"),
        ("NFT", nft_articles, "nft"),
        ("GameFi", gamefi_articles, "gamefi"),
        ("Metaverse/Web3社交", metaverse_articles, "metaverse"),
        ("交易所/钱包", exchange_wallet_articles, "exchange_wallet"),
        ("AI + Crypto", ai_crypto_articles, "ai_crypto"),
        ("DePIN", depin_articles, "depin"),
        ("Portfolio", portfolio_articles, "portfolio")
    ]
    
    for category_name, original_articles, result_key in stats_config:
        filtered_count = len(filtered_results.get(result_key, []))
        dedup_removed = dedup_stats.get(category_name, {}).get('removed_count', 0)
        cross_removed = cross_dedup_stats.get(category_name, {}).get('removed_count', 0)
        
        removal_info = []
        if dedup_removed > 0:
            removal_info.append(f"标题去重{dedup_removed}篇")
        if cross_removed > 0:
            removal_info.append(f"跨板块去重{cross_removed}篇")
            
        if removal_info:
            removal_str = f" ({', '.join(removal_info)})"
            print(f"   {category_name}: {len(original_articles)} → {filtered_count} 篇{removal_str}")
        else:
            print(f"   {category_name}: {len(original_articles)} → {filtered_count} 篇")
    
    # 计算总计
    total_original = sum(len(articles) for _, articles, _ in stats_config)
    total_filtered = sum(len(filtered_results.get(result_key, [])) for _, _, result_key in stats_config)
    total_dedup_removed = sum(dedup_stats.get(cat_name, {}).get('removed_count', 0) for cat_name, _, _ in stats_config)
    total_cross_removed = sum(cross_dedup_stats.get(cat_name, {}).get('removed_count', 0) for cat_name, _, _ in stats_config)
    
    print(f"   总计: {total_original} → {total_filtered} 篇")
    
    if total_dedup_removed > 0 or total_cross_removed > 0:
        print(f"\n📊 去重统计汇总:")
        if total_dedup_removed > 0:
            print(f"   标题去重删除: {total_dedup_removed} 篇 ({(total_dedup_removed / total_original * 100):.1f}%)")
        if total_cross_removed > 0:
            print(f"   跨板块去重删除: {total_cross_removed} 篇 ({(total_cross_removed / total_original * 100):.1f}%)")
        print(f"   总去重删除: {total_dedup_removed + total_cross_removed} 篇 ({((total_dedup_removed + total_cross_removed) / total_original * 100):.1f}%)")
    
    
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
    
    # 预览输出前3个有内容的类别
    preview_sections = [
        ("项目融资", "2. 项目融资介绍 (后续需加上项目类别并删除前缀，不要写据XX报道）", "project"),
        ("基金融资", "3. 基金融资介绍", "fund"),
        ("Portfolio", "14. Our portfolio (这里标红的在公众号编辑时对应标红即可)", "portfolio")
    ]
    
    for category_name, section_title, result_key in preview_sections:
        articles_list = filtered_results.get(result_key, [])
        if articles_list:
            print(f"\n# {section_title}")
            for i, article in enumerate(articles_list[:2], 1):
                title = article['title']
                url = article['url']
                content = clean_content_preview(article.get('content_text', ''))
                preview_content = content[:150] + "..." if len(content) > 150 else content
                
                if result_key == "portfolio":
                    mentioned = article.get('mentioned_projects', [])
                    mentioned_str = f" [{', '.join(mentioned)}]" if mentioned else ""
                    print(f"\n{i}.[{title}]({url}){mentioned_str}")
                else:
                    print(f"\n{i}.[{title}]({url})")
                print(f"{preview_content}")

if __name__ == "__main__":
    main()