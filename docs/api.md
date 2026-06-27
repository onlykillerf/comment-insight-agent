# API

基础路径：`http://localhost:8000`

| Method | Path | Description |
| --- | --- | --- |
| POST | `/api/tasks` | 创建分析任务 |
| GET | `/api/tasks` | 获取任务列表 |
| GET | `/api/tasks/{task_id}` | 获取任务详情 |
| POST | `/api/tasks/{task_id}/run` | 启动任务分析流程 |
| GET | `/api/tasks/{task_id}/status` | 获取任务执行状态 |
| GET | `/api/tasks/{task_id}/comments` | 获取评论列表 |
| GET | `/api/tasks/{task_id}/clusters` | 获取聚类结果 |
| GET | `/api/tasks/{task_id}/sentiment` | 获取情绪分析结果 |
| GET | `/api/tasks/{task_id}/painpoints` | 获取痛点分析结果 |
| GET | `/api/tasks/{task_id}/positive-attributions` | 获取好评归因结果 |
| GET | `/api/tasks/{task_id}/insights` | 获取洞察报告 |
| GET | `/api/tasks/{task_id}/strategy-cards` | 获取策略卡片 |
| GET | `/api/tasks/{task_id}/report/markdown` | 导出 Markdown 报告 |

## MediaCrawler Export Payload

```json
{
  "name": "MediaCrawler 导出评论分析",
  "domain": "game",
  "platforms": ["weibo"],
  "keywords": ["广告"],
  "semantic_query": "分析广告体验相关评论",
  "max_comments": 200,
  "data_source": "mediacrawler",
  "source_path": "data/mediacrawler_weibo_note_comment.jsonl"
}
```

`source_path` 可以指向 MediaCrawler 导出的单个 CSV/JSON/JSONL/SQLite 文件，也可以指向导出目录。路径支持绝对路径，也支持相对项目根目录的路径。
