"use client"

import { useState } from "react"
import { Layout } from "@/components/Layout"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { FileText, Play, Database, Clock } from "lucide-react"

export default function SqlPage() {
  const [sql, setSql] = useState("")
  const [result, setResult] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">SQL Workspace</h1>
            <p className="text-muted-foreground">
              Write, validate, and execute read-only SQL. Execution requires an
              explicit user action and server-side authorization.
            </p>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-12">
          <div className="lg:col-span-6">
            <Card>
              <CardHeader>
                <CardTitle>SQL Editor</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Input
                  placeholder="SELECT * FROM customers WHERE ... LIMIT 100"
                  value={sql}
                  onChange={(e) => setSql(e.target.value)}
                  className="font-mono text-sm h-64"
                />
                <div className="flex gap-2">
                  <Button
                    onClick={async () => {
                      setLoading(true)
                      try {
                        const res = await fetch("http://127.0.0.1:8000/auth/me", {
                          method: "POST",
                          headers: { "Content-Type": "application/json" },
                          body: JSON.stringify({ sql }),
                        })
                        const data = await res.json()
                        setResult(JSON.stringify(data, null, 2))
                      } catch {
                        setResult("Unable to reach the QueryMind API.")
                      } finally {
                        setLoading(false)
                      }
                    }}
                    disabled={!sql.trim() || loading}
                    className="w-full"
                  >
                    {loading ? (
                      <Clock className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <Play className="h-4 w-4 mr-2" />
                    )}
                    Validate &amp; Execute
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="lg:col-span-6">
            <Card>
              <CardHeader>
                <CardTitle>Result</CardTitle>
              </CardHeader>
              <CardContent>
                {result ? (
                  <pre className="p-4 rounded-md bg-muted text-sm overflow-auto font-mono">
                    <code>{result}</code>
                  </pre>
                ) : (
                  <div className="flex h-64 items-center justify-center rounded-lg border border-dashed border-border bg-background/50 text-muted-foreground text-sm">
                    Enter and run a query to see results here.
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>

        <Separator />
        <div className="rounded-lg border border-border p-6">
          <CardHeader>
            <CardTitle>Execution Restrictions</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="text-sm text-muted-foreground space-y-2 list-disc pl-5">
              <li>SELECT-only — INSERT, UPDATE, DELETE, DDL rejected</li>
              <li>Single statement only</li>
              <li>Statement timeout enforced</li>
              <li>Result rows capped</li>
              <li>All executions audit-logged</li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </Layout>
  )
}
