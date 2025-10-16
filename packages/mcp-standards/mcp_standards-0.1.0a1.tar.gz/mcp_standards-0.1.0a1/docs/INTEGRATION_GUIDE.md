# Integration Guide - Universal Learning System

**Setup guide for Claude Desktop, Claude Code, and other AI coding assistants**

---

## Overview

This guide covers how to set up the universal learning system to work with:
- Claude Desktop / Claude Code (primary)
- Claude Projects (web platform)
- Other AI coding tools (Cursor, Copilot, Windsurf, Cline)

---

## Quick Start (5 Minutes)

### 1. Install & Configure MCP Server

```bash
git clone https://github.com/airmcp-com/mcp-standards.git
cd mcp-standards
uv sync
```

### 2. Restart Claude Desktop

```bash
# macOS
# Cmd+Q to quit, then reopen
```

### 3. Test It Works

```
# In Claude Desktop chat:
add_episode(
  name="Setup Test",
  content="Universal learning system operational!",
  source="setup"
)
```

---

## Integration 1: Claude Desktop / Claude Code

### What You Get

✅ **Automatic Learning**: Corrections captured via PostToolUse hooks
✅ **Pattern Detection**: After 3+ corrections, preferences promoted
✅ **Auto-Update CLAUDE.md**: Config files updated intelligently
✅ **Cross-Project Sync**: Global patterns promoted automatically

### File Hierarchy

Claude loads CLAUDE.md files in this order:

```
1. ~/.claude/CLAUDE.md              # Your global preferences
2. ../CLAUDE.md                     # Monorepo parent (if exists)
3. ./CLAUDE.md                      # Project root
4. ./CLAUDE.local.md                # Local overrides (gitignored)
5. ./src/*/CLAUDE.md                # Nested directories
```

**Priority**: Most specific (nested) wins

### Initial Setup

#### Create User Global Config

```bash
mkdir -p ~/.claude
cat > ~/.claude/CLAUDE.md << 'EOF'
# My Global Preferences

## Coding Style
- Use type hints in Python
- Prefer async/await over callbacks
- Write docstrings for public APIs

## Workflow
- Run tests before committing
- Format code with auto-formatter

## Tools
- Use uv for Python package management
- Use pytest for testing
EOF
```

#### Create Project Config (Optional)

```bash
# In your project root
cat > CLAUDE.md << 'EOF'
# Project Name

## Tech Stack
- Python 3.11
- FastAPI
- PostgreSQL

## Commands
- Test: `pytest`
- Run: `uvicorn app.main:app`
- Format: `black . && isort .`

## Project-Specific Rules
- Use Pydantic for data validation
- Keep routes in `app/routers/`
- Store schemas in `app/schemas/`
EOF
```

### How Learning Works

1. **User corrects Claude**: "Use • bullets not -"
2. **System detects pattern**: Correction captured via hook
3. **After 3 occurrences**: Promoted to preference in database
4. **Auto-update triggered**: `./CLAUDE.md` updated automatically
5. **User notified**: MCP notification with file path
6. **Future sessions**: Claude respects learned rule

### Verify It's Working

```python
# Check if hooks are active
list_recent()

# Should show captured tool executions

# Check learned preferences
# (This will be available after Week 3 implementation)
```

---

## Integration 2: Claude Projects (Web Platform)

### What You Get

✅ **200K Context Window**: Upload learned preferences
✅ **Knowledge Base**: Persistent across web chats
✅ **Team Sharing**: Share project knowledge with team

### Current Limitation

⚠️ **No API available yet** - Manual upload workflow required

### Setup Workflow

#### 1. Export Learned Preferences

The system periodically exports to:
```
~/.mcp-standards/exports/project-knowledge-YYYYMMDD.md
```

You'll receive a notification when export is ready.

#### 2. Upload to Claude Projects

1. Open [claude.ai/projects](https://claude.ai/projects)
2. Select your project (or create new)
3. Click "Add to Knowledge"
4. Upload the exported Markdown file
5. Claude.ai chats now have access to learned preferences

#### 3. Keep in Sync

**Manual**: Re-export weekly and re-upload

**Future**: When Anthropic releases Projects API, direct sync will be possible

### Export Format

The exported file contains:

```markdown
# Learned Coding Preferences

_Auto-generated: 2025-10-13 14:30_

## Formatting
- 🟢 Use • (bullet) not - (dash) for bullet points
  - Confidence: 95%
  - Used 12 times

## Python
- 🟢 Use uv not pip for package management
  - Confidence: 100%
  - Used 45 times
```

Confidence indicators:
- 🟢 High (90%+)
- 🟡 Medium (70-89%)
- 🟠 Low (50-69%)

---

## Integration 3: Cross-Tool Compatibility

### Supported Tools

| Tool | Support Level | Config File | Auto-Update |
|------|--------------|-------------|-------------|
| **Claude Desktop/Code** | ✅ Primary | CLAUDE.md | Yes (always) |
| **Cursor** | ✅ Full | .cursor/rules/*.mdc | Optional |
| **GitHub Copilot** | ✅ Full | .github/copilot-instructions.md | Optional |
| **Windsurf** | ✅ Full | .windsurf/rules/*.md | Optional |
| **Cline/Roo** | ✅ Full | .clinerules/*.md | Optional |
| **EditorConfig** | ✅ Standard | .editorconfig | Yes (formatting) |
| **Prettier** | ✅ Standard | .prettierrc | Yes (code style) |

### Enable Cross-Tool Updates

By default, only CLAUDE.md is auto-updated.

To enable updates for other tools:

```python
# Set preference (future API)
set_config(
  "cross_tool_updates_enabled": True,
  "tools_to_update": ["cursor", "copilot", "editorconfig"]
)
```

### Setup Other Tools

#### Cursor IDE

1. **Install Cursor**: [cursor.sh](https://cursor.sh)
2. **Create rules file**:
```bash
mkdir -p .cursor/rules
cat > .cursor/rules/learned.mdc << 'EOF'
---
globs: ["**/*"]
---

# Auto-Learned Rules

This file is auto-updated by the learning system.
Manual edits above this line are preserved.

<!-- AUTO-GENERATED BELOW -->
EOF
```

3. **Enable in system**: Add "cursor" to `tools_to_update`

#### GitHub Copilot

1. **Install Copilot**: GitHub subscription required
2. **Create instructions file**:
```bash
mkdir -p .github/instructions
cat > .github/copilot-instructions.md << 'EOF'
# Auto-Learned Coding Instructions

Manual instructions (preserved on update):
- [Your manual rules here]

Auto-learned instructions (updated automatically):
<!-- AUTO-GENERATED BELOW -->
EOF
```

3. **Enable in system**: Add "copilot" to `tools_to_update`

#### Windsurf

1. **Install Windsurf**: [windsurf.com](https://windsurf.com)
2. **Create rules directory**:
```bash
mkdir -p .windsurf/rules
cat > .windsurf/rules/learned.md << 'EOF'
# Auto-Learned Rules

Manual rules above this line.

<!-- AUTO-GENERATED BELOW -->
EOF
```

3. **Enable in system**: Add "windsurf" to `tools_to_update`

---

## Common Patterns

### Pattern 1: Resume Bullet Formatting

**Problem**: Claude keeps using wrong bullet style

**Solution**: System learns after 3 corrections

```
Correction 1: "Use • bullets not -"
  → Captured in database

Correction 2: "Remember, use • not -"
  → Pattern count: 2

Correction 3: "Always use • for bullets"
  → Promoted to preference
  → CLAUDE.md updated automatically
  → .editorconfig updated (if formatting rule)
```

**Result**: Future sessions use correct bullet style

### Pattern 2: Tool Preference

**Problem**: Claude suggests pip instead of uv

**Solution**: Explicit preference learning

```
Correction: "Use uv not pip for this project"
  → Detected as tool substitution
  → High confidence (1.0)
  → Project-specific preference
  → ./CLAUDE.md updated
```

**Result**: Claude suggests uv in this project

### Pattern 3: Workflow Pattern

**Problem**: Forgetting to run tests before commit

**Solution**: Behavioral pattern detection

```
Session 1: Edit → User manually runs tests → Commit
Session 2: Edit → User manually runs tests → Commit
Session 3: Edit → User manually runs tests → Commit
  → Pattern detected: "Always run tests after edits"
  → Workflow preference created
  → CLAUDE.md updated
```

**Result**: Claude reminds to run tests

---

## Troubleshooting

### Learning Not Working

**Check PostToolUse hook is active**:
```bash
cat ~/Library/Application\ Support/Claude/hooks.json
# Should show PostToolUse hook configured
```

**Check MCP server is running**:
```bash
ps aux | grep "mcp-standards"
# Should show running process
```

**Check database**:
```bash
sqlite3 ~/.mcp-standards/knowledge.db "SELECT COUNT(*) FROM tool_logs;"
# Should show >0 if capturing executions
```

### CLAUDE.md Not Updating

**Check auto-update is enabled**:
```python
# In Claude chat:
get_config("auto_update_enabled")
# Should return True
```

**Check logs**:
```bash
# Check server logs if needed
tail -f ~/.mcp-standards/logs/server.log
```

**Manual trigger**:
```python
# Force update
generate_claudemd(
  output_file="./CLAUDE.md",
  project_path="/path/to/project",
  min_confidence=0.7
)
```

### Cross-Tool Updates Not Working

**Verify tool configs exist**:
```bash
# For Cursor
ls .cursor/rules/

# For Copilot
ls .github/copilot-instructions.md
```

**Check enabled tools**:
```python
get_config("tools_to_update")
# Should list enabled tools
```

### Conflicts Between Tools

**Priority order** (what wins in conflicts):
1. Most specific CLAUDE.md (nested directory)
2. CLAUDE.local.md
3. Project CLAUDE.md
4. Cross-tool standards (.editorconfig, .prettierrc)
5. Other AI tool configs

**Resolution**: Most specific always wins

---

## Advanced Configuration

### Custom Update Rules

```python
# Configure which categories trigger updates
set_update_rules({
  "formatting": ["editorconfig", "prettier"],
  "tool_preference": ["CLAUDE.md"],
  "workflow": ["CLAUDE.md", "project-docs"],
  "code_style": ["CLAUDE.md", "eslint", "prettier"]
})
```

### Notification Preferences

```python
# Configure when to notify
set_notification_preferences({
  "on_pattern_learned": True,
  "on_preference_promoted": True,
  "on_claude_md_updated": True,
  "on_cross_tool_updated": False,  # Too noisy
  "notification_channel": "mcp"     # or "file", "both"
})
```

### Backup Strategy

Auto-backups are created before every update:
```
./CLAUDE.md.20251013_143015.bak
```

**Restore a backup**:
```bash
cp CLAUDE.md.20251013_143015.bak CLAUDE.md
```

**Configure backup retention**:
```python
set_config("backup_retention_days", 30)
# Automatically clean backups older than 30 days
```

---

## Best Practices

### ✅ DO

- **Commit** `CLAUDE.md` to git (share with team)
- **Gitignore** `CLAUDE.local.md` (personal notes)
- **Review** auto-updates before accepting
- **Use** nested CLAUDE.md for directory-specific context
- **Keep** CLAUDE.md files concise (<1000 tokens)
- **Update** cross-tool configs when team uses multiple tools

### ❌ DON'T

- **Don't** put sensitive info in CLAUDE.md
- **Don't** make CLAUDE.md files too long
- **Don't** disable backups
- **Don't** manually edit auto-generated sections
- **Don't** ignore update notifications
- **Don't** commit CLAUDE.local.md

---

## Examples

### Example 1: Single Developer, Claude Only

```bash
# Setup
~/.claude/CLAUDE.md          # Personal global preferences
~/projects/myapp/CLAUDE.md   # Project-specific rules

# Learning enabled
# Auto-updates: CLAUDE.md only
# Cross-tool updates: Disabled
```

### Example 2: Team Using Multiple Tools

```bash
# Setup
~/.claude/CLAUDE.md                         # Personal
~/team-project/CLAUDE.md                    # Team (committed)
~/team-project/.editorconfig                # Cross-tool standard
~/team-project/.prettierrc                  # Code formatting
~/team-project/.cursor/rules/learned.mdc    # Cursor users
~/team-project/.github/copilot-instructions.md  # Copilot users

# Learning enabled
# Auto-updates: CLAUDE.md + cross-tool standards
# Cross-tool updates: Optional per developer
```

### Example 3: Monorepo

```bash
# Setup
~/.claude/CLAUDE.md                 # Personal
~/monorepo/CLAUDE.md                # Monorepo-wide
~/monorepo/services/api/CLAUDE.md   # API-specific
~/monorepo/services/web/CLAUDE.md   # Web-specific

# Priority when in ~/monorepo/services/api/:
# 1. ./CLAUDE.md (API-specific)
# 2. ../../CLAUDE.md (monorepo)
# 3. ~/.claude/CLAUDE.md (personal)
```

---

## Migration Guides

### From Manual CLAUDE.md Management

**Before**: Manually edit CLAUDE.md after corrections

**After**: System auto-updates CLAUDE.md

**Migration**:
1. Keep existing CLAUDE.md as-is
2. Enable auto-learning
3. System will append new learnings
4. Review and merge manually if needed

### From Other AI Assistants

#### From Cursor

**Copy rules to CLAUDE.md**:
```bash
cat .cursorrules >> CLAUDE.md
# Or for modern Cursor:
cat .cursor/rules/*.mdc >> CLAUDE.md
```

Then enable learning system.

#### From GitHub Copilot

**Copy instructions to CLAUDE.md**:
```bash
cat .github/copilot-instructions.md >> CLAUDE.md
```

Then enable learning system.

---

## Future Enhancements

### Planned Features

- ✅ Claude Projects API integration (when available)
- ✅ Real-time sync across tools
- ✅ Conflict resolution UI
- ✅ Learning analytics dashboard
- ✅ Export to other formats (JSON, YAML)
- ✅ Team knowledge sharing

### Roadmap

- **Week 1**: Universal config discovery
- **Week 2**: Enhanced pattern learning
- **Week 3**: Auto-update orchestration (you are here)
- **Week 4**: Documentation & testing

---

## Support

### Documentation
- [CONFIG_STANDARDS.md](CONFIG_STANDARDS.md) - Complete config file reference
- [SELF-LEARNING-PRD.md](SELF-LEARNING-PRD.md) - Product requirements
- [README.md](../README.md) - Main documentation

### Issues
Report issues at: https://github.com/airmcp-com/mcp-standards/issues

---

**Last Updated**: 2025-10-13
**Status**: Documentation complete, implementation in progress
