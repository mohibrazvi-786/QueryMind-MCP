import * as React from "react"
import { cn } from "@/lib/utils"

const Separator = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("relative mx-auto flex h-[1px] w-full shrink-0 bg-border", className)}
    {...props}
  />
))
Separator.displayName = "Separator"

export { Separator }
