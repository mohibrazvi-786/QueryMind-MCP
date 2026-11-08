"use client"

import * as React from "react"
import { X, CheckCircle2, AlertTriangle, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

const TOAST_LIMIT = 1
const TOAST_REMOVE_DELAY = 1000000

type ToastActionElement = React.ReactElement

type ToastState = {
  id: string
  title?: string
  description?: string
  action?: ToastActionElement
  duration?: number
  variant?: "default" | "destructive" | "success" | "warning"
}

type ToastPropsWithId = ToastState & {
  id: string
}

type ActionType = {
  addOrUpdate: (props: ToastState) => void
  remove: (id?: string) => void
}

let count = 0

function genId() {
  count = (count + 1) % Number.MAX_SAFE_INTEGER
  return count.toString()
}

type Action = { type: "ADD_TOAST"; toast: ToastState } | { type: "REMOVE_TOAST"; id?: string }

const toastTimeouts = new Map<string, ReturnType<typeof setTimeout>>()

const reducer = (state: { toasts: ToastState[] }, action: Action) => {
  switch (action.type) {
    case "ADD_TOAST":
      return { toasts: [action.toast, ...state.toasts].slice(0, TOAST_LIMIT) }
    case "REMOVE_TOAST":
      return {
        ...state,
        toasts: action.id
          ? state.toasts.filter((t) => t.id !== action.id)
          : [],
      }
  }
  return state
}

function useToast() {
  const [state, dispatch] = React.useReducer(reducer, { toasts: [] })

  const toast = (props: ToastState) => {
    const id = genId()
    dispatch({ type: "ADD_TOAST", toast: { ...props, id } })
    return { id, dismiss: () => dispatch({ type: "REMOVE_TOAST", id }) }
  }

  const dismiss = (id?: string) => dispatch({ type: "REMOVE_TOAST", id })

  return { ...state, toast, dismiss }
}

const VariantStyles: Record<string, string> = {
  default: "bg-background border-border",
  destructive: "border-destructive/50 text-destructive dark:text-destructive bg-destructive/50",
  success: "border-green-500/50 text-green-700 bg-green-500/10",
  warning: "border-amber-500/50 text-amber-800 bg-amber-500/10",
}

const VariantIcons: Record<string, React.ComponentType> = {
  default: CheckCircle2,
  destructive: AlertTriangle,
  success: CheckCircle2,
  warning: AlertTriangle,
}

const Toast = React.forwardRef<
  HTMLDivElement,
  React.ComponentPropsWithoutRef<typeof ToastPrimitive.Root> & {
    duration?: number
  }
>(({ className, variant = "default", ...props }, ref) => {
  const Icon = VariantIcons[variant]
  return (
    <div
      ref={ref}
      className={cn(
        "grid w-full max-w-sm grid-cols-1 items-start gap-4 border p-4 shadow-lg transition-all data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-80 data-[state=open]:slide-in-from-top-10 data-[state=closed]:slide-out-to-bottom-10",
        VariantStyles[variant],
        className
      )}
      {...props}
    >
      <div className="flex items-center gap-3 shrink-0">
        <Icon className="h-5 w-5 shrink-0" />
      </div>
      <div className="grid gap-1">
        <h4 className="text-sm font-semibold">{props.title}</h4>
        {props.description && (
          <p className="text-sm opacity-80">{props.description}</p>
        )}
      </div>
      <button
        className="absolute right-2 top-2 rounded-sm opacity-50 transition-opacity hover:opacity-100 focus:outline-none focus:ring-1 focus:ring-ring"
        onClick={props.onClose}
        aria-label="Close"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  )
})
Toast.displayName = "Toast"

const ToastProvider = React.forwardRef<
  HTMLDivElement,
  { children: React.ReactNode }
>(({ children }, ref) => {
  const { toasts, toast, dismiss } = useToast()
  return (
    <div
      ref={ref}
      className="fixed top-0 z-[100] flex max-h-screen w-full flex-col-reverse p-4 sm:bottom-0 sm:right-0 sm:top-0 sm:left-0"
    >
      {toasts.map((t) => (
        <Toast key={t.id} {...t} onClose={() => dismiss(t.id)} />
      ))}
    </div>
  )
})
ToastProvider.displayName = "ToastProvider"

export { ToastProvider, Toast, useToast }
export type { ToastState }
