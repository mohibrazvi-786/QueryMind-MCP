"use client"

import { Layout } from "@/components/Layout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export default function PerformancePage() {
  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Performance Intelligence</h1>
          <p className="text-muted-foreground">
            Execution plans, slow queries, index recommendations, and
            inefficiency findings.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Slow Queries</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center py-10 text-muted-foreground text-sm">
                Connect a database to view slow-query ranking from
                pg_stat_statements.
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Index Recommendations</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center py-10 text-muted-foreground text-sm">
                Evidence-based CREATE INDEX proposals. No DDL is executed
                automatically.
              </div>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Inefficiency Rules</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="text-sm text-muted-foreground space-y-2 list-disc pl-5">
              <li>SELECT * usage</li>
              <li>Missing LIMIT on exploratory queries</li>
              <li>Leading-wildcard LIKE patterns</li>
              <li>Functions on indexed predicate columns</li>
              <li>Redundant DISTINCT with GROUP BY</li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </Layout>
  )
}
