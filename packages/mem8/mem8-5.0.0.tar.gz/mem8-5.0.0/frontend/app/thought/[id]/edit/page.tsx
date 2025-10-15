'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useFilesystemThought, useUpdateThought, useUpdateFilesystemThought } from '@/hooks/useApi'
import { MagicCard } from '@/components/ui/magic-card'
import { Dock, DockItem } from '@/components/ui/dock'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ArrowLeft, Save, AlertCircle, Eye, FileText, Code, Settings } from 'lucide-react'
import { YamlEditor } from '@/components/editor/YamlEditor'
import { ContentEditor } from '@/components/editor/ContentEditor'
import { MarkdownRenderer } from '@/components/editor/MarkdownRenderer'
import { parseContent, combineContent, validateYaml } from '@/lib/yaml-utils'

type ViewMode = 'preview' | 'content' | 'frontmatter' | 'settings'

export default function EditThoughtPage() {
  const params = useParams()
  const router = useRouter()
  const thoughtId = params.id as string
  
  const { data: thought, isLoading, error } = useFilesystemThought(thoughtId)
  const updateThought = useUpdateThought()
  const updateFilesystemThought = useUpdateFilesystemThought()
  
  const [frontmatter, setFrontmatter] = useState('')
  const [content, setContent] = useState('')
  const [hasChanges, setHasChanges] = useState(false)
  const [yamlError, setYamlError] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<ViewMode>('preview')
  
  // Initialize content when thought loads
  useEffect(() => {
    if (thought) {
      const parsed = parseContent(thought.content)
      setFrontmatter(parsed.frontmatter.replace(/^---\n/, '').replace(/\n---$/, ''))
      setContent(parsed.content)
    }
  }, [thought])

  const handleFrontmatterChange = (value: string) => {
    setFrontmatter(value)
    setHasChanges(true)
    
    // Validate YAML
    const validation = validateYaml(value)
    setYamlError(validation.isValid ? null : validation.error!)
  }

  const handleContentChange = (value: string) => {
    setContent(value)
    setHasChanges(true)
  }

  const handleSave = async () => {
    if (!thought || !hasChanges || yamlError) return
    
    try {
      const combinedContent = combineContent(frontmatter, content)
      
      // Check if this is a filesystem thought (has file_path property)
      if ('file_path' in thought) {
        // Use filesystem update for local thoughts
        await updateFilesystemThought.mutateAsync({
          id: thought.id,
          content: combinedContent
        })
      } else {
        // Use database update for database thoughts
        await updateThought.mutateAsync({
          id: thought.id,
          thought: { content: combinedContent }
        })
      }
      
      setHasChanges(false)
    } catch (error) {
      console.error('Failed to save thought:', error)
    }
  }
  
  if (isLoading) {
    return (
      <div className="min-h-screen bg-background p-6">
        <div className="max-w-7xl mx-auto">
          <div className="terminal-text animate-pulse">
            <span className="terminal-glow">{'>'}</span> Loading thought editor...
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
      <div className="max-w-7xl mx-auto p-6 flex-1 flex flex-col min-h-0">
        {/* Header */}
        <div className="flex items-center justify-between mb-6 shrink-0">
          <div className="flex items-center gap-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => router.back()}
              className="font-mono"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            <h1 className="text-xl font-bold terminal-glow text-primary font-mono">
              {thought.title}
            </h1>
            {hasChanges && <Badge variant="syncing">Unsaved</Badge>}
          </div>
          
          <Button
            onClick={handleSave}
            disabled={!hasChanges || updateThought.isPending || !!yamlError}
            className="font-mono"
            variant="terminal"
          >
            <Save className="w-4 h-4 mr-2" />
            {updateThought.isPending ? 'Saving...' : 'Save'}
          </Button>
        </div>

        {/* YAML Error Alert */}
        {yamlError && (
          <div className="mb-4 p-3 border border-destructive/20 bg-destructive/10 rounded-lg shrink-0">
            <div className="flex items-center gap-2 text-destructive font-mono text-sm">
              <AlertCircle className="w-4 h-4" />
              YAML Syntax Error: {yamlError}
            </div>
          </div>
        )}

        {/* Editor Container */}
        <div className="flex-1 flex flex-col min-h-0 relative">
          {/* Magic Card Content */}
          <MagicCard className="flex-1 border-primary/30 bg-card/50 backdrop-blur-sm">
            <div className="h-full p-6 flex flex-col">
              {viewMode === 'preview' && (
                <div className="h-full overflow-auto">
                  {content ? (
                    <MarkdownRenderer content={content} />
                  ) : (
                    <div className="text-muted-foreground font-mono text-sm italic flex items-center justify-center h-full">
                      No markdown content to preview
                    </div>
                  )}
                </div>
              )}

              {viewMode === 'content' && (
                <div className="h-full">
                  <ContentEditor
                    value={content}
                    onChange={handleContentChange}
                    height="100%"
                  />
                </div>
              )}

              {viewMode === 'frontmatter' && (
                <div className="h-full">
                  <YamlEditor
                    value={frontmatter}
                    onChange={handleFrontmatterChange}
                    height="100%"
                  />
                </div>
              )}

              {viewMode === 'settings' && (
                <div className="h-full overflow-auto">
                  <div className="space-y-6">
                    <div>
                      <h3 className="text-lg font-semibold mb-3 terminal-glow">Document Settings</h3>
                      <div className="grid grid-cols-2 gap-4 text-sm font-mono">
                        <div>
                          <span className="text-muted-foreground">Title:</span>
                          <div className="text-primary">{thought?.title}</div>
                        </div>
                        <div>
                          <span className="text-muted-foreground">ID:</span>
                          <div className="text-primary">{thoughtId}</div>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Words:</span>
                          <div className="text-primary">{content.split(/\s+/).length}</div>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Characters:</span>
                          <div className="text-primary">{content.length}</div>
                        </div>
                      </div>
                    </div>
                    
                    {yamlError && (
                      <div>
                        <h4 className="text-md font-semibold mb-2 text-destructive">YAML Issues</h4>
                        <div className="bg-destructive/10 p-3 rounded border border-destructive/20">
                          <div className="text-destructive text-sm font-mono">{yamlError}</div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </MagicCard>

          {/* Floating Dock Navigation */}
          <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 z-50">
            <Dock>
              <DockItem 
                isActive={viewMode === 'preview'} 
                onClick={() => setViewMode('preview')}
                className="group relative"
              >
                <Eye className="w-5 h-5" />
                <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-card border border-primary/20 px-2 py-1 rounded text-xs font-mono opacity-0 group-hover:opacity-100 transition-opacity">
                  Preview
                </div>
              </DockItem>
              
              <DockItem 
                isActive={viewMode === 'content'} 
                onClick={() => setViewMode('content')}
                className="group relative"
              >
                <FileText className="w-5 h-5" />
                <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-card border border-primary/20 px-2 py-1 rounded text-xs font-mono opacity-0 group-hover:opacity-100 transition-opacity">
                  Content
                </div>
              </DockItem>
              
              <DockItem 
                isActive={viewMode === 'frontmatter'} 
                onClick={() => setViewMode('frontmatter')}
                className="group relative"
              >
                <Code className="w-5 h-5" />
                {yamlError && <div className="absolute -top-1 -right-1 w-2 h-2 bg-destructive rounded-full" />}
                <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-card border border-primary/20 px-2 py-1 rounded text-xs font-mono opacity-0 group-hover:opacity-100 transition-opacity">
                  YAML
                </div>
              </DockItem>
              
              <DockItem 
                isActive={viewMode === 'settings'} 
                onClick={() => setViewMode('settings')}
                className="group relative"
              >
                <Settings className="w-5 h-5" />
                <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-card border border-primary/20 px-2 py-1 rounded text-xs font-mono opacity-0 group-hover:opacity-100 transition-opacity">
                  Settings
                </div>
              </DockItem>
            </Dock>
          </div>
        </div>
      </div>
    </div>
  )
}