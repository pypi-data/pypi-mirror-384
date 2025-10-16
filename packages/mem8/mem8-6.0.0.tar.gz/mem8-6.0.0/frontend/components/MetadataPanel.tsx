import { Badge } from '@/components/ui/badge';
import { CalendarDays, GitCommit, User } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ResearchMetadata, PlanMetadata } from '@/lib/content-types';

interface MetadataPanelProps {
  metadata: ResearchMetadata | PlanMetadata;
  type: 'research' | 'plan';
  className?: string;
}

export function MetadataPanel({ metadata, type, className }: MetadataPanelProps) {
  return (
    <div className={cn(
      "border-t border-primary/20 pt-3 mt-3 space-y-2",
      "bg-primary/5 rounded-b-lg -mx-4 px-4 pb-3",
      className
    )}>
      <div className="flex flex-wrap items-center gap-3 text-xs">
        {/* Author/Researcher */}
        <div className="flex items-center gap-1 text-primary">
          <User className="w-3 h-3" />
          <span className="font-mono">
            {'researcher' in metadata ? metadata.researcher : metadata.author}
          </span>
        </div>
        
        {/* Status */}
        <Badge 
          variant={metadata.status === 'complete' ? 'active' : 'syncing'} 
          className="text-xs"
        >
          {metadata.status}
        </Badge>
        
        {/* Priority (plans only) */}
        {type === 'plan' && 'priority' in metadata && metadata.priority && (
          <Badge 
            variant={metadata.priority === 'high' ? 'error' : 'terminal'} 
            className="text-xs"
          >
            {metadata.priority}
          </Badge>
        )}
        
        {/* Date */}
        <div className="flex items-center gap-1 text-muted-foreground">
          <CalendarDays className="w-3 h-3" />
          <span className="font-mono">
            {new Date(metadata.date).toLocaleDateString()}
          </span>
        </div>
        
        {/* Git Commit (research only) */}
        {type === 'research' && 'git_commit' in metadata && metadata.git_commit && (
          <div className="flex items-center gap-1 text-accent">
            <GitCommit className="w-3 h-3" />
            <span className="font-mono text-xs">
              {metadata.git_commit.substring(0, 8)}
            </span>
          </div>
        )}
      </div>
      
      {/* Topic (research) or Effort (plans) */}
      {type === 'research' && 'topic' in metadata && (
        <div className="text-xs text-muted-foreground font-mono">
          <span className="text-primary">Topic:</span> {metadata.topic}
        </div>
      )}
      
      {type === 'plan' && 'estimated_effort' in metadata && metadata.estimated_effort && (
        <div className="text-xs text-muted-foreground font-mono">
          <span className="text-primary">Effort:</span> {metadata.estimated_effort}
        </div>
      )}
    </div>
  );
}