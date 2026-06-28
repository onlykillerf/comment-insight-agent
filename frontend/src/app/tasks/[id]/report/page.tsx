"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  Alert,
  Button,
  Descriptions,
  Empty,
  Image,
  List,
  Skeleton,
  Statistic,
  Table,
  Tabs,
  Tag,
  message
} from "antd";
import { Clipboard, Download, FlaskConical, Newspaper, RefreshCw, Scale, ShieldCheck, Sparkles, X } from "lucide-react";
import { api } from "@/api/client";
import { ClassificationBar, ClusterBubble, SentimentPie, WordCloudPanel } from "@/charts/Charts";
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

type EvidenceFilter = { type: "painpoint" | "positive" | "cluster" | "keyword"; value: string | number; label: string };

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
  const [strategies, setStrategies] = useState<StrategyCard[]>([]);
  const [filter, setFilter] = useState<EvidenceFilter | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const taskData = await api.getTask(taskId);
      setTask(taskData);
      if (taskData.status !== "completed") return;
      const [commentsData, sentimentData, painData, positiveData, clusterData, insightData, qualityData, wordcloudData, strategyData] = await Promise.all([
        api.getComments(taskId),
        api.getSentiment(taskId),
        api.getPainpoints(taskId),
        api.getPositiveAttributions(taskId),
        api.getClusters(taskId),
        api.getInsights(taskId),
        api.getQuality(taskId),
        api.getWordclouds(taskId),
        api.getStrategyCards(taskId)
      ]);
      setComments(commentsData);
      setSentiment(sentimentData.distribution);
      setPainpoints(painData);
      setPositives(positiveData);
      setClusters(clusterData);
      setInsight(insightData);
      setQuality(qualityData);
      setWordclouds(wordcloudData);
      setStrategies(strategyData);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "报告加载失败");
    } finally {
      setLoading(false);
    }
  }, [taskId]);

  useEffect(() => { load(); }, [load]);

  const dedupComments = useMemo(() => comments.filter((comment) => !comment.is_duplicate), [comments]);
  const filteredComments = useMemo(() => {
    if (!filter) return dedupComments.filter((comment) => comment.representative_reason).slice(0, 36);
    if (filter.type === "painpoint") return dedupComments.filter((comment) => comment.painpoint === filter.value);
    if (filter.type === "positive") return dedupComments.filter((comment) => comment.positive_attribution === filter.value);
    if (filter.type === "cluster") return dedupComments.filter((comment) => comment.cluster_id === filter.value);
    const keyword = String(filter.value).toLowerCase();
    return dedupComments.filter((comment) => comment.cleaned_content.toLowerCase().includes(keyword));
  }, [dedupComments, filter]);
  const negativeCount = (sentiment.negative || 0) + (sentiment.strong_negative || 0);
  const negativeRatio = dedupComments.length ? negativeCount / dedupComments.length : 0;
  const dominantTopic = clusters.filter((cluster) => !cluster.is_noise).sort((a, b) => b.cluster_size - a.cluster_size)[0];
  const displayQuality = quality || fallbackQualityFor(comments, dedupComments);
  const allContextMedia = insight?.context_media || [];
  const contextMedia = allContextMedia.filter((item) => item.included_in_summary);

  const selectCluster = (clusterId: number) => {
    const cluster = clusters.find((item) => item.cluster_id === clusterId);
    setFilter({ type: "cluster", value: clusterId, label: `主题：${cluster?.cluster_name || clusterId}` });
  };
  const selectKeyword = useCallback((word: string) => setFilter({ type: "keyword", value: word, label: `关键词：${word}` }), []);

  if (loading && !task) return <div className="tool-panel p-5"><Skeleton active /></div>;

  if (task && task.status !== "completed") {
    return (
      <div className="space-y-4">
        <Alert type={task.status === "failed" ? "error" : "info"} showIcon message="报告尚未生成" description={task.status === "failed" ? task.error_message || "任务执行失败" : "任务完成后，这里会展示完整分析报告。"} />
        <Link href={`/tasks/${task.id}`}><Button>返回任务状态</Button></Link>
      </div>
    );
  }

  const evidencePanel = <EvidenceTable filter={filter} comments={filteredComments} onClear={() => setFilter(null)} />;
  const tabs = [
    {
      key: "overview",
      label: "概览",
      children: (
        <div className="space-y-5">
          {displayQuality.warning && <Alert type="warning" showIcon message={displayQuality.warning} />}
          <section className="tool-panel p-5">
            <div className="mb-3 flex items-center gap-2"><Sparkles size={18} className="text-teal-700" /><h2 className="m-0 text-lg font-semibold text-ink">执行摘要</h2></div>
            <p className="m-0 text-sm leading-7 text-slate-700">{insight?.summary || "暂无摘要"}</p>
          </section>
          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
            <Metric title="样本可信度" value={displayQuality.sample_confidence_level} />
            <Metric title="重复率" value={displayQuality.duplicate_ratio * 100} suffix="%" precision={1} />
            <Metric title="负向占比" value={negativeRatio * 100} suffix="%" precision={1} />
            <Metric title="主导话题" value={dominantTopic?.cluster_name || "暂无"} />
            <Metric title="有效上下文图" value={contextMedia.length} suffix={`/ ${allContextMedia.length}`} />
          </section>
          <section className="grid gap-4 lg:grid-cols-2">
            <div className="tool-panel p-4"><h2 className="m-0 text-lg font-semibold text-ink">情绪分布</h2><SentimentPie distribution={sentiment} /><p className="m-0 text-sm text-slate-500">负向评论占去重样本的 {formatPercent(negativeRatio)}。</p></div>
            <DataQualityPanel quality={displayQuality} />
          </section>
          <section className="grid gap-4 lg:grid-cols-3">
            <WordCloudSection title="全量词云" words={wordclouds?.all_words || []} explanation={wordclouds?.explanations.all} onSelect={selectKeyword} />
            <WordCloudSection title="正向词云" words={wordclouds?.positive_words || []} explanation={wordclouds?.explanations.positive} onSelect={selectKeyword} />
            <WordCloudSection title="负向词云" words={wordclouds?.negative_words || []} explanation={wordclouds?.explanations.negative} onSelect={selectKeyword} />
          </section>
          {filter?.type === "keyword" && evidencePanel}
        </div>
      )
    },
    {
      key: "pain-points",
      label: "痛点与观点",
      children: (
        <div className="space-y-5">
          <section className="grid gap-4 lg:grid-cols-2">
            <div className="tool-panel p-4"><ClassificationBar rows={painpoints} title="争议与负向标签" onSelect={(category) => setFilter({ type: "painpoint", value: category, label: `负向标签：${category}` })} /><p className="m-0 text-sm text-slate-500">点击标签查看支撑该分类的原始评论。</p></div>
            <div className="tool-panel p-4"><ClassificationBar rows={positives} title="正向评价标签" onSelect={(category) => setFilter({ type: "positive", value: category, label: `正向标签：${category}` })} /><p className="m-0 text-sm text-slate-500">标签占比来自去重后的真实分类计数。</p></div>
          </section>
          {evidencePanel}
        </div>
      )
    },
    {
      key: "clusters",
      label: "主题聚类",
      children: (
        <div className="space-y-5">
          <section className="tool-panel p-4"><ClusterBubble clusters={clusters} onSelect={selectCluster} /><p className="m-0 text-sm text-slate-500">点击气泡下钻；气泡大小表示主题样本量，半径已限制。</p></section>
          <Table<Cluster> rowKey="cluster_id" pagination={false} dataSource={clusters} onRow={(record) => ({ onClick: () => selectCluster(record.cluster_id), className: "cursor-pointer" })} columns={[
            { title: "主题", dataIndex: "cluster_name" },
            { title: "样本", dataIndex: "cluster_size", width: 90 },
            { title: "占比", dataIndex: "cluster_ratio", width: 100, render: (value: number) => formatPercent(value) },
            { title: "关键词", dataIndex: "top_keywords", render: (values: string[]) => values.map((value) => <Tag key={value}>{value}</Tag>) },
            { title: "方法", dataIndex: "method", width: 110 }
          ]} />
          {evidencePanel}
        </div>
      )
    },
    {
      key: "evidence",
      label: "证据",
      children: (
        <div className="space-y-5">
          <MatchContext task={task} insight={insight} />
          <ContextMediaPanel media={contextMedia} reviewedCount={allContextMedia.length} />
          <section className="grid gap-4 lg:grid-cols-2">
            <InsightList title="关键观点" items={insight?.key_viewpoints || []} />
            <InsightList title="争议焦点" items={insight?.controversies || []} />
          </section>
          <section className="tool-panel p-4"><div className="mb-3 flex items-center gap-2"><Scale size={18} className="text-teal-700" /><h2 className="m-0 text-lg font-semibold text-ink">事实与观点边界</h2></div><List size="small" dataSource={[...(insight?.fact_opinion_gaps || []), ...(insight?.risks || [])]} renderItem={(item) => <List.Item>{item}</List.Item>} locale={{ emptyText: "暂无上下文对照结果" }} /></section>
          <EvidenceTable filter={null} comments={dedupComments.slice(0, 60)} onClear={() => undefined} />
        </div>
      )
    },
    {
      key: "strategy-cards",
      label: "策略卡片",
      children: <StrategyCards cards={strategies} />
    }
  ];

  return (
    <div className="space-y-5">
      {error && <Alert type="error" showIcon message="报告加载失败" description={error} />}
      {task && (
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div><div className="mb-2 flex gap-2"><Tag>{task.domain === "football" ? "足球" : "篮球"}</Tag><Tag>{task.board}</Tag></div><h1 className="m-0 text-2xl font-semibold text-ink">{task.match_name || task.name}</h1><p className="m-0 mt-1 text-sm text-slate-600">虎扑赛事评论洞察报告</p></div>
          <div className="flex gap-2"><Button icon={<RefreshCw size={16} />} onClick={load} aria-label="刷新报告" /><Link href={api.markdownUrl(taskId)} target="_blank"><Button icon={<Download size={16} />}>导出 Markdown</Button></Link></div>
        </div>
      )}
      <Tabs defaultActiveKey="overview" items={tabs} destroyInactiveTabPane={false} />
    </div>
  );
}

function Metric({ title, value, suffix, precision }: { title: string; value: string | number; suffix?: string; precision?: number }) {
  return <div className="metric-tile"><Statistic title={title} value={value} suffix={suffix} precision={precision} valueStyle={{ fontSize: typeof value === "string" ? 18 : 24 }} /></div>;
}

function DataQualityPanel({ quality }: { quality: DataQuality }) {
  return <section className="tool-panel p-5"><div className="mb-4 flex items-center gap-2"><ShieldCheck size={18} className="text-teal-700" /><h2 className="m-0 text-lg font-semibold text-ink">数据质量</h2></div><div className="grid grid-cols-2 gap-4 md:grid-cols-3"><Statistic title="原始" value={quality.raw_count} /><Statistic title="清洗" value={quality.clean_count} /><Statistic title="去重" value={quality.dedup_count} /><Statistic title="重复率" value={quality.duplicate_ratio * 100} precision={1} suffix="%" /><Statistic title="噪声率" value={quality.noise_ratio * 100} precision={1} suffix="%" /><Statistic title="语言" value={Object.keys(quality.language_distribution).join(" / ") || "未知"} /></div></section>;
}

function EvidenceTable({ filter, comments, onClear }: { filter: EvidenceFilter | null; comments: CommentItem[]; onClear: () => void }) {
  return <section className="tool-panel p-4"><div className="mb-3 flex flex-wrap items-center justify-between gap-3"><div><h2 className="m-0 text-lg font-semibold text-ink">{filter ? "筛选后的评论证据" : "典型评论证据"}</h2>{filter && <Tag className="mt-2" color="cyan">{filter.label} · {comments.length} 条</Tag>}</div>{filter && <Button icon={<X size={16} />} onClick={onClear}>清除筛选</Button>}</div><Table<CommentItem> rowKey="id" pagination={{ pageSize: 8 }} dataSource={comments} locale={{ emptyText: filter ? "没有匹配该条件的评论" : "暂无代表评论" }} columns={[
    { title: "评论", dataIndex: "cleaned_content" },
    { title: "情绪", dataIndex: "sentiment_label", width: 100, render: (value?: string | null) => value || "中性" },
    { title: "标签", width: 170, render: (_, record) => <Tag>{record.painpoint || record.positive_attribution || "中性"}</Tag> },
    { title: "点赞", dataIndex: "like_count", width: 80 },
    { title: "代表性原因", dataIndex: "representative_reason", width: 230, render: (value?: string | null) => value || "按分类或主题命中" }
  ]} /></section>;
}

function WordCloudSection({ title, words, explanation, onSelect }: { title: string; words: WordClouds["all_words"]; explanation?: string; onSelect: (word: string) => void }) {
  return <div className="tool-panel p-4"><h2 className="m-0 mb-3 text-lg font-semibold text-ink">{title}</h2><WordCloudPanel words={words} onSelect={onSelect} /><p className="m-0 mt-2 text-sm text-slate-500">{explanation || "TF-IDF 领域加权；点击关键词查看评论证据。"}</p></div>;
}

function MatchContext({ task, insight }: { task: Task | null; insight: Insight | null }) {
  if (!task) return null;
  return <section className="grid gap-4 lg:grid-cols-2"><div className="tool-panel p-5"><h2 className="m-0 mb-3 text-lg font-semibold text-ink">比赛与帖子</h2><Descriptions size="small" column={1}><Descriptions.Item label="对阵">{task.home_team} vs {task.away_team}</Descriptions.Item><Descriptions.Item label="阶段">{task.match_stage || "-"}</Descriptions.Item><Descriptions.Item label="日期">{task.match_date || "-"}</Descriptions.Item><Descriptions.Item label="帖子">{task.thread_urls.length ? task.thread_urls.map((url, index) => <a className="mr-3" href={url} target="_blank" rel="noreferrer" key={url}>帖子 {index + 1}</a>) : "离线或上传样本"}</Descriptions.Item></Descriptions></div><div className="tool-panel p-5"><div className="mb-3 flex items-center gap-2"><Newspaper size={18} className="text-teal-700" /><h2 className="m-0 text-lg font-semibold text-ink">新闻背景</h2></div><p className="m-0 text-sm leading-6 text-slate-700">{insight?.news_context_summary || "本次未提供相关新闻背景。"}</p></div></section>;
}

function ContextMediaPanel({ media, reviewedCount }: { media: Insight["context_media"]; reviewedCount: number }) {
  return <section className="tool-panel p-4"><h2 className="m-0 mb-1 text-lg font-semibold text-ink">主帖与权威来源图像证据</h2><p className="m-0 mb-4 text-sm text-slate-500">只分析主帖、数据帖、裁判报告、新闻或官网信息图；评论区图片不参与。</p>{media.length ? <div className="grid gap-4 md:grid-cols-2">{media.map((item) => <article className="border border-slate-200 p-3" key={item.source_id}><div className="mb-2 flex justify-between gap-3"><a href={item.source_url} target="_blank" rel="noreferrer" className="font-medium text-ink">{item.title || "未命名来源"}</a><Tag>{item.authority_level}</Tag></div><Image.PreviewGroup><div className="mb-3 flex gap-2 overflow-x-auto">{item.image_urls.slice(0, 2).map((url) => <Image key={url} src={api.mediaUrl(url)} alt="赛事上下文信息图" width={160} height={112} className="object-cover" />)}</div></Image.PreviewGroup><p className="m-0 text-sm leading-6 text-slate-700">{item.summary}</p>{!!item.data_points?.length && <List size="small" dataSource={item.data_points} renderItem={(point) => <List.Item>{point}</List.Item>} />}</article>)}</div> : <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={reviewedCount ? `已审查 ${reviewedCount} 张，均未达到摘要信息量要求` : "没有候选信息图"} />}</section>;
}

function InsightList({ title, items }: { title: string; items: string[] }) {
  return <div className="tool-panel p-4"><h2 className="m-0 mb-2 text-lg font-semibold text-ink">{title}</h2>{items.length ? <List size="small" dataSource={items} renderItem={(item) => <List.Item>{item}</List.Item>} /> : <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无" />}</div>;
}

function StrategyCards({ cards }: { cards: StrategyCard[] }) {
  const copyCard = async (card: StrategyCard) => {
    try { await navigator.clipboard.writeText(JSON.stringify(card, null, 2)); message.success("策略卡 JSON 已复制"); }
    catch { message.error("浏览器未授予剪贴板权限"); }
  };
  const createDraft = async (card: StrategyCard) => {
    try { const draft = await api.createABTestDraft(card.id); message.success(`已创建草案 #${draft.id}`); }
    catch (caught) { message.error(caught instanceof Error ? caught.message : "草案创建失败"); }
  };
  if (!cards.length) return <Empty description="没有达到至少两条证据门槛的策略卡" />;
  return <div className="grid gap-4 lg:grid-cols-2">{cards.map((card) => <article key={card.id} className="tool-panel p-5"><div className="flex items-start justify-between gap-3"><div><Tag>{card.card_type}</Tag><h2 className="m-0 mt-2 text-lg font-semibold text-ink">{card.title}</h2></div><Tag color={card.confidence === "high" ? "green" : card.confidence === "medium" ? "gold" : "default"}>{card.confidence} 可信度</Tag></div><div className="my-4 grid grid-cols-3 gap-3"><Statistic title="证据数" value={card.evidence_count} /><Statistic title="样本量" value={card.sample_size} /><Statistic title="影响占比" value={card.affected_ratio * 100} precision={1} suffix="%" /></div><Alert type="info" showIcon message="为什么可信" description={card.confidence_reason} /><h3 className="mb-1 mt-4 text-sm font-semibold">建议动作</h3><List size="small" dataSource={card.suggested_actions} renderItem={(item) => <List.Item>{item}</List.Item>} /><p className="text-sm text-slate-600"><strong>预期影响：</strong>{card.expected_impact}</p><h3 className="mb-2 mt-4 text-sm font-semibold">证据评论</h3><List size="small" dataSource={card.evidence_comments} renderItem={(item) => <List.Item><span>{item.content}</span><Tag className="ml-2">赞 {item.like_count || 0}</Tag></List.Item>} /><div className="mt-4 flex flex-wrap gap-2"><Button icon={<Clipboard size={16} />} onClick={() => copyCard(card)}>复制卡片</Button><Button icon={<Download size={16} />} href={api.strategyCardExportUrl(card.id)} target="_blank">导出 JSON</Button><Button type="primary" icon={<FlaskConical size={16} />} onClick={() => createDraft(card)}>创建 A/B 草案</Button></div></article>)}</div>;
}

function fallbackQualityFor(comments: CommentItem[], dedupComments: CommentItem[]): DataQuality {
  return { raw_count: comments.length, clean_count: comments.length, dedup_count: dedupComments.length, duplicate_ratio: comments.length ? (comments.length - dedupComments.length) / comments.length : 0, noise_ratio: 0, language_distribution: {}, sample_confidence_level: dedupComments.length < 100 ? "low" : dedupComments.length < 300 ? "medium" : "high", warning: dedupComments.length < 100 ? "样本量较小，仅适合演示" : "" };
}

function formatPercent(value: number) { return `${(value * 100).toFixed(1)}%`; }
