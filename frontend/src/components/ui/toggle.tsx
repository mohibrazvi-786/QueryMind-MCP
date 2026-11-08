"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

interface ToggleProps extends React.HTMLAttributes<HTMLButtonElement> {
  checked?: boolean
  defaultChecked?: boolean
  onCheckedChange?: (checked: boolean) => void
  size?: "default" | "sm"
}

const Toggle = React.forwardRef<
  HTMLButtonElement,
  ToggleProps
>(({ className, checked, defaultChecked, onCheckedChange, size = "default", ...props }, ref) => {
  const [pressed, setPressed] = React.useState<boolean>(defaultChecked ?? false)
  const isControlled = checked !== undefined
  const isPressed = isControlled ? checked : pressed

  const handleChange = React.useCallback(() => {
    const newValue = !isPressed
    if (!isControlled) {
      setPressed(newValue)
    }
    onCheckedChange?.(newValue)
  }, [isPressed, isControlled, onCheckedChange])

  const sizes = {
    default: "h-9 w-18",
    sm: "h-8 w-14",
  }

  return (
    <button
      ref={ref}
      type="button"
      role="switch"
      aria-checked={isPressed}
      onClick={handleChange}
      className={cn(
        "relative inline-flex items-center shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:bg-primary data-[state=unchecked]:bg-input",
        sizes[size],
        className
      )}
      data-state={isPressed ? "checked" : "unchecked"}
      {...props}
    >
      <span className={cn(
        "pointer-events-none block h-3 w-3 rounded-full bg-white shadow ring-0 transition-transform",
        isPressed ? "translate-x-5" : "translate-x-0.5"
      )} />
    </button>
  )
})
Toggle.displayName = "Toggle"

export { Toggle }
