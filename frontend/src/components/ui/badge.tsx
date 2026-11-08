import * as React from "react"
import { cn } from "@/lib/utils"

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "secondary" | "destructive" | "outline"
  className?: string
}

export function Badge({
  className,
  variant = "default",
  ...props
}: BadgeProps) {
  return (
    <div
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
        {
          default: "bg-primary text-primary-foreground",
          secondary: "bg-secondary text-secondary-foreground",
          destructive:
            "bg-destructive text-destructive-foreground",
          outline: "border-input bg-transparent",
        }[variant],
        className
      )},
      {...props}
    />
  )
}
