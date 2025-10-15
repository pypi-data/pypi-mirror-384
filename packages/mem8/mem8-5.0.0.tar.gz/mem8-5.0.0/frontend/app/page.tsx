"use client";

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { UserDropdown } from '@/components/UserDropdown';
import { Search, Brain, Users, Zap, Database, Terminal, Plus, RefreshCw, Download, FileText, Code } from 'lucide-react';
import Image from 'next/image';
import { useHealth, useThoughts, useFilesystemThoughts, useTeams, useSystemStats, useSearchThoughts, useSyncTeam, useCreateThought } from '@/hooks/useApi';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useAuth } from '@/hooks/useAuth';
import { cn } from '@/lib/utils';
import { detectContentType, parseYamlMetadata } from '@/lib/content-types';
import { MetadataPanel } from '@/components/MetadataPanel';
import { getAppTitle } from '@/lib/version';

export default function Home() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTeamId, setSelectedTeamId] = useState<string | undefined>();
  const [contentTypeFilter, setContentTypeFilter] = useState<'all' | 'research' | 'plan'>('all');
  const [searchType] = useState<'fulltext' | 'semantic'>('fulltext');
  
  // Router hook
  const router = useRouter();
  
  // Auth hook
  const { user, isAuthenticated, isLoading: authLoading, logout, getGitHubAuthUrl } = useAuth();
  
  // API hooks
  const { data: health, isLoading: healthLoading } = useHealth();
  const { data: teams, isLoading: teamsLoading } = useTeams();
  // Filesystem thoughts (always available, no auth needed)
  const { data: filesystemThoughts, isLoading: filesystemLoading } = useFilesystemThoughts({
    limit: 10
  });
  
  // Type helper for filesystem thoughts API response
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const fsThoughts = filesystemThoughts as any;
  
  const { data: thoughts, isLoading: thoughtsLoading, refetch: refetchThoughts } = useThoughts({
    team_id: selectedTeamId,
    limit: 10
  });
  const { data: systemStats } = useSystemStats();
  const { data: searchResults, isLoading: searchLoading } = useSearchThoughts({
    query: searchQuery,
    search_type: searchType,
    team_id: selectedTeamId,
    limit: 20
  });
  
  // Mutations
  const syncTeamMutation = useSyncTeam();
  const createThoughtMutation = useCreateThought();
  
  // WebSocket for real-time updates
  const { isConnected: wsConnected } = useWebSocket({
    teamId: selectedTeamId,
    enabled: !!selectedTeamId
  });
  
  // TODO: activeUsers will be implemented when WebSocket user tracking is added
  const activeUsers: unknown[] = [];

  // Warn when backend/system values are missing so users can configure them
  useEffect(() => {
    if (systemStats) {
      const missing: string[] = [];
      if (systemStats.totalThoughts == null) missing.push('totalThoughts');
      if (systemStats.activeTeams == null) missing.push('activeTeams');
      if (systemStats.syncStatus == null) missing.push('syncStatus');
      if (systemStats.memoryUsage == null) missing.push('memoryUsage');
      if (missing.length) {
        console.warn(
          `System stats missing: ${missing.join(', ')}. Ensure backend /api/v1/system/stats provides these fields.`
        );
      }
    }
  }, [systemStats]);

  useEffect(() => {
    if (teams && teams.length) {
      const missingMemberCount = teams.filter(t => t?.settings?.memberCount == null).length;
      if (missingMemberCount > 0) {
        console.warn(
          `${missingMemberCount} team(s) missing settings.memberCount. Set this in team configuration to show accurate member counts.`
        );
      }
    }
  }, [teams]);
  
  const isConnected = !healthLoading && health?.status === 'healthy';
  
  // Event handlers
  const handleSearch = (query: string) => {
    setSearchQuery(query);
  };
  
  const handleSyncAll = async () => {
    if (selectedTeamId) {
      try {
        await syncTeamMutation.mutateAsync(selectedTeamId);
        await refetchThoughts();
      } catch (error) {
        console.error('Sync failed:', error);
      }
    }
  };
  
  const handleNewThought = async () => {
    if (!selectedTeamId) return;
    
    try {
      const newThought = {
        title: 'New Thought',
        content: '# New Thought\n\nStart writing your thoughts here...',
        path: `/thoughts/shared/new-thought-${Date.now()}.md`,
        team_id: selectedTeamId,
        thought_metadata: {
          tags: [],
          created_by: 'current-user' // TODO: Get from auth
        }
      };
      
      await createThoughtMutation.mutateAsync(newThought);
    } catch (error) {
      console.error('Failed to create thought:', error);
    }
  };
  
  const handleExportData = () => {
    // TODO: Implement data export functionality
    console.log('Export data functionality to be implemented');
  };

  const handleLogin = async () => {
    try {
      const authUrl = await getGitHubAuthUrl();
      window.location.href = authUrl;
    } catch (error) {
      console.error('Failed to get GitHub auth URL:', error);
    }
  };

  const handleLocalMode = () => {
    // Set a local storage flag to indicate we're using local mode
    localStorage.setItem('mem8-local-mode', 'true');
    // Refresh to re-evaluate authentication state
    window.location.reload();
  };

  const handleLogout = async () => {
    try {
      await logout();
      // Optionally refresh the page to reset state
      window.location.reload();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };
  
  // Get current team for display
  const currentTeam = teams?.find(team => team.id === selectedTeamId) || teams?.[0];
  
  // Transform thoughts data for display - prioritize filesystem thoughts
  const recentThoughts = (() => {
    let thoughts = [];
    
    if (searchQuery.length > 2) {
      thoughts = searchResults?.thoughts || [];
    } else if (fsThoughts?.thoughts) {
      // Use filesystem thoughts if available
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      thoughts = fsThoughts.thoughts.slice(0, 50).map((thought: any) => {
        const contentType = detectContentType(thought.tags || []);
        const metadata = parseYamlMetadata(thought.content);
        
        return {
          id: thought.id,
          title: thought.title,
          excerpt: thought.content.substring(0, 150) + '...',
          path: thought.path,
          team: thought.repository || 'Local',
          lastModified: new Date(thought.updated_at).toLocaleString(),
          tags: thought.tags || [],
          contentType,
          metadata,
          fullContent: thought.content
        };
      });
    } else {
      // Fallback to database thoughts
      thoughts = thoughts?.slice(0, 50).map(thought => {
        const tags = Array.isArray(thought.thought_metadata?.tags) ? thought.thought_metadata.tags : [];
        const contentType = detectContentType(tags);
        const metadata = parseYamlMetadata(thought.content);
        
        return {
          id: thought.id,
          title: thought.title,
          excerpt: thought.content.substring(0, 150) + '...',
          path: thought.path,
          team: currentTeam?.name || 'Unknown Team',
          lastModified: new Date(thought.updated_at).toLocaleString(),
          tags,
          contentType,
          metadata,
          fullContent: thought.content
        };
      }) || [];
    }
    
    // Apply content type filter
    if (contentTypeFilter !== 'all') {
      thoughts = thoughts.filter(thought => thought.contentType === contentTypeFilter);
    }
    
    return thoughts.slice(0, 10);
  })();
  
  // Transform teams data for team status display
  const teamStatuses = teams?.map(team => ({
    id: team.id,
    name: team.name,
    status: (wsConnected && selectedTeamId === team.id) ? 'active' : 
             syncTeamMutation.isPending ? 'syncing' : 'active',
    memberCount: team.settings?.memberCount ?? 'N/A',
    thoughtCount: systemStats?.totalThoughts ?? 'N/A'
  })) || [];

  // Set default team when teams load
  useState(() => {
    if (teams && teams.length > 0 && !selectedTeamId) {
      setSelectedTeamId(teams[0].id);
    }
  });

  // Show login screen if not authenticated
  if (!authLoading && !isAuthenticated) {
    return (
      <div className="min-h-screen bg-black text-green-400 font-mono flex items-center justify-center">
        <div className="max-w-md w-full text-center space-y-4">
          <div className="text-2xl font-bold">
            &gt; AgenticInsights TERMINAL
          </div>
          
          <div className="space-y-4">
            <div className="text-lg">&gt; AUTHENTICATION REQUIRED</div>
            
            <div className="space-y-2">
              <button
                onClick={handleLogin}
                className="w-full px-6 py-2 border border-green-400 text-green-400 hover:bg-green-400 hover:text-black transition-colors"
              >
                &gt; Connect GitHub
              </button>
              <div className="text-gray-400 text-sm text-center">&gt; Secure OAuth2 authentication</div>
              <div className="text-gray-400 text-sm text-center">&gt; No passwords stored locally</div>
            </div>

            <div className="border-t border-gray-600 pt-4">
              <button
                onClick={handleLocalMode}
                className="w-full px-6 py-2 border border-gray-500 text-gray-400 hover:bg-gray-500 hover:text-black transition-colors"
              >
                &gt; Use Local Mode
              </button>
              <div className="text-gray-500 text-sm text-center mt-1">&gt; Access local thoughts/shared directories </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      {/* Terminal Header */}
      <header className="h-8 bg-muted border-b border-border flex items-center justify-between px-4 flex-shrink-0">
        <div className="flex items-center gap-2">
          <Image 
            src="/logo_mark.png" 
            alt="AgenticInsights" 
            width={16} 
            height={16} 
            className="opacity-70"
          />
          <span className="text-xs text-muted-foreground font-mono">
            {getAppTitle()}
          </span>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant={isConnected ? 'active' : 'syncing'} className="text-xs">
            {isConnected ? (
              <>
                <Database className="w-3 h-3 mr-1" />
                Connected
              </>
            ) : (
              <>
                <Zap className="w-3 h-3 mr-1" />
                Connecting...
              </>
            )}
          </Badge>
          
          {/* Auth Status */}
          {authLoading ? (
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <div className="w-3 h-3 border-2 border-primary/30 border-t-primary rounded-full animate-spin"></div>
              Authenticating...
            </div>
          ) : isAuthenticated && user ? (
            <UserDropdown user={user} onLogout={handleLogout} />
          ) : (
            <button 
              onClick={handleLogin}
              className="text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              Login
            </button>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden flex">
        {/* Sidebar */}
        <aside className="w-80 bg-card border-r border-border flex flex-col">
          {/* Search */}
          <div className="p-4 border-b border-border">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search memories..."
                value={searchQuery}
                onChange={(e) => handleSearch(e.target.value)}
                className="w-full bg-input border border-border rounded-md pl-10 pr-4 py-2 text-sm font-mono
                         focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent
                         placeholder:text-muted-foreground terminal-glow"
              />
              {searchLoading && (
                <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                  <div className="animate-spin w-4 h-4 border-2 border-primary border-t-transparent rounded-full"></div>
                </div>
              )}
            </div>
            
            {/* Content Type Filter */}
            <div className="flex gap-1 mt-3">
              <Button
                variant={contentTypeFilter === 'all' ? 'terminal' : 'outline'}
                size="sm"
                onClick={() => setContentTypeFilter('all')}
                className="flex-1 text-xs font-mono"
              >
                All
              </Button>
              <Button
                variant={contentTypeFilter === 'research' ? 'terminal' : 'outline'}
                size="sm"
                onClick={() => setContentTypeFilter('research')}
                className="flex-1 text-xs font-mono"
              >
                <FileText className="w-3 h-3 mr-1" />
                Research
              </Button>
              <Button
                variant={contentTypeFilter === 'plan' ? 'terminal' : 'outline'}
                size="sm"
                onClick={() => setContentTypeFilter('plan')}
                className="flex-1 text-xs font-mono"
              >
                <Code className="w-3 h-3 mr-1" />
                Plans
              </Button>
            </div>
          </div>

          {/* System Metrics - Always Visible */}
          <div className="p-4 border-b border-border bg-muted/30">
            <div className="grid grid-cols-3 gap-2 text-center">
              <div className="flex flex-col">
                <span className="text-lg font-bold terminal-glow text-primary">
                  {fsThoughts?.total ?? systemStats?.totalThoughts ?? '0'}
                </span>
                <span className="text-xs text-muted-foreground">Thoughts</span>
              </div>
              <div className="flex flex-col">
                <span className="text-lg font-bold terminal-glow text-accent">
                  {systemStats?.activeTeams ?? '0'}
                </span>
                <span className="text-xs text-muted-foreground">Teams</span>
              </div>
              <div className="flex flex-col">
                <span className="text-lg font-bold terminal-glow text-secondary">
                  {systemStats?.syncStatus != null ? `${systemStats.syncStatus}%` : '0%'}
                </span>
                <span className="text-xs text-muted-foreground">Synced</span>
              </div>
            </div>
          </div>

          {/* Teams Status */}
          <div className="p-4 border-b border-border">
            <h3 className="text-sm font-semibold mb-3 terminal-glow flex items-center gap-2">
              <Users className="w-4 h-4" />
              Team Status
            </h3>
            <div className="space-y-2">
              {teamsLoading ? (
                <div className="text-center text-muted-foreground text-xs">Loading teams...</div>
              ) : teamStatuses.length > 0 ? (
                teamStatuses.map((team) => (
                  <div 
                    key={team.id} 
                    className={cn(
                      "memory-cell p-3 rounded-md cursor-pointer transition-colors",
                      selectedTeamId === team.id ? "border border-primary/30 bg-primary/10" : "hover:bg-muted/50"
                    )}
                    onClick={() => setSelectedTeamId(team.id)}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium">{team.name}</span>
                      <Badge 
                        variant={team.status === 'active' ? 'active' : team.status === 'syncing' ? 'syncing' : 'error'}
                        className="text-xs"
                      >
                        {team.status}
                      </Badge>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {String(team.memberCount)} members • {String(team.thoughtCount)} thoughts
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center text-muted-foreground text-xs">No teams found</div>
              )}
            </div>
          </div>

          {/* Quick Actions */}
          <div className="p-4">
            <h3 className="text-sm font-semibold mb-3 terminal-glow flex items-center gap-2">
              <Terminal className="w-4 h-4" />
              Quick Actions
            </h3>
            <div className="space-y-2">
              <Button 
                variant="terminal" 
                className="w-full justify-start text-xs" 
                onClick={handleNewThought}
                disabled={createThoughtMutation.isPending || !selectedTeamId || !isAuthenticated}
              >
                {createThoughtMutation.isPending ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <Plus className="w-4 h-4" />
                )}
                New Thought
              </Button>
              <Button 
                variant="terminal" 
                className="w-full justify-start text-xs" 
                onClick={handleSyncAll}
                disabled={syncTeamMutation.isPending || !selectedTeamId || !isAuthenticated}
              >
                {syncTeamMutation.isPending ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <Zap className="w-4 h-4" />
                )}
                Sync All
              </Button>
              <Button 
                variant="terminal" 
                className="w-full justify-start text-xs" 
                onClick={handleExportData}
              >
                <Download className="w-4 h-4" />
                Export Data
              </Button>
            </div>
          </div>
        </aside>

        {/* Main Dashboard */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Terminal Prompt & Context */}
          <div className="border-b border-border bg-muted/50">
            <div className="p-4 pb-2">
              <div className="terminal-text text-sm">
                <span className="text-primary">{user?.username || 'user'}@agenticinsights</span>
                <span className="text-muted-foreground">:</span>
                <span className="text-accent">~/memories{searchQuery ? '/search' : ''}</span>
                <span className="text-primary">$</span>
                <span className="ml-2">
                  {searchQuery ? `grep -r "${searchQuery}"` : 'ls -la recent_thoughts'}
                </span>
                <span className="ml-2 animate-pulse">█</span>
              </div>
            </div>
            
            {/* Live Status Strip */}
            <div className="px-4 pb-2 flex items-center justify-between text-xs text-muted-foreground">
              <div className="flex items-center gap-3">
                <span className="flex items-center gap-1">
                  <Database className="w-3 h-3" />
                  {fsThoughts?.source === 'local-filesystem' ? 'Local' : 'Database'}
                </span>
                {fsThoughts?.repositories_found && fsThoughts.repositories_found.length > 0 && (
                  <>
                    <span>•</span>
                    <span>Repos: {fsThoughts.repositories_found.join(', ')}</span>
                  </>
                )}
                {searchQuery && (
                  <>
                    <span>•</span>
                    <span className="text-accent">Searching...</span>
                  </>
                )}
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-xs">
                  Showing {recentThoughts?.length ?? 0} of {fsThoughts?.total ?? systemStats?.totalThoughts ?? 0}
                </Badge>
              </div>
            </div>
          </div>

          {/* Recent Thoughts */}
          <div className="flex-1 overflow-auto p-6">
            <div className="mb-6">
              <h2 className="text-xl font-semibold mb-4 terminal-glow flex items-center gap-2">
                <Brain className="w-5 h-5" />
                {searchQuery ? 'Search Results' : 
                 fsThoughts?.source === 'local-filesystem' ? 'Local Thoughts' : 
                 'Recent Thoughts'}
                {contentTypeFilter !== 'all' && (
                  <Badge variant={contentTypeFilter === 'research' ? 'active' : 'syncing'} className="text-xs">
                    {contentTypeFilter === 'research' ? 'Research' : 'Plans'}
                  </Badge>
                )}
              </h2>
              
              <div className="space-y-4">
                {(thoughtsLoading || filesystemLoading) ? (
                  <div className="text-center text-muted-foreground">Loading thoughts...</div>
                ) : recentThoughts.length > 0 ? (
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  recentThoughts.map((thought: any, index: number) => (
                    <div 
                      key={`${thought.id}-${index}`} 
                      className="memory-cell p-4 rounded-lg hover:scale-[1.02] transition-all cursor-pointer"
                      onClick={() => router.push(`/thought/${thought.id}/edit`)}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <h3 className="font-medium text-base">{thought.title}</h3>
                          {thought.contentType !== 'thought' && (
                            <Badge 
                              variant={thought.contentType === 'research' ? 'active' : 'syncing'} 
                              className="text-xs"
                            >
                              {thought.contentType === 'research' ? 'Research' : 'Plan'}
                            </Badge>
                          )}
                        </div>
                        <Badge variant="terminal" className="text-xs shrink-0">
                          {thought.team}
                        </Badge>
                      </div>
                      
                      <p className="text-sm text-muted-foreground mb-3 leading-relaxed">
                        {thought.excerpt}
                      </p>
                      
                      <div className="flex items-center justify-between text-xs">
                        <div className="flex items-center gap-2">
                          <span className="text-muted-foreground font-mono">{thought.path}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-muted-foreground">{thought.lastModified}</span>
                        </div>
                      </div>
                      
                      {thought.tags && thought.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                          {thought.tags.map((tag: any, index: number) => (
                            <Badge key={`${tag}-${index}`} variant="outline" className="text-xs">
                              {String(tag)}
                            </Badge>
                          ))}
                        </div>
                      )}
                      
                      {/* Add metadata panel for research/plans */}
                      {thought.contentType !== 'thought' && thought.metadata && (
                        <MetadataPanel 
                          metadata={thought.metadata} 
                          type={thought.contentType} 
                        />
                      )}
                    </div>
                  ))
                ) : (
                  <div className="text-center text-muted-foreground">
                    {searchQuery ? 'No matching thoughts found' : 'No thoughts yet. Create your first thought!'}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Status Bar */}
      <footer className="h-7 bg-muted border-t border-border flex items-center justify-between px-4 text-xs flex-shrink-0">
        <div className="flex items-center gap-4">
          <span className={cn("w-2 h-2 rounded-full", isConnected ? "bg-primary" : "bg-destructive")}></span>
          <span>Backend API: {isConnected ? 'Connected' : 'Disconnected'}</span>
          <span>•</span>
          <span>WebSocket: {wsConnected ? 'Connected' : 'Disconnected'}</span>
          {activeUsers.length > 0 && (
            <>
              <span>•</span>
              <span>{activeUsers.length} active users</span>
            </>
          )}
        </div>
        <div className="flex items-center gap-4">
          <span>Memory usage: {systemStats?.memoryUsage ?? 'N/A'}</span>
          <span>•</span>
          <span>Thoughts indexed: {systemStats?.totalThoughts ?? 'N/A'}</span>
        </div>
      </footer>
    </>
  );
}
