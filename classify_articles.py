#!/usr/bin/env python3
"""
加密货币文章分类器
根据关键词对文章进行分类
"""

import json
import os
import re
import yaml
from datetime import datetime
from collections import defaultdict

class CryptoArticleClassifier:
    def __init__(self):
        # 从YAML配置文件加载配置
        self.config = self._load_config()
        self.portfolios = self.config.get('portfolio_projects', [])
        self.categories = self.config.get('classification', {}).get('categories', {})
        self.title_exclusion_keywords = self.config.get('content_filters', {}).get('title_exclusion_keywords', [])

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
            return self._get_default_config()
        except Exception as e:
            print(f"❌ 加载配置失败: {e}，使用默认配置")
            return self._get_default_config()

    def _get_default_config(self):
        """返回默认配置（作为fallback）"""
        return {
            'portfolio_projects': [],
            'classification': {'categories': {}},
            'content_filters': {'title_exclusion_keywords': []}
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
    # 读取最新的feeds文件
    input_file = "latest_feeds.json"
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ 文件 {input_file} 不存在")
        print("请先运行 python fetch_specific_feeds.py")
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
    
    # 创建分类器
    classifier = CryptoArticleClassifier()
    
    # 使用YAML配置中的标题关键词筛选
    title_keywords = classifier.title_exclusion_keywords
    
    if title_keywords:
        print(f"\n=== 应用标题关键词过滤 ===")
        print(f"排除关键词: {len(title_keywords)} 个")
        
        original_count = len(articles)
        # 标题关键词筛选 - 只保留标题不包含任何关键词的文章
        articles = [
            article for article in articles 
            if not any(keyword.lower() in article.get('title', '').lower() for keyword in title_keywords)
        ]
        filtered_count = len(articles)
        
        print(f"原始文章数: {original_count}")
        print(f"过滤后文章数: {filtered_count}")
        print(f"过滤掉: {original_count - filtered_count} 篇（包含排除关键词）")
    
    # 进行分类
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
    
    # 保存分类结果到固定文件
    output_file = "latest_classified.json"
    historical_classified_file = "historical_classified.json"
    
    # 如果存在旧的分类文件，将其归档到历史文件
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                old_classified_data = json.load(f)
            
            # 读取或创建历史分类文件
            historical_classified = {'all_articles': []}
            if os.path.exists(historical_classified_file):
                try:
                    with open(historical_classified_file, 'r', encoding='utf-8') as f:
                        loaded_data = json.load(f)
                    
                    # 检查文件格式
                    if 'all_articles' in loaded_data:
                        # 新格式，直接使用
                        historical_classified = loaded_data
                    elif 'articles' in loaded_data:
                        # 旧格式，提取文章数据
                        print("🔄 转换旧格式历史分类文件...")
                        historical_classified = {'all_articles': loaded_data['articles']}
                    else:
                        # 其他格式，创建新的
                        historical_classified = {'all_articles': []}
                        
                except Exception as e:
                    print(f"⚠️ 历史分类文件读取失败: {e}，将创建新文件")
                    historical_classified = {'all_articles': []}
            
            # 将旧的分类数据的所有文章添加到历史记录
            old_articles = old_classified_data.get('articles', [])
            if old_articles:
                # 给每个文章添加分类批次标识
                batch_id = old_classified_data['metadata']['classification_date']
                for article in old_articles:
                    article['classification_batch_id'] = batch_id
                
                # 合并到历史文章列表
                historical_classified['all_articles'].extend(old_articles)
                print(f"📚 已将 {len(old_articles)} 篇分类文章归档到历史文件")
            
            # 更新历史分类文件元数据
            historical_classified['last_updated'] = datetime.now().isoformat()
            historical_classified['total_articles'] = len(historical_classified['all_articles'])
            
            with open(historical_classified_file, 'w', encoding='utf-8') as f:
                json.dump(historical_classified, f, ensure_ascii=False, indent=2)
            
            print(f"📚 历史分类文件已更新，共包含 {historical_classified['total_articles']} 篇分类文章")
            
        except Exception as e:
            print(f"⚠️ 归档旧分类数据时出错: {e}")
    
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
    
    # 输出分类结果
    print(f"\n🎯 分类完成！共处理 {len(classified_articles)} 篇文章")

if __name__ == "__main__":
    main()