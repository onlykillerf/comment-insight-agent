# Real Xiaohongshu Workflow

这个流程用于真实小红书评论分析，但保持合规边界：

- 你自己正常登录账号。
- 不绕过登录、验证码、付费墙、风控或平台权限。
- 不使用代理池做规避。
- 只分析你已经合法导出的评论数据。

## 1. 采集/导出

可以参考 NanmiCoder/MediaCrawler 的平台结构和导出能力，选择小红书 `xhs` 平台，开启评论导出，低频采集目标话题或指定笔记。

建议关键词：

```text
梅西 世界杯 表现
```

导出格式建议用 JSONL、CSV 或 SQLite。

## 2. 放入项目

示例路径：

```text
data/xhs_messi_worldcup_comments.jsonl
```

## 3. 运行真实数据分析

在 `backend` 目录执行：

```bash
python scripts/run_real_export_task.py \
  --source-path data/xhs_messi_worldcup_comments.jsonl \
  --platform xhs \
  --domain sports \
  --name "小红书：梅西世界杯表现评论分析" \
  --keywords "梅西,世界杯,表现" \
  --semantic-query "分析小红书用户对梅西本次世界杯表现的评论" \
  --max-comments 300
```

如果真实 LLM provider 暂时限流，可以先加：

```bash
--disable-llm
```

这只会关闭洞察生成，不影响真实评论清洗、去重、情绪、痛点、归因、聚类和策略卡片流程。

