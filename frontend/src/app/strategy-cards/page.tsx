"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button, Empty, Select, Statistic } from "antd";
import { api } from "@/api/client";
import { StrategyCards } from "@/components/StrategyCards";
import type { StrategyCard, Task } from "@/types/task";

export default function StrategyCardsPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [task, setTask] = useState<Task | null>(null);
  const [cards, setCards] = useState<StrategyCard[]>([]);

  useEffect(() => {
    api.listTasks().then(async (items) => {
      const completed = items.filter((item) => item.status === "completed");
      setTasks(completed);
      const first = completed[0];
      if (first) {
        await selectTask(first.id, completed);
      }
    });
  }, []);

  const selectTask = async (taskId: number, sourceTasks = tasks) => {
    const selected = sourceTasks.find((item) => item.id === taskId) || null;
    setTask(selected);
    setCards(await api.getStrategyCards(taskId));
  };

  const evidenceTotal = cards.reduce((sum, card) => sum + card.evidence_count, 0);

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="m-0 text-2xl font-semibold text-ink">Evidence-grounded Strategy Cards</h1>
          <p className="m-0 mt-1 text-sm text-slate-600">Every visible card must trace back to real comments and confidence reasons.</p>
        </div>
        {task && (
          <div className="flex gap-2">
            <Select
              className="min-w-[260px]"
              value={task.id}
              options={tasks.map((item) => ({ value: item.id, label: `#${item.id} ${item.name}` }))}
              onChange={(value) => selectTask(value)}
            />
            <Link href={`/tasks/${task.id}/report`}>
              <Button>Open Report</Button>
            </Link>
          </div>
        )}
      </div>

      <section className="grid gap-4 md:grid-cols-3">
        <div className="metric-tile">
          <Statistic title="Cards" value={cards.length} />
        </div>
        <div className="metric-tile">
          <Statistic title="Evidence comments" value={evidenceTotal} />
        </div>
        <div className="metric-tile">
          <Statistic title="High confidence" value={cards.filter((card) => card.confidence === "high").length} />
        </div>
      </section>

      {cards.length ? <StrategyCards cards={cards} /> : <Empty description="No evidence-grounded strategy cards yet. Run a completed demo task first." />}
    </div>
  );
}
