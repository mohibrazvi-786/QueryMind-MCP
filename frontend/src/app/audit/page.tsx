"use client"

import { Layout } from "@/components/Layout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export default function AuditPage() {
  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Audit Logs</h1>
          <p className="text-muted-foreground">
            Append-only security and operational audit trail. Only authorized
            roles may view this section.
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Recent Audit Events</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="rounded-lg border border-border p-6 text-center text-muted-foreground">
              Connect a database and generate activity to view audit events.
              Events are append-only and never log credentials.
            </div>
          </CardContent>
        </Card>
      </div>
    </Layout>
  )
}
