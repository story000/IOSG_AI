#!/usr/bin/env python3
"""
获取指定feeds的所有未读文章并保存为JSON
"""

from inoreader_client import InoreaderClient
import json
from datetime import datetime, timedelta
import re

def clean_html(html_content):
    """简单清理HTML标签"""
    if not html_content:
        return ""
    # 移除HTML标签
    clean = re.sub(r'<[^>]+>', '', html_content)
    # 解码HTML实体
    import html
    clean = html.unescape(clean)
    # 移除多余空白
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean

def format_article(article):
    """格式化文章信息"""
    # 基本信息
    formatted = {
        'id': article.get('id', ''),
        'title': article.get('title', ''),
        'author': article.get('author', ''),
        'published': article.get('published', 0),
        'published_formatted': '',
        'updated': article.get('updated', 0),
        'url': '',
        'feed_title': '',
        'feed_url': '',
        'content': '',
        'content_text': '',
        'categories': article.get('categories', [])
    }
    
    # 格式化发布时间
    try:
        if formatted['published']:
            dt = datetime.fromtimestamp(formatted['published'])
            formatted['published_formatted'] = dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        pass
    
    # 获取文章URL
    canonical = article.get('canonical', [])
    if canonical:
        formatted['url'] = canonical[0].get('href', '')
    
    # 获取feed信息
    origin = article.get('origin', {})
    formatted['feed_title'] = origin.get('title', '')
    formatted['feed_url'] = origin.get('streamId', '')
    
    # 获取内容
    summary = article.get('summary', {})
    content = summary.get('content', '')
    formatted['content'] = content
    formatted['content_text'] = clean_html(content)
    
    return formatted

def main():
    import glob
    import os
    
    # 检查是否已存在feeds文件
    existing_files = glob.glob("crypto_feeds_unread_*.json")
    if existing_files:
        latest_file = max(existing_files, key=os.path.getctime)
        file_time = datetime.fromtimestamp(os.path.getctime(latest_file))
        time_diff = datetime.now() - file_time
        
        print(f"=== 发现已存在的feeds文件 ===")
        print(f"📄 文件: {latest_file}")
        print(f"🕒 创建时间: {file_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏰ 距离现在: {time_diff}")

        # 如果文件创建时间在24小时内，直接使用现有文件
        if time_diff.total_seconds() < 86400:  
            print("✅ 文件较新（24小时内），直接使用现有文件，跳过下载")
            return
        else:
            print("⚠️ 文件较旧，将重新下载最新feeds")
    
    # 目标feeds
    target_feeds = [
        "feed/https://rss.panewslab.com/zh/gtimg/rss",
        "feed/https://www.techflowpost.com/rss.aspx", 
        "feed/https://wublockchain123.substack.com/feed",
        "feed/https://cn.cointelegraph.com/rss"
    ]
    
    feed_names = {
        "feed/https://rss.panewslab.com/zh/gtimg/rss": "PANews",
        "feed/https://www.techflowpost.com/rss.aspx": "TechFlow",
        "feed/https://wublockchain123.substack.com/feed": "Wu Blockchain",
        "feed/https://cn.cointelegraph.com/rss": "Cointelegraph中文"
    }
    
    CLIENT_ID = "1000001559"
    CLIENT_SECRET = "lDyl2_XuuueJYcFZOwNipRy79_TibMOH"
    
    # 创建客户端
    client = InoreaderClient(CLIENT_ID, CLIENT_SECRET)
    
    if not client.is_authenticated():
        print("⚠️ 需要认证，请运行 smart_client.py 先进行认证")
        return
    
    print("=== 获取指定Feeds的未读文章 ===")
    print(f"目标feeds: {len(target_feeds)} 个")
    for feed_id in target_feeds:
        feed_name = feed_names.get(feed_id, feed_id)
        print(f"  📰 {feed_name}")
    
    all_articles = []
    feed_stats = {}
    
    for feed_id in target_feeds:
        feed_name = feed_names.get(feed_id, feed_id)
        print(f"\n正在获取 {feed_name} 的未读文章...")
        
        try:
            # 获取该feed的所有未读文章
            result = client.get_unread_articles(
                stream_id=feed_id,
                max_articles=None,  # 获取所有未读文章
                include_read=False
            )
            
            articles = result['articles']
            count = len(articles)
            
            print(f"✓ {feed_name}: 找到 {count} 篇未读文章")
            
            # 格式化文章并添加feed标识
            for article in articles:
                formatted_article = format_article(article)
                formatted_article['source_feed'] = feed_name
                formatted_article['source_feed_id'] = feed_id
                all_articles.append(formatted_article)
            
            feed_stats[feed_name] = count
            
        except Exception as e:
            print(f"✗ {feed_name}: 获取失败 - {e}")
            feed_stats[feed_name] = 0
    
    # 统计结果
    total_articles = len(all_articles)
    print(f"\n=== 获取完成 ===")
    print(f"总计: {total_articles} 篇未读文章")
    
    for feed_name, count in feed_stats.items():
        print(f"  📰 {feed_name}: {count} 篇")
    
    if total_articles == 0:
        print("🎉 所有指定feeds都没有未读文章！")
        return
    
    # 过滤近7天内的文章
    seven_days_ago = datetime.now() - timedelta(days=7)
    seven_days_timestamp = seven_days_ago.timestamp()
    
    print(f"\n=== 应用7天时间过滤 ===")
    print(f"过滤基准时间: {seven_days_ago.strftime('%Y-%m-%d %H:%M:%S')}")
    
    original_count = len(all_articles)
    all_articles = [article for article in all_articles if article.get('published', 0) >= seven_days_timestamp]
    filtered_count = len(all_articles)
    
    print(f"原始文章数: {original_count}")
    print(f"过滤后文章数: {filtered_count}")
    print(f"过滤掉: {original_count - filtered_count} 篇（超过7天）")
    
    # 按发布时间排序（最新的在前）
    all_articles.sort(key=lambda x: x.get('published', 0), reverse=True)
    
    # 显示最新的几篇文章
    print(f"\n=== 最新 {min(5, filtered_count)} 篇文章预览 ===")
    for i, article in enumerate(all_articles[:5], 1):
        print(f"\n{i}. 【{article['source_feed']}】{article['title']}")
        print(f"   作者: {article['author'] or '未知'}")
        print(f"   时间: {article['published_formatted']}")
        print(f"   链接: {article['url']}")
        if article['content_text']:
            preview = article['content_text'][:100] + "..." if len(article['content_text']) > 100 else article['content_text']
            print(f"   预览: {preview}")
    
    # 保存到固定的JSON文件
    latest_filename = "latest_feeds.json"
    historical_filename = "historical_feeds.json"
    
    # 准备保存的数据
    save_data = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'total_articles': filtered_count,
            'original_total': original_count,
            'filtered_out': original_count - filtered_count,
            'filter_days': 7,
            'filter_cutoff': seven_days_ago.isoformat(),
            'feeds_stats': feed_stats,
            'target_feeds': list(feed_names.values())
        },
        'articles': all_articles
    }
    
    # 如果存在旧的最新文件，将其合并到历史文件中
    if os.path.exists(latest_filename):
        try:
            with open(latest_filename, 'r', encoding='utf-8') as f:
                old_latest_data = json.load(f)
            
            # 读取或创建历史文件
            historical_data = {'batches': []}
            if os.path.exists(historical_filename):
                try:
                    with open(historical_filename, 'r', encoding='utf-8') as f:
                        historical_data = json.load(f)
                except:
                    print("⚠️ 历史文件读取失败，将创建新的历史文件")
                    historical_data = {'batches': []}
            
            # 将旧的最新数据添加到历史数据中
            batch_info = {
                'generated_at': old_latest_data['metadata']['generated_at'],
                'total_articles': old_latest_data['metadata']['total_articles'],
                'feeds_stats': old_latest_data['metadata']['feeds_stats']
            }
            historical_data['batches'].append(batch_info)
            
            # 保持历史记录在合理数量（最多保留50个批次）
            if len(historical_data['batches']) > 50:
                historical_data['batches'] = historical_data['batches'][-50:]
            
            # 更新历史文件
            historical_data['last_updated'] = datetime.now().isoformat()
            historical_data['total_batches'] = len(historical_data['batches'])
            
            with open(historical_filename, 'w', encoding='utf-8') as f:
                json.dump(historical_data, f, ensure_ascii=False, indent=2)
            
            print(f"📚 旧数据已归档到历史文件 ({len(historical_data['batches'])} 个批次)")
            
        except Exception as e:
            print(f"⚠️ 归档旧数据时出错: {e}")
    
    # 保存新的最新数据
    with open(latest_filename, 'w', encoding='utf-8') as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 最新数据已保存到: {latest_filename}")
    print(f"📊 文件包含 {filtered_count} 篇文章的完整信息（近7天内）")
    
    # 询问是否标记为已读
    if filtered_count > 0:
        print(f"\n❓ 是否将这 {filtered_count} 篇文章标记为已读？")
        choice = input("输入 'y' 确认，其他键跳过: ").lower().strip()
        
        if choice == 'y':
            print("正在标记文章为已读...")
            try:
                # 逐个标记为已读
                success_count = 0
                for article in all_articles:
                    try:
                        client.mark_article_as_read(article['id'])
                        success_count += 1
                    except Exception as e:
                        print(f"标记失败: {article['title']} - {e}")
                
                print(f"✓ 成功标记 {success_count}/{filtered_count} 篇文章为已读")
                
            except Exception as e:
                print(f"✗ 批量标记失败: {e}")
        else:
            print("跳过标记已读")
    
    print("\n🎯 任务完成！")

if __name__ == "__main__":
    main()