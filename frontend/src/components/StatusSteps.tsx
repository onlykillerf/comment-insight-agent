"use client";

import { Steps, Table, Tag } from "antd";
import type { AgentProgress } from "@/types/task";

const names: Record<string, string> = {
  understand: "任务理解",
  route: "平台路由",
  crawl: "采集/导入",
  clean: "清洗",
  dedup: "去重",
  quality: "数据质量",
  sentiment: "情绪",
  attribute: "归因/痛点",
  cluster: "聚类",
  sample: "代表评论",
  insight: "洞察",
  strategy: "策略",
  visualize: "可视化"
};

export function StatusSteps({ progress }: { progress: Record<string, AgentProgress | string> }) {
  const keys = Object.keys(names);
  const normalized = keys.map((key) => ({ key, ...normalizeProgress(progress[key]) }));
  return (
    <div className="space-y-4">
      <Steps
        size="small"
        items={normalized.map((item) => ({
          title: names[item.key],
          status: item.status === "completed" ? "finish" : item.status === "running" ? "process" : item.status === "error" ? "error" : "wait"
        }))}
      />
      <Table
        size="small"
        pagination={false}
        rowKey="key"
        dataSource={normalized}
        columns={[
          { title: "Agent", dataIndex: "key", render: (key: string) => names[key] },
          {
            title: "状态",
            dataIndex: "status",
            render: (status: string) => <Tag color={statusColor(status)}>{status}</Tag>
          },
          {
            title: "耗时",
            dataIndex: "duration_ms",
            render: (value?: number | null) => (typeof value === "number" ? `${value} ms` : "-")
          },
          { title: "输入摘要", dataIndex: "input_summary", render: (value?: string) => value || "-" },
          { title: "输出摘要", dataIndex: "output_summary", render: (value?: string) => value || "-" },
          { title: "错误信息", dataIndex: "error", render: (value?: string) => value || "-" }
        ]}
      />
    </div>
  );
}

function normalizeProgress(value: AgentProgress | string | undefined): AgentProgress {
  if (!value) {
    return { status: "pending", duration_ms: null, error: "" };
  }
  if (typeof value === "string") {
    return { status: value, duration_ms: null, error: "" };
  }
  return value;
}

function statusColor(status: string) {
  if (status === "completed") {
    return "green";
  }
  if (status === "running") {
    return "blue";
  }
  if (status === "error") {
    return "red";
  }
  return "default";
}
