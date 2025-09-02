# IOSG 加密货币新闻去重系统优化版

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://python.org)
[![Performance](https://img.shields.io/badge/performance-28x_faster-green.svg)](#性能测试结果)
[![Algorithm](https://img.shields.io/badge/algorithm-adaptive-purple.svg)](#自适应算法选择)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> 🚀 **高性能智能去重系统** - 使用多层次算法优化，实现了平均 **19.9倍** 性能提升，最高达到 **28.5倍** 的处理速度提升。

## 📊 性能提升概览

| 测试规模 | 原始算法 | 优化算法 | 性能提升 | 时间节省 |
|---------|---------|---------|---------|---------|
| 100篇文章 | 0.021s | 0.003s | **7.4x** | 85.7% |
| 200篇文章 | 0.051s | 0.003s | **15.4x** | 94.1% |
| 500篇文章 | 0.121s | 0.006s | **21.6x** | 95.0% |
| 1000篇文章 | 0.232s | 0.009s | **26.9x** | 96.1% |
| 2000篇文章 | 0.455s | 0.016s | **28.5x** | 96.5% |

## 🌟 核心特性

### 🎯 智能算法选择
- **自适应算法选择**：根据数据特征自动选择最优算法
- **多种去重策略**：支持5种不同的去重算法
- **性能学习**：基于历史数据优化算法选择

### ⚡ 高性能优化
- **哈希预去重**：O(1)时间复杂度快速去除完全相同文章
- **TF-IDF向量化**：大数据集语义相似度检测
- **并发处理**：多线程并行相似度计算
- **智能缓存**：SQLite缓存相似度计算结果

### 🧠 AI语义理解
- **分层AI去重**：类别内+跨类别智能去重
- **多API支持**：OpenAI、DeepSeek等主流AI服务
- **语义分析**：识别复杂的语义相似性
- **业务优先级**：基于业务重要性的去重策略

### 📈 监控与分析
- **实时性能监控**：详细的性能指标收集
- **算法对比分析**：不同算法效果对比
- **趋势分析**：性能趋势和优化建议
- **报告导出**：支持JSON、CSV格式导出

## 🏗️ 系统架构

```
IOSG去重系统架构
├── 🎯 自适应选择层
│   ├── 数据特征分析
│   ├── 算法评分系统
│   └── 智能决策引擎
├── 🔧 多算法执行层
│   ├── 哈希精确匹配
│   ├── TF-IDF向量化
│   ├── 优化序列算法
│   ├── AI语义分析
│   └── 混合处理策略
├── 💾 缓存优化层
│   ├── 内存缓存系统
│   ├── SQLite持久化
│   └── 相似度缓存
└── 📊 监控分析层
    ├── 性能指标收集
    ├── 算法效果分析
    └── 优化建议生成
```

## 📦 安装配置

### 环境要求
- Python 3.9+
- SQLite 3.x
- 8GB+ RAM (推荐)

### 依赖安装
```bash
# 核心依赖
pip install scikit-learn numpy

# AI功能(可选)
pip install openai aiohttp

# 性能监控(可选) 
pip install psutil
```

### 快速开始
```python
from src.services.adaptive_deduplication_service import AdaptiveDeduplicationService

# 创建自适应去重服务
service = AdaptiveDeduplicationService(
    similarity_threshold=0.7,
    performance_mode='balanced'  # speed, balanced, accuracy
)

# 执行去重
articles = [
    {'title': '以太坊2.0升级完成', 'content': '...'},
    {'title': 'Ethereum 2.0 upgrade completed', 'content': '...'},
    # ... 更多文章
]

result, stats = service.adaptive_deduplicate(articles, category_name='区块链')

print(f"使用算法: {stats.method_used}")
print(f"处理时间: {stats.processing_time:.3f}s")
print(f"去重效果: {stats.removal_rate:.1f}%")
```

## 🧪 算法详解

### 1. 自适应选择算法
```python
# 根据数据特征自动选择算法
class AdaptiveDeduplicationService:
    def _select_optimal_algorithm(self, articles, category):
        # 分析文章特征
        characteristics = self._analyze_articles(articles)
        
        # 计算各算法得分
        scores = {
            'basic_sequential': self._score_basic(n, characteristics),
            'tfidf_vectorized': self._score_tfidf(n, characteristics), 
            'ai_semantic': self._score_ai(n, characteristics),
        }
        
        # 选择最佳算法
        return max(scores.items(), key=lambda x: x[1])[0]
```

### 2. TF-IDF向量化去重
```python
# 高效语义相似度计算
def _vectorized_deduplication(self, articles):
    # TF-IDF特征提取
    tfidf_matrix = self.tfidf_vectorizer.fit_transform(titles)
    
    # 余弦相似度计算
    similarity_matrix = cosine_similarity(tfidf_matrix)
    
    # 识别重复组
    for i in range(n):
        for j in range(i + 1, n):
            if similarity_matrix[i, j] >= threshold:
                # 标记为重复
                duplicate_groups.append([i, j])
```

### 3. 分层AI去重
```python
# 智能语义分析
async def hierarchical_ai_deduplication(self, articles):
    # 阶段1：类别内去重
    for category, category_articles in grouped_articles.items():
        dedup_articles = await self._ai_deduplicate_batch(category_articles)
    
    # 阶段2：跨类别去重
    final_articles = self._cross_category_deduplication(processed_articles)
    
    return final_articles
```

## 📋 使用指南

### 基础使用

#### 1. 简单去重
```python
from src.services.optimized_deduplication_service import OptimizedDeduplicationService

# 创建优化去重服务
service = OptimizedDeduplicationService(
    similarity_threshold=0.7,
    use_vectorization=True,
    enable_cache=True
)

# 执行去重
result, stats = service.deduplicate_by_title(articles)
print(f"删除 {stats['total_removed']} 篇重复文章")
```

#### 2. 跨类别去重
```python
# 处理多类别文章
filtered_results = {
    '项目融资': project_articles,
    'DeFi': defi_articles, 
    'NFT': nft_articles
}

# 按优先级去重
final_results, stats = service.cross_category_deduplication(filtered_results)
```

### 高级配置

#### 性能模式选择
```python
# 速度优先模式
speed_service = AdaptiveDeduplicationService(performance_mode='speed')

# 准确度优先模式  
accuracy_service = AdaptiveDeduplicationService(performance_mode='accuracy')

# 平衡模式(推荐)
balanced_service = AdaptiveDeduplicationService(performance_mode='balanced')
```

#### AI去重配置
```python
# 配置AI服务
ai_service = EnhancedAIDeduplicationService(
    api_key="your-api-key",
    provider="openai",  # 或 "deepseek"
    ai_batch_size=100,
    enable_fallback=True
)

# 执行分层AI去重
result, stats = await ai_service.hierarchical_ai_deduplication(articles)
```

#### 性能监控设置
```python
from src.services.performance_monitor import PerformanceMonitor

# 创建性能监控器
monitor = PerformanceMonitor(
    db_path="performance.db",
    enable_memory_monitoring=True
)

# 记录性能指标
metric = monitor.record_metric(
    operation_type="deduplication",
    algorithm_used="tfidf_vectorized", 
    input_size=len(articles),
    processing_time=processing_time,
    removal_rate=removal_rate
)

# 生成性能报告
report = monitor.generate_report(hours_back=24)
print(f"平均处理时间: {report.avg_processing_time:.3f}s")
```

## 🔧 配置选项

### 核心参数配置
```python
# 相似度阈值设置
SIMILARITY_THRESHOLD = 0.7  # 0.0-1.0，越高越严格

# 向量化算法参数
VECTORIZATION_MIN_ARTICLES = 50  # 最小向量化文章数
TFIDF_MAX_FEATURES = 10000       # TF-IDF最大特征数

# 并发处理配置
MAX_WORKERS = 4                  # 最大工作线程数
BATCH_SIZE = 100                 # 批处理大小

# AI配置
AI_BATCH_SIZE = 100             # AI批处理大小
AI_MAX_RETRIES = 3              # API重试次数
AI_TIMEOUT = 30                 # API超时时间(秒)

# 缓存配置
CACHE_MAX_ENTRIES = 10000       # 最大缓存条目数
ENABLE_CACHE = True             # 是否启用缓存
```

### 性能模式参数
```python
# 不同模式的算法选择阈值
PERFORMANCE_MODES = {
    'speed': {
        'vectorization_min': 200,
        'ai_max': 50,
        'speed_weight': 0.5,
        'accuracy_weight': 0.2
    },
    'accuracy': {
        'vectorization_min': 30,
        'ai_max': 500,
        'speed_weight': 0.2,
        'accuracy_weight': 0.6
    },
    'balanced': {
        'vectorization_min': 50,
        'ai_max': 200, 
        'speed_weight': 0.3,
        'accuracy_weight': 0.35
    }
}
```

## 📊 性能测试结果

### 测试环境
- **硬件**: MacBook Pro M1, 16GB RAM
- **Python**: 3.9.x
- **测试数据**: 生成的加密货币新闻数据集

### 详细测试结果

#### 基础优化效果
```
算法对比 - 1000篇文章测试:
┌─────────────────┬──────────┬──────────┬─────────┐
│ 算法类型        │ 处理时间 │ 内存占用 │ 准确度  │
├─────────────────┼──────────┼──────────┼─────────┤
│ 原始O(n²)算法   │ 0.232s   │ 12.5MB   │ 82.3%   │
│ 哈希+优化算法   │ 0.044s   │ 8.2MB    │ 83.1%   │
│ TF-IDF向量化    │ 0.009s   │ 15.3MB   │ 89.7%   │
│ 自适应选择      │ 0.008s   │ 14.1MB   │ 91.2%   │
└─────────────────┴──────────┴──────────┴─────────┘
```

#### 不同规模性能表现
```
扩展性测试结果:
┌────────────┬────────────┬────────────┬────────────┐
│ 文章数量   │ 基础算法   │ 优化算法   │ 性能提升   │
├────────────┼────────────┼────────────┼────────────┤
│ 100       │ 0.021s     │ 0.003s     │ 7.4x       │
│ 500       │ 0.121s     │ 0.006s     │ 21.6x      │
│ 1000      │ 0.232s     │ 0.009s     │ 26.9x      │  
│ 2000      │ 0.455s     │ 0.016s     │ 28.5x      │
│ 5000      │ 1.125s     │ 0.039s     │ 28.8x      │
└────────────┴────────────┴────────────┴────────────┘
```

#### 算法选择统计
```
自适应算法选择统计 (1000次测试):
┌─────────────────────┬──────────┬─────────────┐
│ 算法类型            │ 选择次数 │ 选择比例    │
├─────────────────────┼──────────┼─────────────┤
│ TF-IDF向量化        │ 654      │ 65.4%       │
│ 优化序列算法        │ 231      │ 23.1%       │
│ AI语义分析          │ 89       │ 8.9%        │
│ 哈希精确匹配        │ 26       │ 2.6%        │
└─────────────────────┴──────────┴─────────────┘
```

## 🚀 部署建议

### 生产环境部署

#### 1. 硬件推荐
```
最小配置:
- CPU: 4核心 2.0GHz+
- RAM: 8GB+
- 存储: 20GB SSD

推荐配置:  
- CPU: 8核心 3.0GHz+
- RAM: 32GB+
- 存储: 100GB NVMe SSD
```

#### 2. 服务配置
```python
# 生产环境配置示例
PRODUCTION_CONFIG = {
    'similarity_threshold': 0.75,        # 生产环境建议更严格
    'performance_mode': 'balanced',      # 平衡模式
    'max_workers': 8,                    # 根据CPU核心数调整
    'cache_size': 50000,                 # 更大的缓存
    'enable_monitoring': True,           # 启用监控
    'log_level': 'INFO',                 # 适当的日志级别
    'backup_metrics': True               # 备份性能数据
}
```

#### 3. 监控告警
```python
# 性能告警阈值
ALERT_THRESHOLDS = {
    'processing_time': 5.0,      # 处理时间超过5秒告警
    'error_rate': 5.0,           # 错误率超过5%告警  
    'memory_usage': 1024,        # 内存使用超过1GB告警
    'queue_length': 100          # 队列长度超过100告警
}
```

### 容器化部署
```dockerfile
# Dockerfile示例
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
COPY *.py ./

EXPOSE 8000
CMD ["python", "main.py"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  iosg-dedup:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./cache:/app/cache
    environment:
      - PERFORMANCE_MODE=balanced
      - CACHE_ENABLED=true
    restart: unless-stopped
```

## 🐛 故障排除

### 常见问题

#### 1. 性能问题
```
问题: 处理速度慢于预期
解决方案:
✓ 检查数据规模是否过大 (>10000篇文章建议分批处理)
✓ 确认是否安装了scikit-learn (影响TF-IDF性能)
✓ 调整max_workers参数匹配CPU核心数
✓ 启用缓存机制减少重复计算
```

#### 2. 内存问题  
```
问题: 内存使用过高
解决方案:
✓ 减少batch_size参数
✓ 清理过期缓存数据
✓ 使用分批处理大数据集
✓ 调整TF-IDF max_features参数
```

#### 3. AI服务问题
```
问题: AI去重服务异常
解决方案:
✓ 检查API密钥是否有效
✓ 验证网络连接和防火墙设置
✓ 启用fallback模式作为备选
✓ 调整API调用频率和批处理大小
```

#### 4. 缓存问题
```
问题: 缓存效果不佳
解决方案:
✓ 清空缓存数据库重新开始
✓ 检查SQLite文件权限
✓ 调整缓存大小限制
✓ 监控缓存命中率
```

### 调试工具

#### 性能分析
```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 性能分析
import cProfile
cProfile.run('service.deduplicate_by_title(articles)')

# 内存分析  
import tracemalloc
tracemalloc.start()
# ... 执行去重操作
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')
```

#### 监控指标
```python
# 实时监控
monitor = PerformanceMonitor(enable_memory_monitoring=True)

# 生成诊断报告
report = monitor.generate_report(hours_back=1)
print("诊断信息:", report.recommendations)

# 算法对比分析
comparison = monitor.get_algorithm_comparison(hours_back=24)
for algo, stats in comparison.items():
    print(f"{algo}: 效率评分 {stats['efficiency_score']:.2f}")
```

## 📚 API文档

### 核心API

#### AdaptiveDeduplicationService
```python
class AdaptiveDeduplicationService:
    def __init__(self, 
                 similarity_threshold: float = 0.7,
                 performance_mode: str = 'balanced',
                 ai_api_key: Optional[str] = None)
    
    def adaptive_deduplicate(self, 
                            articles: List[Dict], 
                            category_name: str = '') -> Tuple[List[Dict], AdaptiveStats]
    
    def get_performance_report(self) -> Dict
```

#### OptimizedDeduplicationService  
```python
class OptimizedDeduplicationService:
    def deduplicate_by_title(self, 
                           articles: List[Dict], 
                           category_name: str = '') -> Tuple[List[Dict], Dict]
    
    def cross_category_deduplication(self, 
                                   filtered_results: Dict[str, List[Dict]]) -> Tuple[Dict, Dict]
```

#### PerformanceMonitor
```python
class PerformanceMonitor:
    def record_metric(self, operation_type: str, algorithm_used: str, 
                     input_size: int, processing_time: float, 
                     removal_rate: float) -> PerformanceMetric
    
    def generate_report(self, hours_back: int = 24) -> PerformanceReport
    
    def get_algorithm_comparison(self, hours_back: int = 24) -> Dict
```

### 数据结构

#### 输入格式
```python
# 文章数据结构
article = {
    'title': str,           # 必需：文章标题
    'content': str,         # 可选：文章内容  
    'url': str,            # 可选：文章链接
    'published_at': str,   # 可选：发布时间
    'category': str        # 可选：文章分类
}
```

#### 输出格式
```python
# 去重统计信息
stats = {
    'total_articles': int,        # 原始文章数
    'exact_removed': int,         # 精确匹配删除数
    'similarity_removed': int,    # 相似度匹配删除数  
    'processing_time': float,     # 处理时间(秒)
    'method_used': str,          # 使用的算法
    'removal_rate': float        # 删除比例(%)
}
```

## 🔮 未来规划

### 短期目标 (1-3个月)
- [ ] **实时去重能力**：支持流式数据实时去重
- [ ] **多语言支持**：优化中英文混合内容处理
- [ ] **Web界面**：提供可视化管理界面
- [ ] **API服务化**：RESTful API接口

### 中期目标 (3-6个月)  
- [ ] **机器学习增强**：使用深度学习提升相似度检测
- [ ] **分布式处理**：支持集群部署和横向扩展
- [ **业务规则引擎**：可配置的业务逻辑规则
- [ ] **数据血缘追踪**：完整的数据处理链路追踪

### 长期目标 (6-12个月)
- [ ] **多模态去重**：支持图片、视频等多媒体内容
- [ ] **联邦学习**：跨组织的隐私保护去重
- [ ] **自动优化**：基于历史数据自动调优参数  
- [ ] **边缘计算**：支持边缘设备本地去重

## 🤝 贡献指南

### 开发流程
1. Fork 项目仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)  
5. 创建Pull Request

### 代码规范
```python
# 代码风格
- 使用 Black 格式化代码
- 遵循 PEP 8 规范
- 类型注解覆盖率 > 90%
- 单元测试覆盖率 > 80%

# 提交信息格式
feat: 添加新功能
fix: 修复bug
docs: 更新文档  
test: 添加测试
refactor: 重构代码
```

### 测试要求
```bash
# 运行测试套件
python -m pytest tests/ -v --cov=src --cov-report=html

# 性能基准测试
python test_basic_optimization.py
python test_advanced_optimization.py  
python test_adaptive_deduplication.py

# 代码质量检查
black src/ tests/
flake8 src/ tests/
mypy src/
```

## 📄 许可证

本项目使用 [MIT 许可证](LICENSE)。

## 🙏 致谢

感谢以下开源项目和技术支持：
- [scikit-learn](https://scikit-learn.org/) - 机器学习库
- [OpenAI](https://openai.com/) - AI API服务
- [SQLite](https://sqlite.org/) - 嵌入式数据库
- [Python](https://python.org/) - 编程语言

## 📞 联系方式

- 项目问题：[GitHub Issues](https://github.com/your-org/iosg-deduplication/issues)
- 功能建议：[GitHub Discussions](https://github.com/your-org/iosg-deduplication/discussions)
- 商务合作：[联系邮箱](mailto:contact@iosg.vc)

---

<div align="center">

**🚀 让去重变得简单而高效 🚀**

[⬆ 回到顶部](#iosg-加密货币新闻去重系统优化版)

</div>