import yaml from 'js-yaml'

export interface ParsedContent {
  frontmatter: string
  content: string
  metadata: Record<string, unknown>
}

export function parseContent(rawContent: string): ParsedContent {
  const frontmatterMatch = rawContent.match(/^---\n([\s\S]*?)\n---\n?([\s\S]*)$/)
  
  if (!frontmatterMatch) {
    return {
      frontmatter: '---\n---',
      content: rawContent,
      metadata: {}
    }
  }

  const [, frontmatterStr, content] = frontmatterMatch
  let metadata: Record<string, unknown> = {}
  
  try {
    metadata = yaml.load(frontmatterStr) as Record<string, unknown> || {}
  } catch (error) {
    console.error('Error parsing YAML frontmatter:', error)
  }

  return {
    frontmatter: `---\n${frontmatterStr}\n---`,
    content: content.trim(),
    metadata
  }
}

export function combineContent(frontmatter: string, content: string): string {
  // Remove existing --- markers from frontmatter if present
  const cleanFrontmatter = frontmatter.replace(/^---\n?/, '').replace(/\n?---$/, '')
  
  return `---\n${cleanFrontmatter}\n---\n\n${content}`
}

export function validateYaml(yamlString: string): { isValid: boolean; error?: string } {
  try {
    yaml.load(yamlString)
    return { isValid: true }
  } catch (error) {
    return { 
      isValid: false, 
      error: error instanceof Error ? error.message : 'Invalid YAML'
    }
  }
}