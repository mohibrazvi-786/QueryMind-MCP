"use client"

import { useState } from "react"
import { Layout } from "@/components/Layout"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Separator } from "@/components/ui/separator"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
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
  ChevronRight,
  Plus,
  Activity,
  TrendingUp,
  Clock,
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

export default function Layout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(true)

  return (
    <div className="flex h-screen bg-background text-foreground">
      <aside
        className={cn(
          "hidden md:flex w-64 flex-col border-r border-border",
          sidebarOpen ? "" : "translate-x-[-100%] transition-transform duration-300"
        )}
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
                className="flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors hover:bg-accent hover:text-primary"
              >
                <item.icon className="h-4 w-4" />
                {item.name}
                <ChevronRight className="ml-auto h-3.5 w-3.5 opacity-50" />
              </Link>
            ))}
          </nav>
        </div>
        <div className="p-4 mt-auto border-t border-border">
          <Link href="/org" className="flex items-center gap-3 px-3 py-2 rounded-md text-sm text-muted-foreground hover:bg-accent">
            <Shield className="h-4 w-4" /> Organization
          </Link>
        </div>
      </aside>

      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="flex items-center justify-between px-4 py-3 border-b border-border bg-background/50 md:px-6">
          <button
            onClick={() => setSidebarOpen((o) => !o)}
            className="md:hidden p-2 text-muted-foreground hover:text-foreground"
          >
            <span className="sr-only">Toggle sidebar</span>
            <Plus className="h-5 w-5" />
          </button>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-green-500" />
            <span className="text-xs text-muted-foreground">Connected</span>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-6 md:p-8">{children}</main>
      </div>
    </div>
  )
)

function Link({ children, href, className }: { children: React.ReactNode; href: string; className?: string }) {
  return (
    <a href={href} className={className}>
      {children}
    </a>
  )
}

function cn(...classes: (string | undefined | false)[]) {
  return classes.filter(Boolean).join(" ")
}
