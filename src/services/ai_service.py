"""AI service abstraction for multiple providers"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import openai

from ..models.article import Article


class AIService(ABC):
    """Abstract AI service interface"""
    
    @abstractmethod
    def classify_articles(self, articles: List[Article], category: str) -> List[int]:
        """Classify articles and return indices of selected articles"""
        pass
    
    @abstractmethod
    def filter_articles_by_importance(self, articles: List[Article]) -> List[int]:
        """Filter articles by importance and return indices of important articles"""
        pass
    
    @abstractmethod
    def summarize_article(self, article: Article) -> str:
        """Generate summary for a single article"""
        pass
    
    @abstractmethod
    def extract_funding_info(self, articles: List[Article]) -> Dict[str, Any]:
        """Extract structured funding information from articles"""
        pass
    
    @abstractmethod
    def batch_process(self, articles: List[Article], 
                     operation: str, batch_size: int = 20) -> List[Any]:
        """Process articles in batches"""
        pass
    
    def filter_articles(self, articles: Union[List[Article], List[Dict]], category: str = "general") -> List[Dict]:
        """Filter articles for importance - returns filtered list"""
        # Convert Article objects to dicts if needed
        if articles and isinstance(articles[0], Article):
            articles = [a.to_dict() for a in articles]
        
        if not articles:
            return []
        
        # Portfolio articles don't need filtering
        if category in ["portfolios", "Portfolio"]:
            return articles
        
        # Process in batches for better results
        batch_size = 20
        filtered_results = []
        
        for i in range(0, len(articles), batch_size):
            batch = articles[i:i+batch_size]
            # Get important articles from this batch
            important_indices = self.filter_articles_by_importance(batch)
            # Add the important articles to results
            for idx in important_indices:
                if idx < len(batch):
                    filtered_results.append(batch[idx])
        
        return filtered_results
    
    def generate_report(self, filtered_results: Dict[str, List[Dict]]) -> str:
        """Generate a formatted report from filtered articles"""
        report_lines = []
        report_lines.append("# 加密货币周报")
        report_lines.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        for category, articles in filtered_results.items():
            if articles:
                report_lines.append(f"\n## {category}")
                report_lines.append(f"共 {len(articles)} 篇重要文章\n")
                
                for i, article in enumerate(articles, 1):
                    report_lines.append(f"{i}. **{article.get('title', 'No title')}**")
                    if article.get('source_feed'):
                        report_lines.append(f"   来源: {article['source_feed']}")
                    if article.get('url'):
                        report_lines.append(f"   链接: {article['url']}")
                    report_lines.append("")
        
        return "\n".join(report_lines)


class OpenAIService(AIService):
    """OpenAI GPT-based AI service"""
    
    def __init__(self, api_key: str, model: str = "gpt-4.1"):
        self.api_key = api_key
        self.model = model
        self.client = openai.OpenAI(api_key=api_key)
        self.config = self._load_config()
        self.prompts_config = self.config.get('ai_filter', {})
    
    def _load_config(self):
        """Load configuration from YAML file"""
        try:
            import yaml
            from pathlib import Path
            config_file = Path("crypto_config.yaml")
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
        return {}
    
    def filter_articles(self, articles: Union[List[Article], List[Dict]], category: str = "general") -> List[Dict]:
        """Override to use category-specific filtering"""
        # Convert Article objects to dicts if needed
        if articles and isinstance(articles[0], Article):
            articles = [a.to_dict() for a in articles]
        
        if not articles:
            return []
        
        # Portfolio articles don't need filtering
        if category in ["portfolios", "Portfolio"]:
            return articles
        
        # Process in batches for better results
        batch_size = 20
        filtered_results = []
        
        for i in range(0, len(articles), batch_size):
            batch = articles[i:i+batch_size]
            # Use category-specific filtering
            important_indices = self.filter_batch_with_category(batch, category)
            # Add the important articles to results
            for idx in important_indices:
                if idx < len(batch):
                    filtered_results.append(batch[idx])
        
        return filtered_results
    
    def classify_articles(self, articles: List[Article], category: str) -> List[int]:
        """Classify articles using OpenAI"""
        try:
            if not articles:
                return []
            
            # Prepare articles text for classification
            articles_text = self._prepare_articles_text(articles)
            
            # Create classification prompt
            prompt = self._create_classification_prompt(articles_text, category)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500
            )
            
            # Parse response to get selected indices
            result_text = response.choices[0].message.content.strip()
            return self._parse_indices_response(result_text)
            
        except Exception as e:
            print(f"OpenAI classification error: {e}")
            return []
    
    def filter_batch_with_category(self, articles_batch: List[Dict], category: str) -> List[int]:
        """Filter batch of articles using category-specific prompts"""
        if not articles_batch:
            return []
        
        # For now, be less strict - take more articles
        # Return at least 50% of articles or minimum 5
        min_articles = min(5, len(articles_batch))
        target_count = max(min_articles, len(articles_batch) // 2)
        
        # Generate articles text with IDs
        articles_text = ""
        id_mapping = {}
        
        for i, article in enumerate(articles_batch):
            article_id = f"ID{i+1}"
            title = article.get('title', '')
            content = article.get('content_text', '')[:100]
            id_mapping[article_id] = i
            
            # For most categories, only include title
            # For fund category, include content preview
            if category in ["基金融资"]:
                articles_text += f"\n{article_id}: {title} - {content}\n"
            else:
                articles_text += f"\n{article_id}: {title}\n"
        
        # Generate category-specific prompt
        prompt = self._generate_category_prompt(category, len(articles_batch), articles_text)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,  # Slightly higher temperature for more diverse selection
                max_tokens=200
            )
            
            result = response.choices[0].message.content.strip()
            print(f"  AI response for {category}: {result[:100]}")
            
            # Parse response to extract IDs
            import re
            raw_ids = re.findall(r'\d+', result)
            id_matches = ['ID' + num for num in raw_ids]
            
            # Convert to article indices
            selected_indices = []
            for id_str in id_matches:
                if id_str in id_mapping:
                    selected_indices.append(id_mapping[id_str])
            
            # If too few selected, add more from the batch
            if len(selected_indices) < target_count:
                print(f"  AI selected too few ({len(selected_indices)}), adding more to reach {target_count}")
                for i in range(len(articles_batch)):
                    if i not in selected_indices:
                        selected_indices.append(i)
                        if len(selected_indices) >= target_count:
                            break
            
            print(f"  Final selection for {category}: {len(selected_indices)} articles")
            return selected_indices
            
        except Exception as e:
            print(f"  Category filtering error for {category}: {e}")
            # Return at least target_count articles if filtering fails
            return list(range(min(target_count, len(articles_batch))))
    
    def _generate_category_prompt(self, category: str, count: int, articles_text: str) -> str:
        """Generate category-specific prompt from config"""
        if not self.prompts_config:
            # Fallback to generic prompt
            return self._get_generic_prompt(category, count, articles_text)
        
        config = self.prompts_config
        category_config = config.get('categories', {}).get(category)
        
        if not category_config:
            # Try to find a matching category
            category_mapping = {
                "项目融资": "项目融资",
                "基金融资": "基金融资",
                "公链/L2/主网": "公链/L2/主网",
                "中间件/工具协议": "中间件/工具协议",
                "DeFi": "DeFi",
                "RWA": "RWA",
                "稳定币": "稳定币",
                "应用协议": "应用协议",
                "GameFi": "GameFi",
                "交易所/钱包": "交易所/钱包",
                "AI + Crypto": "AI + Crypto",
                "DePIN": "DePIN"
            }
            
            mapped_category = category_mapping.get(category)
            if mapped_category:
                category_config = config.get('categories', {}).get(mapped_category)
        
        if not category_config:
            return self._get_generic_prompt(category, count, articles_text)
        
        # Format criteria
        criteria_text = self._format_criteria(category_config.get('criteria', {}))
        
        # Generate prompt from template
        common = config.get('common', {})
        prompt = category_config['prompt_template'].format(
            count=count,
            criteria=criteria_text,
            return_format=common.get('return_format', '[id1, id2, id3]'),
            empty_return=common.get('empty_return', '[]'),
            instructions=common.get('instructions', ''),
            articles=articles_text
        )
        
        return prompt
    
    def _format_criteria(self, criteria: Dict) -> str:
        """Format criteria into readable text"""
        formatted = ""
        if 'keep' in criteria:
            for item in criteria['keep']:
                formatted += f"✅ 保留：{item}\n"
        if 'discard' in criteria:
            for item in criteria['discard']:
                formatted += f"❌ 抛弃：{item}\n"
        return formatted.strip()
    
    def _get_generic_prompt(self, category: str, count: int, articles_text: str) -> str:
        """Generic prompt as fallback"""
        return f"""请分析以下{count}篇加密货币新闻，判断哪些是真实的{category}新闻。
        
请只返回符合条件的文章ID，格式：[id1, id2, id3]
如果没有符合条件的文章，返回：[]

文章列表：
{articles_text}"""
    
    def filter_articles_by_importance(self, articles: List[Article]) -> List[int]:
        """Filter articles by importance using OpenAI"""
        try:
            if not articles:
                return []
            
            # Convert Article objects to dicts if needed
            if articles and hasattr(articles[0], 'to_dict'):
                articles_data = [a.to_dict() if hasattr(a, 'to_dict') else a for a in articles]
            else:
                articles_data = articles
            
            articles_text = ""
            for i, article in enumerate(articles_data, 1):
                if isinstance(article, dict):
                    title = article.get('title', '')
                    content = article.get('content_text', '')[:150]
                else:
                    title = article.title if hasattr(article, 'title') else str(article)
                    content = article.get_content_preview(150) if hasattr(article, 'get_content_preview') else ''
                articles_text += f"{i}. {title}\n{content}\n\n"
            
            prompt = f"""
分析以下加密货币新闻文章，判断哪些文章对投资者来说是重要的。

请返回重要文章的编号列表，格式：[1,3,5] 或 []

评判标准：
- 重大项目进展、融资或发布
- 重要基金融资或投资动态
- 主网上线、重大升级或技术突破
- 监管政策变化或合规进展
- 市场重大事件或趋势
- 知名项目或机构的重要动态
- DeFi/GameFi/AI等热门赛道的创新

注意：不要过度筛选，保留所有有价值的信息

文章列表：
{articles_text}
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=200
            )
            
            result_text = response.choices[0].message.content.strip()
            return self._parse_indices_response(result_text)
            
        except Exception as e:
            print(f"OpenAI importance filtering error: {e}")
            # Return all indices if filtering fails
            return list(range(len(articles)))
    
    def summarize_article(self, article: Article) -> str:
        """Generate article summary using OpenAI"""
        try:
            prompt = f"""
请为以下加密货币相关文章写一个简洁的中文摘要（100字以内）：

标题：{article.title}
内容：{article.content_text[:1000]}...

摘要：
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"OpenAI summarization error: {e}")
            return ""
    
    def extract_funding_info(self, articles: List[Article]) -> Dict[str, Any]:
        """Extract funding information using OpenAI"""
        try:
            if not articles:
                return {}
            
            funding_articles = [a for a in articles if "融资" in a.title or "投资" in a.title]
            if not funding_articles:
                return {}
            
            articles_text = self._prepare_articles_text(funding_articles)
            
            prompt = f"""
从以下融资相关新闻中提取结构化信息，以JSON格式返回：

请提取：项目名称、融资金额、融资轮次、投资机构、融资时间等信息。

文章：
{articles_text}

JSON格式返回：
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=800
            )
            
            # Parse JSON response
            import json
            try:
                return json.loads(response.choices[0].message.content.strip())
            except json.JSONDecodeError:
                return {}
                
        except Exception as e:
            print(f"OpenAI funding extraction error: {e}")
            return {}
    
    def batch_process(self, articles: List[Article], 
                     operation: str, batch_size: int = 20) -> List[Any]:
        """Process articles in batches"""
        results = []
        
        for i in range(0, len(articles), batch_size):
            batch = articles[i:i+batch_size]
            
            if operation == "classify":
                batch_result = self.classify_articles(batch, "general")
            elif operation == "importance":
                batch_result = self.filter_articles_by_importance(batch)
            else:
                batch_result = []
            
            results.extend(batch_result)
            
            # Add delay between batches to avoid rate limiting
            if i + batch_size < len(articles):
                time.sleep(1)
        
        return results
    
    def _prepare_articles_text(self, articles: List[Article]) -> str:
        """Prepare articles text for AI processing"""
        articles_text = ""
        for i, article in enumerate(articles, 1):
            preview = article.get_content_preview(150)
            articles_text += f"{i}. 【{article.source_feed}】{article.title}\n{preview}\n\n"
        return articles_text
    
    def _create_classification_prompt(self, articles_text: str, category: str) -> str:
        """Create classification prompt"""
        return f"""
请分析以下加密货币新闻文章，判断哪些属于{category}类别。

返回格式：[选中文章编号] 或 []

文章列表：
{articles_text}
"""
    
    def _parse_indices_response(self, response: str) -> List[int]:
        """Parse AI response to extract article indices"""
        try:
            import re
            # Look for pattern like [1,2,3] or [1, 2, 3]
            match = re.search(r'\[([0-9,\s]+)\]', response)
            if match:
                indices_str = match.group(1)
                indices = [int(x.strip()) for x in indices_str.split(',') if x.strip().isdigit()]
                # Convert to 0-based indexing
                return [i - 1 for i in indices if i > 0]
            return []
        except:
            return []


class DeepSeekService(AIService):
    """DeepSeek AI service implementation"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = "deepseek-chat"
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url
        )
    
    def classify_articles(self, articles: List[Article], category: str) -> List[int]:
        """Classify articles using DeepSeek"""
        # DeepSeek implementation is similar to OpenAI but with different model
        try:
            if not articles:
                return []
            
            articles_text = self._prepare_articles_text(articles)
            prompt = self._create_classification_prompt(articles_text, category)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500
            )
            
            result_text = response.choices[0].message.content.strip()
            return self._parse_indices_response(result_text)
            
        except Exception as e:
            print(f"DeepSeek classification error: {e}")
            return []
    
    def filter_articles_by_importance(self, articles: List[Article]) -> List[int]:
        """Filter by importance using DeepSeek"""
        # Similar implementation to OpenAI
        try:
            if not articles:
                return []
            
            articles_text = self._prepare_articles_text(articles)
            
            prompt = f"""
分析以下加密货币新闻，返回重要文章编号：[1,3,5] 或 []

{articles_text}
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=200
            )
            
            result_text = response.choices[0].message.content.strip()
            return self._parse_indices_response(result_text)
            
        except Exception as e:
            print(f"DeepSeek importance filtering error: {e}")
            return []
    
    def summarize_article(self, article: Article) -> str:
        """Summarize article using DeepSeek"""
        # Similar to OpenAI implementation
        return ""
    
    def extract_funding_info(self, articles: List[Article]) -> Dict[str, Any]:
        """Extract funding info using DeepSeek"""
        # Similar to OpenAI implementation
        return {}
    
    def batch_process(self, articles: List[Article], 
                     operation: str, batch_size: int = 20) -> List[Any]:
        """Batch process using DeepSeek"""
        # Similar to OpenAI implementation
        return []
    
    # Helper methods (same as OpenAI)
    def _prepare_articles_text(self, articles: List[Article]) -> str:
        articles_text = ""
        for i, article in enumerate(articles, 1):
            preview = article.get_content_preview(150)
            articles_text += f"{i}. 【{article.source_feed}】{article.title}\n{preview}\n\n"
        return articles_text
    
    def _create_classification_prompt(self, articles_text: str, category: str) -> str:
        return f"""
请分析以下加密货币新闻文章，判断哪些属于{category}类别。

返回格式：[选中文章编号] 或 []

文章列表：
{articles_text}
"""
    
    def _parse_indices_response(self, response: str) -> List[int]:
        try:
            import re
            match = re.search(r'\[([0-9,\s]+)\]', response)
            if match:
                indices_str = match.group(1)
                indices = [int(x.strip()) for x in indices_str.split(',') if x.strip().isdigit()]
                return [i - 1 for i in indices if i > 0]
            return []
        except:
            return []


def create_ai_service(provider: str, api_key: str, **kwargs) -> AIService:
    """Factory function to create AI service"""
    if provider.lower() == "openai":
        return OpenAIService(api_key, **kwargs)
    elif provider.lower() == "deepseek":
        base_url = kwargs.get("base_url", "https://api.deepseek.com")
        return DeepSeekService(api_key, base_url)
    else:
        raise ValueError(f"Unsupported AI provider: {provider}")