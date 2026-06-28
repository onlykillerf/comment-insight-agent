"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Alert, Button, Empty, Table, Tag, message } from "antd";
import { Activity, BarChart3, CheckCircle2, FileText, MessageSquareText, Play, Plus, ShieldCheck, Trophy } from "lucide-react";
import { api } from "@/api/client";
import type { Task } from "@/types/task";

const demos = [
  {
    title: "NBA 单场赛后讨论",
    sport: "basketball",
    board: "NBA",
    description: "围绕具体系列赛场次，分析球员表现、战术调整、关键球与判罚争议。",
    action: "basketball" as const
  },
  {
    title: "世界杯单场舆情",
    sport: "football",
    board: "世界杯",
    description: "聚焦进攻组织、防线表现、VAR 判罚、教练换人与球迷立场。",
    action: "football" as const
  }
];

export default function DashboardPage() {
  const router = useRouter();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [demoLoading, setDemoLoading] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.listTasks().then(setTasks).catch((caught) => setError(caught instanceof Error ? caught.message : "任务列表加载失败")).finally(() => setLoading(false));
  }, []);

  const startDemo = async (scenario: "basketball" | "football") => {
    setDemoLoading(scenario);
    setError("");
    try {
      const task = await api.createDemo(scenario);
      message.success("Demo 已加入分析队列");
      router.push(`/tasks/${task.id}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Demo 启动失败");
    } finally {
      setDemoLoading(null);
    }
  };

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
              虎扑赛事评论洞察 Agent
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

      {error && <Alert type="error" showIcon message="服务暂不可用" description={error} />}

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
            <p className="m-0 mt-1 text-sm text-slate-500">无需命令行，使用 Mock 数据与 MockLLM 在浏览器内跑完整流程。</p>
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
              <Button
                type="primary"
                icon={<Play size={16} />}
                loading={demoLoading === demo.action}
                disabled={demoLoading !== null && demoLoading !== demo.action}
                onClick={() => startDemo(demo.action)}
              >
                一键运行 Demo
              </Button>
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
              { title: "来源", dataIndex: "data_source", width: 130, render: (value: string) => sourceText(value) },
              { title: "状态", dataIndex: "status", width: 110, render: (status: string) => <Tag color={statusColor(status)}>{statusText(status)}</Tag> },
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

function statusText(status: string) {
  return ({ created: "待运行", queued: "排队中", running: "运行中", completed: "已完成", failed: "失败", cancelled: "已取消" } as Record<string, string>)[status] || status;
}

function statusColor(status: string) {
  return ({ completed: "green", failed: "red", cancelled: "default", queued: "gold", running: "blue" } as Record<string, string>)[status] || "default";
}

function sourceText(source: string) {
  return ({ mock: "Mock 演示", hupu_public: "虎扑公开帖子", csv: "CSV 上传", json: "JSON 上传", mediacrawler: "MediaCrawler 导出" } as Record<string, string>)[source] || source;
}
