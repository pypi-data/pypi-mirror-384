"use client"

import React from "react"
import { motion } from "framer-motion"
import { cn } from "@/lib/utils"

interface DockProps {
  className?: string
  children: React.ReactNode
}

interface DockItemProps {
  className?: string
  children: React.ReactNode
  onClick?: () => void
  isActive?: boolean
}

const Dock = React.forwardRef<HTMLDivElement, DockProps>(
  ({ className, children }, ref) => {
    return (
      <motion.div
        ref={ref}
        className={cn(
          "mx-auto flex h-16 items-center justify-center gap-2 rounded-2xl border border-primary/20 bg-card/80 backdrop-blur-md px-4 shadow-lg",
          "supports-[backdrop-filter]:bg-card/60",
          className
        )}
        initial={{ y: 50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
      >
        {children}
      </motion.div>
    )
  }
)
Dock.displayName = "Dock"

const DockItem = React.forwardRef<HTMLButtonElement, DockItemProps>(
  ({ className, children, onClick, isActive, ...props }, ref) => {
    return (
      <motion.button
        ref={ref}
        onClick={onClick}
        className={cn(
          "flex h-12 w-12 items-center justify-center rounded-xl text-muted-foreground transition-all duration-200",
          "hover:bg-primary/10 hover:text-primary focus:outline-none focus:ring-2 focus:ring-primary/50",
          "active:scale-95",
          isActive && "bg-primary/20 text-primary terminal-glow",
          className
        )}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
        {...props}
      >
        {children}
      </motion.button>
    )
  }
)
DockItem.displayName = "DockItem"

export { Dock, DockItem }