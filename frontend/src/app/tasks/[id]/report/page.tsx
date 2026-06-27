"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Alert, Button, Empty, List, Statistic, Table, Tag } from "antd";
import { Download, RefreshCw, ShieldCheck, Sparkles } from "lucide-react";
import { api } from "@/api/client";
import { ClassificationBar, ClusterBubble, SentimentPie, WordCloudPanel } from "@/charts/Charts";
import { StrategyCards } from "@/components/StrategyCards";
import type {
  ClassificationRow,
  Cluster,
  CommentItem,
  DataQuality,
  Insight,
  StrategyCard,
  Task,
  WordClouds
} from "@/types/task";

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
  const [cards, setCards] = useState<StrategyCard[]>([]);
  const [error, setError] = useState("");

  const load = async () => {
    setError("");
    try {
      const [taskData, commentsData, sentimentData, painData, positiveData, clusterData, insightData, cardData, qualityData, wordcloudData] =
        await Promise.all([
          api.getTask(taskId),
          api.getComments(taskId),
          api.getSentiment(taskId),
          api.getPainpoints(taskId),
          api.getPositiveAttributions(taskId),
          api.getClusters(taskId),
          api.getInsights(taskId).catch(() => null),
          api.getStrategyCards(taskId),
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
      setCards(cardData);
      setQuality(qualityData);
      setWordclouds(wordcloudData);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Failed to load report");
    }
  };

  useEffect(() => {
    load();
  }, [taskId]);

  const dedupComments = useMemo(() => comments.filter((comment) => !comment.is_duplicate), [comments]);
  const negativeCount = (sentiment.negative || 0) + (sentiment.strong_negative || 0);
  const negativeRatio = dedupComments.length ? negativeCount / dedupComments.length : 0;
  const dominantTopic = clusters.filter((cluster) => !cluster.is_noise).sort((a, b) => b.cluster_size - a.cluster_size)[0];
  const topCard = cards[0];
  const fallbackQuality: DataQuality = {
    raw_count: comments.length,
    clean_count: comments.length,
    dedup_count: dedupComments.length,
    duplicate_ratio: comments.length ? (comments.length - dedupComments.length) / comments.length : 0,
    noise_ratio: 0,
    language_distribution: {},
    sample_confidence_level: dedupComments.length < 100 ? "low" : dedupComments.length < 300 ? "medium" : "high",
    warning: dedupComments.length < 100 ? "样本量较小，仅适合演示" : ""
  };
  const displayQuality = quality || fallbackQuality;

  if (!task && !error) {
    return <div className="tool-panel p-5">Loading...</div>;
  }

  return (
    <div className="space-y-5">
      {error && <Alert type="error" showIcon message="Report load failed" description={error} />}
      {task && (
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="m-0 text-2xl font-semibold text-ink">{task.name}</h1>
            <p className="m-0 mt-1 text-sm text-slate-600">Analysis report</p>
          </div>
          <div className="flex gap-2">
            <Button icon={<RefreshCw size={16} />} onClick={load} />
            <Link href={api.markdownUrl(taskId)} target="_blank">
              <Button icon={<Download size={16} />}>Markdown</Button>
            </Link>
          </div>
        </div>
      )}

      {displayQuality.warning && <Alert type="warning" showIcon message={displayQuality.warning} />}
      {!quality && <Alert type="info" showIcon message="This task was generated before the new DataQualityReport. Re-run it for full quality metrics." />}

      <section className="tool-panel p-5">
        <div className="mb-3 flex items-center gap-2">
          <Sparkles size={18} className="text-teal-700" />
          <h2 className="m-0 text-lg font-semibold text-ink">Executive Summary</h2>
        </div>
        <p className="m-0 text-sm leading-6 text-slate-700">
          The dominant topic is <strong>{dominantTopic?.cluster_name || "not available"}</strong>. Negative comments cover{" "}
          <strong>{formatPercent(negativeRatio)}</strong> of the deduplicated sample. The current sample confidence is{" "}
          <strong>{displayQuality.sample_confidence_level}</strong>, so strategy cards should be read together with their evidence count,
          affected ratio, and confidence reason.
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-4">
        <div className="metric-tile">
          <Statistic title="Sample confidence" value={displayQuality.sample_confidence_level} />
        </div>
        <div className="metric-tile">
          <Statistic title="Duplicate ratio" value={displayQuality.duplicate_ratio * 100} precision={1} suffix="%" />
        </div>
        <div className="metric-tile">
          <Statistic title="Negative ratio" value={negativeRatio * 100} precision={1} suffix="%" />
        </div>
        <div className="metric-tile">
          <Statistic title="Dominant topic" value={dominantTopic?.cluster_name || "N/A"} />
        </div>
      </section>

      <section className="tool-panel p-5">
        <div className="mb-3 flex items-center gap-2">
          <ShieldCheck size={18} className="text-teal-700" />
          <h2 className="m-0 text-lg font-semibold text-ink">Data Quality Panel</h2>
        </div>
        <div className="grid gap-4 md:grid-cols-5">
          <Statistic title="raw_count" value={displayQuality.raw_count} />
          <Statistic title="clean_count" value={displayQuality.clean_count} />
          <Statistic title="dedup_count" value={displayQuality.dedup_count} />
          <Statistic title="noise_ratio" value={displayQuality.noise_ratio * 100} precision={1} suffix="%" />
          <Statistic title="languages" value={Object.keys(displayQuality.language_distribution).join(" / ") || "N/A"} />
        </div>
      </section>

      {topCard && (
        <section className="tool-panel p-5">
          <h2 className="m-0 text-lg font-semibold text-ink">Strategy Card Highlight</h2>
          <p className="mt-2 text-sm leading-6 text-slate-700">
            <strong>{topCard.title}</strong> covers <strong>{topCard.affected_ratio}</strong> of the deduplicated sample with{" "}
            <strong>{topCard.evidence_count}</strong> evidence comments. Confidence is <strong>{topCard.confidence}</strong> because{" "}
            {topCard.confidence_reason}
          </p>
        </section>
      )}

      <section className="grid gap-4 lg:grid-cols-2">
        <div className="tool-panel p-4">
          <h2 className="m-0 text-lg font-semibold text-ink">Sentiment Distribution</h2>
          <SentimentPie distribution={sentiment} />
          <p className="m-0 text-sm text-slate-500">Negative comments cover {formatPercent(negativeRatio)} of deduplicated comments.</p>
        </div>
        <div className="tool-panel p-4">
          <h2 className="m-0 text-lg font-semibold text-ink">Topic Clusters</h2>
          <ClusterBubble clusters={clusters} />
          <p className="m-0 text-sm text-slate-500">Bubble radius is capped so one large cluster cannot hide smaller themes.</p>
        </div>
        <div className="tool-panel p-4">
          <ClassificationBar rows={painpoints} title="Negative Labels TopN" />
          <p className="m-0 text-sm text-slate-500">Negative labels come from domain taxonomy and real classification counts.</p>
        </div>
        <div className="tool-panel p-4">
          <ClassificationBar rows={positives} title="Positive Labels TopN" />
          <p className="m-0 text-sm text-slate-500">Positive labels show content opportunities and product proof points.</p>
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <div className="tool-panel p-4">
          <h2 className="m-0 mb-3 text-lg font-semibold text-ink">All Word Cloud</h2>
          <WordCloudPanel words={wordclouds?.all_words || []} />
          <p className="m-0 mt-2 text-sm text-slate-500">{wordclouds?.explanations.all || "Run the task again to generate TF-IDF word clouds."}</p>
        </div>
        <div className="tool-panel p-4">
          <h2 className="m-0 mb-3 text-lg font-semibold text-ink">Positive Word Cloud</h2>
          <WordCloudPanel words={wordclouds?.positive_words || []} />
          <p className="m-0 mt-2 text-sm text-slate-500">{wordclouds?.explanations.positive || "High-weight words from positive comments."}</p>
        </div>
        <div className="tool-panel p-4">
          <h2 className="m-0 mb-3 text-lg font-semibold text-ink">Negative Word Cloud</h2>
          <WordCloudPanel words={wordclouds?.negative_words || []} />
          <p className="m-0 mt-2 text-sm text-slate-500">{wordclouds?.explanations.negative || "High-weight words from negative comments."}</p>
        </div>
      </section>

      <section className="tool-panel p-4">
        <h2 className="m-0 mb-3 text-lg font-semibold text-ink">LLM Insight Summary</h2>
        {insight ? (
          <List
            size="small"
            header={<p className="m-0 text-sm leading-6 text-slate-700">{insight.summary}</p>}
            dataSource={[...insight.positive_insights, ...insight.negative_insights, ...insight.recommendations]}
            renderItem={(item) => <List.Item>{item}</List.Item>}
          />
        ) : (
          <Empty description="No insights" />
        )}
      </section>

      <section className="tool-panel p-4">
        <h2 className="m-0 mb-3 text-lg font-semibold text-ink">Representative Comments</h2>
        <Table<CommentItem>
          rowKey="id"
          pagination={{ pageSize: 6 }}
          dataSource={dedupComments.slice(0, 24)}
          columns={[
            { title: "Platform", dataIndex: "platform", width: 90 },
            { title: "Comment", dataIndex: "cleaned_content" },
            { title: "Sentiment", dataIndex: "sentiment_label", width: 130 },
            {
              title: "Label",
              width: 180,
              render: (_, record) => <Tag>{record.painpoint || record.positive_attribution || "neutral"}</Tag>
            },
            {
              title: "Representative reason",
              dataIndex: "representative_reason",
              width: 240,
              render: (value?: string | null) => value || "-"
            }
          ]}
        />
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold text-ink">Strategy Cards</h2>
        <StrategyCards cards={cards} />
      </section>
    </div>
  );
}

function formatPercent(value: number) {
  return `${(value * 100).toFixed(1)}%`;
}
