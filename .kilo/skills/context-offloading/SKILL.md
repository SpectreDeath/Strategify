---
name: context-offloading
description: "Use when: saving agent context for future sessions, retrieving historical context, tracking decisions across sessions, enabling cross-session memory for agents, or maintaining project memory. Triggers: 'save context', 'remember', 'memory', 'prior context', 'load history', 'session memory', 'project memory'. NOT for: ephemeral context only, single-session tasks, or when context should not persist."
---

# Context Offloading

Enable agents to save and retrieve context across sessions, creating persistent memory for coding agents. This skill stores decisions, session logs, and project identity in human-readable markdown files.

## When to Use This Skill

Use this skill when:
- Saving important decisions and context for future sessions
- Retrieving historical context before answering questions
- Tracking architecture decisions across sessions
- Enabling cross-session memory for agents
- Onboarding new agents with project context

Do NOT use this skill when:
- Ephemeral context only
- Single-session tasks
- Context should not persist
- Project already has memory system

## Input Format

```yaml
context_request:
  action: string              # "init", "write", "query", "manage"
  content: string             # Context to save (for write)
  tags: array                  # Optional: ["decision", "architecture", "setup"]
  query: string                # Search query (for query)
  context_path: string        # Custom path (optional, default: .context/)
  session_name: string        # Session identifier (optional)
```

## Output Format

```yaml
context_result:
  status: "success" | "error"
  message: string
  written_to: string          # File path if written
  results: array              # Query results
  context_path: string        # Where context is stored
  files_created: array        # Files created during init
```

## Capabilities

### 1. Initialize Context Storage (5 min)

- Create `.context/` directory structure
- Create `identity.md` for project purpose, stack, conventions
- Create `decisions.md` for architecture decisions
- Create `session-logs/` for episodic notes
- Create `.gitignore` to exclude from version control

### 2. Write Memory Note (5 min)

- Accept context content with optional tags
- Route to appropriate file (identity, decisions, session-logs)
- Append with timestamp and session identifier
- Handle markdown formatting

### 3. Query Context (10 min)

- Accept search query string
- Search all context files using grep
- Rank results by relevance
- Return results with source file and timestamp
- Highlight matching content

### 4. Manage Session Logs (5 min)

- Create daily session files (YYYY-MM-DD.md)
- Archive old sessions
- List recent sessions
- Clean up based on retention policy

## File Structure

```
.context/
├── .gitignore           # Exclude from Git
├── identity.md         # Project purpose, stack, conventions
├── decisions.md        # Architecture decisions, policies
├── session-logs/       # Episodic notes
│   ├── 2026-04-07.md
│   └── 2026-04-08.md
└── index.md           # Optional: quick reference index
```

## Usage Examples

### Initialize Context Storage
"Set up context storage in my project for persistent memory."

### Write a Decision
"Save this decision: We chose PostgreSQL over MongoDB because of ACID compliance needs for financial data."

### Query Prior Context
"What decisions were made about the database architecture?"
"Find prior context about authentication implementation."

### Session Memory
"Remember that we hit a bug with the payment API - the workaround was to retry with exponential backoff."

## Configuration Options

- `context_path`: Where to store context (default: `.context/`)
- `retention_days`: Days to keep session logs (default: 90)
- `include_gitignore`: Create .gitignore (default: true)
- `auto_init`: Auto-create context on first write if missing

## Constraints

- MUST create human-readable markdown files
- MUST maintain context across sessions
- SHOULD support search functionality
- MUST include timestamps on entries
- SHOULD exclude from version control by default

## Integration Examples

- **Before answering**: Query context for relevant prior decisions
- **After making decision**: Write decision to context
- **On session start**: Load recent session logs for continuity
- **Project onboarding**: Read identity.md for project context

## Dependencies

- Python 3.10+
- Standard library: pathlib, subprocess (grep), datetime, re
- Optional: SQLite (for future FTS5 search enhancement)