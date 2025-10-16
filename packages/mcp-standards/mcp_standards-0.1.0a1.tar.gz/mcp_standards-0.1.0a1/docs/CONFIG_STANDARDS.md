# Configuration File Standards - Universal Learning System

**Complete reference for all AI coding assistant configuration files**

---

## Overview

Each AI coding assistant uses its own configuration file conventions. This document provides a comprehensive mapping of all supported formats, their priority levels, and how they're discovered and merged.

**Key Insight**: There is **NO universal standard** across AI coding tools. This system supports all major formats.

---

## Supported Configuration Files

### Priority Matrix

| Priority | File Pattern | Tool | Status | Purpose |
|----------|-------------|------|--------|---------|
| **100** | `./**/CLAUDE.md` | Claude | Official ✅ | Most specific (nested directories) |
| **90** | `./CLAUDE.local.md` | Claude | Official ✅ | Local overrides (gitignored) |
| **80** | `./CLAUDE.md` | Claude | Official ✅ | Project root (committed to git) |
| **70** | `~/.claude/CLAUDE.md` | Claude | Official ✅ | User global (all projects) |
| **60** | `./.editorconfig` | Cross-tool | Standard ✅ | Indentation, encoding, line endings |
| **55** | `./.prettierrc*` | Cross-tool | Standard ✅ | Code formatting (quotes, semicolons, etc.) |
| **55** | `./.eslintrc*` | Cross-tool | Standard ✅ | JavaScript/TypeScript linting rules |
| **50** | `./.cursor/rules/*.mdc` | Cursor | Official ✅ | Modern Cursor rules (MDC format) |
| **50** | `./.github/copilot-instructions.md` | Copilot | Official ✅ | Repository-wide instructions |
| **50** | `./.github/instructions/*.instructions.md` | Copilot | Official ✅ | Context-specific instructions |
| **50** | `./.windsurf/rules/*.md` | Windsurf | Official ✅ | Windsurf AI rules |
| **45** | `./.clinerules/*.md` | Cline/Roo | Official ✅ | Multi-file rules |
| **40** | `./.cursorrules` | Cursor | Deprecated ⚠️ | Legacy (still supported) |
| **40** | `./.clinerules` | Cline/Roo | Official ✅ | Single-file rules |
| **30** | `./README.md` | Documentation | Standard ✅ | Project context |
| **30** | `./CONTRIBUTING.md` | Documentation | Standard ✅ | Contribution guidelines |
| **20** | `./package.json` | JavaScript | Standard ✅ | Dependencies, scripts |
| **20** | `./pyproject.toml` | Python | Standard ✅ | Dependencies, project metadata |
| **20** | `./tsconfig.json` | TypeScript | Standard ✅ | TypeScript configuration |

### Priority Rules

1. **Most specific wins**: Nested `CLAUDE.md` files override parent directories
2. **Local overrides global**: `CLAUDE.local.md` > `CLAUDE.md` > `~/.claude/CLAUDE.md`
3. **Claude-native first**: CLAUDE.md files take precedence over other tools
4. **Cross-tool standards**: `.editorconfig`, `.prettierrc` respected across tools
5. **Tool-specific last**: Other AI assistant configs for compatibility only

---

## Tool-by-Tool Breakdown

### Claude Desktop / Claude Code

**Official Format**: `CLAUDE.md`

#### File Locations (in loading order):

```
1. ~/.claude/CLAUDE.md              # User global (lowest priority)
   ↓ merged with
2. ../CLAUDE.md                     # Parent directory (monorepos)
   ↓ merged with
3. ./CLAUDE.md                      # Project root
   ↓ merged with
4. ./CLAUDE.local.md                # Local overrides (gitignored)
   ↓ merged with
5. ./src/CLAUDE.md                  # Nested directory (highest priority)
```

#### Format Specification:
- **Format**: Markdown
- **Structure**: Free-form with recommended sections:
  - Tech Stack
  - Project Structure
  - Commands
  - Coding Standards
  - Preferences

#### Example:
```markdown
# Project Name

## Tech Stack
- Python 3.11
- FastAPI
- PostgreSQL

## Coding Standards
- Use type hints
- Follow PEP 8
- Write docstrings for public functions

## Commands
- Run tests: `pytest`
- Format code: `black .`
```

**Documentation**: [Claude Code settings](https://docs.claude.com/en/docs/claude-code/settings)

---

### Cursor IDE

**Official Formats**: `.cursor/rules/*.mdc` (modern) or `.cursorrules` (legacy)

#### Modern Approach (Recommended):
```
.cursor/
  rules/
    general.mdc
    python.mdc
    testing.mdc
```

**MDC Format**: Markdown with YAML frontmatter
```markdown
---
globs: ["**/*.py"]
---

# Python Coding Rules

- Use type hints
- Follow PEP 8
```

#### Legacy Approach:
`.cursorrules` - Single file in project root

**Format**: Plain text or Markdown

**Status**: Deprecated but still works

**Documentation**: [Cursor Rules](https://docs.cursor.com/context/rules)

---

### GitHub Copilot

**Official Format**: `.github/copilot-instructions.md`

#### File Location:
```
.github/
  copilot-instructions.md           # Repository-wide
  instructions/
    backend.instructions.md         # Context-specific
    frontend.instructions.md
```

#### Format Specification:
- **Format**: Markdown
- **Structure**: One instruction per paragraph (separated by blank lines)
- **Frontmatter**: Optional YAML to specify file/directory scope

#### Example:
```markdown
Use Python type hints for all function parameters and return values.

Follow PEP 8 style guide with 88-character line length.

Write docstrings in Google style format.
```

**Documentation**: [Adding custom instructions](https://docs.github.com/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot)

---

### Windsurf (Codeium)

**Official Format**: `.windsurf/rules/*.md`

#### File Location:
```
.windsurf/
  rules/
    coding-standards.md
    project-context.md
```

**Format**: Markdown files

**GUI**: Windsurf provides a GUI wrapper for editing rules

**Documentation**: [Windsurf Rules](https://docs.windsurf.com/windsurf/getting-started)

---

### Cline / Roo Coder

**Official Formats**: `.clinerules` or `.clinerules/*.md`

#### Single File Approach:
`.clinerules` - Plain text in project root

#### Multi-File Approach:
```
.clinerules/
  coding.md
  testing.md
  deployment.md
```

#### Roo Coder Extensions:
- `.clinerules-architect` - Architecture mode
- `.clinerules-coder` - Coding mode
- `.clinerules-debug` - Debug mode
- `.roomodes` - Custom mode definitions

**Format**: Markdown or plain text

**Documentation**: Community-driven (see GitHub)

---

### Cross-Tool Standards

#### .editorconfig
**Purpose**: Indentation, encoding, line endings
**Supported by**: VS Code, JetBrains IDEs, Sublime, Atom, Vim, Emacs

```ini
root = true

[*]
indent_style = space
indent_size = 2
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true

[*.py]
indent_size = 4

[Makefile]
indent_style = tab
```

**Documentation**: [editorconfig.org](https://editorconfig.org/)

---

#### .prettierrc
**Purpose**: Code formatting (JavaScript, TypeScript, CSS, JSON, Markdown)
**Supported by**: VS Code, Sublime, Atom, JetBrains IDEs

```json
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 88
}
```

**Documentation**: [prettier.io](https://prettier.io/docs/en/configuration.html)

---

#### .eslintrc
**Purpose**: JavaScript/TypeScript linting rules
**Supported by**: VS Code, Sublime, JetBrains IDEs

```json
{
  "extends": ["eslint:recommended"],
  "rules": {
    "indent": ["error", 2],
    "quotes": ["error", "single"],
    "semi": ["error", "always"]
  }
}
```

**Documentation**: [eslint.org](https://eslint.org/docs/user-guide/configuring/)

---

## Discovery Algorithm

### How the System Finds Config Files

```python
1. Start in current directory
2. Recursively search for all config patterns
3. Resolve symlinks and relative paths
4. Calculate priority score for each file
5. Sort by priority (highest first)
6. Parse each file with appropriate parser
7. Merge rules (most specific wins)
8. Return unified ProjectContext
```

### Example Discovery Output

```
Discovered Configuration Files:
  [100] ./src/components/CLAUDE.md
  [90]  ./CLAUDE.local.md
  [80]  ./CLAUDE.md
  [70]  ~/.claude/CLAUDE.md
  [60]  ./.editorconfig
  [55]  ./.prettierrc.json
  [50]  ./.cursor/rules/python.mdc
  [50]  ./.github/copilot-instructions.md
  [40]  ./.cursorrules (deprecated)
  [30]  ./README.md
  [20]  ./package.json
```

---

## Merging Strategy

### Conflict Resolution

When multiple config files specify conflicting rules:

1. **Higher priority wins** (by file priority score)
2. **More specific wins** (nested directory > parent directory)
3. **Explicit wins over implicit** (declared rule > inferred pattern)
4. **Recent wins over old** (if same priority, use newest)

### Example Conflict:

```
~/.claude/CLAUDE.md:        "Use 2-space indentation"
./CLAUDE.md:                "Use 4-space indentation"
./src/CLAUDE.md:            "Use tabs"
./.editorconfig:            indent_size = 2

Resolution:
  → Use tabs (from ./src/CLAUDE.md - highest priority: 100)
  → .editorconfig ignored for this conflict
```

---

## Best Practices

### For Claude Desktop/Code Users:

✅ **DO**:
- Use `CLAUDE.md` in project root (commit to git)
- Use `~/.claude/CLAUDE.md` for personal global preferences
- Use `CLAUDE.local.md` for temporary/private notes (gitignore)
- Use nested `CLAUDE.md` files for directory-specific context

❌ **DON'T**:
- Don't commit `CLAUDE.local.md` to git
- Don't put sensitive info in CLAUDE.md (committed files)
- Don't make CLAUDE.md files too long (>1000 tokens impacts context)

### For Multi-Tool Teams:

✅ **DO**:
- Use CLAUDE.md as primary (works with this learning system)
- Use `.editorconfig` for basic formatting (cross-tool standard)
- Use `.prettierrc` for code style (widely supported)
- Document which AI tools your team uses

❌ **DON'T**:
- Don't maintain duplicate rules across multiple formats
- Don't forget to update all configs when changing standards
- Don't assume everyone uses the same AI coding tool

### For Learning System:

✅ **DO**:
- Primary updates: Always update CLAUDE.md
- Secondary updates: Update cross-tool standards (`.editorconfig`, etc.)
- Tertiary updates: Optionally update other tools (user preference)

❌ **DON'T**:
- Don't update other tools' configs without user opt-in
- Don't silently overwrite manual edits
- Don't skip creating backups before updates

---

## File Templates

### CLAUDE.md Template

```markdown
# Project Name

## Tech Stack
- [List your technologies]

## Project Structure
- `src/` - [Description]
- `tests/` - [Description]

## Commands
- Build: `[command]`
- Test: `[command]`
- Deploy: `[command]`

## Coding Standards
- [Your standards]

## Preferences
- [AI assistant preferences]
```

### .cursor/rules/general.mdc Template

```markdown
---
globs: ["**/*"]
---

# General Coding Rules

- Write clear, self-documenting code
- Add comments for complex logic
- Keep functions small and focused
```

### .github/copilot-instructions.md Template

```markdown
Use type hints for all function parameters.

Follow project coding standards in CONTRIBUTING.md.

Write unit tests for all new features.

Update documentation when changing APIs.
```

---

## Future Standards

### Proposed: .ai-rules (Universal Format)

**Status**: Not yet standard, but proposed for cross-tool compatibility

**Idea**: Single format that all AI coding tools could adopt

```yaml
# .ai-rules.yaml
version: "1.0"
tools: ["claude", "cursor", "copilot"]

rules:
  coding_style:
    - "Use type hints"
    - "Follow PEP 8"

  preferences:
    - "Explain complex logic"
    - "Suggest performance improvements"
```

**Watch**: Community initiatives for standardization

---

## References

- [Claude Code Documentation](https://docs.claude.com/en/docs/claude-code/)
- [Cursor Rules](https://docs.cursor.com/context/rules)
- [GitHub Copilot Custom Instructions](https://docs.github.com/copilot/customizing-copilot)
- [EditorConfig Specification](https://editorconfig.org/)
- [Prettier Documentation](https://prettier.io/)
- [ESLint Configuration](https://eslint.org/docs/user-guide/configuring/)

---

**Last Updated**: 2025-10-13
**Part of**: Universal Learning System for AI Coding Assistants
