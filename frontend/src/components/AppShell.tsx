"use client";

import Link from "next/link";
import { BarChart3, ClipboardList, LayoutDashboard } from "lucide-react";

const navItems = [
  { href: "/", label: "工作台", icon: LayoutDashboard },
  { href: "/tasks/new", label: "新建分析", icon: ClipboardList }
];

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen">
      <header className="app-band sticky top-0 z-20">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-3">
          <Link href="/" className="flex items-center gap-2 font-semibold text-ink">
            <BarChart3 size={22} color="#1f7a8c" />
            <span>虎扑赛事评论洞察</span>
          </Link>
          <nav className="flex items-center gap-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <Link key={item.href} href={item.href} className="flex h-9 items-center gap-2 rounded-md px-3 text-sm text-slate-700 hover:bg-slate-100">
                  <Icon size={16} />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-5 py-6">{children}</main>
    </div>
  );
}
