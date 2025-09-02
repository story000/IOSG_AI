"""Enhanced AI-powered deduplication with hierarchical processing"""

import asyncio
import aiohttp
import hashlib
import json
import time
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np

# Try to import OpenAI client
try:
    from openai import OpenAI, AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    print("⚠️ OpenAI not available, AI deduplication will be disabled")
    OPENAI_AVAILABLE = False

# Import TF-IDF for fallback
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


@dataclass
class AIDeduplicationStats:
    """Statistics for AI deduplication operations"""
    total_articles: int = 0
    processed_articles: int = 0
    ai_removed: int = 0
    fallback_removed: int = 0
    api_calls: int = 0
    processing_time: float = 0.0
    method_used: str = ""
    duplicate_groups: List = field(default_factory=list)
    category_stats: Dict = field(default_factory=dict)
    
    @property
    def total_removed(self) -> int:
        return self.ai_removed + self.fallback_removed
    
    @property
    def removal_rate(self) -> float:
        if self.total_articles == 0:
            return 0.0
        return (self.total_removed / self.total_articles) * 100


class EnhancedAIDeduplicationService:
    """Enhanced AI deduplication with hierarchical processing and fallback mechanisms"""
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 provider: str = "openai",
                 similarity_threshold: float = 0.7,
                 ai_batch_size: int = 100,
                 max_retries: int = 3,
                 timeout: int = 30,
                 enable_fallback: bool = True):
        
        self.api_key = api_key
        self.provider = provider.lower()
        self.similarity_threshold = similarity_threshold
        self.ai_batch_size = ai_batch_size
        self.max_retries = max_retries
        self.timeout = timeout
        self.enable_fallback = enable_fallback
        
        # Initialize API client
        self.client = None
        self.async_client = None
        
        if OPENAI_AVAILABLE and api_key:
            if provider == "deepseek":
                self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
                self.async_client = AsyncOpenAI(api_key=api_key, base_url="https://api.deepseek.com")
                self.model = "deepseek-chat"
            else:
                self.client = OpenAI(api_key=api_key)
                self.async_client = AsyncOpenAI(api_key=api_key)
                self.model = "gpt-4o-mini"
        else:
            print("⚠️ AI deduplication disabled - no API key provided or OpenAI not available")
        
        # Fallback TF-IDF vectorizer
        if self.enable_fallback and SKLEARN_AVAILABLE:
            self.tfidf_vectorizer = TfidfVectorizer(
                ngram_range=(1, 2),
                max_features=5000,
                lowercase=True
            )
        
        # Category priority mapping
        self.category_priorities = {
            "portfolios": 1,
            "项目融资": 2,
            "基金融资": 3,
            "公链/L2/主网": 4,
            "中间件/工具协议": 5,
            "DeFi": 6,
            "RWA": 7,
            "稳定币": 8,
            "应用协议": 9,
            "GameFi": 10,
            "交易所/钱包": 11,
            "AI + Crypto": 12,
            "DePIN": 13
        }
        
        print(f"✅ Enhanced AI Deduplication Service initialized")
        print(f"   - Provider: {provider}")
        print(f"   - Model: {getattr(self, 'model', 'N/A')}")
        print(f"   - AI enabled: {self.client is not None}")
        print(f"   - Fallback enabled: {enable_fallback}")
    
    async def hierarchical_ai_deduplication(self, filtered_results: Dict[str, List[Dict]]) -> Tuple[Dict, AIDeduplicationStats]:
        """
        Hierarchical AI deduplication with category-level and cross-category processing
        """
        start_time = time.time()
        stats = AIDeduplicationStats()
        
        print("\n🤖 Starting hierarchical AI deduplication...")
        
        # Phase 1: Collect all articles with metadata
        all_articles = self._collect_articles_with_metadata(filtered_results)
        stats.total_articles = len(all_articles)
        
        if len(all_articles) <= 1:
            stats.processing_time = time.time() - start_time
            return filtered_results, stats
        
        print(f"   📊 Processing {len(all_articles)} articles across {len(filtered_results)} categories")
        
        # Phase 2: Category-level AI deduplication
        if self.client:
            print("   🔍 Phase 2: Category-level AI deduplication")
            category_results = await self._ai_category_deduplication(all_articles, stats)
        else:
            print("   🔍 Phase 2: Fallback category-level deduplication")
            category_results = self._fallback_category_deduplication(all_articles, stats)
        
        # Phase 3: Cross-category deduplication  
        print("   🔄 Phase 3: Cross-category priority-based deduplication")
        final_results = self._cross_category_deduplication(category_results, stats)
        
        # Phase 4: Apply results back to original structure
        updated_results = self._apply_deduplication_results(filtered_results, final_results)
        
        stats.processing_time = time.time() - start_time
        stats.method_used = "hierarchical_ai" if self.client else "hierarchical_fallback"
        
        # Print summary
        print(f"   ✅ Hierarchical deduplication complete:")
        print(f"      Total processed: {stats.total_articles} articles") 
        print(f"      AI removed: {stats.ai_removed} articles")
        print(f"      Fallback removed: {stats.fallback_removed} articles")
        print(f"      API calls: {stats.api_calls}")
        print(f"      Processing time: {stats.processing_time:.2f}s")
        print(f"      Method: {stats.method_used}")
        
        return updated_results, stats
    
    def _collect_articles_with_metadata(self, filtered_results: Dict[str, List[Dict]]) -> List[Dict]:
        """Collect all articles with category metadata"""
        all_articles = []
        article_id = 1
        
        for category_key, articles in filtered_results.items():
            priority = self.category_priorities.get(category_key, 999)
            
            for i, article in enumerate(articles):
                enhanced_article = {
                    'id': f"ID{article_id}",
                    'title': article.get('title', ''),
                    'content': article.get('content', ''),
                    'category_key': category_key,
                    'category_priority': priority,
                    'original_index': i,
                    'article_data': article,
                    'keep': True  # Default to keep
                }
                all_articles.append(enhanced_article)
                article_id += 1
        
        return all_articles
    
    async def _ai_category_deduplication(self, articles: List[Dict], stats: AIDeduplicationStats) -> List[Dict]:
        """AI-powered category-level deduplication"""
        
        # Group articles by category
        category_groups = {}
        for article in articles:
            category = article['category_key']
            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(article)
        
        # Process each category
        processed_articles = []
        
        for category, category_articles in category_groups.items():
            if len(category_articles) <= 1:
                processed_articles.extend(category_articles)
                continue
            
            print(f"      🔍 Processing {category}: {len(category_articles)} articles")
            
            try:
                # Try AI deduplication for this category
                if len(category_articles) <= self.ai_batch_size:
                    dedup_articles = await self._ai_deduplicate_batch(category_articles, category, stats)
                else:
                    # Split into smaller batches
                    dedup_articles = await self._ai_deduplicate_large_category(category_articles, category, stats)
                
                processed_articles.extend(dedup_articles)
                
            except Exception as e:
                print(f"         ⚠️ AI deduplication failed for {category}: {e}")
                # Fallback to TF-IDF if available
                if self.enable_fallback:
                    dedup_articles = self._fallback_deduplicate_category(category_articles, stats)
                    processed_articles.extend(dedup_articles)
                else:
                    processed_articles.extend(category_articles)
        
        return processed_articles
    
    async def _ai_deduplicate_batch(self, articles: List[Dict], category: str, stats: AIDeduplicationStats) -> List[Dict]:
        """AI deduplication for a single batch"""
        
        # Build prompt
        articles_text = ""
        for article in articles:
            articles_text += f"\n{article['id']}: {article['title']}"
        
        prompt = f"""请分析以下{len(articles)}篇{category}类别的加密货币新闻标题，找出描述同一事件的重复文章组。

判断标准：
1. 同一公司的同一笔融资/投资
2. 同一产品的同一次发布/上线  
3. 同一事件的不同表述但本质相同
4. 融资金额、时间、参与方必须基本一致

返回格式：JSON数组，包含重复组的ID列表
如果没有重复，返回：[]
示例：[["ID1","ID2"],["ID3","ID4","ID5"]]

文章列表：{articles_text}"""

        try:
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0
            )
            
            stats.api_calls += 1
            result = response.choices[0].message.content.strip()
            
            # Parse AI response
            duplicate_groups = self._parse_ai_response(result)
            
            # Apply deduplication
            return self._apply_ai_deduplication(articles, duplicate_groups, stats)
            
        except Exception as e:
            print(f"         ❌ AI API call failed: {e}")
            raise
    
    async def _ai_deduplicate_large_category(self, articles: List[Dict], category: str, stats: AIDeduplicationStats) -> List[Dict]:
        """AI deduplication for large categories using batching"""
        
        # Split into batches
        batches = []
        for i in range(0, len(articles), self.ai_batch_size):
            batch = articles[i:i + self.ai_batch_size]
            batches.append(batch)
        
        print(f"         📦 Processing {len(batches)} batches for {category}")
        
        # Process batches concurrently  
        processed_batches = []
        semaphore = asyncio.Semaphore(3)  # Limit concurrent requests
        
        async def process_batch(batch):
            async with semaphore:
                return await self._ai_deduplicate_batch(batch, category, stats)
        
        batch_results = await asyncio.gather(*[process_batch(batch) for batch in batches])
        
        # Combine results
        all_processed = []
        for batch_result in batch_results:
            all_processed.extend(batch_result)
        
        return all_processed
    
    def _fallback_category_deduplication(self, articles: List[Dict], stats: AIDeduplicationStats) -> List[Dict]:
        """Fallback category-level deduplication using TF-IDF"""
        
        # Group by category
        category_groups = {}
        for article in articles:
            category = article['category_key']
            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(article)
        
        processed_articles = []
        
        for category, category_articles in category_groups.items():
            if len(category_articles) <= 1:
                processed_articles.extend(category_articles)
                continue
            
            print(f"      🔄 Fallback processing {category}: {len(category_articles)} articles")
            dedup_articles = self._fallback_deduplicate_category(category_articles, stats)
            processed_articles.extend(dedup_articles)
        
        return processed_articles
    
    def _fallback_deduplicate_category(self, articles: List[Dict], stats: AIDeduplicationStats) -> List[Dict]:
        """TF-IDF based fallback deduplication for a category"""
        
        if not SKLEARN_AVAILABLE or len(articles) <= 1:
            return articles
        
        try:
            # Extract titles
            titles = [self._clean_title(a['title']) for a in articles]
            
            # TF-IDF vectorization
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(titles)
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            # Find duplicates
            keep_indices = set(range(len(articles)))
            removed_count = 0
            
            for i in range(len(articles)):
                if i not in keep_indices:
                    continue
                    
                for j in range(i + 1, len(articles)):
                    if j not in keep_indices:
                        continue
                        
                    if similarity_matrix[i, j] >= self.similarity_threshold:
                        keep_indices.remove(j)
                        removed_count += 1
            
            stats.fallback_removed += removed_count
            return [articles[i] for i in sorted(keep_indices)]
            
        except Exception as e:
            print(f"         ⚠️ Fallback deduplication failed: {e}")
            return articles
    
    def _cross_category_deduplication(self, articles: List[Dict], stats: AIDeduplicationStats) -> List[Dict]:
        """Cross-category deduplication based on priority"""
        
        # Sort by category priority
        articles.sort(key=lambda x: (x['category_priority'], x['id']))
        
        seen_titles = set()
        final_articles = []
        removed_count = 0
        
        for article in articles:
            if not article['keep']:  # Already marked for removal
                continue
                
            clean_title = self._clean_title(article['title'])
            title_hash = hashlib.md5(clean_title.encode('utf-8')).hexdigest()
            
            # Check for exact matches first
            if title_hash in seen_titles:
                removed_count += 1
                continue
            
            # Check for similarity matches
            is_duplicate = False
            for seen_title in seen_titles:
                if self._calculate_similarity(clean_title, seen_title) >= self.similarity_threshold:
                    is_duplicate = True
                    removed_count += 1
                    break
            
            if not is_duplicate:
                seen_titles.add(title_hash)
                final_articles.append(article)
        
        print(f"      📊 Cross-category removed {removed_count} duplicates")
        return final_articles
    
    def _apply_deduplication_results(self, original_results: Dict[str, List[Dict]], 
                                   final_articles: List[Dict]) -> Dict[str, List[Dict]]:
        """Apply deduplication results back to original structure"""
        
        # Group final articles by category
        category_results = {}
        for article in final_articles:
            category = article['category_key']
            if category not in category_results:
                category_results[category] = []
            category_results[category].append(article['article_data'])
        
        # Update original results
        updated_results = {}
        for category in original_results.keys():
            updated_results[category] = category_results.get(category, [])
        
        return updated_results
    
    def _parse_ai_response(self, response: str) -> List[List[str]]:
        """Parse AI response to extract duplicate groups"""
        try:
            # Try to find JSON array in response
            import re
            
            # Look for JSON array pattern
            json_pattern = r'\[.*?\]'
            match = re.search(json_pattern, response, re.DOTALL)
            
            if match:
                json_str = match.group(0)
                groups = json.loads(json_str)
                
                # Validate format
                if isinstance(groups, list):
                    valid_groups = []
                    for group in groups:
                        if isinstance(group, list) and len(group) >= 2:
                            valid_groups.append(group)
                    return valid_groups
            
            return []
            
        except Exception as e:
            print(f"         ⚠️ Failed to parse AI response: {e}")
            print(f"         Response: {response}")
            return []
    
    def _apply_ai_deduplication(self, articles: List[Dict], duplicate_groups: List[List[str]], 
                              stats: AIDeduplicationStats) -> List[Dict]:
        """Apply AI deduplication results"""
        
        if not duplicate_groups:
            return articles
        
        # Create ID to article mapping
        id_to_article = {a['id']: a for a in articles}
        remove_ids = set()
        
        # Process each duplicate group
        for group in duplicate_groups:
            if len(group) < 2:
                continue
                
            # Keep the first article in each group, remove others
            for article_id in group[1:]:
                if article_id in id_to_article:
                    remove_ids.add(article_id)
        
        # Filter out removed articles
        kept_articles = []
        for article in articles:
            if article['id'] not in remove_ids:
                kept_articles.append(article)
        
        removed_count = len(articles) - len(kept_articles)
        stats.ai_removed += removed_count
        
        print(f"         ✅ AI removed {removed_count} articles from {len(duplicate_groups)} groups")
        
        return kept_articles
    
    def _clean_title(self, title: str) -> str:
        """Clean title for comparison"""
        import re
        title = title.lower()
        title = re.sub(r'[^\w\s]', ' ', title)
        title = re.sub(r'\s+', ' ', title).strip()
        return title
    
    def _calculate_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between two titles"""
        import difflib
        return difflib.SequenceMatcher(None, title1, title2).ratio()
    
    def get_stats(self) -> Dict:
        """Get service statistics"""
        return {
            'provider': self.provider,
            'model': getattr(self, 'model', 'N/A'),
            'ai_enabled': self.client is not None,
            'fallback_enabled': self.enable_fallback,
            'batch_size': self.ai_batch_size,
            'similarity_threshold': self.similarity_threshold,
            'openai_available': OPENAI_AVAILABLE,
            'sklearn_available': SKLEARN_AVAILABLE
        }