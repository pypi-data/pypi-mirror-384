'use client'

import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import { cn } from '@/lib/utils'

interface MarkdownRendererProps {
  content: string
  className?: string
}

export function MarkdownRenderer({ content, className }: MarkdownRendererProps) {
  return (
    <div 
      className={cn(
        // Base prose styling
        "prose prose-invert max-w-none font-mono text-sm",
        // Terminal color customizations
        "prose-headings:text-primary prose-headings:terminal-glow prose-headings:font-mono",
        "prose-strong:text-primary prose-strong:terminal-glow",
        "prose-code:bg-muted prose-code:text-accent prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:font-mono",
        "prose-pre:bg-card prose-pre:border prose-pre:border-primary/20 prose-pre:shadow-lg",
        "prose-blockquote:border-l-primary prose-blockquote:text-muted-foreground",
        "prose-a:text-accent prose-a:no-underline hover:prose-a:underline",
        "prose-ul:text-foreground prose-ol:text-foreground prose-li:text-foreground",
        "prose-table:border-primary/20 prose-th:border-primary/20 prose-td:border-primary/20",
        "prose-th:bg-muted prose-th:text-primary prose-th:font-mono",
        // Custom terminal effects
        "[&_h1]:text-xl [&_h1]:mb-4 [&_h1]:border-b [&_h1]:border-primary/20 [&_h1]:pb-2",
        "[&_h2]:text-lg [&_h2]:mb-3 [&_h2]:text-primary",
        "[&_h3]:text-base [&_h3]:mb-2 [&_h3]:text-accent",
        "[&_p]:mb-4 [&_p]:leading-relaxed",
        "[&_code]:before:content-none [&_code]:after:content-none",
        className
      )}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          // Custom components for terminal styling
          h1: ({ children }) => (
            <h1 className="terminal-glow text-primary font-mono border-b border-primary/20 pb-2">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="terminal-glow text-primary font-mono">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-accent font-mono">
              {children}
            </h3>
          ),
          code: ({ children, ...props }) => {
            // Check if this is an inline code element by looking at the props
            const isInline = !props.className || !props.className.includes('hljs')
            
            if (isInline) {
              return (
                <code className="bg-muted text-accent px-1 py-0.5 rounded font-mono text-xs" {...props}>
                  {children}
                </code>
              )
            }
            return (
              <code className="font-mono text-sm" {...props}>
                {children}
              </code>
            )
          },
          pre: ({ children, ...props }) => (
            <pre className="bg-card border border-primary/20 p-4 rounded-lg overflow-x-auto" {...props}>
              {children}
            </pre>
          ),
          blockquote: ({ children, ...props }) => (
            <blockquote className="border-l-4 border-primary/40 pl-4 italic text-muted-foreground" {...props}>
              {children}
            </blockquote>
          ),
          a: ({ children, href, ...props }) => (
            <a 
              href={href} 
              className="text-accent hover:text-accent/80 underline transition-colors" 
              {...props}
            >
              {children}
            </a>
          ),
          table: ({ children, ...props }) => (
            <div className="overflow-x-auto">
              <table className="border-collapse border border-primary/20 w-full" {...props}>
                {children}
              </table>
            </div>
          ),
          th: ({ children, ...props }) => (
            <th className="border border-primary/20 bg-muted px-3 py-2 text-left font-mono text-primary" {...props}>
              {children}
            </th>
          ),
          td: ({ children, ...props }) => (
            <td className="border border-primary/20 px-3 py-2" {...props}>
              {children}
            </td>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}