"use client"

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
import { Database, Plus, RefreshCw, Shield, Link } from "lucide-react"

export default function ConnectionsPage() {
  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Database Connections</h1>
            <p className="text-muted-foreground">
              Manage registered target database connections. All access is
              read-only and organization-scoped.
            </p>
          </div>
          <Button>
            <Plus className="h-4 w-4 mr-2" /> Add Connection
          </Button>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Registered Connections</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="rounded-lg border border-border p-6 text-center text-muted-foreground">
              <Database className="h-8 w-8 mb-2 opacity-50" />
              <p>No connections registered.</p>
              <p className="mt-2 text-xs">
                Use the connect_database MCP tool or add one here to begin
                inspecting a target database.
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Add a Connection</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm font-medium text-muted-foreground">
                  Connection ID
                </label>
                <Input placeholder="ecommerce-prod" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-muted-foreground">
                  Organization ID
                </label>
                <Input placeholder="org-1" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-muted-foreground">
                  Database URL
                </label>
                <Input
                  placeholder="postgresql+psycopg2://readonly@localhost:5432/ecommerce"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-muted-foreground">
                  Statement Timeout (ms)
                </label>
                <Input defaultValue="10000" type="number" />
              </div>
            </div>
            <p className="text-xs text-muted-foreground">
              Credentials are never stored or displayed in plaintext.
              Connections use encrypted credentials at rest and read-only
              database roles.
            </p>
            <div className="flex items-center gap-2">
              <Button onClick={() => {}}>
                <RefreshCw className="h-4 w-4 mr-2" /> Test &amp; Connect
              </Button>
              <Button variant="outline">Cancel</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </Layout>
  )
}
