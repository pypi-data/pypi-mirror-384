---
sidebar_position: 1
---

# Welcome to Codebase Context

**Tools and Techniques for AI Development Workflows**

Codebase Context is a collection of tools and approaches for managing AI context windows, memory, and development workflows. mem8 is the primary CLI tool that helps bridge the gaps between AI capabilities and developer needs.

:::info Historical Note
The original [codebase-context-spec](https://github.com/Agentic-Insights/codebase-context-spec) project is **archived and no longer maintained or supported**. mem8 represents the current, actively developed implementation of these concepts.
:::

## What is mem8?

mem8 addresses common challenges in AI-assisted development:

- 🧠 **Context Window Management** - Persistent memory across long development sessions
- 📝 **Structured Thoughts** - Organize research, plans, and decisions in searchable markdown
- 🔧 **Toolbelt Integration** - Install and manage development tools seamlessly
- 🚢 **Port Management** - Intelligent detection and resolution of port conflicts
- 🤖 **Claude Code Enhancement** - Custom agents, commands, and workflows via plugins
- 🎨 **External Plugins** - Share workflows and standards across teams
- 🔍 **Universal Search** - Find information across all your documentation

## Quick Example

```bash
# Install mem8 CLI
uv tool install mem8

# Check workspace status
mem8 status

# Search your memory
mem8 search "authentication"

# For Claude Code integration, install the plugin:
# See https://github.com/killerapp/mem8-plugin for installation
```

## Next Steps

<div class="row">
  <div class="col col--6">
    <h3>📥 Installation</h3>
    <p>Get mem8 installed and running on your system.</p>
    <a href="./installation">Install mem8 →</a>
  </div>
  <div class="col col--6">
    <h3>💡 Concepts</h3>
    <p>Understand mem8's core concepts and architecture.</p>
    <a href="./concepts">Learn concepts →</a>
  </div>
</div>

<div class="row">
  <div class="col col--6">
    <h3>📖 User Guide</h3>
    <p>Learn how to use mem8 in your daily workflow.</p>
    <a href="./user-guide/getting-started">Read the guide →</a>
  </div>
  <div class="col col--6">
    <h3>🔌 External Plugins</h3>
    <p>Share and customize Claude Code workflows.</p>
    <a href="./external-templates">Explore plugins →</a>
  </div>
</div>

## Features at a Glance

### 🧠 Context Window Management
Persistent memory system keeps AI context relevant across long development sessions. Structured memory captures research, plans, and decisions.

### 🔧 Integrated Toolbelt
Install and manage development tools with `mem8 toolbelt`. Handles dependencies, version conflicts, and environment setup automatically.

### 🚢 Intelligent Port Management
Automatic port conflict detection and resolution. Never waste time debugging "address already in use" errors again.

### 🎯 Claude Code Integration
Deep integration with Claude Code via the mem8 plugin system. Provides 8 workflow commands and 6 specialized agents.

### 🔌 External Plugins
Create custom Claude Code plugins for your team. Use the mem8-plugin template to standardize workflows across your organization.

### 🔍 Full-Text Search
Find information quickly across all your memory and documentation with powerful search capabilities.

## Who is this for?

- **AI-Assisted Developers** - Manage context windows effectively across long sessions
- **Solo Developers** - Keep memory organized and tools readily available
- **Development Teams** - Share standardized workflows and templates
- **Claude Code Users** - Enhance your development experience with better memory and tooling
- **Organizations** - Create custom templates and maintain consistent practices

## Get Support

- 📖 [Documentation](https://github.com/killerapp/mem8)
- 🐛 [Report Issues](https://github.com/killerapp/mem8/issues)
- 💬 [Discussions](https://github.com/killerapp/mem8/discussions)
- 🔧 [Template Repository](https://github.com/killerapp/mem8-plugin)
