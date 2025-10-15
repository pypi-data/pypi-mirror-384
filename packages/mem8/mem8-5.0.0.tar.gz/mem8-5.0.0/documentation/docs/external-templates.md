# External Template Sources

**Share Claude Code workflows across your entire team.** mem8 supports loading templates from external sources, enabling teams to collaborate on prompts, sub-agents, and best practices.

## Why Use External Templates?

### Team Collaboration
- **Standardize workflows** - Everyone uses the same Claude Code commands
- **Share best practices** - Distribute proven sub-agent configurations
- **Version control** - Track changes to prompts and workflows over time
- **Organization-wide consistency** - Same tools, same patterns, same quality

### Official Templates Repository
The [`killerapp/mem8-plugin`](https://github.com/killerapp/mem8-plugin) repository provides:
- Curated Claude Code integration templates
- Battle-tested sub-agent configurations
- Community-contributed workflows
- Regular updates and improvements

### Custom Templates
- Fork and customize the official templates
- Create organization-specific commands
- Develop and test templates locally
- Version and distribute independently

## Quick Start

### Using External Templates

```bash
# Use templates from GitHub (shorthand)
mem8 init --template-source killerapp/mem8-plugin

# Use a specific version
mem8 init --template-source killerapp/mem8-plugin@v2.10.0

# Use templates from a subdirectory
mem8 init --template-source killerapp/mem8-plugin#subdir=templates

# Use local templates (development)
mem8 init --template-source ./my-templates

# Use full Git URL
mem8 init --template-source https://github.com/org/templates.git
```

### Set Default Template Source

```bash
# Set as default for all future init commands
mem8 templates set-default killerapp/mem8-plugin

# Reset to builtin templates
mem8 templates set-default builtin
```

## Template Management Commands

### List Templates

```bash
# List from builtin (or configured default)
mem8 templates list

# List from specific source
mem8 templates list --source killerapp/mem8-plugin

# List with verbose details
mem8 templates list --source killerapp/mem8-plugin -v
```

### Validate Template Source

```bash
# Validate a template source
mem8 templates validate --source killerapp/mem8-plugin

# Validate the configured default
mem8 templates validate
```

The validation checks:
- ✅ Source resolves correctly
- ✅ Manifest file exists and parses
- ✅ Template paths exist
- ✅ cookiecutter.json files present
- ⚠️  Warns about potential issues

## Template Source Formats

### GitHub Shorthand

The most concise format for GitHub repositories:

```bash
# Basic: org/repo
killerapp/mem8-plugin

# With git ref (branch, tag, or commit)
killerapp/mem8-plugin@v2.10.0
killerapp/mem8-plugin@main
killerapp/mem8-plugin@abc123

# With subdirectory
killerapp/mem8-plugin#subdir=templates

# Combined
killerapp/mem8-plugin@v2.10.0#subdir=templates
```

### Full Git URLs

Standard Git URLs are also supported:

```bash
# HTTPS
https://github.com/org/repo.git
https://github.com/org/repo.git@v1.0.0

# With subdirectory
https://github.com/org/repo.git#subdir=templates
```

### Local Paths

For development and testing:

```bash
# Absolute path
/path/to/templates

# Relative path
./templates
../shared-templates
```

## Template Manifest Format

Create a `mem8-templates.yaml` manifest in your template repository:

```yaml
version: 1

# Relative path to templates directory
source: "."

# Metadata (optional)
metadata:
  name: "My Custom Templates"
  version: "1.0.0"
  description: "Custom templates for my organization"
  author: "Your Name"
  license: "MIT"

# Template definitions
templates:
  # Template name (used with mem8 init --template)
  custom-template:
    path: "my-template-dir"
    type: "cookiecutter"
    description: "Description of this template"
    variables:
      # Default variables for cookiecutter
      key: "default value"
      another_key: "{{ env.USERNAME | default('user') }}"
```

### Template Types

- **`cookiecutter`**: Standard cookiecutter template
- **`composite`**: Meta-template that uses multiple templates

### Variables

Variables are passed to cookiecutter's `extra_context`:

```yaml
templates:
  example:
    variables:
      username: "{{ env.USERNAME | default('user') }}"
      shared_enabled: false
      workflow_provider: "github"
```

## Creating Custom Templates

### 1. Fork the Official Repository

```bash
# Fork https://github.com/killerapp/mem8-plugin
gh repo fork killerapp/mem8-plugin --clone

cd mem8-templates
```

### 2. Modify Templates

Edit templates in:
- `claude-dot-md-template/` - Claude Code integration
- `shared-thoughts-template/` - Thoughts repository

### 3. Update Manifest

Edit `mem8-templates.yaml` to reflect your changes:

```yaml
version: 1
source: "."

metadata:
  name: "Acme Corp Templates"
  version: "1.0.0"
  author: "Acme Corp"

templates:
  acme-standard:
    path: "acme-standard-template"
    type: "cookiecutter"
    description: "Acme standard workspace setup"
```

### 4. Test Locally

```bash
# Test your changes
mem8 templates validate --source ./

# Try initialization
cd /path/to/test-project
mem8 init --template-source /path/to/your/mem8-templates
```

### 5. Publish and Use

```bash
# Push to GitHub
git add .
git commit -m "feat: customized templates for Acme Corp"
git push

# Use in projects
mem8 templates set-default acme-corp/mem8-templates
```

## Fallback Behavior

When a manifest is missing, mem8 falls back to directory discovery:
- Scans for directories containing `cookiecutter.json`
- Maps directory names to template names
- Uses template names with `-template` suffix removed

Example:
```
templates/
├── claude-dot-md-template/   → template name: "claude-dot-md-template"
├── custom-template/           → template name: "custom-template"
└── another-one/               → template name: "another-one"
```

## Best Practices

### 1. Version Your Templates

Use Git tags for stable releases:

```bash
git tag -a v1.0.0 -m "Release 1.0.0"
git push --tags
```

Users can then reference specific versions:
```bash
mem8 init --template-source your-org/templates@v1.0.0
```

### 2. Document Template Variables

Include a README in each template explaining:
- Available variables
- Default values
- Configuration options

### 3. Test Before Publishing

Always validate before pushing:

```bash
mem8 templates validate --source ./
```

### 4. Provide Examples

Include example projects or documentation showing:
- How to use each template
- What gets generated
- Customization options

## Security Considerations

### Template Execution

- Templates are executed using cookiecutter
- Post-generation hooks can run Python code
- **Only use templates from trusted sources**

### Validation

Before using an external template source:

```bash
# Validate the source
mem8 templates validate --source org/repo

# Review the manifest
mem8 templates list --source org/repo -v

# Test in a safe location first
cd /tmp/test
mem8 init --template-source org/repo
```

### Private Repositories

For private repositories:

```bash
# Ensure you're authenticated with gh CLI
gh auth login

# Then use as normal
mem8 init --template-source your-org/private-templates
```

## Troubleshooting

### Template Not Found

```
❌ [red]Template not available: template-name[/red]
```

**Solution**: Check template name with `mem8 templates list --source <source>`

### Source Resolution Failed

```
❌ [red]Failed to resolve source: ...[/red]
```

**Causes**:
- Network issues (for remote sources)
- Invalid path (for local sources)
- Private repository without authentication

**Solution**: Validate the source first:
```bash
mem8 templates validate --source <source>
```

### Git Clone Failed

```
❌ Failed to clone repository: ...
```

**Causes**:
- Repository doesn't exist
- No access (private repo)
- Invalid git ref

**Solution**: Check repository exists and you have access:
```bash
gh repo view org/repo
```

## Examples

### Organization Template Repository

```yaml
# .github.com/acme-corp/mem8-templates/mem8-templates.yaml
version: 1
source: "templates"

metadata:
  name: "Acme Corp Templates"
  organization: "Acme Corp"
  version: "2.0.0"

templates:
  acme-standard:
    path: "acme-standard"
    type: "cookiecutter"
    description: "Standard Acme workspace with compliance tools"
    variables:
      compliance_level: "standard"
      team: "engineering"

  acme-fintech:
    path: "acme-fintech"
    type: "cookiecutter"
    description: "Fintech workspace with additional security"
    variables:
      compliance_level: "high"
      audit_enabled: true
```

Usage:
```bash
# Set as org default
mem8 templates set-default acme-corp/mem8-templates

# All engineers now use this
mem8 init  # Uses acme-standard by default
```

### Personal Template Collection

```yaml
# github.com/yourname/my-templates/mem8-templates.yaml
version: 1
source: "."

metadata:
  name: "Personal Dev Templates"
  author: "Your Name"

templates:
  minimal:
    path: "minimal-template"
    type: "cookiecutter"
    description: "Minimal setup for quick projects"

  research:
    path: "research-template"
    type: "cookiecutter"
    description: "Research project with experiment tracking"
```

Usage:
```bash
mem8 init --template-source yourname/my-templates --template minimal
```

## Related

- [Templates Repository](https://github.com/killerapp/mem8-plugin)
- [Cookiecutter Documentation](https://cookiecutter.readthedocs.io/)
- [Template Development Guide](#) <!-- TODO: Add link -->
