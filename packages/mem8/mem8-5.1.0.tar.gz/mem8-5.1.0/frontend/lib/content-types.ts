export type ContentType = 'research' | 'plan' | 'thought';

export interface ResearchMetadata {
  date: string;
  researcher: string;
  git_commit?: string;
  branch?: string;
  repository?: string;
  topic: string;
  status: 'complete' | 'in-progress' | 'draft';
  last_updated?: string;
  last_updated_by?: string;
}

export interface PlanMetadata {
  date: string;
  author: string;
  status: 'proposed' | 'in-progress' | 'complete' | 'on-hold';
  priority: 'high' | 'medium' | 'low';
  complexity?: 'low' | 'medium' | 'high';
  estimated_effort?: string;
}

export function detectContentType(tags: string[]): ContentType {
  if (tags.includes('research')) return 'research';
  if (tags.includes('plans')) return 'plan';
  return 'thought';
}

export function parseYamlMetadata(content: string): Record<string, string | string[]> {
  // Parse YAML frontmatter from content
  const yamlMatch = content.match(/^---\n([\s\S]*?)\n---/);
  if (!yamlMatch) return {};
  
  // Simple YAML parser for our specific metadata structure
  const yamlContent = yamlMatch[1];
  const metadata: Record<string, string | string[]> = {};
  
  yamlContent.split('\n').forEach(line => {
    const colonIndex = line.indexOf(':');
    if (colonIndex > 0) {
      const key = line.substring(0, colonIndex).trim();
      let value: string | string[] = line.substring(colonIndex + 1).trim();
      
      // Handle arrays
      if (value.startsWith('[') && value.endsWith(']')) {
        value = value.slice(1, -1).split(',').map(v => v.trim().replace(/['"]/g, ''));
      }
      
      metadata[key] = value;
    }
  });
  
  return metadata;
}