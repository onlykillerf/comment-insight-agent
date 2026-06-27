"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Alert, Button, Form, Input, InputNumber, Select, Slider, Switch, message } from "antd";
import { Play, Save } from "lucide-react";
import { api } from "@/api/client";

const { TextArea } = Input;

const boards = {
  basketball: [
    { value: "nba", label: "NBA" },
    { value: "cba", label: "CBA" },
    { value: "national_basketball", label: "国家队 / 国际篮球" }
  ],
  football: [
    { value: "world_cup", label: "世界杯" },
    { value: "international_football", label: "国际足球" },
    { value: "premier_league", label: "英超" },
    { value: "champions_league", label: "欧冠" },
    { value: "chinese_football", label: "中国足球" }
  ]
};

export default function NewTaskPage() {
  const router = useRouter();
  const [form] = Form.useForm();
  const [submitting, setSubmitting] = useState(false);
  const sport = Form.useWatch("domain", form) || "basketball";
  const dataSource = Form.useWatch("data_source", form) || "hupu_public";

  const onFinish = async (values: Record<string, any>, runNow: boolean) => {
    setSubmitting(true);
    try {
      const task = await api.createTask({
        ...values,
        platforms: ["hupu"],
        time_range: {},
        language: "zh",
        sentiment_focus: "all",
        thread_urls: splitLines(values.thread_urls),
        news_urls: splitLines(values.news_urls),
        keywords: splitKeywords(values.keywords)
      });
      if (runNow) {
        await api.runTask(task.id);
      }
      message.success(runNow ? "比赛评论分析完成" : "分析任务已创建");
      router.push(runNow ? `/tasks/${task.id}/report` : `/tasks/${task.id}`);
    } catch (caught) {
      message.error(caught instanceof Error ? caught.message : "任务创建失败");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-5">
      <div>
        <h1 className="m-0 text-2xl font-semibold text-ink">新建虎扑赛事分析</h1>
        <p className="m-0 mt-1 text-sm text-slate-600">按板块与具体比赛组织评论样本，可选加入相关新闻背景。</p>
      </div>

      <Alert
        type="info"
        showIcon
        message="仅支持用户指定的公开虎扑帖子；不绕过登录、验证码、付费墙或平台权限。"
      />

      <Form
        form={form}
        layout="vertical"
        className="tool-panel p-5"
        initialValues={{
          name: "尼克斯 vs 马刺 2026 总决赛 G1 虎扑舆情分析",
          domain: "basketball",
          board: "nba",
          match_name: "尼克斯 vs 马刺 2026 总决赛 G1",
          home_team: "马刺",
          away_team: "尼克斯",
          match_stage: "NBA 总决赛 G1",
          match_date: "2026-06-04",
          thread_urls: [
            "https://bbs.hupu.com/639718527.html",
            "https://bbs.hupu.com/639718379.html",
            "https://bbs.hupu.com/639726820.html",
            "https://bbs.hupu.com/639720487.html",
            "https://bbs.hupu.com/639737756.html"
          ].join("\n"),
          news_urls: "",
          news_context: "尼克斯客场 105-95 击败马刺，系列赛 1-0 领先。该背景仅用于对照网友观点，最终事实以可靠赛后报道和官方数据为准。",
          keywords: "马刺 尼克斯 总决赛 G1 福克斯 哈特 战术 球员表现",
          semantic_query: "分析虎扑网友对本场比赛的情绪、争议焦点、球员评价和战术观点",
          max_comments: 200,
          similarity_threshold: 0.9,
          enable_llm: true,
          enable_image_analysis: true,
          max_image_comments: 6,
          data_source: "hupu_public",
          source_path: ""
        }}
        onFinish={(values) => onFinish(values, true)}
      >
        <div className="grid gap-x-5 md:grid-cols-2">
          <Form.Item label="任务名称" name="name" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item label="运动" name="domain" rules={[{ required: true }]}>
            <Select
              onChange={(value) => form.setFieldValue("board", value === "football" ? "world_cup" : "nba")}
              options={[
                { value: "basketball", label: "篮球" },
                { value: "football", label: "足球" }
              ]}
            />
          </Form.Item>
          <Form.Item label="虎扑板块" name="board" rules={[{ required: true }]}>
            <Select options={boards[sport as keyof typeof boards]} />
          </Form.Item>
          <Form.Item label="数据来源" name="data_source" rules={[{ required: true }]}>
            <Select
              options={[
                { value: "hupu_public", label: "虎扑公开帖子" },
                { value: "mock", label: "离线演示数据" },
                { value: "csv", label: "本地 CSV" },
                { value: "json", label: "本地 JSON / JSONL" }
              ]}
            />
          </Form.Item>
          <Form.Item label="主队" name="home_team" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item label="客队" name="away_team" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item label="比赛名称" name="match_name" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item label="比赛阶段" name="match_stage">
            <Input placeholder="例如：总决赛 G6 / 世界杯 1/8 决赛" />
          </Form.Item>
          <Form.Item label="比赛日期" name="match_date">
            <Input placeholder="YYYY-MM-DD" />
          </Form.Item>
          <Form.Item label="最大评论数" name="max_comments">
            <InputNumber min={1} max={2000} className="w-full" />
          </Form.Item>
        </div>

        <Form.Item
          label="虎扑帖子 URL"
          name="thread_urls"
          rules={dataSource === "hupu_public" ? [{ required: true, message: "请至少填写一个公开虎扑帖子 URL" }] : []}
        >
          <TextArea rows={3} placeholder="每行一个，例如 https://bbs.hupu.com/638164133.html" />
        </Form.Item>

        {(dataSource === "csv" || dataSource === "json") && (
          <Form.Item label="本地数据文件" name="source_path" rules={[{ required: true }]}>
            <Input placeholder="data/demo/nba_game_comments.csv" />
          </Form.Item>
        )}

        <div className="grid gap-x-5 md:grid-cols-2">
          <Form.Item label="分析关键词" name="keywords">
            <Input />
          </Form.Item>
          <Form.Item label="分析问题" name="semantic_query">
            <Input />
          </Form.Item>
        </div>

        <section className="border-t border-slate-200 pt-4">
          <h2 className="m-0 mb-3 text-base font-semibold text-ink">相关新闻背景（可选）</h2>
          <Form.Item label="新闻 URL" name="news_urls">
            <TextArea rows={3} placeholder="每行一个公开新闻页面 URL" />
          </Form.Item>
          <Form.Item label="手工背景摘要" name="news_context">
            <TextArea rows={4} placeholder="可粘贴比分、系列赛进程、伤病、首发或官方判罚说明等背景。" />
          </Form.Item>
        </section>

        <div className="grid gap-x-5 md:grid-cols-2">
          <Form.Item label="去重相似度" name="similarity_threshold">
            <Slider min={0.7} max={0.99} step={0.01} />
          </Form.Item>
          <Form.Item label="生成 LLM 上下文洞察" name="enable_llm" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item
            label="分析主帖/新闻信息图（SiliconFlow Qwen/Qwen3.5-4B）"
            name="enable_image_analysis"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>
          <Form.Item label="最多分析上下文图片" name="max_image_comments">
            <InputNumber min={0} max={20} className="w-full" />
          </Form.Item>
        </div>

        <div className="flex justify-end gap-3">
          <Button
            icon={<Save size={16} />}
            htmlType="button"
            disabled={submitting}
            onClick={async () => onFinish(await form.validateFields(), false)}
          >
            仅创建
          </Button>
          <Button type="primary" icon={<Play size={16} />} htmlType="submit" loading={submitting}>
            运行分析
          </Button>
        </div>
      </Form>
    </div>
  );
}

function splitLines(value: unknown) {
  return String(value || "")
    .split(/\r?\n/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function splitKeywords(value: unknown) {
  return String(value || "")
    .split(/[,，\s]+/)
    .map((item) => item.trim())
    .filter(Boolean);
}
