"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Button, Empty, Table, Tag } from "antd";
import { Activity, BarChart3, CheckCircle2, FileText, MessageSquareText, Plus, ShieldCheck, Trophy } from "lucide-react";
import { api } from "@/api/client";
import type { Task } from "@/types/task";

const demos = [
  {
    title: "NBA 单场赛后讨论",
    sport: "basketball",
    board: "NBA",
    description: "围绕具体系列赛场次，分析球员表现、战术调整、关键球与判罚争议。",
    command: "python backend/scripts/run_demo_task.py --scenario nba_game"
  },
  {
    title: "世界杯单场舆情",
    sport: "football",
    board: "世界杯",
    description: "聚焦进攻组织、防线表现、VAR 判罚、教练换人与球迷立场。",
    command: "python backend/scripts/run_demo_task.py --scenario world_cup_game"
  }
];

export default function DashboardPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .listTasks()
      .then(setTasks)
      .finally(() => setLoading(false));
  }, []);

  const latestCompleted = tasks.find((task) => task.status === "completed");
  const metrics = useMemo(
    () => [
      { label: "赛事任务", value: tasks.length, icon: Activity },
      { label: "已完成", value: tasks.filter((task) => task.status === "completed").length, icon: CheckCircle2 },
      { label: "篮球", value: tasks.filter((task) => task.domain === "basketball").length, icon: Trophy },
      { label: "足球", value: tasks.filter((task) => task.domain === "football").length, icon: BarChart3 }
    ],
    [tasks]
  );

  return (
    <div className="space-y-6">
      <section className="app-band px-6 py-7">
        <div className="flex flex-wrap items-end justify-between gap-5">
          <div className="max-w-3xl">
            <div className="mb-2 flex items-center gap-2 text-sm font-medium text-teal-700">
              <MessageSquareText size={17} />
              Hupu Sports Comment Insight Agent
            </div>
            <h1 className="m-0 text-3xl font-semibold text-ink">从一场比赛，看清虎扑球迷在讨论什么</h1>
            <p className="m-0 mt-3 text-sm leading-6 text-slate-600">
              选择篮球或足球板块，指定具体比赛与公开帖子，将评论转化为情绪分布、主题聚类、典型观点和新闻上下文对照。
            </p>
          </div>
          <div className="flex gap-2">
            <Link href="/tasks/new">
              <Button type="primary" icon={<Plus size={16} />}>新建比赛分析</Button>
            </Link>
            {latestCompleted && (
              <Link href={`/tasks/${latestCompleted.id}/report`}>
                <Button icon={<FileText size={16} />}>查看最新报告</Button>
              </Link>
            )}
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-4">
        {metrics.map((metric) => {
          const Icon = metric.icon;
          return (
            <div className="metric-tile" key={metric.label}>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-500">{metric.label}</span>
                <Icon size={17} className="text-teal-700" />
              </div>
              <strong className="mt-2 block text-2xl text-ink">{metric.value}</strong>
            </div>
          );
        })}
      </section>

      <section>
        <div className="mb-3 flex items-center justify-between">
          <div>
            <h2 className="m-0 text-lg font-semibold text-ink">赛事分析模板</h2>
            <p className="m-0 mt-1 text-sm text-slate-500">产品只保留篮球与足球两条主线。</p>
          </div>
          <Tag icon={<ShieldCheck size={13} />}>公开页面 / Mock-first</Tag>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          {demos.map((demo) => (
            <article key={demo.sport} className="tool-panel p-5">
              <div className="flex items-center justify-between gap-3">
                <h3 className="m-0 text-base font-semibold text-ink">{demo.title}</h3>
                <Tag>{demo.board}</Tag>
              </div>
              <p className="min-h-[48px] text-sm leading-6 text-slate-600">{demo.description}</p>
              <code className="block rounded-md bg-slate-950 p-3 text-xs leading-5 text-slate-100">{demo.command}</code>
            </article>
          ))}
        </div>
      </section>

      <section className="tool-panel p-4">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="m-0 text-lg font-semibold text-ink">最近任务</h2>
          <Link href="/tasks/new"><Button icon={<Plus size={16} />} /></Link>
        </div>
        {tasks.length ? (
          <Table<Task>
            rowKey="id"
            loading={loading}
            pagination={{ pageSize: 8 }}
            dataSource={tasks}
            columns={[
              { title: "比赛", dataIndex: "match_name", render: (value: string, row) => value || row.name },
              {
                title: "运动 / 板块",
                width: 170,
                render: (_, row) => <><Tag>{row.domain === "football" ? "足球" : "篮球"}</Tag><Tag>{row.board}</Tag></>
              },
              { title: "来源", dataIndex: "data_source", width: 130 },
              { title: "状态", dataIndex: "status", width: 110, render: (status: string) => <Tag color={status === "completed" ? "green" : "blue"}>{status}</Tag> },
              {
                title: "操作",
                width: 150,
                render: (_, row) => (
                  <div className="flex gap-3">
                    <Link href={`/tasks/${row.id}`}>状态</Link>
                    {row.status === "completed" && <Link href={`/tasks/${row.id}/report`}>报告</Link>}
                  </div>
                )
              }
            ]}
          />
        ) : (
          <Empty description="还没有赛事分析任务" />
        )}
      </section>
    </div>
  );
}
