#!/usr/bin/env python3
"""
标题相似度去重测试脚本
对 formatted txt 文件中的文章标题进行相似度计算，筛选掉相似度大于80%的重复文章
"""

import re
import difflib
from collections import defaultdict
import argparse
import os


class TitleDeduplicator:
    def __init__(self, similarity_threshold=0.8):
        """
        初始化去重器
        :param similarity_threshold: 相似度阈值，默认0.8(80%)
        """
        self.similarity_threshold = similarity_threshold
        
    def clean_title(self, title):
        """
        清理标题，移除多余的符号和空格
        """
        # 移除链接格式 [title](url)
        title = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', title)
        # 移除多余空格和标点
        title = re.sub(r'\s+', ' ', title).strip()
        # 移除常见的新闻前缀
        title = re.sub(r'^\d+\.\s*', '', title)  # 移除序号
        return title
        
    def calculate_similarity(self, title1, title2):
        """
        计算两个标题的相似度
        使用 difflib.SequenceMatcher 计算字符串相似度
        """
        # 清理标题
        clean_title1 = self.clean_title(title1).lower()
        clean_title2 = self.clean_title(title2).lower()
        
        # 计算相似度
        similarity = difflib.SequenceMatcher(None, clean_title1, clean_title2).ratio()
        return similarity
        
    def parse_formatted_file(self, file_path):
        """
        解析 formatted txt 文件，提取文章信息
        返回格式: [{'title': '', 'url': '', 'content': '', 'section': ''}, ...]
        """
        articles = []
        current_section = ""
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 按段落分割
        paragraphs = content.split('\n\n')
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
                
            # 检查是否是章节标题
            if para.startswith('#'):
                current_section = para.strip('# ').strip()
                continue
                
            # 检查是否是文章条目（以数字开头）
            if re.match(r'^\d+\.', para):
                lines = para.split('\n')
                if len(lines) >= 1:
                    # 提取标题和URL
                    title_line = lines[0]
                    url_match = re.search(r'\[([^\]]+)\]\(([^)]+)\)', title_line)
                    
                    if url_match:
                        title = url_match.group(1)
                        url = url_match.group(2)
                        # 内容是剩余的行
                        content = '\n'.join(lines[1:]).strip()
                        
                        articles.append({
                            'title': title,
                            'url': url,
                            'content': content,
                            'section': current_section,
                            'original_text': para
                        })
                        
        return articles
        
    def find_duplicates(self, articles):
        """
        找出相似度高于阈值的重复文章
        返回: (保留的文章列表, 重复文章组列表)
        """
        # 用于存储去重后的文章
        unique_articles = []
        # 用于存储重复文章组
        duplicate_groups = []
        # 已处理的文章索引
        processed = set()
        
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
                    
                similarity = self.calculate_similarity(article1['title'], article2['title'])
                
                if similarity >= self.similarity_threshold:
                    current_group.append(article2)
                    processed.add(j)
                    
            # 如果有重复文章，记录到重复组；否则添加到唯一文章
            if len(current_group) > 1:
                duplicate_groups.append(current_group)
                # 保留第一篇文章（通常是最早发布的）
                unique_articles.append(current_group[0])
            else:
                unique_articles.append(current_group[0])
                
        return unique_articles, duplicate_groups
        
    def generate_report(self, original_articles, unique_articles, duplicate_groups):
        """
        生成去重报告
        """
        print("=" * 60)
        print("📊 标题去重分析报告")
        print("=" * 60)
        
        print(f"原始文章数量: {len(original_articles)}")
        print(f"去重后文章数量: {len(unique_articles)}")
        print(f"重复文章数量: {len(original_articles) - len(unique_articles)}")
        print(f"重复文章组数: {len(duplicate_groups)}")
        print(f"去重率: {((len(original_articles) - len(unique_articles)) / len(original_articles) * 100):.1f}%")
        
        if duplicate_groups:
            print("\n" + "=" * 60)
            print("🔍 重复文章详情")
            print("=" * 60)
            
            for i, group in enumerate(duplicate_groups, 1):
                print(f"\n重复组 {i} (共{len(group)}篇文章):")
                print("-" * 40)
                
                for j, article in enumerate(group):
                    status = "✅ 保留" if j == 0 else "❌ 删除"
                    section = article.get('section', '未知分类')
                    print(f"{status} [{section}] {article['title']}")
                    
                # 显示相似度矩阵
                if len(group) > 1:
                    print("\n相似度矩阵:")
                    for k in range(len(group)):
                        for l in range(k+1, len(group)):
                            sim = self.calculate_similarity(group[k]['title'], group[l]['title'])
                            print(f"  文章{k+1} vs 文章{l+1}: {sim:.2%}")
                            
        # 按分类统计去重效果
        print("\n" + "=" * 60)
        print("📈 各分类去重统计")
        print("=" * 60)
        
        # 统计原始文章分类
        original_by_section = defaultdict(int)
        for article in original_articles:
            original_by_section[article.get('section', '未知分类')] += 1
            
        # 统计去重后文章分类
        unique_by_section = defaultdict(int)
        for article in unique_articles:
            unique_by_section[article.get('section', '未知分类')] += 1
            
        for section in sorted(original_by_section.keys()):
            original_count = original_by_section[section]
            unique_count = unique_by_section[section]
            removed_count = original_count - unique_count
            
            if original_count > 0:
                removal_rate = (removed_count / original_count) * 100
                print(f"{section}: {original_count} → {unique_count} 篇 (删除{removed_count}篇, {removal_rate:.1f}%)")
                
    def save_deduplicated_file(self, unique_articles, output_path):
        """
        保存去重后的文件
        """
        # 按分类重新组织文章
        articles_by_section = defaultdict(list)
        for article in unique_articles:
            section = article.get('section', '未知分类')
            articles_by_section[section].append(article)
            
        with open(output_path, 'w', encoding='utf-8') as f:
            global_counter = 1
            
            for section in sorted(articles_by_section.keys()):
                articles = articles_by_section[section]
                if articles:
                    f.write(f"# {section}\n\n")
                    
                    for article in articles:
                        title = article['title']
                        url = article['url']
                        content = article['content']
                        
                        f.write(f"{global_counter}. [{title}]({url})\n\n{content}\n\n")
                        global_counter += 1
                        
        print(f"\n💾 去重后的文件已保存到: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='标题相似度去重测试脚本')
    parser.add_argument('input_file', help='输入的 formatted txt 文件路径')
    parser.add_argument('--threshold', '-t', type=float, default=0.8, 
                       help='相似度阈值 (0-1), 默认0.8')
    parser.add_argument('--output', '-o', help='输出文件路径 (可选)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_file):
        print(f"❌ 文件不存在: {args.input_file}")
        return
        
    print(f"🔍 开始分析文件: {args.input_file}")
    print(f"📏 相似度阈值: {args.threshold:.0%}")
    
    # 创建去重器
    deduplicator = TitleDeduplicator(similarity_threshold=args.threshold)
    
    # 解析文件
    print("\n📖 正在解析文件...")
    articles = deduplicator.parse_formatted_file(args.input_file)
    print(f"   发现 {len(articles)} 篇文章")
    
    # 执行去重
    print("\n🔄 正在进行相似度分析...")
    unique_articles, duplicate_groups = deduplicator.find_duplicates(articles)
    
    # 生成报告
    deduplicator.generate_report(articles, unique_articles, duplicate_groups)
    
    # 保存去重后的文件
    if args.output:
        deduplicator.save_deduplicated_file(unique_articles, args.output)
    else:
        # 自动生成输出文件名
        base_name = os.path.splitext(args.input_file)[0]
        output_file = f"{base_name}_deduplicated.txt"
        deduplicator.save_deduplicated_file(unique_articles, output_file)


if __name__ == "__main__":
    main()