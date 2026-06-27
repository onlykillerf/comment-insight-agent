"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Button, Empty, Table, Tag } from "antd";
import { Activity, BarChart3, CheckCircle2, FileText, GitBranch, MessageSquareText, Plus, ShieldCheck } from "lucide-react";
import { api } from "@/api/client";
import type { Task } from "@/types/task";

const demoScenarios = [
  {
    title: "NBA Draft",
    domain: "nba_draft",
    description: "Prospect hype, draft-order controversy, player templates, and team-fit narratives.",
    command: "python backend/scripts/run_demo_task.py --scenario nba_draft"
  },
  {
    title: "IAA Game Reviews",
    domain: "iaa_game",
    description: "Ad fatigue, onboarding friction, retention blockers, monetization pressure, and UX opportunities.",
    command: "python backend/scripts/run_demo_task.py --scenario iaa_game"
  },
  {
    title: "News Event",
    domain: "news",
    description: "Stance divergence, information transparency, trust risk, and clarification opportunities.",
    command: "python backend/scripts/run_demo_task.py --scenario news_event"
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
      { label: "Tasks", value: tasks.length, icon: Activity },
      { label: "Completed", value: tasks.filter((task) => task.status === "completed").length, icon: CheckCircle2 },
      { label: "Domains", value: new Set(tasks.map((task) => task.domain)).size, icon: GitBranch }
    ],
    [tasks]
  );

  return (
    <div className="space-y-6">
      <section className="grid gap-5 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="tool-panel p-6">
          <div className="mb-3 flex flex-wrap gap-2">
            <Tag color="cyan">Multi-Agent workflow</Tag>
            <Tag color="green">Evidence-grounded</Tag>
            <Tag color="gold">Mock-first</Tag>
            <Tag color="blue">Compliance-first</Tag>
          </div>
          <h1 className="m-0 max-w-4xl text-3xl font-semibold leading-tight text-ink">
            Turn public comments into sentiment insights, topic clusters, strategy cards, and A/B testing ideas.
          </h1>
          <p className="mt-4 max-w-3xl text-base leading-7 text-slate-600">
            Cross-Platform Comment Insight Agent is an open-source Multi-Agent framework for game, sports, esports,
            news, and community feedback analysis. It connects sample or compliant public data to data quality
            guardrails, domain taxonomy, clustering, representative comments, LLM summaries, and evidence-backed strategy cards.
          </p>
          <div className="mt-5 flex flex-wrap gap-3">
            <Link href="/tasks/new">
              <Button type="primary" icon={<Plus size={16} />}>
                Start Demo
              </Button>
            </Link>
            {latestCompleted && (
              <Link href={`/tasks/${latestCompleted.id}/report`}>
                <Button icon={<FileText size={16} />}>View Report</Button>
              </Link>
            )}
          </div>
        </div>
        <div className="tool-panel p-6">
          <h2 className="m-0 text-lg font-semibold text-ink">Why It Is Different</h2>
          <div className="mt-4 space-y-4 text-sm leading-6 text-slate-700">
            <div className="flex gap-3">
              <BarChart3 className="mt-1 shrink-0 text-teal-700" size={18} />
              <span>It does not stop at sentiment or word clouds; it turns comments into evidence-backed decisions.</span>
            </div>
            <div className="flex gap-3">
              <ShieldCheck className="mt-1 shrink-0 text-teal-700" size={18} />
              <span>Every report includes sample confidence, duplicate ratio, noise ratio, and small-sample warnings.</span>
            </div>
            <div className="flex gap-3">
              <MessageSquareText className="mt-1 shrink-0 text-teal-700" size={18} />
              <span>Strategy cards must trace back to real comments and explain why their confidence is high, medium, or low.</span>
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        {metrics.map((metric) => {
          const Icon = metric.icon;
          return (
            <div key={metric.label} className="metric-tile">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-500">{metric.label}</span>
                <Icon size={19} color="#1f7a8c" />
              </div>
              <div className="mt-4 text-3xl font-semibold text-ink">{metric.value}</div>
            </div>
          );
        })}
      </section>

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="m-0 text-lg font-semibold text-ink">Demo Scenarios</h2>
          <Link href="/tasks/new">
            <Button icon={<Plus size={16} />}>New Task</Button>
          </Link>
        </div>
        <div className="grid gap-4 lg:grid-cols-3">
          {demoScenarios.map((scenario) => (
            <article key={scenario.domain} className="tool-panel p-5">
              <div className="flex items-center justify-between gap-3">
                <h3 className="m-0 text-base font-semibold text-ink">{scenario.title}</h3>
                <Tag>{scenario.domain}</Tag>
              </div>
              <p className="min-h-[72px] text-sm leading-6 text-slate-600">{scenario.description}</p>
              <code className="block rounded-md bg-slate-950 p-3 text-xs leading-5 text-slate-100">{scenario.command}</code>
            </article>
          ))}
        </div>
      </section>

      <section className="tool-panel p-4">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="m-0 text-lg font-semibold text-ink">Recent Tasks</h2>
          <Link href="/tasks/new">
            <Button icon={<Plus size={16} />} />
          </Link>
        </div>
        {tasks.length ? (
          <Table<Task>
            loading={loading}
            rowKey="id"
            pagination={false}
            dataSource={tasks.slice(0, 8)}
            columns={[
              {
                title: "Task",
                dataIndex: "name",
                render: (name, record) => <Link href={`/tasks/${record.id}`}>{name}</Link>
              },
              { title: "Domain", dataIndex: "domain", width: 140 },
              {
                title: "Platforms",
                dataIndex: "platforms",
                render: (platforms: string[]) => platforms.map((platform) => <Tag key={platform}>{platform}</Tag>)
              },
              {
                title: "Status",
                dataIndex: "status",
                width: 130,
                render: (status: string) => <span className="status-pill bg-slate-100 text-slate-700">{status}</span>
              },
              {
                title: "Report",
                width: 110,
                render: (_, record) => (
                  <Link href={`/tasks/${record.id}/report`}>
                    <Button size="small">Open</Button>
                  </Link>
                )
              }
            ]}
          />
        ) : (
          <Empty description="No tasks yet. Run a demo scenario to see the full workflow." />
        )}
      </section>
    </div>
  );
}
