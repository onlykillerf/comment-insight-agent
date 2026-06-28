"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Alert,
  Button,
  Descriptions,
  Empty,
  Form,
  Input,
  InputNumber,
  Radio,
  Select,
  Slider,
  Steps,
  Switch,
  Table,
  Tag,
  Upload,
  message
} from "antd";
import type { UploadFile } from "antd";
import { ArrowLeft, ArrowRight, Check, FileJson, FileSpreadsheet, Play, RadioTower, UploadCloud } from "lucide-react";
import { api } from "@/api/client";
import type { UploadedDataset } from "@/types/task";

const { TextArea } = Input;
const { Dragger } = Upload;

type SourceMode = "mock" | "hupu_public" | "csv" | "json" | "mediacrawler";
type WizardValues = {
  name: string;
  domain: "basketball" | "football";
  board: string;
  match_name: string;
  home_team: string;
  away_team: string;
  match_stage: string;
  match_date: string;
  thread_urls: string;
  news_urls: string;
  news_context: string;
  keywords: string;
  semantic_query: string;
  max_comments: number;
  similarity_threshold: number;
  enable_llm: boolean;
  llm_mode: "mock" | "configured";
  enable_image_analysis: boolean;
  max_image_comments: number;
};

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

const sourceOptions = [
  { value: "mock", title: "Mock Demo", description: "无需文件和密钥，适合首次体验。", icon: Play },
  { value: "hupu_public", title: "虎扑公开帖子", description: "输入你有权访问的帖子和新闻链接。", icon: RadioTower },
  { value: "csv", title: "上传 CSV", description: "上传后自动预览并映射字段。", icon: FileSpreadsheet },
  { value: "json", title: "上传 JSON", description: "支持 JSON 数组或 JSONL。", icon: FileJson },
  { value: "mediacrawler", title: "MediaCrawler Export", description: "读取其合规导出的 CSV / JSON。", icon: UploadCloud }
] as const;

const canonicalFields = [
  ["content", "评论正文（必填）"],
  ["id", "评论 ID"],
  ["platform", "平台"],
  ["topic", "主题"],
  ["author_hash", "作者标识"],
  ["like_count", "点赞数"],
  ["reply_count", "回复数"],
  ["publish_time", "发布时间"],
  ["source_url", "来源链接"],
  ["parent_id", "父评论 ID"]
];

export default function NewTaskPage() {
  const router = useRouter();
  const [form] = Form.useForm<WizardValues>();
  const [step, setStep] = useState(0);
  const [sourceMode, setSourceMode] = useState<SourceMode>("mock");
  const [upload, setUpload] = useState<UploadedDataset | null>(null);
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [uploading, setUploading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const sport = Form.useWatch("domain", form) || "basketball";

  const previewColumns = useMemo(
    () => (upload?.columns || []).slice(0, 6).map((column) => ({
      title: column,
      dataIndex: column,
      ellipsis: true,
      render: (value: unknown) => formatCell(value)
    })),
    [upload]
  );

  const handleUpload = async (file: UploadFile | File) => {
    const browserFile = file instanceof File ? file : file.originFileObj;
    if (!browserFile) return Upload.LIST_IGNORE;
    setUploading(true);
    setError("");
    try {
      const result = await api.uploadDataset(browserFile, sourceMode as "csv" | "json" | "mediacrawler");
      setUpload(result);
      setMapping(result.field_mapping);
      message.success(`已读取 ${result.row_count} 条数据`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "上传失败");
    } finally {
      setUploading(false);
    }
    return Upload.LIST_IGNORE;
  };

  const saveMapping = async () => {
    if (!upload) return;
    setUploading(true);
    setError("");
    try {
      const updated = await api.updateUploadMapping(upload.id, mapping);
      setUpload(updated);
      setMapping(updated.field_mapping);
      message.success(updated.status === "ready" ? "字段映射已通过校验" : "请继续检查字段映射");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "字段映射保存失败");
    } finally {
      setUploading(false);
    }
  };

  const next = async () => {
    setError("");
    if (step === 1 && ["csv", "json", "mediacrawler"].includes(sourceMode) && upload?.status !== "ready") {
      setError("请先上传数据文件并完成评论正文字段映射。");
      return;
    }
    if (step === 1 && sourceMode === "hupu_public") {
      const urls = splitLines(form.getFieldValue("thread_urls"));
      if (!urls.length) {
        setError("请至少填写一个公开虎扑帖子 URL。");
        return;
      }
    }
    setStep((current) => Math.min(3, current + 1));
  };

  const submit = async (runNow: boolean) => {
    setSubmitting(true);
    setError("");
    try {
      const values = await form.validateFields();
      const task = await api.createTask({
        ...values,
        platforms: ["hupu"],
        data_source: sourceMode,
        upload_id: upload?.id,
        field_mapping: upload?.field_mapping || {},
        source_path: null,
        time_range: {},
        language: "zh",
        sentiment_focus: "all",
        thread_urls: splitLines(values.thread_urls),
        news_urls: splitLines(values.news_urls),
        keywords: splitKeywords(values.keywords),
        enable_image_analysis: sourceMode === "mock" ? false : values.enable_image_analysis,
        llm_mode: sourceMode === "mock" ? "mock" : values.llm_mode
      });
      if (runNow) await api.runTask(task.id);
      message.success(runNow ? "任务已加入分析队列" : "任务已创建");
      router.push(`/tasks/${task.id}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "任务创建失败");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-5">
      <div>
        <h1 className="m-0 text-2xl font-semibold text-ink">新建赛事评论分析</h1>
        <p className="m-0 mt-1 text-sm text-slate-600">从数据来源到分析范围，四步完成配置。</p>
      </div>
      <Alert type="info" showIcon message="仅处理公开可访问或你主动上传的数据；不绕过登录、验证码、付费墙或平台权限。" />
      {error && <Alert type="error" showIcon message="请检查当前步骤" description={error} />}

      <section className="tool-panel p-5">
        <Steps current={step} responsive items={[{ title: "选择来源" }, { title: "准备数据" }, { title: "分析设置" }, { title: "确认运行" }]} />

        <Form<WizardValues>
          form={form}
          layout="vertical"
          className="mt-7"
          initialValues={{
            name: "虎扑赛事评论分析",
            domain: "basketball",
            board: "nba",
            match_name: "马刺 vs 尼克斯比赛讨论",
            home_team: "马刺",
            away_team: "尼克斯",
            match_stage: "系列赛",
            match_date: "",
            thread_urls: "",
            news_urls: "",
            news_context: "",
            keywords: "球员表现 战术 裁判 关键球",
            semantic_query: "分析虎扑网友对本场比赛的情绪、争议焦点、球员评价和战术观点",
            max_comments: 200,
            similarity_threshold: 0.9,
            enable_llm: true,
            llm_mode: "mock",
            enable_image_analysis: true,
            max_image_comments: 6
          }}
        >
          {step === 0 && (
            <div>
              <h2 className="m-0 mb-4 text-lg font-semibold text-ink">评论数据从哪里来？</h2>
              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                {sourceOptions.map((option) => {
                  const Icon = option.icon;
                  const selected = sourceMode === option.value;
                  return (
                    <button
                      type="button"
                      key={option.value}
                      className={`source-choice text-left ${selected ? "source-choice-active" : ""}`}
                      onClick={() => { setSourceMode(option.value); setUpload(null); setMapping({}); }}
                    >
                      <Icon size={20} className="text-teal-700" />
                      <strong className="mt-3 block text-sm text-ink">{option.title}</strong>
                      <span className="mt-1 block text-sm leading-6 text-slate-500">{option.description}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {step === 1 && (
            <div className="space-y-5">
              <div className="grid gap-x-5 md:grid-cols-2">
                <Form.Item label="运动" name="domain" rules={[{ required: true }]}>
                  <Select onChange={(value) => form.setFieldValue("board", value === "football" ? "world_cup" : "nba")} options={[{ value: "basketball", label: "篮球" }, { value: "football", label: "足球" }]} />
                </Form.Item>
                <Form.Item label="板块" name="board" rules={[{ required: true }]}><Select options={boards[sport]} /></Form.Item>
              </div>

              {sourceMode === "mock" && <Alert type="success" showIcon message="将使用内置赛事评论与 MockLLM" description="无需 API Key，任务仍会生成数据质量、情绪、聚类、代表评论、洞察和策略卡。" />}

              {sourceMode === "hupu_public" && (
                <>
                  <Form.Item label="虎扑公开帖子 URL" name="thread_urls" required><TextArea rows={5} placeholder="每行一个公开帖子 URL" /></Form.Item>
                  <Alert type="warning" showIcon message="若页面要求登录，请先在你自己的浏览器中正常登录；本项目不会绕过平台限制。" />
                </>
              )}

              {["csv", "json", "mediacrawler"].includes(sourceMode) && (
                <>
                  <Dragger accept=".csv,.json,.jsonl" showUploadList={false} disabled={uploading} beforeUpload={handleUpload}>
                    <p><UploadCloud size={28} className="mx-auto text-teal-700" /></p>
                    <p className="font-medium">点击或拖拽 CSV / JSON / JSONL 到这里</p>
                    <p className="text-sm text-slate-500">文件只保存在本项目配置的上传目录，不要求填写服务器路径。</p>
                  </Dragger>
                  {upload && (
                    <div className="space-y-4">
                      <div className="flex flex-wrap items-center gap-2"><Tag color={upload.status === "ready" ? "green" : "gold"}>{upload.status === "ready" ? "可使用" : "需要映射"}</Tag><span className="text-sm">{upload.original_name} · {upload.row_count} 行</span></div>
                      {!!upload.validation_errors.length && <Alert type="warning" showIcon message={upload.validation_errors.join("；")} />}
                      <div className="grid gap-x-4 md:grid-cols-2 xl:grid-cols-3">
                        {canonicalFields.map(([field, label]) => (
                          <div key={field}>
                            <label className="mb-1 block text-sm text-slate-600">{label}</label>
                            <Select allowClear className="w-full" placeholder="不映射" value={mapping[field]} options={upload.columns.map((column) => ({ value: column, label: column }))} onChange={(value) => setMapping((current) => ({ ...current, [field]: value }))} />
                          </div>
                        ))}
                      </div>
                      <Button icon={<Check size={16} />} loading={uploading} onClick={saveMapping}>保存字段映射</Button>
                      <Table<Record<string, unknown>> size="small" rowKey={(_, index) => String(index)} scroll={{ x: true }} pagination={false} dataSource={upload.preview_rows.slice(0, 5)} columns={previewColumns} locale={{ emptyText: "没有可预览的数据" }} />
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          {step === 2 && (
            <div className="space-y-2">
              <div className="grid gap-x-5 md:grid-cols-2">
                <Form.Item label="任务名称" name="name" rules={[{ required: true, message: "请输入任务名称" }]}><Input /></Form.Item>
                <Form.Item label="比赛名称" name="match_name" rules={[{ required: true, message: "请输入比赛名称" }]}><Input /></Form.Item>
                <Form.Item label="主队" name="home_team"><Input /></Form.Item>
                <Form.Item label="客队" name="away_team"><Input /></Form.Item>
                <Form.Item label="比赛阶段" name="match_stage"><Input placeholder="例如：总决赛 G6 / 世界杯 1/8 决赛" /></Form.Item>
                <Form.Item label="比赛日期" name="match_date"><Input placeholder="YYYY-MM-DD" /></Form.Item>
                <Form.Item label="分析关键词" name="keywords"><Input /></Form.Item>
                <Form.Item label="最大评论数" name="max_comments"><InputNumber min={1} max={5000} className="w-full" /></Form.Item>
              </div>
              <Form.Item label="分析问题" name="semantic_query"><Input /></Form.Item>
              <Form.Item label="相关新闻 URL（每行一个，可选）" name="news_urls"><TextArea rows={3} /></Form.Item>
              <Form.Item label="新闻或官方背景摘要（可选）" name="news_context"><TextArea rows={4} /></Form.Item>
              <div className="grid gap-x-5 md:grid-cols-2">
                <Form.Item label="去重相似度" name="similarity_threshold"><Slider min={0.7} max={0.99} step={0.01} /></Form.Item>
                <Form.Item label="生成上下文洞察" name="enable_llm" valuePropName="checked"><Switch /></Form.Item>
                <Form.Item label="LLM 模式" name="llm_mode"><Radio.Group optionType="button" options={[{ value: "mock", label: "MockLLM（默认）" }, { value: "configured", label: "使用 .env 配置" }]} /></Form.Item>
                <Form.Item label="分析主帖/新闻信息图" name="enable_image_analysis" valuePropName="checked"><Switch disabled={sourceMode === "mock"} /></Form.Item>
                <Form.Item label="最多分析上下文图片" name="max_image_comments"><InputNumber min={0} max={20} className="w-full" /></Form.Item>
              </div>
            </div>
          )}

          {step === 3 && (
            <div>
              <h2 className="m-0 mb-4 text-lg font-semibold text-ink">确认任务配置</h2>
              <Descriptions bordered column={{ xs: 1, md: 2 }} size="small">
                <Descriptions.Item label="数据来源">{sourceLabel(sourceMode)}</Descriptions.Item>
                <Descriptions.Item label="上传数据">{upload ? `${upload.original_name}（${upload.row_count} 行）` : "不需要"}</Descriptions.Item>
                <Descriptions.Item label="运动 / 板块">{sport === "football" ? "足球" : "篮球"} / {form.getFieldValue("board")}</Descriptions.Item>
                <Descriptions.Item label="比赛">{form.getFieldValue("match_name")}</Descriptions.Item>
                <Descriptions.Item label="样本上限">{form.getFieldValue("max_comments")} 条</Descriptions.Item>
                <Descriptions.Item label="洞察模式">{sourceMode === "mock" || form.getFieldValue("llm_mode") === "mock" ? "MockLLM" : "使用 .env 配置"}</Descriptions.Item>
                <Descriptions.Item label="上下文图片">{sourceMode !== "mock" && form.getFieldValue("enable_image_analysis") ? `最多 ${form.getFieldValue("max_image_comments")} 张` : "关闭"}</Descriptions.Item>
                <Descriptions.Item label="合规边界">仅处理公开可访问或主动上传的数据</Descriptions.Item>
              </Descriptions>
              <div className="mt-5"><Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="提交后将立即进入异步队列，可在任务页实时查看每个 Agent 的进度。" /></div>
            </div>
          )}
        </Form>

        <div className="mt-7 flex items-center justify-between border-t border-slate-200 pt-4">
          <Button icon={<ArrowLeft size={16} />} disabled={step === 0 || submitting} onClick={() => setStep((current) => Math.max(0, current - 1))}>上一步</Button>
          {step < 3 ? (
            <Button type="primary" icon={<ArrowRight size={16} />} iconPosition="end" onClick={next}>下一步</Button>
          ) : (
            <div className="flex gap-2"><Button loading={submitting} onClick={() => submit(false)}>仅创建</Button><Button type="primary" icon={<Play size={16} />} loading={submitting} onClick={() => submit(true)}>创建并运行</Button></div>
          )}
        </div>
      </section>
    </div>
  );
}

function splitLines(value: unknown) {
  return String(value || "").split(/\r?\n/).map((item) => item.trim()).filter(Boolean);
}

function splitKeywords(value: unknown) {
  return String(value || "").split(/[,，\s]+/).map((item) => item.trim()).filter(Boolean);
}

function sourceLabel(source: SourceMode) {
  return ({ mock: "Mock Demo", hupu_public: "虎扑公开帖子", csv: "CSV 上传", json: "JSON 上传", mediacrawler: "MediaCrawler Export" } as Record<SourceMode, string>)[source];
}

function formatCell(value: unknown) {
  if (value === null || value === undefined) return "-";
  return typeof value === "object" ? JSON.stringify(value) : String(value);
}
