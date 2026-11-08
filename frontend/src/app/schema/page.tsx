"use client"

import { Layout } from "@/components/Layout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"

export default function SchemaPage() {
  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Schema Explorer</h1>
            <p className="text-muted-foreground">
              Browse discovered tables, columns, keys, indexes, and
              relationships.
            </p>
          </div>
        </div>

        <div className="space-y-4">
          <Input placeholder="Search tables, columns..." />
          <Card>
            <CardHeader>
              <CardTitle>Discovered Tables</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="rounded-lg border border-border p-6 text-center text-muted-foreground">
                Connect a database to discover its schema. Table and column
                information is retrieved from PostgreSQL system catalogues —
                nothing is hardcoded.
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </Layout>
  )
}
