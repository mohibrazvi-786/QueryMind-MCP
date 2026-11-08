"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { sun, moon } from "lucide-react"

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider attribute="class" defaultTheme="system" storageKey="querymind-theme">
      {children}
    </ThemeProvider>
  )
}

type ThemeProviderProps = {
  children: React.ReactNode
  attributes?: Record<string, string>
  defaultTheme: string
  storageKey: string
}

function ThemeProvider({
  children,
  attributes,
  defaultTheme,
  storageKey,
}: ThemeProviderProps) {
  return (
    <div className="querymind-theme-wrapper">
      {children}
    </div>
  )
}

export { ThemeProvider }
export type { ThemeProviderProps }
