import * as React from "react"
import { cn } from "@/lib/utils"
import { User } from "lucide-react"

export const Avatar = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "relative flex shrink-0 overflow-hidden rounded-full",
      className
    )}
    {...props}
  >
    <span className="absolute inset-0 flex items-center justify-center bg-secondary text-muted-foreground">
      <User className="h-4 w-4" />
    </span>
  </div>
))
Avatar.displayName = "Avatar"

export { Avatar }
