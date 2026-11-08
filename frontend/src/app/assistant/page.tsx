"use client"

import { useState } from "react"
import { Layout } from "@/components/Layout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

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
                >
                  {loading ? "Generating..." : "Generate SQL"}
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
                    <pre className="p-4 rounded-md bg-muted text-sm overflow-auto">
                      <code>{sql}</code>
                    </pre>
                    <div className="mt-4 flex gap-2">
                      <Button variant="outline" size="sm">
                        Copy SQL
                      </Button>
                      <Button variant="secondary" size="sm" disabled>
                        Execute Query
                      </Button>
                    </div>
                    {answer && (
                      <div className="mt-4 text-sm text-muted-foreground">
                        {answer}
                      </div>
                    )}
                  </>
                ) : (
                  <div className="text-center py-10 text-muted-foreground text-sm">
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
