"use client"

import { Layout } from "@/components/Layout"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

export default function OrgPage() {
  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Organization &amp; Users</h1>
          <p className="text-muted-foreground">
            Manage organizations, members, roles, and service accounts.
            Platform administrators only.
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Roles</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="text-sm text-muted-foreground space-y-3 list-disc pl-5">
              <li>
                <strong>Platform Administrator</strong> — manage users,
                organizations, configuration
              </li>
              <li>
                <strong>Organization Administrator</strong> — manage members,
                roles, connections, reports
              </li>
              <li>
                <strong>Database Analyst</strong> — discover metadata,
                generate/validate SQL, analyze performance
              </li>
              <li>
                <strong>Read-only Viewer</strong> — view schema docs and
                reports; no query execution
              </li>
              <li>
                <strong>Service Account</strong> — machine-to-machine MCP
                access, scoped permissions
              </li>
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Organization</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="rounded-lg border border-border p-6 text-center text-muted-foreground">
              No organization context available. Sign in to see your
              organization and its members.
            </div>
          </CardContent>
        </Card>
      </div>
    </Layout>
  )
}
