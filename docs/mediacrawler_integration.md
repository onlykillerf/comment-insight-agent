# MediaCrawler Integration

本项目参考 NanmiCoder/MediaCrawler 的平台分层思路，但不复制其登录、签名、代理或浏览器自动化实现。

## 采用的设计思路

- 平台层解耦：真实平台采集器按平台拆分，避免把所有平台逻辑写进一个爬虫。
- Client/Connector 分离：采集逻辑和数据归一化逻辑分离。
- Store/Export 桥接：优先读取 CSV、JSON、JSONL、SQLite 等导出数据，再进入评论洞察闭环。
- 评论字段统一：将 `comment_id`、`content`、`like_count`、`parent_comment_id`、`create_time` 等平台字段映射为系统内的 `RawComment`。

## 当前实现

`MediaCrawlerExportConnector` 支持读取：

- `.csv`
- `.json`
- `.jsonl`
- `.db` / `.sqlite` / `.sqlite3`

支持的 MediaCrawler 评论表名：

- `xhs_note_comment`
- `douyin_aweme_comment`
- `kuaishou_video_comment`
- `bilibili_video_comment`
- `weibo_note_comment`
- `tieba_comment`
- `zhihu_comment`

## API 使用示例

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

也可以把 `source_path` 指向 MediaCrawler 的导出目录，系统会递归查找评论相关文件。路径支持绝对路径，也支持相对项目根目录的路径。

本仓库提供了一个最小样例文件：

```text
data/mediacrawler_weibo_note_comment.jsonl
```

## 合规边界

真实采集由用户在合法、合规、低频、公开可访问的前提下自行完成。本项目只导入已经得到授权或可合法处理的导出数据，不提供绕过登录、验证码、付费墙、反爬机制或平台权限控制的功能。
