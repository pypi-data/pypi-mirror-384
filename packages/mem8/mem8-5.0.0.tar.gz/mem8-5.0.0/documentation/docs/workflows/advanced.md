---
sidebar_position: 6
---

## Advanced Workflows

### Team Collaboration

```mermaid
graph TB
    A[Dev 1: Research] --> B[commits to memory/shared/research/]
    B --> C[Dev 2: git pull]
    C --> D[Dev 2: /m8-browse-memories]
    D --> E[Dev 2: Build on research]
    E --> F[Dev 2: Create plan]
    F --> G[commits to memory/shared/plans/]
    G --> H[Dev 1: git pull]
    H --> I[Dev 1: /m8-implement]

    style B fill:#e1f5ff
    style F fill:#fff4e1
    style I fill:#e8f5e9
```

### Context Accumulation

Each phase builds on previous work:

```mermaid
graph LR
    A[Research Document] -->|References| B[Plan]
    B -->|Guides| C[Implementation]
    C -->|Describes| D[Commits]
    D -->|Explains| E[PR]
    E -.Future Reference.-> F[Next Research]
    F -.Builds On.-> A

    style A fill:#e1f5ff
    style B fill:#fff4e1
    style C fill:#e8f5e9
    style D fill:#f3e5f5
    style E fill:#fce4ec
```

### Multi-Feature Development

```mermaid
gantt
    title Parallel Feature Development with mem8
    dateFormat HH:mm
    section Feature A
    Research      :a1, 00:00, 30m
    Plan         :a2, after a1, 20m
    Implement    :a3, after a2, 2h
    section Feature B
    Research     :b1, 00:15, 30m
    Plan        :b2, after b1, 20m
    Implement   :b3, after b2, 2h
    section Integration
    Test        :c1, after a3 b3, 30m
    PR          :c2, after c1, 15m
```

## Context Engineering Architecture

mem8 implements [Anthropic's context engineering principles](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) to maximize Claude's effectiveness while minimizing context usage.

### The Context Economy

```mermaid
graph TD
    A[Finite Context Window] --> B{Context Strategy}
    B -->|❌ Naive| C[Load Everything]
    C --> D[Context Overflow]
    C --> E[Slow Performance]
    C --> F[Loss of Focus]

    B -->|✅ mem8| G[Just-in-Time Context]
    G --> H[Parallel Sub-Agents]
    G --> I[Structured Notes]
    G --> J[Persistent Memory]

    H --> K[Efficient Exploration]
    I --> L[Compact References]
    J --> M[Build on Past Work]

    K --> N[High-Signal Results]
    L --> N
    M --> N

    style A fill:#ffebee
    style G fill:#e8f5e9
    style N fill:#c8e6c9
```

### mem8's Context Engineering Approach

#### 1. Sub-Agent Architecture

Instead of loading entire codebases into context, mem8 spawns specialized sub-agents:

```mermaid
graph TB
    Main[Main Claude Agent<br/>Synthesis & Orchestration] --> Sub1[codebase-locator<br/>Find Files]
    Main --> Sub2[codebase-analyzer<br/>Deep Dive]
    Main --> Sub3[thoughts-locator<br/>Find Docs]

    Sub1 -.Lightweight Results.-> R1[File paths only]
    Sub2 -.Focused Analysis.-> R2[Specific insights]
    Sub3 -.Relevant Links.-> R3[Document refs]

    R1 --> Synthesis[Main Agent Synthesis]
    R2 --> Synthesis
    R3 --> Synthesis

    Synthesis --> Output[High-Signal Output<br/>Minimal Tokens]

    style Main fill:#e3f2fd
    style Synthesis fill:#fff3e0
    style Output fill:#c8e6c9
```

**Key Benefits:**
- **Parallel Exploration** - Multiple agents search simultaneously
- **Context Isolation** - Each agent has focused context
- **Result Compaction** - Only high-signal findings returned
- **Scalable** - Works on codebases of any size

#### 2. Structured Note-Taking

mem8 creates persistent, structured documents that serve as lightweight context:

```mermaid
graph LR
    A[Research Phase] -->|Creates| B[Research Doc]
    B -->|References| C[Plan Phase]
    C -->|Creates| D[Plan Doc]
    D -->|Guides| E[Implementation]

    B -.Key Findings Only.-> F[~2KB]
    D -.Concrete Steps.-> G[~5KB]

    F --> H[Future Context]
    G --> H

    style B fill:#e1f5ff
    style D fill:#fff4e1
    style H fill:#c8e6c9
```

**vs Loading Full Files:**
- **Research doc** (~2KB) vs **Full codebase** (~500KB+)
- **Plan doc** (~5KB) vs **Re-analyzing everything** (~1MB+)
- **File reference** (`auth.py:45`) vs **Full file content** (~10KB)

#### 3. Just-in-Time Context Retrieval

Context loaded only when needed:

```mermaid
sequenceDiagram
    participant C as Claude
    participant M as mem8 Memory
    participant FS as Filesystem

    Note over C: Starting implementation
    C->>M: Do we have research on auth?
    M->>C: Yes: memory/shared/research/auth.md
    C->>FS: Load research doc (2KB)

    Note over C: Need code details
    C->>C: Research mentions auth.py:45
    C->>FS: Read auth.py lines 40-60 (0.5KB)

    Note over C: vs Naive Approach
    Note over C: ❌ Load entire codebase (500KB+)
    Note over C: ❌ All past research (100KB+)
    Note over C: ❌ Context overflow!
```

#### 4. Compaction Through Synthesis

```mermaid
graph TD
    A[Sub-Agent 1<br/>Found 50 files] --> D[Main Agent]
    B[Sub-Agent 2<br/>Analyzed 10 files] --> D
    C[Sub-Agent 3<br/>5 past docs] --> D

    D --> E[Synthesize Findings]
    E --> F[Extract High-Signal]
    F --> G[Research Document<br/>~2KB, 95% signal]

    style A fill:#ffebee
    style B fill:#ffebee
    style C fill:#ffebee
    style G fill:#c8e6c9

    H[❌ Raw Data<br/>~500KB] -.vs.-> G
```

### Anthropic's Principles → mem8 Implementation

| Principle | mem8 Implementation |
|-----------|---------------------|
| **Minimal Context** | File references (`file:line`) not full files |
| **Just-in-Time** | Load research docs only when relevant |
| **Sub-Agents** | Parallel exploration with `codebase-locator`, etc. |
| **Structured Notes** | Research → Plan → Implement documents |
| **Compaction** | Synthesize sub-agent findings into concise docs |
| **Autonomous Navigation** | Agents explore codebase independently |
| **Lightweight References** | Links to thoughts, not full content |

### Context Budget Example

**Feature: Add OAuth2 Support**

```mermaid
gantt
    title Context Usage Across Development Cycle
    dateFormat X
    axisFormat %s

    section Research
    Sub-Agents Spawn   :a1, 0, 10
    Results Synthesis  :a2, 10, 5
    Document Creation  :a3, 15, 5

    section Plan
    Load Research Doc  :b1, 20, 2
    Codebase Analysis  :b2, 22, 8
    Plan Generation    :b3, 30, 5

    section Implement
    Load Plan Doc      :c1, 35, 2
    Phase 1 Impl       :c2, 37, 15
    Phase 2 Impl       :c3, 52, 15
    Phase 3 Impl       :c4, 67, 10

    section Total
    Context Efficient  :milestone, 77, 0
```

**Context Savings:**
- **Without mem8:** ~2M tokens (reload codebase each time)
- **With mem8:** ~200K tokens (use persistent documents)
- **10x reduction** in context usage

## Why Memory-First Development Works

### Context Preservation

```mermaid
mindmap
  root((mem8))
    Research Documents
      File references
      Architecture insights
      Historical context
      Git metadata
    Plans
      Executable roadmaps
      Progress tracking
      Decision rationale
      Team communication
    Implementation
      Plan-aware
      Resumable
      Verified
      Documented
    Memory
      Search past work
      Build on research
      Avoid repetition
      Team knowledge
```

### Compounding Knowledge

Each cycle adds to your project's knowledge base:

1. **First Feature:** Research from scratch → plan → implement
2. **Second Feature:** Browse past research → faster planning → reuse patterns
3. **Third Feature:** Rich context → precise plans → confident implementation
4. **Nth Feature:** Comprehensive memory → minimal research → rapid delivery

