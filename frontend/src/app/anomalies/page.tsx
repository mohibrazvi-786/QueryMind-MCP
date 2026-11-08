"use client"

import { Layout } from "@/components/Layout"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

export default function AnomaliesPage() {
  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Anomaly Monitor</h1>
          <p className="text-muted-foreground">
            Statistical baselines (Z-score, EWMA) and Isolation Forest anomaly
            detection over database metrics.
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Detected Anomalies</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center py-10 text-muted-foreground text-sm">
              No anomalies detected. Connect a database and collect metrics to
              begin baselining.
            </div>
          </CardContent>
        </Card>

        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardContent className="p-4">
              <div className="text-2xl font-bold">0</div>
              <div className="text-xs text-muted-foreground">Active anomalies</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-2xl font-bold">—</div>
              <div className="text-xs text-muted-foreground">Baseline</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-2xl font-bold">statistical + ml</div>
              <div className="text-xs text-muted-foreground">Detection method</div>
            </CardContent>
          </Card>
        </div>
      </div>
    </Layout>
  )
}
