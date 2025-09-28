# RSS Fetcher

`fetch_feeds.py` 按项目配置的 8 个 RSS/Atom 源抓取内容，并维护一个滚动 7 天窗口的聚合文件，结构与根目录 `latest_feeds.json` 完全一致（含 `metadata` 与 `articles`）。脚本会在每次运行时读取已有文件，增量合并新文章，自动去重并剔除 7 天前的数据。

## 常用命令

```bash
# 一次性抓取，结果写入默认位置 tools/rss_fetcher/latest_feeds.json
python tools/rss_fetcher/fetch_feeds.py

# 覆盖根目录 latest_feeds.json，并优先保留完整 HTML 内容
python tools/rss_fetcher/fetch_feeds.py -o latest_feeds.json --raw

# 每小时轮询更新（Ctrl+C 结束），持续维护 7 天内的全部文章
python tools/rss_fetcher/fetch_feeds.py --interval 3600 -o latest_feeds.json

# 仅查看统计信息，不写入文件（dry run）
python tools/rss_fetcher/fetch_feeds.py --no-save --quiet
```

脚本依赖 `requests`（已在项目 `requirements.txt` 中）。轮询模式下，每个周期都会读取已有文件并增量合并，确保 7 天内的文章始终保留在输出文件中。
