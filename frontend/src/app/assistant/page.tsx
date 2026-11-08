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
import { Zap, Copy, Play, Database, Clock } from "lucide-react"

export default function AssistantPage() {
  const [question, setQuestion] = useState("")
  const [answer, setAnswer] = useState<string | null>(null)
  const [sql, setSql] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleGenerate = async () => {
    setLoading(true)
    try {
      const res = await fetch("http://127.0.0.1:8000/auth/me", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      })
      if (!res.ok) throw new Error("API request failed")
      const data = await res.json()
      setAnswer(data.explanation || "")
      setSql(data.sql || "")
    } catch {
      setAnswer(
        "Unable to reach the QueryMind API. Start the backend and try again."
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">AI Database Assistant</h1>
            <p className="text-muted-foreground">
              Ask questions about your database in natural language. SQL is
              validated as read-only before execution.
            </p>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-12">
          <div className="lg:col-span-4">
            <Card>
              <CardHeader>
                <CardTitle>Ask a Question</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Input
                  placeholder="e.g. Find my top 10 customers by spending"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                />
                <Button
                  onClick={handleGenerate}
                  disabled={loading || !question.trim()}
                  className="w-full"
                >
                  {loading ? (
                    <>
                      <Clock className="h-4 w-4 mr-2 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Zap className="h-4 w-4 mr-2" /> Generate SQL
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          </div>

          <div className="lg:col-span-8">
            <Card>
              <CardHeader>
                <CardTitle>Generated SQL</CardTitle>
              </CardHeader>
              <CardContent>
                {sql ? (
                  <>
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-xs font-medium text-muted-foreground">
                        PostgreSQL
                      </span>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          navigator.clipboard.writeText(sql)
                        }}
                      >
                        <Copy className="h-3 w-3 mr-2" /> Copy
                      </Button>
                    </div>
                    <pre className="p-4 rounded-md bg-muted text-sm overflow-auto font-mono">
                      <code>{sql}</code>
                    </pre>
                    <div className="mt-4 flex gap-2">
                      <Button variant="outline" size="sm" disabled>
                        <Play className="h-3 w-3 mr-2" /> Execute Query
                      </Button>
                    </div>
                    {answer && (
                      <div className="mt-4 pt-4 border-t border-border text-sm text-muted-foreground">
                        {answer}
                      </div>
                    )}
                  </>
                ) : (
                  <div className="flex h-64 items-center justify-center rounded-lg border border-dashed border-border bg-background/50 text-muted-foreground text-sm">
                    Generate a query to see SQL, validation results, and
                    explanation here.
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </Layout>
  )
}
