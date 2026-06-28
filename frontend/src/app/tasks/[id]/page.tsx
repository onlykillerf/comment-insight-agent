"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Alert, Button, Descriptions, Skeleton, Tag, message } from "antd";
import { FileText, Play, RefreshCw, RotateCcw, Square } from "lucide-react";
import { api } from "@/api/client";
import { StatusSteps } from "@/components/StatusSteps";
import type { DataQuality, Task } from "@/types/task";

const ACTIVE_STATUSES = new Set(["queued", "running"]);

export default function TaskDetailPage() {
  const params = useParams<{ id: string }>();
  const taskId = Number(params.id);
  const [task, setTask] = useState<Task | null>(null);
  const [quality, setQuality] = useState<DataQuality | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState("");
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    let mounted = true;
    const refresh = async () => {
      try {
        const taskData = await api.getTask(taskId);
        if (!mounted) return;
        setTask(taskData);
        setError("");
        if (taskData.status === "completed") {
          setQuality(await api.getQuality(taskId).catch(() => null));
        }
        if (ACTIVE_STATUSES.has(taskData.status)) {
          timerRef.current = setTimeout(refresh, 1200);
        }
      } catch (caught) {
        if (mounted) setError(caught instanceof Error ? caught.message : "任务加载失败");
      }
    };
    refresh();
    return () => {
      mounted = false;
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [taskId]);

  const runAction = async (action: "run" | "cancel" | "retry") => {
    setActionLoading(true);
    setError("");
    try {
      if (action === "cancel") {
        await api.cancelTask(taskId);
        message.success("已提交取消请求");
      } else if (action === "retry") {
        await api.retryTask(taskId);
        message.success("任务已重新加入队列");
      } else {
        await api.runTask(taskId);
        message.success("任务已加入队列");
      }
      setTask(await api.getTask(taskId));
      window.location.reload();
    } catch (caught) {
      const text = caught instanceof Error ? caught.message : "操作失败";
      setError(text);
      message.error(text);
    } finally {
      setActionLoading(false);
    }
  };

  if (!task && !error) return <div className="tool-panel p-5"><Skeleton active /></div>;

  return (
    <div className="space-y-5">
      {error && <Alert type="error" showIcon message="任务错误" description={error} />}
      {task && (
        <>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="mb-2 flex items-center gap-2"><Tag color={statusColor(task.status)}>{statusText(task.status)}</Tag><span className="text-sm text-slate-500">任务 #{task.id}</span></div>
              <h1 className="m-0 text-2xl font-semibold text-ink">{task.name}</h1>
            </div>
            <div className="flex flex-wrap gap-2">
              {task.status === "created" && <Button type="primary" icon={<Play size={16} />} loading={actionLoading} onClick={() => runAction("run")}>开始分析</Button>}
              {ACTIVE_STATUSES.has(task.status) && <Button danger icon={<Square size={16} />} loading={actionLoading} onClick={() => runAction("cancel")}>取消任务</Button>}
              {["failed", "cancelled"].includes(task.status) && <Button type="primary" icon={<RotateCcw size={16} />} loading={actionLoading} onClick={() => runAction("retry")}>重试</Button>}
              <Button icon={<RefreshCw size={16} />} onClick={() => window.location.reload()} aria-label="刷新任务" />
              <Link href={`/tasks/${task.id}/report`}><Button icon={<FileText size={16} />} disabled={task.status !== "completed"}>查看报告</Button></Link>
            </div>
          </div>

          {task.error_message && <Alert type={task.status === "failed" ? "error" : "warning"} showIcon message={task.status === "failed" ? "任务执行失败" : "任务提示"} description={task.error_message} />}

          <section className="tool-panel p-5">
            <div className="mb-4 flex flex-wrap gap-2">
              <Tag color={task.data_source === "mock" ? "gold" : "blue"}>数据：{sourceText(task.data_source)}</Tag>
              <Tag color={task.llm_mode === "mock" ? "gold" : "cyan"}>洞察：{task.enable_llm ? (task.llm_mode === "mock" ? "MockLLM" : "已配置 LLM") : "关闭"}</Tag>
              <Tag color={task.enable_image_analysis ? "geekblue" : "default"}>上下文图像：{task.enable_image_analysis ? `最多 ${task.max_image_comments} 张` : "关闭"}</Tag>
              <Tag>第 {task.run_attempt || 0} 次运行</Tag>
              {quality?.warning && <Tag color="orange">{quality.warning}</Tag>}
            </div>
            <StatusSteps progress={task.progress || {}} />
          </section>

          <section className="tool-panel p-5">
            <Descriptions column={{ xs: 1, md: 2 }} size="small">
              <Descriptions.Item label="运动">{task.domain === "football" ? "足球" : "篮球"}</Descriptions.Item>
              <Descriptions.Item label="虎扑板块"><Tag>{task.board}</Tag></Descriptions.Item>
              <Descriptions.Item label="比赛">{task.match_name || `${task.home_team} vs ${task.away_team}`}</Descriptions.Item>
              <Descriptions.Item label="比赛阶段">{task.match_stage || "-"}</Descriptions.Item>
              <Descriptions.Item label="数据来源">{sourceText(task.data_source)}</Descriptions.Item>
              <Descriptions.Item label="有效样本上限">{task.max_comments}</Descriptions.Item>
              <Descriptions.Item label="排队时间">{formatTime(task.queued_at)}</Descriptions.Item>
              <Descriptions.Item label="开始时间">{formatTime(task.started_at)}</Descriptions.Item>
              <Descriptions.Item label="结束时间">{formatTime(task.finished_at)}</Descriptions.Item>
              <Descriptions.Item label="新闻上下文">{task.news_urls.length + (task.news_context ? 1 : 0)} 条</Descriptions.Item>
              <Descriptions.Item label="关键词">{task.keywords.join(" / ") || "-"}</Descriptions.Item>
              <Descriptions.Item label="分析问题">{task.semantic_query}</Descriptions.Item>
            </Descriptions>
          </section>
        </>
      )}
    </div>
  );
}

function statusText(status: string) {
  return ({ created: "待运行", queued: "排队中", running: "运行中", completed: "已完成", failed: "失败", cancelled: "已取消" } as Record<string, string>)[status] || status;
}

function statusColor(status: string) {
  return ({ completed: "green", failed: "red", queued: "gold", running: "blue" } as Record<string, string>)[status] || "default";
}

function sourceText(source: string) {
  return ({ mock: "Mock 演示", hupu_public: "虎扑公开帖子", csv: "CSV 上传", json: "JSON 上传", mediacrawler: "MediaCrawler 导出" } as Record<string, string>)[source] || source;
}

function formatTime(value?: string | null) {
  return value ? new Date(value).toLocaleString("zh-CN") : "-";
}
