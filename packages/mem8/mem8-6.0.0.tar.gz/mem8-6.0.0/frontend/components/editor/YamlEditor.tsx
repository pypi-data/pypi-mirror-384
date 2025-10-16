'use client'

import React from 'react'
import CodeMirror from '@uiw/react-codemirror'
import { yaml } from '@codemirror/lang-yaml'
import { createTheme } from '@uiw/codemirror-themes'

interface YamlEditorProps {
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
    { tag: 'punctuation', color: '#00ff41' },
    { tag: 'propertyName', color: '#ffb700' },
    { tag: 'literal', color: '#00ffff' },
  ]
})

export function YamlEditor({ 
  value, 
  onChange, 
  height = '100%', 
  readOnly = false 
}: YamlEditorProps) {
  return (
    <div className="w-full h-full border border-primary/20 rounded-lg overflow-hidden">
      <CodeMirror
        value={value}
        height={height}
        theme={terminalTheme}
        extensions={[yaml()]}
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