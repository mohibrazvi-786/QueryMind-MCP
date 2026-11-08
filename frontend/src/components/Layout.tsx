"use client"

import { useState } from "react"
import Link from "next/link"
import {
  LayoutDashboard,
  Database,
  Zap,
  FileText,
  Search,
  BarChart3,
  AlertTriangle,
  FileCheck,
  Shield,
  Settings,
  Menu,
  ChevronRight,
} from "lucide-react"

const nav = [
  { name: "Overview", href: "/", icon: LayoutDashboard },
  { name: "Connections", href: "/connections", icon: Database },
  { name: "AI Assistant", href: "/assistant", icon: Zap },
  { name: "SQL Workspace", href: "/sql", icon: FileText },
  { name: "Schema Explorer", href: "/schema", icon: Search },
  { name: "Performance", href: "/performance", icon: BarChart3 },
  { name: "Anomaly Monitor", href: "/anomalies", icon: AlertTriangle },
  { name: "Audit Logs", href: "/audit", icon: FileCheck },
  { name: "Organization", href: "/org", icon: Shield },
]

export function Layout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(true)

  return (
    <div className="flex h-screen bg-background text-foreground">
      <aside
        className={`hidden md:flex w-64 flex-col border-r border-border ${
          sidebarOpen ? "" : "translate-x-[-100%] transition-transform duration-300"
        }`}
      >
        <div className="p-4">
          <Link href="/" className="flex items-center gap-2 font-bold text-lg mb-6">
            <Database className="h-5 w-5" /> QueryMind
          </Link>
          <nav className="space-y-1">
            {nav.map((item) => (
              <Link
                key={item.name}
                href={item.href}
                className="flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors hover:bg-muted hover:text-primary"
              >
                <item.icon className="h-4 w-4" />
                {item.name}
                <ChevronRight className="ml-auto h-3.5 w-3.5 opacity-50" />
              </Link>
            ))}
          </nav>
        </div>
        <div className="p-4 mt-auto border-t border-border">
          <Link href="/org" className="flex items-center gap-3 px-3 py-2 rounded-md text-sm text-muted-foreground hover:bg-muted">
            <Settings className="h-4 w-4" /> Organization
          </Link>
        </div>
      </aside>

      <div className="flex-1 flex flex-col overflow-hidden md:pl-0">
        <header className="flex items-center justify-between px-4 py-3 border-b border-border bg-background/50">
          <button
            onClick={() => setSidebarOpen((o) => !o)}
            className="md:hidden p-2 text-muted-foreground hover:text-foreground"
          >
            <Menu className="h-5 w-5" />
          </button>
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">Connected</span>
            <span className="h-2 w-2 rounded-full bg-green-500" aria-label="status" />
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>
    </div>
  )
}
