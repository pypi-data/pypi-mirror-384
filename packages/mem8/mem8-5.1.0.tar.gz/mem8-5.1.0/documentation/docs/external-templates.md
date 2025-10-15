# External Plugin Sources

**Share Claude Code workflows across your entire team.** mem8 uses the Claude Code plugin system to enable teams to collaborate on commands, agents, and development practices.

## Why Use External Plugins?

### Team Collaboration
- **Standardize workflows** - Everyone uses the same Claude Code commands
- **Share best practices** - Distribute proven agent configurations
- **Version control** - Track changes to commands and workflows over time
- **Organization-wide consistency** - Same tools, same patterns, same quality

### Official Plugin Repository
The [`killerapp/mem8-plugin`](https://github.com/killerapp/mem8-plugin) repository provides:
- 8 workflow commands (`/m8-*`)
- 6 specialized agents (codebase-analyzer, memory-analyzer, etc.)
- Battle-tested configurations
- Community-contributed workflows
- Regular updates and improvements

### Custom Plugins
- Fork and customize the official plugin
- Create organization-specific commands
- Develop and test plugins locally
- Version and distribute independently

## Quick Start

### Installing the Official Plugin

The mem8 plugin provides 8 workflow commands and 6 specialized agents. See the [plugin repository](https://github.com/killerapp/mem8-plugin) for:
- Complete command list
- Installation instructions
- Usage examples
- Agent descriptions

**Installation**: Follow Claude Code's plugin installation process using the mem8 plugin repository.

## Plugin Management

Use Claude Code's built-in plugin management features to:
- View installed plugins
- Update plugins to latest versions
- Uninstall plugins

Refer to [Claude Code documentation](https://docs.claude.com/) for specific plugin management commands.

## Plugin Structure

A Claude Code plugin for mem8 includes:

```
.claude-plugin/
├── plugin.json          # Plugin metadata
└── marketplace.json     # Marketplace listing info

.claude/
├── commands/            # Slash commands (/m8-*)
│   ├── m8-plan.md
│   ├── m8-implement.md
│   └── ...
├── agents/              # Specialized agents
│   ├── codebase-analyzer.md
│   ├── memory-analyzer.md
│   └── ...
└── hooks/               # Lifecycle hooks
    └── after-plugin-install.sh
```

### Plugin Manifest (plugin.json)

```json
{
  "name": "mem8",
  "version": "1.0.0",
  "description": "Context management and workflow automation",
  "author": "killerapp",
  "repository": "https://github.com/killerapp/mem8-plugin",
  "commands": [
    "/m8-plan",
    "/m8-implement",
    "/m8-research",
    "/m8-validate",
    "/m8-commit",
    "/m8-describe-pr",
    "/m8-debug",
    "/m8-local-review"
  ],
  "agents": [
    "codebase-analyzer",
    "codebase-locator",
    "codebase-pattern-finder",
    "memory-analyzer",
    "memory-locator",
    "web-search-researcher"
  ],
  "hooks": {
    "postInstall": ".claude-plugin/hooks/after-plugin-install.sh"
  }
}
```

## Creating Custom Slash Commands

Slash commands are markdown files in `.claude/commands/`. Each command defines a prompt that Claude Code executes.

### Command File Format

`.claude/commands/my-command.md`:

```markdown
# My Custom Command

You are helping the user with a specific task. Follow these steps:

1. Analyze the current codebase
2. Perform the requested action
3. Report results back to the user

## Guidelines

- Use the Read tool to examine files
- Use the Edit tool to make changes
- Be thorough and methodical

## Success Criteria

- [ ] All files are properly updated
- [ ] Tests pass
- [ ] User is informed of changes
```

### Calling Commands

After installing your plugin, users can call:

```bash
/my-command
/my-command with additional context
```

## Creating Custom Agents

Agents are specialized markdown files in `.claude/agents/` that define focused behaviors.

### Agent File Format

`.claude/agents/my-analyzer.md`:

```markdown
# My Analyzer Agent

You are a specialized agent for analyzing specific patterns in the codebase.

## Your Role

Analyze code to identify:
- Pattern A
- Pattern B
- Potential issues

## Tools Available

You have access to:
- Read tool
- Grep tool
- Glob tool

## Output Format

Provide your analysis in this format:

1. **Summary**: Brief overview
2. **Findings**: Detailed results
3. **Recommendations**: Suggested actions
```

## Creating Custom Plugins

### 1. Use the Template Repository

The [`killerapp/mem8-plugin`](https://github.com/killerapp/mem8-plugin) repository is a GitHub template. Create your own plugin by using it as a template:

```bash
# Create from template using GitHub CLI
gh repo create my-org/my-workflows --template killerapp/mem8-plugin --private --clone

cd my-workflows
```

Or use the GitHub web interface:
1. Go to https://github.com/killerapp/mem8-plugin
2. Click "Use this template" button
3. Create your new repository

### 2. Customize Plugin Content

Modify the plugin to fit your needs:

**Commands** (`.claude/commands/`):
- Edit existing commands or add new ones
- Each `.md` file becomes a `/command-name` in Claude Code

**Agents** (`.claude/agents/`):
- Customize agent behaviors
- Add organization-specific analysis patterns

**Hooks** (`.claude-plugin/hooks/`):
- Customize post-install behavior
- Add setup scripts for your environment

### 3. Update Plugin Manifest

Edit `.claude-plugin/plugin.json`:

```json
{
  "name": "acme-workflows",
  "version": "1.0.0",
  "description": "Acme Corp development workflows",
  "author": "acme-corp",
  "repository": "https://github.com/acme-corp/acme-workflows",
  "commands": [
    "/acme-deploy",
    "/acme-review",
    "/acme-test"
  ],
  "agents": [
    "acme-compliance-checker",
    "acme-security-analyzer"
  ]
}
```

### 4. Test Locally

Test your custom plugin locally:

1. Use Claude Code's local plugin loading features
2. Verify all commands work as expected
3. Test agents with real codebase scenarios
4. Confirm hooks execute properly

Refer to Claude Code documentation for local plugin testing.

### 5. Publish and Share

```bash
# Push to GitHub
git add .
git commit -m "feat: customized plugin for Acme Corp"
git push
```

Team members can then install your plugin using Claude Code's plugin system. Share your repository URL with the team.

## Best Practices

### 1. Version Your Plugins

Use Git tags for stable releases:

```bash
git tag -a v1.0.0 -m "Release 1.0.0"
git push --tags
```

Users can then install specific versions if supported by Claude Code.

### 2. Document Your Commands

Include a README explaining:
- Available commands and what they do
- Agent purposes and capabilities
- Usage examples
- Configuration options

### 3. Test Thoroughly

Before publishing:
- Test all commands in Claude Code
- Verify agents work as expected
- Test hooks execute properly
- Document any prerequisites

### 4. Provide Examples

Include documentation showing:
- How to use each command
- What each agent analyzes
- Real-world use cases
- Common workflows

## Security Considerations

### Plugin Execution

- Plugins can define commands that execute prompts in Claude Code
- Hooks can run shell scripts during installation
- **Only install plugins from trusted sources**

### Validation

Before installing a plugin:

1. Review the plugin repository on GitHub
2. Check the commands in `.claude/commands/`
3. Inspect any hooks in `.claude-plugin/hooks/`
4. Read the plugin's README and documentation

### Private Repositories

For private plugin repositories:

```bash
# Ensure you're authenticated with gh CLI
gh auth login

# Claude Code should be able to access private repos if authenticated
```

## Troubleshooting

### Plugin Not Found

**Issue**: Can't find the plugin in marketplace

**Solution**:
1. Verify you've added the marketplace source
2. Check the repository URL is correct
3. Ensure the repository is public or you're authenticated

### Installation Failed

**Issue**: Plugin installation fails

**Common Causes**:
- Repository doesn't exist
- No access to private repository
- Invalid plugin structure (missing plugin.json)

**Solution**:
1. Check repository exists: `gh repo view org/repo`
2. Verify plugin.json exists in `.claude-plugin/`
3. Check Claude Code logs for detailed error messages

### Commands Not Working

**Issue**: Plugin commands don't appear or don't work

**Solution**:
1. Verify installation: Check Claude Code plugin list
2. Restart Claude Code if needed
3. Check command files exist in `.claude/commands/`
4. Verify command markdown is properly formatted

## Examples

### Organization Plugin Repository

**Repository**: `acme-corp/acme-workflows`

**Structure**:
```
.claude-plugin/
  plugin.json              # Defines plugin metadata
  marketplace.json         # Marketplace listing
  hooks/
    after-plugin-install.sh  # Setup Acme tools

.claude/
  commands/
    acme-deploy.md         # Deploy to Acme infrastructure
    acme-review.md         # Code review checklist
    acme-compliance.md     # Run compliance checks
  agents/
    acme-security-analyzer.md  # Security analysis
    acme-docs-generator.md     # Generate internal docs
```

### Personal Plugin

**Repository**: `yourname/my-workflows`

**Structure**:
```
.claude/
  commands/
    quick-test.md          # Run tests with your preferred setup
    deploy-personal.md     # Deploy to your environments
  agents/
    my-analyzer.md         # Custom analysis patterns
```

## Related

- [Plugin Repository](https://github.com/killerapp/mem8-plugin)
- [Claude Code Documentation](https://docs.claude.com/)
- [Full mem8 Documentation](https://codebasecontext.org)
