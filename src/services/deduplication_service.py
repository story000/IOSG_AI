"""Article deduplication service"""

import difflib
from typing import List, Dict, Tuple, Set


class DeduplicationService:
    """Service for removing duplicate articles"""
    
    def __init__(self, similarity_threshold: float = 0.7):
        self.similarity_threshold = similarity_threshold
    
    def deduplicate_by_title(self, articles: List[Dict], category_name: str = "") -> Tuple[List[Dict], Dict]:
        """Remove duplicate articles based on title similarity"""
        if not articles:
            return articles, {'removed_count': 0, 'duplicate_groups': [], 'removal_rate': 0}
        
        print(f"  🔍 Checking {len(articles)} articles for duplicates...")
        
        # Clean and normalize titles for comparison
        def clean_title(title: str) -> str:
            # Remove special characters and convert to lowercase
            import re
            title = re.sub(r'[^\w\s]', '', title.lower())
            title = re.sub(r'\s+', ' ', title).strip()
            return title
        
        # Track which articles to keep
        keep_indices = []
        seen_titles = []
        duplicate_groups = []
        
        for i, article in enumerate(articles):
            title = article.get('title', '')
            clean_current = clean_title(title)
            
            # Check against all previously seen titles
            is_duplicate = False
            for j, seen_title in enumerate(seen_titles):
                similarity = difflib.SequenceMatcher(None, clean_current, seen_title).ratio()
                if similarity >= self.similarity_threshold:
                    is_duplicate = True
                    # Add to duplicate group
                    duplicate_groups.append({
                        'original': keep_indices[j],
                        'duplicate': i,
                        'similarity': similarity
                    })
                    print(f"    ❌ Duplicate found (similarity: {similarity:.2f})")
                    print(f"       Original: {articles[keep_indices[j]]['title'][:60]}")
                    print(f"       Duplicate: {title[:60]}")
                    break
            
            if not is_duplicate:
                keep_indices.append(i)
                seen_titles.append(clean_current)
        
        # Create deduplicated list
        deduplicated = [articles[i] for i in keep_indices]
        
        # Calculate statistics
        removed_count = len(articles) - len(deduplicated)
        removal_rate = (removed_count / len(articles)) * 100 if articles else 0
        
        stats = {
            'removed_count': removed_count,
            'duplicate_groups': duplicate_groups,
            'removal_rate': removal_rate
        }
        
        if removed_count > 0:
            print(f"  ✅ Removed {removed_count} duplicates ({removal_rate:.1f}%)")
        else:
            print(f"  ✅ No duplicates found")
        
        return deduplicated, stats
    
    def cross_category_deduplication(self, filtered_results: Dict[str, List[Dict]]) -> Tuple[Dict, Dict]:
        """
        Remove duplicates across categories based on priority
        Priority: Portfolio > 项目融资 > 基金融资 > other categories
        """
        # Define priority order
        priority_order = [
            "portfolios",
            "项目融资", 
            "基金融资",
            "公链/L2/主网",
            "中间件/工具协议",
            "DeFi",
            "RWA",
            "稳定币",
            "应用协议",
            "GameFi",
            "交易所/钱包",
            "AI + Crypto",
            "DePIN"
        ]
        
        seen_titles: Set[str] = set()
        cross_dedup_stats = {}
        
        print("\n🔄 Starting cross-category deduplication...")
        
        # Process categories by priority
        for category in priority_order:
            if category not in filtered_results:
                continue
                
            articles = filtered_results[category]
            if not articles:
                cross_dedup_stats[category] = {'removed_count': 0}
                continue
            
            remaining_articles = []
            removed_count = 0
            
            for article in articles:
                # Clean title for comparison
                title = article.get('title', '')
                clean_title = self._clean_title_for_comparison(title)
                
                # Check if similar title already seen
                is_duplicate = False
                for seen_title in seen_titles:
                    similarity = difflib.SequenceMatcher(None, clean_title, seen_title).ratio()
                    if similarity >= self.similarity_threshold:
                        is_duplicate = True
                        removed_count += 1
                        print(f"  ❌ Removing from {category}: {title[:50]}...")
                        break
                
                if not is_duplicate:
                    remaining_articles.append(article)
                    seen_titles.add(clean_title)
            
            # Update results
            filtered_results[category] = remaining_articles
            cross_dedup_stats[category] = {'removed_count': removed_count}
            
            if removed_count > 0:
                print(f"  📊 {category}: {len(articles)} → {len(remaining_articles)} articles (removed {removed_count})")
        
        # Report total cross-category removals
        total_removed = sum(stats['removed_count'] for stats in cross_dedup_stats.values())
        if total_removed > 0:
            print(f"\n📊 Cross-category deduplication complete: removed {total_removed} duplicate articles")
        else:
            print(f"\n📊 Cross-category deduplication complete: no duplicates found")
        
        return filtered_results, cross_dedup_stats
    
    def _clean_title_for_comparison(self, title: str) -> str:
        """Clean and normalize title for comparison"""
        import re
        # Remove special characters and extra spaces
        title = re.sub(r'[^\w\s]', '', title.lower())
        title = re.sub(r'\s+', ' ', title).strip()
        return title