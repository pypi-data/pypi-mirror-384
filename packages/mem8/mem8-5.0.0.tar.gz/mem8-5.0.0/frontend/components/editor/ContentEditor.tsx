'use client'

import React from 'react'
import CodeMirror from '@uiw/react-codemirror'
import { markdown } from '@codemirror/lang-markdown'
import { createTheme } from '@uiw/codemirror-themes'

interface ContentEditorProps {
  value: string
  onChange: (value: string) => void
  height?: string
  readOnly?: boolean
}

// Terminal-style theme matching the app's design
const terminalTheme = createTheme({
  theme: 'dark',
  settings: {
    background: '#0a0e27',
    foreground: '#00ff41',
    caret: '#00ff41',
    selection: '#00ff4133',
    selectionMatch: '#00ff4122',
    lineHighlight: '#1a1e37',
    gutterBackground: '#0a0e27',
    gutterForeground: '#666666',
    gutterActiveForeground: '#00ff41',
  },
  styles: [
    { tag: 'comment', color: '#666666' },
    { tag: 'string', color: '#00ff41' },
    { tag: 'number', color: '#00ffff' },
    { tag: 'keyword', color: '#ff6b6b' },
    { tag: 'operator', color: '#ffb700' },
    { tag: 'punctuation', color: '#888888' },
    
    // Enhanced Markdown syntax highlighting
    { tag: 'heading', color: '#00ff41', fontWeight: 'bold' },
    { tag: 'emphasis', color: '#00ffff', fontStyle: 'italic' },
    { tag: 'strong', color: '#ffb700', fontWeight: 'bold' },
    { tag: 'link', color: '#4fc3f7' },
    { tag: 'url', color: '#4fc3f7' },
    { tag: 'monospace', color: '#ff9800', backgroundColor: '#1a1a1a' },
    { tag: 'quote', color: '#999999', fontStyle: 'italic' },
    { tag: 'list', color: '#00ff41' },
    { tag: 'strikethrough', color: '#888888', textDecoration: 'line-through' },
    
    // Code blocks
    { tag: 'codeMark', color: '#ff9800' },
    { tag: 'codeText', color: '#ff9800', backgroundColor: '#1a1a1a' },
    
    // Additional markdown elements
    { tag: 'processingInstruction', color: '#666666' },
    { tag: 'definition', color: '#4fc3f7' },
    { tag: 'contentSeparator', color: '#666666' },
  ]
})

export function ContentEditor({ 
  value, 
  onChange, 
  height = '100%', 
  readOnly = false 
}: ContentEditorProps) {
  return (
    <div className="w-full h-full border border-primary/20 rounded-lg overflow-hidden">
      <CodeMirror
        value={value}
        height={height}
        theme={terminalTheme}
        extensions={[markdown()]}
        onChange={(val) => onChange(val)}
        editable={!readOnly}
        basicSetup={{
          lineNumbers: true,
          foldGutter: true,
          dropCursor: false,
          allowMultipleSelections: false,
          highlightActiveLine: true,
          searchKeymap: true,
          autocompletion: true,
          closeBrackets: true,
          history: true,
          drawSelection: true,
        }}
        style={{
          fontFamily: 'var(--font-mono), JetBrains Mono, monospace',
          fontSize: '14px',
        }}
      />
    </div>
  )
}