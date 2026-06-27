"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Alert, Button, Descriptions, message, Tag } from "antd";
import { Download, Play } from "lucide-react";
import { api } from "@/api/client";
import { StatusSteps } from "@/components/StatusSteps";
import type { DataQuality, Task } from "@/types/task";

export default function TaskDetailPage() {
  const params = useParams<{ id: string }>();
  const taskId = Number(params.id);
  const [task, setTask] = useState<Task | null>(null);
  const [quality, setQuality] = useState<DataQuality | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");

  const load = async () => {
    setError("");
    try {
      const taskData = await api.getTask(taskId);
      setTask(taskData);
      setQuality(await api.getQuality(taskId).catch(() => null));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "任务加载失败");
    }
  };

  useEffect(() => {
    load();
  }, [taskId]);

  const run = async () => {
    setRunning(true);
    setError("");
    try {
      await api.runTask(taskId);
      await load();
      message.success("分析完成");
    } catch (caught) {
      const messageText = caught instanceof Error ? caught.message : "运行失败";
      setError(messageText);
      message.error("运行失败");
      await load();
    } finally {
      setRunning(false);
    }
  };

  if (!task && !error) {
    return <div className="tool-panel p-5">Loading...</div>;
  }

  return (
    <div className="space-y-5">
      {error && <Alert type="error" showIcon message="任务错误" description={error} />}
      {task && (
        <>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h1 className="m-0 text-2xl font-semibold text-ink">{task.name}</h1>
              <p className="m-0 mt-1 text-sm text-slate-600">Task #{task.id}</p>
            </div>
            <div className="flex gap-2">
              <Button icon={<Play size={16} />} type="primary" loading={running} onClick={run}>
                运行
              </Button>
              <Link href={`/tasks/${task.id}/report`}>
                <Button icon={<Download size={16} />}>报告</Button>
              </Link>
            </div>
          </div>
          <section className="tool-panel p-5">
            <div className="mb-4 flex flex-wrap gap-2">
              <Tag color={task.data_source === "mock" || task.data_source === "csv" ? "gold" : "blue"}>
                data source: {task.data_source}
              </Tag>
              <Tag color={task.enable_llm ? "cyan" : "default"}>{task.enable_llm ? "LLM enabled" : "LLM disabled"}</Tag>
              <Tag color={task.enable_image_analysis ? "geekblue" : "default"}>
                {task.enable_image_analysis ? `Vision enabled · max ${task.max_image_comments}` : "Vision disabled"}
              </Tag>
              {quality?.warning && <Tag color="orange">{quality.warning}</Tag>}
              {quality && <Tag color="purple">sample confidence: {quality.sample_confidence_level}</Tag>}
            </div>
            <StatusSteps progress={task.progress || {}} />
          </section>
          <section className="tool-panel p-5">
            <Descriptions column={2} size="small">
              <Descriptions.Item label="状态">{task.status}</Descriptions.Item>
              <Descriptions.Item label="运动">{task.domain === "football" ? "足球" : "篮球"}</Descriptions.Item>
              <Descriptions.Item label="虎扑板块"><Tag>{task.board}</Tag></Descriptions.Item>
              <Descriptions.Item label="比赛">{task.match_name || `${task.home_team} vs ${task.away_team}`}</Descriptions.Item>
              <Descriptions.Item label="比赛阶段">{task.match_stage || "-"}</Descriptions.Item>
              <Descriptions.Item label="比赛日期">{task.match_date || "-"}</Descriptions.Item>
              <Descriptions.Item label="虎扑帖子">{task.thread_urls.length || (task.data_source === "mock" ? "Mock" : 0)}</Descriptions.Item>
              <Descriptions.Item label="新闻上下文">{task.news_urls.length + (task.news_context ? 1 : 0)} 条</Descriptions.Item>
              <Descriptions.Item label="关键词">{task.keywords.join(" / ")}</Descriptions.Item>
              <Descriptions.Item label="最大评论数">{task.max_comments}</Descriptions.Item>
              <Descriptions.Item label="配图理解">{task.enable_image_analysis ? `Qwen/Qwen3.5-4B，最多 ${task.max_image_comments} 条` : "关闭"}</Descriptions.Item>
              <Descriptions.Item label="相似度阈值">{task.similarity_threshold}</Descriptions.Item>
              <Descriptions.Item label="语义查询">{task.semantic_query}</Descriptions.Item>
            </Descriptions>
          </section>
        </>
      )}
    </div>
  );
}
