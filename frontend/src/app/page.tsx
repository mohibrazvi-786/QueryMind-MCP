"use client"

import { Layout } from "@/components/Layout"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
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
  Activity,
  TrendingUp,
  Clock,
  DollarSign,
  Users,
} from "lucide-react"

const statCards = [
  {
    title: "Databases",
    value: "1",
    subtitle: "Connected",
    icon: Database,
    trend: "+0%",
  },
  {
    title: "Schema Objects",
    value: "24",
    subtitle: "Tables, views, columns",
    icon: FileText,
    trend: "+2",
  },
  {
    title: "Slow Queries",
    value: "4",
    subtitle: "Last 24h",
    icon: Clock,
    trend: "-1",
  },
  {
    title: "Recommendations",
    value: "6",
    subtitle: "Pending index advice",
    icon: Zap,
    trend: "+3",
  },
  {
    title: "Active Anomalies",
    value: "0",
    subtitle: "Detected events",
    icon: AlertTriangle,
    trend: "0",
  },
  {
    title: "Health",
    value: "OK",
    subtitle: "All systems nominal",
    icon: FileCheck,
    trend: "",
  },
]

const recentActivity = [
  {
    time: "2 min ago",
    actor: "db_analyst",
    action: "Generated SQL",
    target: "customers → orders",
    outcome: "success",
  },
  {
    time: "12 min ago",
    actor: "org_admin",
    action: "Index recommendation",
    target: "orders(customer_id)",
    outcome: "success",
  },
  {
    time: "45 min ago",
    actor: "viewer",
    action: "Schema discovery",
    target: "ecommerce",
    outcome: "success",
  },
  {
    time: "2 hours ago",
    actor: "service_account",
    action: "Read-only query",
    target: "monthly_sales_report",
    outcome: "denied",
  },
]

export default function OverviewPage() {
  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold">Overview</h1>
            <p className="text-muted-foreground">
              Database health, recent activity, and key metrics at a glance.
            </p>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-6">
          {statCards.map((card) => (
            <Card key={card.title}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">{card.title}</CardTitle>
                <card.icon className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{card.value}</div>
                <p className="text-xs text-muted-foreground">{card.subtitle}</p>
                {card.trend && (
                  <div className="mt-2 flex items-center gap-1">
                    <TrendingUp className="h-3 w-3 text-green-600" />
                    <span className="text-xs text-green-600 font-medium">{card.trend}</span>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-4">
          <Card>
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {recentActivity.map((item, i) => (
                  <div key={i} className="flex items-start gap-3">
                    <div className="h-2 w-2 rounded-full bg-muted shrink-0 mt-2" />
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs font-medium">{item.actor}</span>
                        <Badge
                          variant={item.outcome === "success" ? "success" : "danger"}
                          className="text-xs"
                        >
                          {item.outcome}
                        </Badge>
                      </div>
                      <div className="text-sm">{item.action}</div>
                      <div className="text-xs text-muted-foreground">
                        {item.target} &middot; {item.time}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button className="w-full" onClick={() => {}}>
                <Database className="h-4 w-4 mr-2" /> Connect a Database
              </Button>
              <Button variant="outline" className="w-full" onClick={() => {}}>
                <Zap className="h-4 w-4 mr-2" /> Ask AI a Question
              </Button>
              <Button variant="outline" className="w-full" onClick={() => {}}>
                <FileText className="h-4 w-4 mr-2" /> Open SQL Workspace
              </Button>
              <Button variant="outline" className="w-full" onClick={() => {}}>
                <BarChart3 className="h-4 w-4 mr-2" /> View Performance
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </Layout>
  )
}
