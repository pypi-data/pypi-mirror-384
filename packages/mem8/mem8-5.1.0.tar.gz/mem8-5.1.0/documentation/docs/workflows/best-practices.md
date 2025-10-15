---
sidebar_position: 7
---

## Best Practices

### Start Every Feature with Research

```bash
# Don't just jump in
❌ /m8-plan "add feature"

# Understand first
✅ /m8-research "how do similar features work?"
✅ /m8-browse-memories "past features like this"
✅ /m8-plan "add feature based on patterns"
```

### Keep Plans Updated

```bash
# As you implement
- [x] Phase 1: Complete
- [ ] Phase 2: In progress  # Update checkboxes!
- [ ] Phase 3: Not started
```

### Document Decisions

```bash
# When you make a choice
# Add to plan or research document:
## Decision: Chose X over Y
Rationale: Performance tests showed...
Trade-offs: More complexity but 10x faster
```

### Use Doctor Regularly

```bash
# Before starting work
mem8 doctor

# Catches issues early
✅ git: installed
✅ gh: authenticated
✅ memory/: synced
⚠️  .claude/agents/: 2 deprecated agents found
```

## Next Steps

- **[CLI Commands](../user-guide/cli-commands)** - Full command documentation
- **[User Guide](../user-guide/getting-started)** - Practical examples
- **[External Templates](../external-templates)** - Customize workflows
- **[GitHub](https://github.com/killerapp/mem8)** - Explore source

## Real-World Example

```mermaid
timeline
    title Adding OAuth2 Support (Real Timeline)
    section Day 1
      09:00 : /m8-research "current auth system"
      09:45 : /m8-plan "add OAuth2"
      10:00 : User review
      10:15 : /m8-implement (Phase 1)
    section Day 2
      09:00 : Continue Phase 2
      11:00 : Phase 2 tests passing
      11:30 : /m8-implement (Phase 3)
      14:00 : All phases complete
      14:30 : /m8-commit
    section Day 3
      09:00 : /m8-describe-pr
      09:30 : PR submitted
      10:00 : Team review using memory/
```

**Result:**
- 3 days from idea to PR
- Fully documented in memory/
- Team can understand all decisions
- Next OAuth2 provider takes 1 day (memory!)
