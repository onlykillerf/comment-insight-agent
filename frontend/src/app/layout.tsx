import type { Metadata } from "next";
import { ConfigProvider } from "antd";
import "antd/dist/reset.css";
import "./globals.css";
import { AppShell } from "@/components/AppShell";

export const metadata: Metadata = {
  title: "Cross-Platform Comment Insight Agent",
  description: "Multi-Agent comment insight and strategy generation system",
  icons: {
    icon: "/favicon.ico",
    shortcut: "/favicon.ico"
  }
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <ConfigProvider
          theme={{
            token: {
              colorPrimary: "#1f7a8c",
              borderRadius: 8,
              fontFamily: "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
            }
          }}
        >
          <AppShell>{children}</AppShell>
        </ConfigProvider>
      </body>
    </html>
  );
}
