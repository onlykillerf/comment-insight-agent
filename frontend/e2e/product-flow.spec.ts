import { expect, test } from "@playwright/test";

test("浏览器一键 Demo 展示实时 Agent 状态并生成报告", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "一键运行 Demo" }).first().click();

  await expect(page).toHaveURL(/\/tasks\/\d+$/, { timeout: 20_000 });
  await expect(page.getByText("任务理解").first()).toBeVisible();
  await expect(page.getByText(/排队中|运行中|已完成/).first()).toBeVisible();
  await expect(page.getByRole("button", { name: "查看报告" })).toBeEnabled({ timeout: 40_000 });

  await page.getByRole("button", { name: "查看报告" }).click();
  await expect(page).toHaveURL(/\/report$/, { timeout: 20_000 });
  for (const tab of ["概览", "痛点与观点", "主题聚类", "证据", "策略卡片"]) {
    await expect(page.getByRole("tab", { name: tab })).toBeVisible();
  }
  await page.getByRole("tab", { name: "策略卡片" }).click();
  await expect(page.getByText("为什么可信").first()).toBeVisible();
});

test("Wizard 上传 CSV 后预览并通过自动字段映射", async ({ page }) => {
  await page.goto("/tasks/new");
  await page.getByRole("button", { name: /上传 CSV/ }).click();
  await page.getByRole("button", { name: "下一步" }).click();

  await page.locator('input[type="file"]').setInputFiles({
    name: "comments.csv",
    mimeType: "text/csv",
    buffer: Buffer.from("comment_id,comment_text,likes\n1,裁判尺度需要解释,12\n2,末节防守很有针对性,18\n", "utf-8")
  });

  await expect(page.getByText("comments.csv · 2 行")).toBeVisible();
  await expect(page.getByText("可使用")).toBeVisible();
  await page.getByRole("button", { name: "下一步" }).click();
  await expect(page.getByText("LLM 模式")).toBeVisible();
});
