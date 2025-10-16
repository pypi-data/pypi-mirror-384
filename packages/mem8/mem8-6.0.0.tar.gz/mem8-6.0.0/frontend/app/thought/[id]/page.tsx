'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useFilesystemThought } from '@/hooks/useApi'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { ArrowLeft, Edit } from 'lucide-react'
import { MarkdownRenderer } from '@/components/editor/MarkdownRenderer'
import { parseContent } from '@/lib/yaml-utils'
import yaml from 'js-yaml'

export default function ViewThoughtPage() {
  const params = useParams()
  const router = useRouter()
  const thoughtId = params.id as string
  
  const { data: thought, isLoading, error } = useFilesystemThought(thoughtId)
  
  const [parsedContent, setParsedContent] = useState<{
    frontmatter: string
    content: string
    metadata: Record<string, any>
  } | null>(null)
  
  // Parse content when thought loads
  useEffect(() => {
    if (thought) {
      const parsed = parseContent(thought.content)
      setParsedContent(parsed)
    }
  }, [thought])
  
  if (isLoading) {
    return (
      <div className="min-h-screen bg-background p-6">
        <div className="max-w-7xl mx-auto">
          <div className="terminal-text animate-pulse">
            <span className="terminal-glow">{'>'}</span> Loading thought...
          </div>
        </div>
      </div>
    )
  }
  
  if (error || !thought) {
    return (
      <div className="min-h-screen bg-background p-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-destructive font-mono">
            <span className="terminal-glow">{'>'}</span> {error ? 'Error loading thought' : 'Thought not found'}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background bg-grid flex flex-col">
      <div className="max-w-7xl mx-auto p-6 flex-1 flex flex-col min-h-0 w-full">
        {/* Header */}
        <div className="flex items-center justify-between mb-6 shrink-0">
          <div className="flex items-center gap-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => router.push('/')}
              className="font-mono"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Home
            </Button>
            <h1 className="text-xl font-bold terminal-glow text-primary font-mono">
              {thought.title}
            </h1>
          </div>
          
          <Button
            onClick={() => router.push(`/thought/${thoughtId}/edit`)}
            className="font-mono"
            variant="terminal"
          >
            <Edit className="w-4 h-4 mr-2" />
            Edit
          </Button>
        </div>

        {/* Content View - Preview First */}
        <div className="memory-cell rounded-lg p-6 flex-1 flex flex-col min-h-0">
          <Tabs defaultValue="preview" className="flex-1 flex flex-col">
            <TabsList className="grid w-full grid-cols-3 mb-4 shrink-0">
              <TabsTrigger value="preview">Preview</TabsTrigger>
              <TabsTrigger value="frontmatter">YAML Frontmatter</TabsTrigger>
              <TabsTrigger value="raw">Raw Markdown</TabsTrigger>
            </TabsList>
            
            {/* Preview Tab (Default) */}
            <TabsContent value="preview" className="flex-1 min-h-0">
              <div className="h-full border border-primary/20 rounded-lg bg-card overflow-hidden">
                <div className="h-full overflow-auto p-6">
                  {parsedContent?.content ? (
                    <MarkdownRenderer content={parsedContent.content} />
                  ) : (
                    <div className="text-muted-foreground font-mono text-sm italic">
                      No markdown content to display
                    </div>
                  )}
                </div>
              </div>
            </TabsContent>
            
            {/* YAML Frontmatter Tab */}
            <TabsContent value="frontmatter" className="flex-1 min-h-0">
              <div className="h-full border border-primary/20 rounded-lg bg-card overflow-hidden">
                <div className="h-full overflow-auto p-6">
                  {parsedContent?.metadata && Object.keys(parsedContent.metadata).length > 0 ? (
                    <div className="font-mono text-sm">
                      <pre className="text-primary">
                        {yaml.dump(parsedContent.metadata, { indent: 2 })}
                      </pre>
                    </div>
                  ) : (
                    <div className="text-muted-foreground font-mono text-sm italic">
                      No frontmatter metadata
                    </div>
                  )}
                </div>
              </div>
            </TabsContent>
            
            {/* Raw Markdown Tab */}
            <TabsContent value="raw" className="flex-1 min-h-0">
              <div className="h-full border border-primary/20 rounded-lg bg-card overflow-hidden">
                <div className="h-full overflow-auto p-6">
                  <pre className="font-mono text-sm text-foreground whitespace-pre-wrap">
                    {parsedContent?.content || 'No content'}
                  </pre>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  )
}