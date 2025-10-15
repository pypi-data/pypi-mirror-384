---
sidebar_position: 4
---

# Phase 4: Commit with `/m8-commit`
Create conventional commits based on session context.

### Commit Process

```mermaid
graph LR
    A[commit] --> B[Review Session History]
    B --> C[Run git status]
    C --> D[Analyze Changes]
    D --> E[Draft Commit Messages]
    E --> F[Present Plan to User]
    F --> G{User Approves?}
    G -->|Yes| H[Execute Commits]
    G -->|No| E
    H --> I[Show git log]

    style A fill:#f3e5f5
    style H fill:#c8e6c9
```

### Commit Guidelines

**mem8 follows best practices:**
- **Conventional commits** format (feat:, fix:, docs:, etc.)
- **Focused commits** - groups related changes
- **Clear messages** - explains why, not just what
- **User attribution** - commits are authored by you, not Claude
- **No AI mentions** - professional commit history
