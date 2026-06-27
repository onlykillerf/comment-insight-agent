"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button, Checkbox, DatePicker, Form, Input, InputNumber, Select, Slider, Switch, message } from "antd";
import { Play, Save } from "lucide-react";
import { api } from "@/api/client";

const { RangePicker } = DatePicker;

export default function NewTaskPage() {
  const router = useRouter();
  const [form] = Form.useForm();
  const [submitting, setSubmitting] = useState(false);

  const onFinish = async (values: Record<string, any>, runNow: boolean) => {
    setSubmitting(true);
    try {
      const timeRange = values.time_range
        ? { start: values.time_range[0]?.format("YYYY-MM-DD"), end: values.time_range[1]?.format("YYYY-MM-DD") }
        : {};
      const task = await api.createTask({
        ...values,
        time_range: timeRange,
        keywords: String(values.keywords || "")
          .split(/[,，\s]+/)
          .map((keyword) => keyword.trim())
          .filter(Boolean)
      });
      if (runNow) {
        await api.runTask(task.id);
      }
      message.success(runNow ? "Task completed" : "Task created");
      router.push(runNow ? `/tasks/${task.id}/report` : `/tasks/${task.id}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-5">
      <div>
        <h1 className="m-0 text-2xl font-semibold text-ink">Create Analysis Task</h1>
        <p className="m-0 mt-1 text-sm text-slate-600">Configure connectors, taxonomy, sample size, and LLM behavior.</p>
      </div>
      <Form
        form={form}
        layout="vertical"
        className="tool-panel p-5"
        initialValues={{
          name: "NBA Draft Opinion Demo",
          domain: "nba_draft",
          platforms: ["xhs", "weibo", "bili", "zhihu"],
          keywords: "2026 NBA选秀 迪班萨 皮特森 顺位 球队适配",
          semantic_query: "Analyze public comments about NBA draft prospects, pick value, player templates, and team fit.",
          max_comments: 320,
          similarity_threshold: 0.9,
          language: "zh",
          sentiment_focus: "all",
          enable_llm: true,
          data_source: "csv",
          source_path: "data/demo/nba_draft_comments.csv"
        }}
        onFinish={(values) => onFinish(values, true)}
      >
        <div className="grid gap-4 md:grid-cols-2">
          <Form.Item label="Task name" name="name" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item label="Domain taxonomy" name="domain">
            <Select
              options={[
                { value: "nba_draft", label: "NBA Draft" },
                { value: "iaa_game", label: "IAA Game Reviews" },
                { value: "game", label: "Game" },
                { value: "esports", label: "Esports" },
                { value: "sports", label: "Sports" },
                { value: "news", label: "News" }
              ]}
            />
          </Form.Item>
          <Form.Item label="Platforms" name="platforms">
            <Checkbox.Group
              options={[
                { value: "xhs", label: "XHS" },
                { value: "weibo", label: "Weibo" },
                { value: "bili", label: "Bilibili" },
                { value: "zhihu", label: "Zhihu" },
                { value: "hupu", label: "Hupu" },
                { value: "reddit", label: "Reddit" },
                { value: "youtube", label: "YouTube" }
              ]}
            />
          </Form.Item>
          <Form.Item label="Data source" name="data_source">
            <Select
              options={[
                { value: "mock", label: "MockConnector" },
                { value: "csv", label: "CSVConnector" },
                { value: "json", label: "JsonConnector" },
                { value: "mediacrawler", label: "MediaCrawler Export" },
                { value: "mediacrawler_adapter", label: "MediaCrawler Adapter" }
              ]}
            />
          </Form.Item>
          <Form.Item label="Keywords" name="keywords">
            <Input />
          </Form.Item>
          <Form.Item label="Semantic query" name="semantic_query">
            <Input />
          </Form.Item>
          <Form.Item label="Time range" name="time_range">
            <RangePicker className="w-full" />
          </Form.Item>
          <Form.Item label="Max comments" name="max_comments">
            <InputNumber min={1} max={5000} className="w-full" />
          </Form.Item>
          <Form.Item label="Similarity threshold" name="similarity_threshold">
            <Slider min={0.6} max={0.99} step={0.01} />
          </Form.Item>
          <Form.Item label="Language" name="language">
            <Select options={[{ value: "zh", label: "Chinese" }, { value: "en", label: "English" }, { value: "multi", label: "Multi-language" }]} />
          </Form.Item>
          <Form.Item label="Sentiment focus" name="sentiment_focus">
            <Select options={[{ value: "all", label: "All" }, { value: "negative", label: "Negative" }, { value: "positive", label: "Positive" }]} />
          </Form.Item>
          <Form.Item label="Enable LLM insight" name="enable_llm" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item label="Local CSV / JSON / MediaCrawler export path" name="source_path">
            <Input />
          </Form.Item>
        </div>
        <div className="flex justify-end gap-3">
          <Button
            icon={<Save size={16} />}
            htmlType="button"
            disabled={submitting}
            onClick={async () => onFinish(await form.validateFields(), false)}
          >
            Create only
          </Button>
          <Button type="primary" icon={<Play size={16} />} htmlType="submit" loading={submitting}>
            Run workflow
          </Button>
        </div>
      </Form>
    </div>
  );
}
