---
sidebar_position: 7
---

# Utility Workflows

Helpful utility patterns and workflows for common tasks.

## Quick Reference

### Status Checks

```bash
# Quick health check
mem8 status

# Detailed information
mem8 status --detailed

# Run diagnostics
mem8 doctor
```

### Search Operations

```bash
# Basic search
mem8 search "query"

# Limited results
mem8 search "query" --limit 5

# Specific directory
mem8 search "query" --path memory/shared/research

# Category filter
mem8 search "query" --category plans
```

## File Management

### Archive Old Thoughts

Keep your memory directory organized:

```bash
# Create archive structure
mkdir -p memory/archive/$(date +%Y)

# Move old files
mv memory/shared/research/old-* memory/archive/$(date +%Y)/

# Commit changes
cd thoughts
git add .
git commit -m "chore: archive old research"
git push
```

### Clean Up Duplicates

Find and remove duplicate thoughts:

```bash
# Find duplicates by name
find thoughts -type f -name "*.md" | sort | uniq -d

# Review before deleting
ls -lh memory/shared/research/*duplicate*

# Remove after review
rm memory/shared/research/duplicate-file.md
```

## Template Management

### Update Templates

Keep your templates current:

```bash
# Check current template source
mem8 templates show-default

# Update to latest
mem8 init --template-source killerapp/mem8-plugin --force

# Verify update
mem8 status
```

### Custom Template Testing

Test custom templates before sharing:

```bash
# Create test directory
mkdir -p /tmp/test-project
cd /tmp/test-project

# Test your template
mem8 init --template-source /path/to/your/template

# Verify structure
mem8 status --detailed
```

## Git Operations

### Batch Commit Thoughts

Commit multiple thought files:

```bash
cd thoughts

# Review changes
git status

# Add all new thoughts
git add shared/

# Commit with date
git commit -m "docs: update thoughts $(date +%Y-%m-%d)"

# Push
git push
```

### Sync Multiple Repositories

If you have multiple projects:

```bash
#!/bin/bash
# sync-all-thoughts.sh

for project in ~/projects/*/; do
  echo "Syncing $project"
  cd "$project"
  if [ -d "thoughts" ]; then
    mem8 sync
  fi
done
```

## Reporting

### Generate Statistics

Get insights about your thoughts:

```bash
# Count thoughts by type
find memory/shared -type f -name "*.md" | \
  awk -F/ '{print $(NF-1)}' | sort | uniq -c

# Total thoughts
find memory/shared -type f -name "*.md" | wc -l

# Recent activity
find memory/shared -type f -name "*.md" -mtime -7
```

### Export Search Results

Save search results for later:

```bash
# Export to file
mem8 search "authentication" --limit 20 > auth-results.txt

# Save and display simultaneously
mem8 search "OAuth" | tee oauth-findings.txt
```

## Backup & Restore

### Backup Workspace

Create a complete backup:

```bash
# Create backup directory
mkdir -p ~/.mem8/backups/$(date +%Y%m%d)

# Backup thoughts
tar czf ~/.mem8/backups/$(date +%Y%m%d)/thoughts.tar.gz memory/

# Backup config
tar czf ~/.mem8/backups/$(date +%Y%m%d)/claude.tar.gz .claude/

# Backup settings
cp -r ~/.mem8/config.yaml ~/.mem8/backups/$(date +%Y%m%d)/
```

### Restore from Backup

Restore a previous state:

```bash
# List backups
ls -lh ~/.mem8/backups/

# Restore thoughts
tar xzf ~/.mem8/backups/20240101/thoughts.tar.gz

# Restore config
tar xzf ~/.mem8/backups/20240101/claude.tar.gz
```

## Team Utilities

### Share Specific Thoughts

Share select thoughts with teammates:

```bash
# Create shareable bundle
tar czf research-bundle.tar.gz \
  memory/shared/research/auth-*.md \
  memory/shared/plans/oauth-*.md

# Send to team
# They extract with:
tar xzf research-bundle.tar.gz
```

### Sync Review

Preview what will be synced:

```bash
# Dry run
mem8 sync --dry-run

# Show differences
cd thoughts
git status
git diff

# Sync if looks good
mem8 sync
```

## Automation

### Scheduled Sync

Auto-sync with cron:

```bash
# Edit crontab
crontab -e

# Add sync every hour
0 * * * * cd ~/projects/myproject && mem8 sync --quiet

# Add morning pull
0 9 * * * cd ~/projects/myproject && mem8 sync --direction pull
```

### Git Hooks

Auto-document commits:

```bash
# .git/hooks/post-commit
#!/bin/bash
mem8 search "$(git log -1 --pretty=%B)" --limit 1
```

## Maintenance

### Database Optimization

Keep database performant:

```bash
# Check database size
du -sh ~/.mem8/mem8.db

# Optimize (backup first!)
sqlite3 ~/.mem8/mem8.db "VACUUM;"
```

### Clear Cache

Reset caches if needed:

```bash
# Clear search cache
rm -rf ~/.mem8/cache/

# Rebuild index
mem8 status
```

## Quality Checks

### Validate Markdown

Check thought files:

```bash
# Find malformed markdown
find thoughts -name "*.md" -exec grep -l "^---$" {} \; | \
  xargs -I {} sh -c 'echo "Checking {}" && head -n 20 {}'

# Check for broken links
grep -r "\[.*\](.*/.*)" memory/
```

### Check Git Status

Ensure nothing uncommitted:

```bash
# Check all repos
cd thoughts && git status
git log --oneline -5

# Verify remote sync
git fetch --dry-run
```

## Troubleshooting Utilities

### Debug Information

Collect debug info:

```bash
# System info
mem8 --version
python --version
git --version

# Environment
env | grep MEM8

# Workspace info
mem8 status --detailed
mem8 doctor
```

### Reset Workspace

Clean reset when needed:

```bash
# Backup first
cp -r .claude .claude.backup
cp -r thoughts thoughts.backup

# Remove and reinitialize
rm -rf .claude thoughts
mem8 init --template full

# Restore thoughts history
mv thoughts.backup/.git memory/
```

## Next Steps

- **[Best Practices](./best-practices)** - Tips for better workflows
- **[Advanced Workflows](./advanced)** - Complex patterns
- **[Troubleshooting](../user-guide/troubleshooting)** - Fix issues
