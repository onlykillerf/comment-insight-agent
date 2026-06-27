"use client";

import type { StrategyCard } from "@/types/task";
import { Badge, Button, Empty, Tag, Tooltip } from "antd";
import { FlaskConical } from "lucide-react";

const priorityColor: Record<string, string> = {
  high: "red",
  medium: "orange",
  low: "blue"
};

const confidenceColor: Record<string, string> = {
  high: "green",
  medium: "gold",
  low: "default"
};

export function StrategyCards({ cards }: { cards: StrategyCard[] }) {
  if (!cards.length) {
    return <Empty description="暂无有证据支撑的策略卡片" />;
  }
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {cards.map((card) => (
        <article key={card.id} className="tool-panel p-5">
          <div className="mb-3 flex items-start justify-between gap-3">
            <div>
              <h3 className="m-0 text-base font-semibold text-ink">{card.title}</h3>
              <div className="mt-2 flex flex-wrap gap-2">
                <Tag color="cyan">{card.type}</Tag>
                <Tag color={priorityColor[card.priority]}>{card.priority}</Tag>
                <Tooltip title={card.confidence_reason}>
                  <Tag color={confidenceColor[card.confidence]}>confidence: {card.confidence}</Tag>
                </Tooltip>
                <Badge color="#1f7a8c" text={card.affected_ratio} />
                <Badge color="#64748b" text={`${card.evidence_count}/${card.sample_size} evidence`} />
              </div>
            </div>
            <Button icon={<FlaskConical size={16} />} />
          </div>
          <p className="text-sm leading-6 text-slate-700">{card.problem_or_opportunity}</p>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <div>
              <div className="mb-2 text-xs font-semibold uppercase text-slate-500">Evidence</div>
              <ul className="m-0 space-y-2 pl-4 text-sm text-slate-700">
                {card.evidence_comments.map((comment) => (
                  <li key={comment}>{comment}</li>
                ))}
              </ul>
            </div>
            <div>
              <div className="mb-2 text-xs font-semibold uppercase text-slate-500">Actions</div>
              <ul className="m-0 space-y-2 pl-4 text-sm text-slate-700">
                {card.suggested_actions.map((action) => (
                  <li key={action}>{action}</li>
                ))}
              </ul>
            </div>
          </div>
          <div className="mt-4 rounded-md bg-slate-50 p-3 text-sm text-slate-700">{card.expected_impact}</div>
        </article>
      ))}
    </div>
  );
}
