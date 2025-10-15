---
sidebar_position: 4
---

# Troubleshooting

Common issues and solutions for mem8.

## Diagnostics

Always start with diagnostics:

```bash
# Run all checks
mem8 doctor

# Check workspace status
mem8 status --detailed
```

## Common Issues

### Installation Problems

#### Command Not Found

**Problem:** `mem8: command not found`

**Solutions:**

```bash
# Verify installation
uv tool list

# Reinstall
uv tool install mem8

# Check PATH
echo $PATH | grep .local/bin
```

#### Version Mismatch

**Problem:** Wrong version installed

**Solutions:**

```bash
# Update to latest
uv tool install --upgrade mem8

# Verify version
mem8 --version
```

### Initialization Issues

#### Template Not Found

**Problem:** `Template source not found`

**Solutions:**

```bash
# Check template source
mem8 templates list

# Use official templates
mem8 init --template-source killerapp/mem8-plugin

# Use local templates
mem8 init --template-source /path/to/templates
```

#### Permission Denied

**Problem:** Cannot write to directory

**Solutions:**

```bash
# Check permissions
ls -la .

# Fix ownership
sudo chown -R $USER:$USER .

# Use --force if needed
mem8 init --force
```

### Search Issues

#### No Results Found

**Problem:** Search returns no results

**Solutions:**

```bash
# Check if thoughts exist
ls memory/shared/

# Check search path
mem8 search "query" --path memory/

# Try broader search
mem8 search "query"
```

#### Slow Search

**Problem:** Search is slow

**Solutions:**

```bash
# Limit results
mem8 search "query" --limit 5

# Search specific path
mem8 search "query" --path memory/shared/research

# Check for large files
find thoughts -type f -size +1M
```

### Sync Issues

#### Git Conflicts

**Problem:** Merge conflicts during sync

**Solutions:**

```bash
# Check git status
cd thoughts
git status

# Resolve conflicts manually
git mergetool

# Continue sync
mem8 sync
```

#### Authentication Failed

**Problem:** Cannot push to remote

**Solutions:**

```bash
# Check git remote
cd thoughts
git remote -v

# Update credentials
git config credential.helper store

# Use SSH instead of HTTPS
git remote set-url origin git@github.com:org/repo.git
```

#### Sync Stuck

**Problem:** Sync appears frozen

**Solutions:**

```bash
# Check network
ping github.com

# Try dry-run first
mem8 sync --dry-run

# Force sync
mem8 sync --force
```

### Claude Code Integration

#### Commands Not Found

**Problem:** Slash commands don't work

**Solutions:**

```bash
# Check .claude directory
ls .claude/commands/

# Reinitialize
mem8 init --template claude-config --force

# Restart Claude Code
```

#### Agents Not Working

**Problem:** Custom agents not loading

**Solutions:**

```bash
# Check agent files
ls .claude/agents/

# Verify format
cat .claude/agents/your-agent.md

# Check Claude Code logs
```

### Database Issues

#### Database Locked

**Problem:** `Database is locked`

**Solutions:**

```bash
# Close other mem8 processes
pkill mem8

# Remove lock file
rm ~/.mem8/db.lock

# Restart
mem8 status
```

#### Corrupted Database

**Problem:** Database errors

**Solutions:**

```bash
# Backup first
cp -r ~/.mem8 ~/.mem8.backup

# Reset database
rm ~/.mem8/mem8.db

# Rebuild
mem8 status
```

## Performance Issues

### Slow Commands

**Problem:** Commands take too long

**Solutions:**

```bash
# Enable verbose mode
mem8 --verbose status

# Check for large files
du -sh memory/

# Optimize git repository
cd thoughts
git gc --aggressive
```

### High Memory Usage

**Problem:** mem8 uses too much memory

**Solutions:**

```bash
# Limit search results
mem8 search "query" --limit 5

# Check file sizes
find thoughts -type f -size +1M

# Archive old thoughts
mkdir memory/archive
mv memory/shared/old-* memory/archive/
```

## Configuration Issues

### Wrong Configuration

**Problem:** Settings not applied

**Solutions:**

```bash
# Check config location
cat ~/.mem8/config.yaml
cat .mem8/config.yaml

# Reset config
mv ~/.mem8/config.yaml ~/.mem8/config.yaml.backup

# Reinitialize
mem8 init
```

### Template Problems

**Problem:** Template variables not expanding

**Solutions:**

```bash
# Set environment variables
export MEM8_USERNAME=yourname
export MEM8_EMAIL=your@email.com

# Verify
echo $MEM8_USERNAME

# Reinitialize
mem8 init --force
```

## Getting Help

### Check Logs

```bash
# Enable debug logging
export MEM8_DEBUG=1
mem8 status

# Check system logs
tail -f ~/.mem8/logs/mem8.log
```

### Report Issues

If you can't resolve the issue:

1. **Run diagnostics:**
   ```bash
   mem8 doctor > diagnostics.txt
   mem8 status --detailed >> diagnostics.txt
   ```

2. **Collect logs:**
   ```bash
   cat ~/.mem8/logs/mem8.log > logs.txt
   ```

3. **Report:**
   - GitHub: https://github.com/killerapp/mem8/issues
   - Include diagnostics and logs
   - Describe steps to reproduce

## Advanced Troubleshooting

### Debug Mode

Enable detailed debugging:

```bash
export MEM8_DEBUG=1
export MEM8_LOG_LEVEL=DEBUG
mem8 status
```

### Manual Database Inspection

```bash
# SQLite CLI
sqlite3 ~/.mem8/mem8.db

# List tables
.tables

# Query
SELECT * FROM thoughts LIMIT 10;
```

### Reset Everything

Last resort - complete reset:

```bash
# Backup first
cp -r .claude .claude.backup
cp -r thoughts thoughts.backup
cp -r ~/.mem8 ~/.mem8.backup

# Remove all mem8 files
rm -rf .claude thoughts ~/.mem8

# Reinstall and reinitialize
uv tool install --upgrade mem8
mem8 init --template full
```

## Prevention

### Best Practices

1. **Regular backups:**
   ```bash
   # Thoughts are git repos
   cd thoughts && git push
   ```

2. **Keep updated:**
   ```bash
   uv tool install --upgrade mem8
   ```

3. **Run diagnostics regularly:**
   ```bash
   mem8 doctor
   ```

4. **Monitor disk space:**
   ```bash
   df -h
   du -sh memory/
   ```

## Next Steps

- **[Getting Started](./getting-started)** - Start fresh
- **[CLI Commands](./cli-commands)** - Command reference
- **[Workflows](./workflows)** - Best practices
- **[GitHub Issues](https://github.com/killerapp/mem8/issues)** - Report bugs
