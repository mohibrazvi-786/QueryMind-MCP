import * as React from "react"
import { cn } from "@/lib/utils"

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  className?: string
}

export function Card({ className, ...props }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-border bg-card text-card-foreground shadow-sm",
        className
      )}
      {...props}
    />
  )
}

export interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  className?: string
}

export function CardHeader({ className, ...props }: CardHeaderProps) {
  return (
    <div className={cn("flex flex-col space-y-1.5 p-6", className)} {...props} />
  )
}

export interface CardTitleProps extends React.HTMLAttributes<HTMLHeadingElement> {
  className?: string
}

export function CardTitle({ className, ...props }: CardTitleProps) {
  return (
    <h3
      className={cn(
        "text-2xl font-bold leading-none tracking-tight",
        className
      )}
      {...props}
    />
  )
}

export interface CardContentProps extends React.HTMLAttributes<HTMLDivElement> {
  className?: string
}

export function CardContent({ className, ...props }: CardContentProps) {
  return (
    <div className={cn("p-6 pt-0", className)} {...props} />
  )
}
