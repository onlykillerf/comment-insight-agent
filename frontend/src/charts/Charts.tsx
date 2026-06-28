"use client";

import { useEffect, useMemo, useRef } from "react";
import ReactECharts from "echarts-for-react";
import type { ClassificationRow, Cluster, WordCloudItem } from "@/types/task";

export function SentimentPie({ distribution }: { distribution: Record<string, number> }) {
  return (
    <ReactECharts
      style={{ height: 280 }}
      option={{
        tooltip: { trigger: "item" },
        series: [
          {
            type: "pie",
            radius: ["42%", "70%"],
            data: Object.entries(distribution).map(([name, value]) => ({ name, value }))
          }
        ]
      }}
    />
  );
}

export function ClassificationBar({ rows, title, onSelect }: { rows: ClassificationRow[]; title: string; onSelect?: (category: string) => void }) {
  return (
    <ReactECharts
      style={{ height: 300 }}
      option={{
        title: { text: title, left: 0, textStyle: { fontSize: 14 } },
        tooltip: { trigger: "axis" },
        grid: { left: 100, right: 16, top: 42, bottom: 24 },
        xAxis: { type: "value" },
        yAxis: { type: "category", data: rows.map((row) => row.category).reverse() },
        series: [{ type: "bar", data: rows.map((row) => row.count).reverse(), color: "#1f7a8c" }]
      }}
      onEvents={{ click: (params: { name: string }) => onSelect?.(params.name) }}
    />
  );
}

export function ClusterBubble({ clusters, onSelect }: { clusters: Cluster[]; onSelect?: (clusterId: number) => void }) {
  return (
    <ReactECharts
      style={{ height: 320 }}
      option={{
        tooltip: {
          formatter: (params: { data: [number, number, number, string, number] }) => `${params.data[3]}：${params.data[2]} 条`
        },
        xAxis: { type: "value", show: false },
        yAxis: { type: "value", show: false },
        series: [
          {
            type: "scatter",
            symbolSize: (data: [number, number, number]) => Math.min(72, Math.max(24, Math.sqrt(data[2]) * 18)),
            data: clusters.map((cluster, index) => [index + 1, cluster.cluster_ratio, cluster.cluster_size, cluster.cluster_name, cluster.cluster_id]),
            itemStyle: {
              color: (params: { dataIndex: number }) => (clusters[params.dataIndex]?.is_noise ? "#94a3b8" : "#c75c2f")
            },
            label: {
              show: true,
              width: 120,
              overflow: "truncate",
              formatter: (params: { data: [number, number, number, string, number] }) => params.data[3]
            }
          }
        ]
      }}
      onEvents={{ click: (params: { data: [number, number, number, string, number] }) => onSelect?.(params.data[4]) }}
    />
  );
}

export function WordCloudPanel({ words, onSelect }: { words: WordCloudItem[]; onSelect?: (word: string) => void }) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const wrapperRef = useRef<HTMLDivElement | null>(null);
  const list = useMemo(() => buildWordList(words), [words]);

  useEffect(() => {
    let cancelled = false;

    async function renderCloud() {
      const canvas = canvasRef.current;
      const wrapper = wrapperRef.current;
      if (!canvas || !wrapper || !list.length) {
        return;
      }

      const rect = wrapper.getBoundingClientRect();
      const width = Math.max(320, Math.floor(rect.width));
      const height = 240;
      canvas.width = width;
      canvas.height = height;
      canvas.style.width = "100%";
      canvas.style.height = `${height}px`;

      const mod = await import("wordcloud");
      if (cancelled) {
        return;
      }
      const WordCloud = (mod.default || mod) as unknown as (
        element: HTMLCanvasElement,
        options: Record<string, unknown>
      ) => void;

      WordCloud(canvas, {
        list,
        backgroundColor: "#ffffff",
        clearCanvas: true,
        gridSize: Math.max(8, Math.round(width / 64)),
        weightFactor: (weight: number) => Math.max(12, Math.min(34, weight * 3.2)),
        fontFamily: "Inter, Microsoft YaHei, PingFang SC, Arial, sans-serif",
        fontWeight: "600",
        color: (_word: string, weight: number) => {
          if (weight >= 7) {
            return "#1f7a8c";
          }
          if (weight >= 4) {
            return "#c75c2f";
          }
          return "#334155";
        },
        rotateRatio: 0.18,
        rotationSteps: 2,
        minRotation: -Math.PI / 8,
        maxRotation: Math.PI / 8,
        drawOutOfBound: false,
        shrinkToFit: true,
        abortThreshold: 1500,
        minSize: 8,
        click: (item: [string, number] | undefined) => item && onSelect?.(item[0])
      });
    }

    renderCloud();
    const observer = new ResizeObserver(() => renderCloud());
    if (wrapperRef.current) {
      observer.observe(wrapperRef.current);
    }

    return () => {
      cancelled = true;
      observer.disconnect();
    };
  }, [list, onSelect]);

  return (
    <div ref={wrapperRef} className="min-h-[240px] w-full overflow-hidden rounded-md border border-line bg-white">
      <canvas ref={canvasRef} aria-label="keyword word cloud" />
    </div>
  );
}

function buildWordList(words: WordCloudItem[]): [string, number][] {
  return words
    .filter((item) => item.word.trim().length > 1 && item.word.trim().length <= 12)
    .slice(0, 50)
    .map((item) => [item.word, Math.max(1, item.weight)]);
}
