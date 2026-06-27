"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Alert, Button, Empty, Image, List, Statistic, Table, Tag } from "antd";
import { Download, Newspaper, RefreshCw, Scale, ShieldCheck, Sparkles } from "lucide-react";
import { api } from "@/api/client";
import { ClassificationBar, ClusterBubble, SentimentPie, WordCloudPanel } from "@/charts/Charts";
import type { ClassificationRow, Cluster, CommentItem, DataQuality, Insight, Task, WordClouds } from "@/types/task";

export default function ReportPage() {
  const params = useParams<{ id: string }>();
  const taskId = Number(params.id);
  const [task, setTask] = useState<Task | null>(null);
  const [quality, setQuality] = useState<DataQuality | null>(null);
  const [comments, setComments] = useState<CommentItem[]>([]);
  const [sentiment, setSentiment] = useState<Record<string, number>>({});
  const [painpoints, setPainpoints] = useState<ClassificationRow[]>([]);
  const [positives, setPositives] = useState<ClassificationRow[]>([]);
  const [clusters, setClusters] = useState<Cluster[]>([]);
  const [wordclouds, setWordclouds] = useState<WordClouds | null>(null);
  const [insight, setInsight] = useState<Insight | null>(null);
  const [error, setError] = useState("");

  const load = async () => {
    setError("");
    try {
      const [taskData, commentsData, sentimentData, painData, positiveData, clusterData, insightData, qualityData, wordcloudData] =
        await Promise.all([
          api.getTask(taskId),
          api.getComments(taskId),
          api.getSentiment(taskId),
          api.getPainpoints(taskId),
          api.getPositiveAttributions(taskId),
          api.getClusters(taskId),
          api.getInsights(taskId).catch(() => null),
          api.getQuality(taskId).catch(() => null),
          api.getWordclouds(taskId).catch(() => null)
        ]);
      setTask(taskData);
      setComments(commentsData);
      setSentiment(sentimentData.distribution);
      setPainpoints(painData);
      setPositives(positiveData);
      setClusters(clusterData);
      setInsight(insightData);
      setQuality(qualityData);
      setWordclouds(wordcloudData);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "报告加载失败");
    }
  };

  useEffect(() => {
    load();
  }, [taskId]);

  const dedupComments = useMemo(() => comments.filter((comment) => !comment.is_duplicate), [comments]);
  const negativeCount = (sentiment.negative || 0) + (sentiment.strong_negative || 0);
  const negativeRatio = dedupComments.length ? negativeCount / dedupComments.length : 0;
  const dominantTopic = clusters.filter((cluster) => !cluster.is_noise).sort((a, b) => b.cluster_size - a.cluster_size)[0];
  const displayQuality = quality || fallbackQualityFor(comments, dedupComments);
  const imageComments = useMemo(() => comments.filter((comment) => comment.image_urls.length > 0), [comments]);
  const analyzedImages = useMemo(
    () => imageComments.filter((comment) => comment.image_analysis.status === "completed"),
    [imageComments]
  );

  if (!task && !error) {
    return <div className="tool-panel p-5">Loading...</div>;
  }

  return (
    <div className="space-y-5">
      {error && <Alert type="error" showIcon message="报告加载失败" description={error} />}
      {task && (
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="mb-2 flex gap-2"><Tag>{task.domain === "football" ? "足球" : "篮球"}</Tag><Tag>{task.board}</Tag></div>
            <h1 className="m-0 text-2xl font-semibold text-ink">{task.match_name || task.name}</h1>
            <p className="m-0 mt-1 text-sm text-slate-600">虎扑赛事评论洞察报告</p>
          </div>
          <div className="flex gap-2">
            <Button icon={<RefreshCw size={16} />} onClick={load} />
            <Link href={api.markdownUrl(taskId)} target="_blank"><Button icon={<Download size={16} />}>Markdown</Button></Link>
          </div>
        </div>
      )}

      {displayQuality.warning && <Alert type="warning" showIcon message={displayQuality.warning} />}

      <section className="tool-panel p-5">
        <div className="mb-3 flex items-center gap-2">
          <Sparkles size={18} className="text-teal-700" />
          <h2 className="m-0 text-lg font-semibold text-ink">舆情摘要</h2>
        </div>
        <p className="m-0 text-sm leading-7 text-slate-700">
          {insight?.summary || `当前主导话题为「${dominantTopic?.cluster_name || "暂无"}」，负向评论占去重样本的 ${formatPercent(negativeRatio)}。`}
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-5">
        <div className="metric-tile"><Statistic title="样本可信度" value={displayQuality.sample_confidence_level} /></div>
        <div className="metric-tile"><Statistic title="重复率" value={displayQuality.duplicate_ratio * 100} precision={1} suffix="%" /></div>
        <div className="metric-tile"><Statistic title="负向占比" value={negativeRatio * 100} precision={1} suffix="%" /></div>
        <div className="metric-tile"><Statistic title="主导话题" value={dominantTopic?.cluster_name || "N/A"} /></div>
        <div className="metric-tile"><Statistic title="配图已理解" value={analyzedImages.length} suffix={`/ ${imageComments.length}`} /></div>
      </section>

      {task && (
        <section className="grid gap-4 lg:grid-cols-2">
          <div className="tool-panel p-5">
            <h2 className="m-0 mb-3 text-lg font-semibold text-ink">比赛与帖子</h2>
            <dl className="grid grid-cols-[100px_1fr] gap-x-3 gap-y-2 text-sm">
              <dt className="text-slate-500">对阵</dt><dd className="m-0">{task.home_team} vs {task.away_team}</dd>
              <dt className="text-slate-500">阶段</dt><dd className="m-0">{task.match_stage || "-"}</dd>
              <dt className="text-slate-500">日期</dt><dd className="m-0">{task.match_date || "-"}</dd>
              <dt className="text-slate-500">帖子</dt>
              <dd className="m-0 space-y-1">
                {task.thread_urls.length ? task.thread_urls.map((url, index) => <a className="block" href={url} target="_blank" rel="noreferrer" key={url}>虎扑帖子 {index + 1}</a>) : "离线演示样本"}
              </dd>
            </dl>
          </div>
          <div className="tool-panel p-5">
            <div className="mb-3 flex items-center gap-2"><Newspaper size={18} className="text-teal-700" /><h2 className="m-0 text-lg font-semibold text-ink">新闻背景</h2></div>
            <p className="m-0 text-sm leading-6 text-slate-700">{insight?.news_context_summary || "本次未提供相关新闻背景。"}</p>
            {!!insight?.context_alignment.length && <List size="small" className="mt-2" dataSource={insight.context_alignment} renderItem={(item) => <List.Item>{item}</List.Item>} />}
          </div>
        </section>
      )}

      <section className="tool-panel p-5">
        <div className="mb-3 flex items-center gap-2"><ShieldCheck size={18} className="text-teal-700" /><h2 className="m-0 text-lg font-semibold text-ink">数据质量</h2></div>
        <div className="grid gap-4 md:grid-cols-5">
          <Statistic title="原始" value={displayQuality.raw_count} />
          <Statistic title="清洗" value={displayQuality.clean_count} />
          <Statistic title="去重" value={displayQuality.dedup_count} />
          <Statistic title="噪声率" value={displayQuality.noise_ratio * 100} precision={1} suffix="%" />
          <Statistic title="语言" value={Object.keys(displayQuality.language_distribution).join(" / ") || "N/A"} />
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <div className="tool-panel p-4"><h2 className="m-0 text-lg font-semibold text-ink">情绪分布</h2><SentimentPie distribution={sentiment} /><p className="m-0 text-sm text-slate-500">负向评论占去重样本的 {formatPercent(negativeRatio)}。</p></div>
        <div className="tool-panel p-4"><h2 className="m-0 text-lg font-semibold text-ink">讨论主题</h2><ClusterBubble clusters={clusters} /><p className="m-0 text-sm text-slate-500">气泡大小表示主题样本量，半径已限制以保留小主题。</p></div>
        <div className="tool-panel p-4"><ClassificationBar rows={painpoints} title="争议与负向标签" /><p className="m-0 text-sm text-slate-500">标签来自篮球或足球赛事词典及真实分类计数。</p></div>
        <div className="tool-panel p-4"><ClassificationBar rows={positives} title="正向评价标签" /><p className="m-0 text-sm text-slate-500">用于观察球迷认可的球员表现、战术和比赛环节。</p></div>
      </section>

      <section className="tool-panel p-4">
        <h2 className="m-0 mb-1 text-lg font-semibold text-ink">评论配图证据</h2>
        <p className="m-0 mb-4 text-sm text-slate-500">
          配图由 SiliconFlow Qwen/Qwen3.5-4B 描述，仅作为评论语义的辅助证据，不作为独立新闻事实。
        </p>
        {analyzedImages.length ? (
          <div className="grid gap-4 md:grid-cols-2">
            {analyzedImages.map((comment) => (
              <article className="border border-slate-200 p-3" key={comment.id}>
                <Image.PreviewGroup>
                  <div className="mb-3 flex gap-2 overflow-x-auto">
                    {comment.image_urls.slice(0, 2).map((url) => (
                      <Image key={url} src={api.mediaUrl(url)} alt="虎扑公开评论配图" width={112} height={84} className="object-cover" />
                    ))}
                  </div>
                </Image.PreviewGroup>
                <p className="m-0 text-sm text-slate-700">{comment.image_analysis.summary}</p>
                {comment.image_analysis.ocr_text && (
                  <p className="m-0 mt-2 text-xs text-slate-500">OCR：{comment.image_analysis.ocr_text}</p>
                )}
                <div className="mt-3 flex flex-wrap gap-2">
                  <Tag>{comment.image_analysis.relevance || "unknown"}</Tag>
                  <Tag>{comment.image_analysis.sentiment_cue || "unclear"}</Tag>
                  <Tag>{comment.image_analysis.model}</Tag>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="本次样本没有完成配图分析" />
        )}
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <WordCloudSection title="全量词云" words={wordclouds?.all_words || []} explanation={wordclouds?.explanations.all} />
        <WordCloudSection title="正向词云" words={wordclouds?.positive_words || []} explanation={wordclouds?.explanations.positive} />
        <WordCloudSection title="负向词云" words={wordclouds?.negative_words || []} explanation={wordclouds?.explanations.negative} />
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <InsightList title="关键观点" items={insight?.key_viewpoints || []} />
        <InsightList title="争议焦点" items={insight?.controversies || []} />
        <InsightList title="正向评价" items={insight?.positive_insights || []} />
        <InsightList title="负向评价" items={insight?.negative_insights || []} />
      </section>

      <section className="tool-panel p-4">
        <div className="mb-3 flex items-center gap-2"><Scale size={18} className="text-teal-700" /><h2 className="m-0 text-lg font-semibold text-ink">事实与观点边界</h2></div>
        <List size="small" dataSource={[...(insight?.fact_opinion_gaps || []), ...(insight?.risks || [])]} renderItem={(item) => <List.Item>{item}</List.Item>} locale={{ emptyText: "暂无上下文对照结果" }} />
      </section>

      <section className="tool-panel p-4">
        <h2 className="m-0 mb-3 text-lg font-semibold text-ink">典型评论</h2>
        <Table<CommentItem>
          rowKey="id"
          pagination={{ pageSize: 6 }}
          dataSource={dedupComments.slice(0, 36)}
          columns={[
            { title: "评论", dataIndex: "cleaned_content" },
            {
              title: "配图",
              width: 120,
              render: (_, record) => record.image_urls[0] ? <Image src={api.mediaUrl(record.image_urls[0])} alt="评论配图" width={72} height={54} className="object-cover" /> : "-"
            },
            { title: "情绪", dataIndex: "sentiment_label", width: 120 },
            { title: "赛事标签", width: 180, render: (_, record) => <Tag>{record.painpoint || record.positive_attribution || "中性"}</Tag> },
            { title: "代表性原因", dataIndex: "representative_reason", width: 240, render: (value?: string | null) => value || "-" }
          ]}
        />
      </section>
    </div>
  );
}

function WordCloudSection({ title, words, explanation }: { title: string; words: WordClouds["all_words"]; explanation?: string }) {
  return <div className="tool-panel p-4"><h2 className="m-0 mb-3 text-lg font-semibold text-ink">{title}</h2><WordCloudPanel words={words} /><p className="m-0 mt-2 text-sm text-slate-500">{explanation || "运行任务后生成 TF-IDF 领域加权词云。"}</p></div>;
}

function InsightList({ title, items }: { title: string; items: string[] }) {
  return <div className="tool-panel p-4"><h2 className="m-0 mb-2 text-lg font-semibold text-ink">{title}</h2>{items.length ? <List size="small" dataSource={items} renderItem={(item) => <List.Item>{item}</List.Item>} /> : <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无" />}</div>;
}

function fallbackQualityFor(comments: CommentItem[], dedupComments: CommentItem[]): DataQuality {
  return {
    raw_count: comments.length,
    clean_count: comments.length,
    dedup_count: dedupComments.length,
    duplicate_ratio: comments.length ? (comments.length - dedupComments.length) / comments.length : 0,
    noise_ratio: 0,
    language_distribution: {},
    sample_confidence_level: dedupComments.length < 100 ? "low" : dedupComments.length < 300 ? "medium" : "high",
    warning: dedupComments.length < 100 ? "样本量较小，仅适合演示" : ""
  };
}

function formatPercent(value: number) {
  return `${(value * 100).toFixed(1)}%`;
}
