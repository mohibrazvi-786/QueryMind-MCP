"use client"

import { Layout } from "@/components/Layout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { useEffect, useState } from "react"
import { getJSON } from "@/lib/api"

export default function OverviewPage() {
  const [health, setHealth] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getJSON<any>("/auth/me")
      .then(() => {})
      .catch((e) => setError("Not connected — connect a database to begin."))
  }, [])

  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Overview</h1>
          <p className="text-muted-foreground">
            Database health, recent activity, and key metrics at a glance.
          </p>
        </div>

        {error && (
          <div className="rounded-md border border-destructive/50 bg-destructive/10 p-4 text-destructive text-sm">
            {error}
          </div>
        )}

        <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-4">
          <StatCard title="Databases" value="0" subtitle="No connections" />
          <StatCard title="Schema Objects" value="—" subtitle="Tables, views, columns" />
          <StatCard title="Slow Queries" value="0" subtitle="Last 24h" />
          <StatCard title="Recommendations" value="0" subtitle="Pending index advice" />
          <StatCard title="Active Anomalies" value="0" subtitle="Detected events" />
          <StatCard title="Health" value="—" subtitle={health?.status || "unknown"} />
        </div>

        <div className="rounded-lg border border-border p-6">
          <h2 className="text-lg font-semibold mb-4">Recent Activity</h2>
          <p className="text-muted-foreground text-sm">
            Connect a database to see recent activity, query history, and audit events.
          </p>
        </div>
      </div>
    </Layout>
  )
}

function StatCard({
  title,
  value,
  subtitle,
}: {
  title: string
  value: string | number
  subtitle: string
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Badge variant="outline" className="h-8 w-8">
          <span className="sr-only">{title}</span>
        </Badge>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        <p className="text-xs text-muted-foreground">{subtitle}</p>
      </CardContent>
    </Card>
  )
}
